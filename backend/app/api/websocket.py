"""WebSocket para notificar en vivo cuando se clasifica un nuevo paciente."""
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, data: dict):
        payload = json.dumps(data)
        for connection in list(self.active):
            try:
                await connection.send_text(payload)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws/triage")
async def triage_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # No esperamos mensajes del cliente; solo mantenemos la conexion
            # viva para poder emitir eventos (broadcast) desde el backend.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
