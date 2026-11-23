import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import get_settings
from app.core.red import ip_cliente
from app.services import tiempo_real
from app.services.tiempo_real import gestor

router = APIRouter(tags=["tiempo-real"])


@router.websocket("/ws/encharcamientos")
async def canal_encharcamientos(ws: WebSocket) -> None:
    """Encharcamientos nuevos o actualizados, sin datos personales.

    Mensajes del servidor: `hola` (al conectar), `ping` (latido), `encharcamiento.creado|actualizado|retirado`.
    El cliente responde `pong` a cada `ping`. Si no hay actividad en dos latidos seguidos, el servidor cierra.
    """
    ajustes = get_settings()
    origen = ws.headers.get("origin")
    if origen and origen.rstrip("/") != ajustes.frontend_url.rstrip("/"):
        await ws.close(code=1008)  # misma política que CORS: sólo el frontend autorizado
        return
    # Un cliente que no es navegador puede omitir o falsificar Origin: el límite real es el tope de conexiones.
    ip = ip_cliente(ws)
    if not gestor.hay_cupo(ip, ajustes.ws_max_conexiones, ajustes.ws_max_conexiones_por_ip):
        await ws.close(code=1013)  # «intenta más tarde»; el frontend recurre al sondeo HTTP
        return
    await gestor.conectar(ws, ip)
    await gestor.enviar(ws, {"tipo": "hola", "heartbeat_segundos": tiempo_real.HEARTBEAT_SEGUNDOS})
    silencios = 0
    try:
        while True:
            try:
                texto = await asyncio.wait_for(ws.receive_text(), timeout=tiempo_real.HEARTBEAT_SEGUNDOS)
            except asyncio.TimeoutError:
                silencios += 1
                if silencios >= 2:
                    await ws.close(code=1001)
                    break
                await gestor.enviar(ws, {"tipo": "ping"})
                continue
            silencios = 0
            try:
                if json.loads(texto).get("tipo") == "ping":
                    await gestor.enviar(ws, {"tipo": "pong"})
            except (ValueError, AttributeError):
                pass  # cualquier otro texto cuenta como actividad y se ignora
    except WebSocketDisconnect:
        pass
    finally:
        gestor.desconectar(ws)
