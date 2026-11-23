from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.errores import ErrorAPI
from app.core.red import ip_cliente
from app.schemas.comun import Latitud, Longitud, respuestas
from app.schemas.geocoding import RespuestaGeocodificacion, RespuestaGeocodificacionInversa
from app.services import geocoding as servicio
from app.services.limitador import LimitadorVentana
from app.services.sqlutil import error_validacion

router = APIRouter(prefix="/geocoding", tags=["geocoding"])

# Protege la cuota de LocationIQ: 30 búsquedas por minuto por IP real del cliente (por proceso, ver app/core/red.py).
_limitador = LimitadorVentana(maximo=30, ventana_segundos=60)


def _limitar(request: Request) -> None:
    espera = _limitador.intentar(ip_cliente(request))
    if espera is not None:
        raise ErrorAPI(
            429,
            "LIMITE_BUSQUEDAS",
            "Hiciste demasiadas búsquedas en poco tiempo. Espera unos segundos e intenta de nuevo.",
            headers={"Retry-After": str(espera)},
        )


@router.get(
    "/buscar",
    response_model=RespuestaGeocodificacion,
    summary="Buscar direcciones o códigos postales en Ciudad Juárez (proxy de LocationIQ con respaldo local)",
    responses=respuestas(422, 429),
)
def buscar(
    request: Request,
    q: Annotated[str, Query(min_length=3, max_length=120, description="Calle, cruce, lugar, colonia o código postal (32000–32730).")],
    limite: Annotated[int, Query(ge=1, le=10)] = 5,
    db: Session = Depends(get_db),
) -> RespuestaGeocodificacion:
    _limitar(request)
    texto = servicio.limpiar_consulta(q)
    if len(texto) < 3:
        raise error_validacion("q", "Escribe al menos 3 caracteres para buscar.")
    return servicio.buscar(db, texto, limite)


@router.get(
    "/inversa",
    response_model=RespuestaGeocodificacionInversa,
    summary="Geocodificación inversa dentro de Ciudad Juárez: coordenada → calle y colonia sugeridas",
    responses=respuestas(422, 429),
)
def inversa(
    request: Request,
    latitud: Annotated[Latitud, Query()],
    longitud: Annotated[Longitud, Query()],
    db: Session = Depends(get_db),
) -> RespuestaGeocodificacionInversa:
    _limitar(request)
    return servicio.inversa(db, latitud, longitud)
