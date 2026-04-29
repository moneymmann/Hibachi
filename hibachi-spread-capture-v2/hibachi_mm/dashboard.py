from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from hibachi_mm.dashboard_store import DashboardStore

def build_dashboard_app(store: DashboardStore) -> FastAPI:
    app=FastAPI()
    static=Path(__file__).parent/'dashboard_static'
    @app.get('/health')
    async def health(): return {'ok':True}
    @app.get('/dashboard')
    async def dashboard(): return HTMLResponse((static/'index.html').read_text(encoding='utf-8'))
    @app.get('/dashboard/app.js')
    async def js(): return FileResponse(static/'app.js')
    @app.get('/dashboard/app.css')
    async def css(): return FileResponse(static/'app.css')
    @app.websocket('/ws/dashboard')
    async def dashboard_ws(websocket: WebSocket):
        await websocket.accept(); store._sockets.append(websocket)
        try:
            await websocket.send_json({'type':'snapshot','latest':store.latest})
            while True: await websocket.receive_text()
        except WebSocketDisconnect:
            if websocket in store._sockets: store._sockets.remove(websocket)
    return app
