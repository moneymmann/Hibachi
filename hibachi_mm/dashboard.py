from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import asyncio, os, json

def create_app(store):
    app=FastAPI()
    @app.get('/health')
    async def health(): return {'ok':True}
    @app.get('/dashboard')
    async def dashboard(): return FileResponse(os.path.join(os.path.dirname(__file__),'dashboard_static','index.html'))
    @app.get('/dashboard_static/{name}')
    async def static_file(name:str): return FileResponse(os.path.join(os.path.dirname(__file__),'dashboard_static',name))
    @app.get('/api/snapshot')
    async def snap(): return store.snapshot
    @app.get('/api/events')
    async def events(limit:int=200): return store.events[-limit:]
    @app.get('/api/orders')
    async def orders(): return [e for e in store.events if 'order' in e.get('event','')]
    @app.get('/api/fills')
    async def fills(): return [e for e in store.events if e.get('event')=='order_filled']
    @app.websocket('/ws/dashboard')
    async def dashboard_ws(websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                await websocket.send_text(json.dumps(store.snapshot))
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            return
    return app
