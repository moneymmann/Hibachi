from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse


def create_app(store):
    app = FastAPI()

    @app.get("/dashboard")
    async def dashboard_page():
        with open("hibachi_mm/dashboard_static/index.html", encoding="utf-8") as f:
            return HTMLResponse(f.read())

    @app.get("/api/dashboard")
    async def dashboard_api():
        return store.latest

    @app.websocket("/ws/dashboard")
    async def dashboard_ws(websocket: WebSocket):
        await websocket.accept()
        try:
            await websocket.send_json(store.latest)
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            return

    return app
