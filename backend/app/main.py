"""Punto de entrada de la API de Calles Seguras Juárez."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.errores import registrar_manejadores
from app.routers import admin, auth, catalogos, clima, geocoding, indicadores, moderacion, reportes
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
    tarea = asyncio.create_task(_ciclo_vencimiento())
    yield
    tarea.cancel()


app = FastAPI(
    title="Calles Seguras Juárez — API",
    description="Reportes ciudadanos de baches y encharcamientos en Ciudad Juárez, Chihuahua.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if settings.es_produccion else "/docs",
    redoc_url=None,
    openapi_url=None if settings.es_produccion else "/openapi.json",
)

registrar_manejadores(app)

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
    return respuesta


PREFIJO = "/api/v1"
for modulo in (auth, reportes, moderacion, catalogos, admin, indicadores, clima, geocoding):
    app.include_router(modulo.router, prefix=PREFIJO)


@app.get("/salud", tags=["salud"], summary="Verificación de disponibilidad")
def salud() -> dict[str, str]:
    return {"estado": "ok"}
