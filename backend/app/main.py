"""Punto de entrada de la API de Calles Seguras Juárez."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.errores import registrar_manejadores
from app.core.limite_cuerpo import LimiteCuerpo
from app.routers import admin, auth, catalogos, clima, geocoding, indicadores, moderacion, notificaciones, operacion, reportes, ws
from app.services.tiempo_real import gestor
from app.services.vigencia import expirar_vencidos

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
for _ruidoso in ("httpx", "httpcore"):  # su nivel INFO imprime URLs completas (podrían incluir llaves)
    logging.getLogger(_ruidoso).setLevel(logging.WARNING)
logger = logging.getLogger("calles_seguras")

INTERVALO_VENCIMIENTO_SEGUNDOS = 300
settings = get_settings()


def _expirar_encharcamientos() -> None:
    with SessionLocal() as db:
        expirar_vencidos(db)


async def _ciclo_vencimiento() -> None:
    """Materializa los vencimientos aunque nadie consulte (la vigencia también se evalúa en cada consulta)."""
    while True:
        try:
            await asyncio.to_thread(_expirar_encharcamientos)
        except Exception:  # noqa: BLE001 - el ciclo nunca debe morir
            logger.exception("Falló la tarea de vencimiento de encharcamientos")
        await asyncio.sleep(INTERVALO_VENCIMIENTO_SEGUNDOS)


@asynccontextmanager
async def lifespan(_: FastAPI):
    gestor.configurar_loop(asyncio.get_running_loop())  # los servicios síncronos publican eventos WebSocket (HU-08.3)
    tarea = asyncio.create_task(_ciclo_vencimiento())
    yield
    tarea.cancel()
    gestor.configurar_loop(None)


app = FastAPI(
    title="Calles Seguras Juárez — API",
    description="Reportes ciudadanos de baches y encharcamientos en Ciudad Juárez, Chihuahua.",
    version="1.1.1",
    lifespan=lifespan,
    docs_url=None if settings.es_produccion else "/docs",
    redoc_url=None,
    openapi_url=None if settings.es_produccion else "/openapi.json",
)

registrar_manejadores(app)

# M7: tope del cuerpo. Se registra ANTES que CORS para quedar por dentro: así el 413 también lleva las
# cabeceras CORS y el navegador puede mostrar el mensaje en español.
app.add_middleware(LimiteCuerpo, maximo_bytes=settings.max_cuerpo_bytes)

# CORS restringido estrictamente al origen del frontend (FRONTEND_URL).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url.rstrip("/")],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["Location", "Retry-After"],
)


@app.middleware("http")
async def encabezados_de_seguridad(request: Request, call_next):
    respuesta = await call_next(request)
    respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
    respuesta.headers.setdefault("Cache-Control", "no-store")
    # M5: la API sólo entrega JSON e imágenes; nunca debe incrustarse ni ejecutar contenido activo.
    respuesta.headers.setdefault("X-Frame-Options", "DENY")
    respuesta.headers.setdefault("Referrer-Policy", "no-referrer")
    if respuesta.headers.get("content-type", "").startswith("application/json"):
        respuesta.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
    if settings.es_produccion:
        respuesta.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains")
    return respuesta


PREFIJO = "/api/v1"
for modulo in (auth, reportes, moderacion, catalogos, admin, indicadores, clima, geocoding, notificaciones, ws):
    app.include_router(modulo.router, prefix=PREFIJO)
# Fase 3: cuadrillas, enlace municipal, perfil, trayecto y resumen público por colonia.
for sub in (operacion.cuadrillas, operacion.enlace, operacion.perfil, operacion.ruta_trayecto, operacion.publico):
    app.include_router(sub, prefix=PREFIJO)


@app.get("/salud", tags=["salud"], summary="Verificación de disponibilidad")
@app.get("/health", tags=["salud"], summary="Verificación de disponibilidad (alias de /salud para Kubernetes)")
def salud() -> dict[str, str]:
    return {"estado": "ok"}
