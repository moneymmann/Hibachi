from datetime import datetime, timezone
from pathlib import Path
import json
class Audit:
    def __init__(self,path:str): self.p=Path(path); self.p.parent.mkdir(parents=True,exist_ok=True)
    def log(self,event:str,**k):
        with self.p.open('a',encoding='utf-8') as f: f.write(json.dumps({'ts':datetime.now(timezone.utc).isoformat(),'event':event,**k})+'\n')
