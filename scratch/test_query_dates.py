import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "app"))

from utils.db_connections import load_connection_info
from sqlalchemy import create_engine, text

conn_str, _ = load_connection_info("SRVAD8_A_energy")
engine = create_engine(conn_str)

with engine.connect() as conn:
    res = conn.execute(text("SELECT TOP 5 sdate FROM [dbo].[atpower_APMo] ORDER BY sdate DESC")).fetchall()
    print("最新 5 筆能量日結算日期：")
    for r in res:
        print(r[0])
