"""WebSocket para notificar en vivo cuando se clasifica un nuevo paciente."""
import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from fastapi.concurrency import run_in_threadpool

from ..db.database import SessionLocal
from .auth import staff_from_token

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    def subscribe(self, websocket: WebSocket):
        """Agrega una conexion ya aceptada y autenticada."""
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


def _is_valid_staff_token(token: str | None) -> bool:
    with SessionLocal() as db:
        return staff_from_token(db, token) is not None


# Segundos que el cliente tiene para enviar su token tras conectar.
AUTH_TIMEOUT_SECONDS = 5


@router.websocket("/ws/triage")
async def triage_ws(websocket: WebSocket):
    # Los navegadores no permiten cabeceras en un WebSocket. En vez de poner
    # el token en la URL (quedaria en los logs de acceso), el cliente lo
    # envia como primer mensaje; solo entonces se suscribe a los eventos.
    await websocket.accept()
    try:
        token = await asyncio.wait_for(websocket.receive_text(), AUTH_TIMEOUT_SECONDS)
    except (asyncio.TimeoutError, WebSocketDisconnect):
        token = None
    if not await run_in_threadpool(_is_valid_staff_token, token):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    manager.subscribe(websocket)
    try:
        while True:
            # No esperamos mensajes del cliente; solo mantenemos la conexion
            # viva para poder emitir eventos (broadcast) desde el backend.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
