import sys
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "app"))

from utils.db_connections import load_connection_info
from resources.energy import energy_daily_sttlement

# 1. 取得連線
conn_str, _ = load_connection_info("SRVAD8_A_energy")
engine = create_engine(conn_str)

# 2. 定義 mock_begin context manager
@contextmanager
def mock_begin():
    conn = engine.connect()
    trans = conn.begin()
    try:
        print("MOCK: 已開啟交易 (Transaction started)")
        yield conn
        
        # 在交易尚未回滾前，查詢計算結果以驗證是否正確！
        print("\n=== 交易中驗證 (Validation inside Transaction) ===")
        
        # 查詢 atpower_APMo 的最新修改時間與修改人，看是否有更新成功
        chk_apmo = conn.execute(text(
            "SELECT sdate, musr, mdtm, [8001000001] FROM [dbo].[atpower_APMo] WHERE sdate = '2026-07-17 07:02:00'"
        )).fetchone()
        if chk_apmo:
            print(f"atpower_APMo 暫存更新結果: sdate={chk_apmo[0]}, musr={chk_apmo[1]}, mdtm={chk_apmo[2]}, 8001000001={chk_apmo[3]}")
        else:
            print("atpower_APMo 暫存更新結果: 找不到紀錄")
        
        # 查詢 ddCFBCcontrol 中的計算結果 (bdate 為 2026-07-16)
        chk_control = conn.execute(text(
            "SELECT TOP 5 bdate, m_id, goal, [real], diff, unit_hr, musr, mdtm FROM ddCFBCcontrol WHERE bdate = '2026-07-16' ORDER BY mdtm DESC"
        )).fetchall()
        print("\nddCFBCcontrol 暫存更新結果 (前 5 筆)：")
        for r in chk_control:
            print(f"bdate={r[0]}, m_id={r[1]}, goal={r[2]}, real={r[3]}, diff={r[4]}, unit_hr={r[5]}, musr={r[6]}")
            
    except Exception as e:
        print(f"MOCK: 交易中發生異常: {e}")
        raise e
    finally:
        print("\nMOCK: 測試結束，強制執行交易回滾 (Rollback executed)")
        trans.rollback()
        conn.close()

# 3. 替換 engine 的 begin 方法
engine.begin = mock_begin

# 4. 準備測試資料
df_mock = pd.DataFrame(
    [["SRVAD8_A_energy", "A_energy", engine]],
    columns=["SERVER", "DB", "create_engine"]
)
servers = {
    'SRVAD8_A_energy': df_mock
}
executor = energy_daily_sttlement(servers)

test_sdate = "2026-07-17 07:02:00"
test_fields = {
    "8001000001": 24.0, # CFBC運轉時間
    "8003001001": 500.0 # 煤炭量
}
user_info = {"FTAId": "TEST"}

print("\n--- 啟動日結算更新計算測試 ---")
try:
    res = executor.patch(test_sdate, test_fields, user_info)
    print("\nAPI 返回結果 (由於讀取在 rollback 後，可能顯示舊資料或預期值):", res)
except Exception as e:
    print("測試執行失敗:", e)
