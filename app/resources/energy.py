import time
import logging
import calendar
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text

logger = logging.getLogger("MES_API")

class energy_daily_sttlement:
    def __init__(self, servers):
        self.servers = servers

    def fetch(self, date: str):
        """依基準日 date (自動加一天並拼接固定時間 07:02:00) 查詢單筆能量日結算紀錄"""
        try:
            base_date = datetime.strptime(date, "%Y-%m-%d")
            target_dt = base_date + timedelta(days=1)
            target_dt = target_dt.replace(hour=7, minute=2, second=0, microsecond=0)

            srv_SRVAD8_A_energy = self.servers['SRVAD8_A_energy']
            with srv_SRVAD8_A_energy['create_engine'][0].connect() as conn:
                sql = "SELECT * FROM [dbo].[atpower_APMo] WHERE sdate = :target_dt"
                query = conn.execute(text(sql), {"target_dt": target_dt})
                df_result = pd.DataFrame([dict(i._mapping) for i in query])

            if not df_result.empty:
                row_dict = df_result.iloc[0].to_dict()
                for key, val in row_dict.items():
                    if isinstance(val, (datetime, pd.Timestamp)):
                        row_dict[key] = val.isoformat()
                    elif pd.isna(val):
                        row_dict[key] = None
                return row_dict
            return None

        except ValueError as ve:
            raise ValueError(f"日期格式不正確: {str(ve)}")
        except Exception as e:
            logger.exception(f"查詢能量日結算失敗: {str(e)}")
            raise e

    def patch(self, sdate_str: str, update_fields: dict, user_info: dict):
        """依 sdate 進行部分欄位修改 (PATCH)"""
        try:
            if 'T' in sdate_str:
                sdate = datetime.fromisoformat(sdate_str)
            else:
                sdate = datetime.strptime(sdate_str, "%Y-%m-%d %H:%M:%S")

            srv_SRVAD8_A_energy = self.servers['SRVAD8_A_energy']
            
            with srv_SRVAD8_A_energy['create_engine'][0].connect() as conn:
                sql_check = "SELECT 1 FROM [dbo].[atpower_APMo] WHERE sdate = :sdate"
                exists = conn.execute(text(sql_check), {"sdate": sdate}).fetchone()
                if not exists:
                    return {"success": False, "message": f"找不到該日期的能量日結算紀錄: {sdate_str}"}

            set_clauses = []
            params = {"sdate": sdate}
            for key, val in update_fields.items():
                if key == "sdate" or key == "musr" or key == "mdtm":
                    continue
                set_clauses.append(f"[{key}] = :{key}")
                params[key] = val

            set_clauses.append("[musr] = :musr")
            params["musr"] = user_info.get("FTAId", "SYSTEM")
            set_clauses.append("[mdtm] = :mdtm")
            params["mdtm"] = datetime.now()

            with srv_SRVAD8_A_energy['create_engine'][0].begin() as conn:
                sql_update = f"UPDATE [dbo].[atpower_APMo] SET {', '.join(set_clauses)} WHERE sdate = :sdate"
                conn.execute(text(sql_update), params)

                bdate = sdate - timedelta(days=1)
                bdate_str = bdate.strftime("%Y-%m-%d")
                
                self.run_ddCFBCcontrol_conn(
                    conn=conn,
                    bdate_str=bdate_str,
                    musr=user_info.get("FTAId", "SYSTEM")
                )

            with srv_SRVAD8_A_energy['create_engine'][0].connect() as conn:
                sql_select = "SELECT * FROM [dbo].[atpower_APMo] WHERE sdate = :sdate"
                query = conn.execute(text(sql_select), {"sdate": sdate})
                df_result = pd.DataFrame([dict(i._mapping) for i in query])

            if not df_result.empty:
                row_dict = df_result.iloc[0].to_dict()
                for key, val in row_dict.items():
                    if isinstance(val, (datetime, pd.Timestamp)):
                        row_dict[key] = val.isoformat()
                    elif pd.isna(val):
                        row_dict[key] = None
                return {"success": True, "data": row_dict}
            
            return {"success": False, "message": "重新讀取更新後的紀錄失敗"}

        except Exception as e:
            logger.exception(f"更新能量日結算失敗: {str(e)}")
            raise e

    def run_ddCFBCcontrol_conn(self, conn, bdate_str: str, musr: str):
        """生產控制表日結 (ddCFBCcontrol) 計算邏輯"""
        target_date = datetime.strptime(bdate_str, "%Y-%m-%d").date()
        
        start_date = target_date
        _, last_day = calendar.monthrange(target_date.year, target_date.month)
        end_date = target_date.replace(day=last_day)
        logger.info(f"開始執行 ddCFBCcontrol 日結計算區間: {start_date} ~ {end_date}")
        
        current_date = start_date
        while current_date <= end_date:
            exists_any = conn.execute(text(
                "SELECT 1 FROM ddCFBCcontrol WHERE bdate = :bdate"
            ), {"bdate": current_date}).fetchone()
            
            if not exists_any:
                logger.info(f"日期 {current_date} 在 ddCFBCcontrol 中無紀錄，中斷後續計算")
                break
            
            bdate = current_date
            sdate = datetime(bdate.year, bdate.month, 1).date()

            bdate_tomorrow = bdate + timedelta(days=1)
            bdate_tomorrow_str = bdate_tomorrow.strftime("%Y/%m/%d")

            stime = f"{bdate_tomorrow_str} 08:00"
            etime = f"{bdate_tomorrow_str} 08:05"

            m_stime = f"{(sdate + timedelta(days=1)).strftime('%Y/%m/%d')} 08:00"
            m_etime = f"{bdate_tomorrow_str} 08:05"
            real_m_stime = f"{sdate.strftime('%Y/%m/%d')} 08:00"

            vars_map = {"8003001001": 1.0, "8003001002": 1.0, "8003001004": 1.0, "8003001005": 1.0}
            mech_res = conn.execute(text(
                "SELECT m_id, m_tex FROM ic_mechine "
                "WHERE m_id IN ('8003001001','8003001002','8003001004','8003001005')"
            )).fetchall()
            for r in mech_res:
                if r[1] is not None:
                    vars_map[r[0]] = float(r[1])
            
            vars1 = vars_map["8003001001"]
            vars2 = vars_map["8003001002"]
            vars4 = vars_map["8003001004"]
            vars5 = vars_map["8003001005"]

            stop_res = conn.execute(text(
                "SELECT ttime FROM ddCFBCstop WHERE bdate = :bdate AND reason IN ('歲休','計畫停車')"
            ), {"bdate": bdate}).fetchone()
            if stop_res and stop_res[0] is not None:
                stop_cnt = int(stop_res[0])
                stop_p = (1440.0 - stop_cnt) / 1440.0
            else:
                stop_p = 1.0
                stop_cnt = 0

            op_res = conn.execute(text(
                "SELECT operate_min FROM ddCFBCoperate WHERE bdate = :bdate"
            ), {"bdate": bdate}).fetchone()
            if op_res and op_res[0] is not None:
                operate_min = (1440.0 - float(op_res[0])) / 1440.0
            else:
                operate_min = 1.0

            op_sum_res = conn.execute(text(
                "SELECT SUM(operate_min) AS operate_min_sum FROM ddCFBCoperate WHERE bdate BETWEEN :sdate AND :bdate"
            ), {"sdate": sdate, "bdate": bdate}).fetchone()
            if op_sum_res and op_sum_res[0] is not None:
                operate_min_sum = float(op_sum_res[0]) / 60.0
                operate_min_sum_CFBC2 = float(op_sum_res[0])
            else:
                operate_min_sum = 0.0
                operate_min_sum_CFBC2 = 0.0

            es_res = conn.execute(text(
                "SELECT COUNT(RecordTime) AS operate_min_real FROM EnergySummary "
                "WHERE Average > 1000 AND totalcount > 30 AND RecordTime BETWEEN :real_m_stime AND :stime"
            ), {"real_m_stime": real_m_stime, "stime": stime}).fetchone()
            if es_res and es_res[0] is not None:
                operate_min_real = float(es_res[0]) / 60.0
            else:
                operate_min_real = 0.0

            stop_cnt_m_res = conn.execute(text(
                "SELECT SUM(ttime) AS ttime FROM ddCFBCstop WHERE reason IN ('歲休','計畫停車') AND bdate BETWEEN :sdate AND :bdate"
            ), {"sdate": sdate, "bdate": bdate}).fetchone()
            if stop_cnt_m_res and stop_cnt_m_res[0] is not None:
                stop_cnt_m = float(stop_cnt_m_res[0]) / 60.0
                operate_min_sum_CFBC1 = float(stop_cnt_m_res[0])
            else:
                stop_cnt_m = 0.0
                operate_min_sum_CFBC1 = 0.0

            m_ids = [
                "",
                "8001000001", "8002000001", "8003001001", "8003001002", "8003001003",
                "8003001004", "8003001005", "8003001006", "8003001007", "8003002001",
                "8003002002", "8003002003", "8003003001", "8003003002", "8003003003",
                "8003004001", "8003004002", "8003004003", "8004001001", "8004001002",
                "8004002001", "8004003001", "8004003002", "8004003003", "8004003004",
                "8004004001", "8004004002", "8004004003", "8004004004", "8004004005",
                "8004004006", "8004004007", "8004004008", "8004004009", "8004005001",
                "8004005002", "8004005003", "8004004015"
            ]

            goal = [0.0] * 39
            m_goal = [0.0] * 39
            real = [0.0] * 39
            m_real = [0.0] * 39
            unit_hr = [0.0] * 39
            diff = [0.0] * 39
            diff_rate = [0.0] * 39
            m_diff = [0.0] * 39
            m_diff_rate = [0.0] * 39

            goals_res = conn.execute(text(
                "SELECT m_id, m_goal FROM ic_mechine WHERE i_id='00008' AND status='Y'"
            )).fetchall()
            goals_map = {r[0]: float(r[1]) if r[1] is not None else 0.0 for r in goals_res}

            for x in range(1, 39):
                m_id = m_ids[x]
                m_goal_val = goals_map.get(m_id, 0.0)
                
                if x == 21:
                    if operate_min == 1.0:
                        goal[21] = m_goal_val * stop_p
                    else:
                        goal[21] = m_goal_val * operate_min
                else:
                    goal[x] = m_goal_val * stop_p

            if bdate.day > 1:
                bdate_yesterday = bdate - timedelta(days=1)
                hist_goal_res = conn.execute(text(
                    "SELECT m_id, SUM(goal) AS m_goal FROM ddCFBCcontrol "
                    "WHERE bdate BETWEEN :sdate AND :yesterday GROUP BY m_id"
                ), {"sdate": sdate, "yesterday": bdate_yesterday}).fetchall()
                
                hist_goal_map = {r[0]: float(r[1]) if r[1] is not None else 0.0 for r in hist_goal_res}
                for x in range(1, 39):
                    m_goal[x] = hist_goal_map.get(m_ids[x], 0.0) + goal[x]
            else:
                for x in range(1, 39):
                    m_goal[x] = goal[x]

            cols_to_select = []
            for x in range(1, 39):
                if 26 <= x <= 34:
                    cols_to_select.append(f"[{m_ids[x]}D]")
                else:
                    cols_to_select.append(f"[{m_ids[x]}]")
            
            sql_select_real = f"SELECT {', '.join(cols_to_select)} FROM atpower_APMo WHERE hrs='08' AND edate BETWEEN :stime AND :etime"
            real_res = conn.execute(text(sql_select_real), {"stime": stime, "etime": etime}).fetchone()

            if real_res:
                for x in range(1, 39):
                    val = real_res[x-1]
                    if val is None:
                        real[x] = 0.0
                    else:
                        if x == 3:
                            real[3] = float(val) * vars1
                        elif x == 4:
                            real[4] = float(val) / vars2 if vars2 != 0 else 0.0
                        elif x == 6:
                            real[6] = float(val) / vars4 if vars4 != 0 else 0.0
                        elif x == 7:
                            real[7] = float(val) / vars5 if vars5 != 0 else 0.0
                        else:
                            real[x] = float(val)
            else:
                for x in range(1, 39):
                    real[x] = 0.0

            if bdate.day > 1:
                bdate_yesterday = bdate - timedelta(days=1)
                hist_real_res = conn.execute(text(
                    "SELECT m_id, SUM(real) AS m_real FROM ddCFBCcontrol "
                    "WHERE bdate BETWEEN :sdate AND :yesterday GROUP BY m_id"
                ), {"sdate": sdate, "yesterday": bdate_yesterday}).fetchall()
                
                hist_real_map = {r[0]: float(r[1]) if r[1] is not None else 0.0 for r in hist_real_res}
                for x in range(1, 39):
                    m_real[x] = hist_real_map.get(m_ids[x], 0.0) + real[x]
            else:
                for x in range(1, 39):
                    m_real[x] = real[x]

            hr_base = m_real[1] / 60.0 if m_real[1] != 0 else 0.0
            
            for x in range(1, 39):
                unit_hr[x] = m_real[x] / hr_base if hr_base != 0 else 0.0

            if operate_min_sum != 0:
                if (operate_min_sum_CFBC2 - operate_min_sum_CFBC1) > 0:
                    denom = round(m_real[1] / 60.0, 1) - ((operate_min_sum_CFBC2 - operate_min_sum_CFBC1) / 60.0)
                    unit_hr[21] = m_real[21] / denom if denom != 0 else 0.0
                else:
                    denom = round(m_real[1] / 60.0, 1)
                    unit_hr[21] = m_real[21] / denom if denom != 0 else 0.0

            for x in range(1, 39):
                diff[x] = real[x] - goal[x]
                diff_rate[x] = diff[x] / goal[x] if goal[x] != 0 else 0.0

                m_diff[x] = m_real[x] - m_goal[x]
                m_diff_rate[x] = m_diff[x] / m_goal[x] if m_goal[x] != 0 else 0.0

            for x in range(1, 39):
                m_id = m_ids[x]
                
                conn.execute(text(
                    "UPDATE ddCFBCcontrol SET "
                    "goal = :goal, [real] = :real, diff = :diff, diff_rate = :diff_rate, "
                    "m_goal = :m_goal, m_real = :m_real, m_diff = :m_diff, m_diff_rate = :m_diff_rate, "
                    "musr = :musr, unit_hr = :unit_hr, mdtm = :mdtm "
                    "WHERE m_id = :m_id AND bdate = :bdate"
                ), {
                    "goal": goal[x], "real": real[x], "diff": diff[x], "diff_rate": diff_rate[x],
                    "m_goal": m_goal[x], "m_real": m_real[x], "m_diff": m_diff[x], "m_diff_rate": m_diff_rate[x],
                    "musr": musr, "unit_hr": unit_hr[x], "mdtm": datetime.now(),
                    "m_id": m_id, "bdate": bdate
                })
            
            current_date += timedelta(days=1)
        
        logger.info(f"ddCFBCcontrol 區間日結計算成功 ({start_date} ~ {current_date - timedelta(days=1) if current_date > start_date else '無'})")
