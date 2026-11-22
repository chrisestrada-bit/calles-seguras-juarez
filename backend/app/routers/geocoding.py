from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.errores import ErrorAPI
from app.schemas.comun import respuestas
from app.schemas.geocoding import RespuestaGeocodificacion
from app.services import geocoding as servicio
from app.services.limitador import LimitadorVentana
from app.services.sqlutil import error_validacion

router = APIRouter(prefix="/geocoding", tags=["geocoding"])

# Protege la cuota de LocationIQ: 30 búsquedas por minuto por IP (por proceso).
_limitador = LimitadorVentana(maximo=30, ventana_segundos=60)


@router.get(
    "/buscar",
    response_model=RespuestaGeocodificacion,
    summary="Buscar direcciones en Ciudad Juárez (proxy de LocationIQ con respaldo local)",
    responses=respuestas(422, 429),
)
def buscar(
    request: Request,
    q: Annotated[str, Query(min_length=3, max_length=120, description="Calle, cruce, lugar o colonia.")],
    limite: Annotated[int, Query(ge=1, le=10)] = 5,
    db: Session = Depends(get_db),
) -> RespuestaGeocodificacion:
    espera = _limitador.intentar(request.client.host if request.client else "desconocida")
    if espera is not None:
        raise ErrorAPI(
            429,
            "LIMITE_BUSQUEDAS",
            "Hiciste demasiadas búsquedas en poco tiempo. Espera unos segundos e intenta de nuevo.",
            headers={"Retry-After": str(espera)},
        )
    texto = servicio.limpiar_consulta(q)
    if len(texto) < 3:
        raise error_validacion("q", "Escribe al menos 3 caracteres para buscar.")
    return servicio.buscar(db, texto, limite)
