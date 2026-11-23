"""Canal WebSocket de encharcamientos en vivo (HU-08.3 · extra 4.5).

Sólo viajan datos públicos (el mismo `ReporteResumenPublico` de la API pública, RN-04): nunca autor, correo ni ids.
Los servicios síncronos (que corren en el *threadpool*) publican con `emitir`; el gestor difunde en el *event loop*.
"""

import asyncio
import logging
import threading
import uuid
from collections import OrderedDict

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.core.tiempo import a_local, ahora_utc
from app.models import EstadoReporte, Reporte, TipoDano

logger = logging.getLogger("calles_seguras")

HEARTBEAT_SEGUNDOS = 20.0
MAX_FIRMAS_RECIENTES = 500


class GestorConexiones:
    def __init__(self) -> None:
        self._conexiones: dict[WebSocket, asyncio.Lock] = {}
        self._ips: dict[WebSocket, str] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._firmas: OrderedDict[str, None] = OrderedDict()
        self._candado = threading.Lock()

    def configurar_loop(self, loop: asyncio.AbstractEventLoop | None) -> None:
        self._loop = loop

    @property
    def total(self) -> int:
        return len(self._conexiones)

    def hay_cupo(self, ip: str, maximo: int, maximo_por_ip: int) -> bool:
        """M6: sin tope, un cliente (navegador o no) podía abrir conexiones hasta agotar memoria y descriptores."""
        if len(self._conexiones) >= maximo:
            return False
        return sum(1 for otra in self._ips.values() if otra == ip) < maximo_por_ip

    async def conectar(self, ws: WebSocket, ip: str = "") -> None:
        await ws.accept()
        self._conexiones[ws] = asyncio.Lock()
        self._ips[ws] = ip

    def desconectar(self, ws: WebSocket) -> None:
        self._conexiones.pop(ws, None)
        self._ips.pop(ws, None)

    async def enviar(self, ws: WebSocket, datos: dict) -> bool:
        candado = self._conexiones.get(ws)
        if candado is None:
            return False
        try:
            async with candado:
                await ws.send_json(datos)
            return True
        except Exception:  # noqa: BLE001 - un cliente caído no debe afectar a los demás
            self.desconectar(ws)
            return False

    async def difundir(self, evento: dict) -> None:
        await asyncio.gather(*(self.enviar(ws, evento) for ws in list(self._conexiones)))

    def es_repetido(self, firma: str) -> bool:
        """Deduplicación en el servidor: la misma firma (folio + estado + vigencia) no se difunde dos veces seguidas."""
        with self._candado:
            if firma in self._firmas:
                return True
            self._firmas[firma] = None
            while len(self._firmas) > MAX_FIRMAS_RECIENTES:
                self._firmas.popitem(last=False)
            return False

    def publicar(self, evento: dict) -> None:
        if self._loop is None or not self._conexiones:
            return
        asyncio.run_coroutine_threadsafe(self.difundir(evento), self._loop)


gestor = GestorConexiones()


def _firma(r: Reporte, tipo: str) -> str:
    return f"{tipo}|{r.folio}|{r.estado.value}|{r.vigente_hasta.isoformat() if r.vigente_hasta else ''}|{r.ciclo_vigencia}"


def emitir(db: Session, reporte: Reporte, tipo: str) -> None:
    """tipo: creado | actualizado | retirado. No hace nada si nadie está conectado (no cuesta consultas)."""
    if gestor.total == 0 or reporte.tipo_dano != TipoDano.ENCHARCAMIENTO:
        return
    try:
        # Import diferido: presentacion importa servicios que a su vez publican eventos.
        from app.services import presentacion

        retirado = tipo == "retirado" or reporte.estado == EstadoReporte.RECHAZADO
        firma = _firma(reporte, "retirado" if retirado else tipo)
        if gestor.es_repetido(firma):
            return
        resumen = None
        if not retirado:
            conteos = presentacion.conteos_confirmaciones(db, [reporte])
            resumen = presentacion.a_resumen(reporte, conteos).model_dump(mode="json")
        gestor.publicar(
            {
                "tipo": "encharcamiento.retirado" if retirado else f"encharcamiento.{tipo}",
                "event_id": str(uuid.uuid4()),
                "folio": reporte.folio,
                "emitido_en": a_local(ahora_utc()).isoformat(),
                "reporte": resumen,
            }
        )
    except Exception:  # noqa: BLE001 - emitir nunca debe romper la operación de negocio
        logger.exception("No se pudo emitir el evento en tiempo real")
