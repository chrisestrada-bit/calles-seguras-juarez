from typing import Literal

from pydantic import BaseModel

from app.schemas.comun import SectorRef, Ubicacion


class ColoniaSugerida(BaseModel):
    id: int
    nombre: str
    sector: SectorRef
    codigo_postal: str | None = None


class ResultadoGeocodificacion(BaseModel):
    etiqueta: str
    calle: str | None
    ubicacion: Ubicacion
    precision: Literal["direccion", "calle", "colonia", "aproximada"]
    colonia_sugerida: ColoniaSugerida | None


class RespuestaGeocodificacion(BaseModel):
    fuente: Literal["locationiq", "catalogo_local"]
    degradado: bool
    datos: list[ResultadoGeocodificacion]
    atribucion: str | None
    mensaje: str | None


class ColoniaCercana(ColoniaSugerida):
    distancia_metros: float


class RespuestaGeocodificacionInversa(BaseModel):
    """Geocodificación inversa dentro de Ciudad Juárez (RN-01)."""

    fuente: Literal["locationiq", "catalogo_local"]
    degradado: bool
    ubicacion: Ubicacion
    calle: str | None
    etiqueta: str
    colonia_sugerida: ColoniaSugerida | None
    colonias_cercanas: list[ColoniaCercana]
    atribucion: str | None
    mensaje: str | None
