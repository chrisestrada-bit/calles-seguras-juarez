"""Tipos y esquemas compartidos (paginación, ubicación, errores, fechas locales)."""

import math
from datetime import datetime
from typing import Annotated, Generic, TypeVar

from fastapi import Query
from pydantic import AfterValidator, BaseModel, ConfigDict, PlainSerializer

from app.core.errores import MARCA_FUERA_DE_JUAREZ
from app.core.tiempo import a_local
from app.services.geo import LAT_MAX, LAT_MIN, LON_MAX, LON_MIN

T = TypeVar("T")

# RN-02: toda marca de tiempo sale en America/Ciudad_Juarez (con desplazamiento -07:00 / -06:00).
FechaLocal = Annotated[
    datetime, PlainSerializer(lambda d: a_local(d), return_type=datetime, when_used="always")
]


def _validar_latitud(valor: float) -> float:
    if not LAT_MIN <= valor <= LAT_MAX:
        raise ValueError(f"{MARCA_FUERA_DE_JUAREZ}Debe estar entre {LAT_MIN:.2f} y {LAT_MAX:.2f}.")
    return round(valor, 6)


def _validar_longitud(valor: float) -> float:
    if not LON_MIN <= valor <= LON_MAX:
        raise ValueError(f"{MARCA_FUERA_DE_JUAREZ}Debe estar entre {LON_MIN:.2f} y {LON_MAX:.2f}.")
    return round(valor, 6)


# RN-01: sólo coordenadas dentro de Ciudad Juárez.
Latitud = Annotated[float, AfterValidator(_validar_latitud)]
Longitud = Annotated[float, AfterValidator(_validar_longitud)]


class Esquema(BaseModel):
    """Base de las peticiones: rechaza campos desconocidos y recorta espacios."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Ubicacion(BaseModel):
    latitud: float
    longitud: float


class ColoniaRef(BaseModel):
    id: int
    nombre: str


class SectorRef(BaseModel):
    id: int
    nombre: str


class Paginacion(BaseModel):
    pagina: int
    por_pagina: int
    total: int
    total_paginas: int


class Pagina(BaseModel, Generic[T]):
    datos: list[T]
    paginacion: Paginacion


class ParametrosPagina:
    def __init__(
        self,
        pagina: int = Query(1, ge=1, description="Número de página."),
        por_pagina: int = Query(20, ge=1, le=100, description="Elementos por página (1–100)."),
    ) -> None:
        self.pagina = pagina
        self.por_pagina = por_pagina

    @property
    def offset(self) -> int:
        return (self.pagina - 1) * self.por_pagina


def armar_pagina(datos: list, total: int, p: ParametrosPagina) -> dict:
    return {
        "datos": datos,
        "paginacion": {
            "pagina": p.pagina,
            "por_pagina": p.por_pagina,
            "total": total,
            "total_paginas": math.ceil(total / p.por_pagina) if total else 0,
        },
    }


class DetalleError(BaseModel):
    campo: str | None = None
    mensaje: str


class CuerpoError(BaseModel):
    codigo: str
    mensaje: str
    detalles: list[DetalleError | dict] = []


class ErrorRespuesta(BaseModel):
    error: CuerpoError


def respuestas(*codigos: int) -> dict[int | str, dict]:
    """Documenta en OpenAPI los errores posibles con la envoltura estándar."""
    return {c: {"model": ErrorRespuesta, "description": f"Error HTTP {c}"} for c in codigos}
