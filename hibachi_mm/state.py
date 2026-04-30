import sqlite3, os

def init_db(path:str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con=sqlite3.connect(path)
    cur=con.cursor()
    for t in ["events","engine_heartbeats","market_snapshots","account_snapshots","risk_snapshots","quote_decisions","orders","fills","pnl_snapshots"]:
        cur.execute(f"create table if not exists {t} (id integer primary key, data text, created_at text default current_timestamp)")
    con.commit(); con.close()
