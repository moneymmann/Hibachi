from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json


def create_dashboard_app(audit_path: str):
    app = FastAPI()

    @app.get('/health')
    async def health():
        return {"ok": True}

    @app.get('/api/events')
    async def events(limit: int = 200):
        p = Path(audit_path)
        if not p.exists():
            return []
        rows = p.read_text(encoding='utf-8').splitlines()[-limit:]
        return [json.loads(x) for x in rows if x.strip()]

    @app.get('/dashboard')
    async def dashboard():
        return HTMLResponse("""
        <html><body style='background:#111;color:#ddd;font-family:monospace'>
        <h2>Hibachi MVP Dashboard</h2>
        <div id='s'>loading...</div>
        <script>
        async function t(){let r=await fetch('/api/events?limit=50');let j=await r.json();
        document.getElementById('s').innerHTML = '<pre>'+JSON.stringify(j,null,2)+'</pre>';}
        setInterval(t,1000); t();
        </script></body></html>
        """)

    return app
