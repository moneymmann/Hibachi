import sqlite3
from pathlib import Path
class StateDB:
    def __init__(self,path:str):
        p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); self.c=sqlite3.connect(p)
        for t in ['events','engine_heartbeats','market_snapshots','account_snapshots','risk_snapshots','quote_decisions','orders','fills']:
            self.c.execute(f'CREATE TABLE IF NOT EXISTS {t}(id INTEGER PRIMARY KEY, payload TEXT)')
        self.c.commit()
    def put(self,table:str,payload:str): self.c.execute(f'INSERT INTO {table}(payload) VALUES (?)',(payload,)); self.c.commit()
