from typing import Literal

from pydantic import BaseModel

from app.schemas.comun import ColoniaRef, FechaLocal, SectorRef


class ClimaActual(BaseModel):
    temperatura_c: float | None
    precipitacion_mm: float | None
    descripcion: str


class ClimaHora(BaseModel):
    hora: FechaLocal
    probabilidad_lluvia_pct: float | None
    precipitacion_mm: float | None


class Pronostico(BaseModel):
    ubicacion: str
    actual: ClimaActual
    proximas_horas: list[ClimaHora]
    alerta_lluvia: bool
    mensaje_alerta: str | None
    obtenido_en: FechaLocal
    desactualizado: bool


class CalleRiesgo(BaseModel):
    calle: str
    colonia: ColoniaRef
    sector: SectorRef
    nivel_riesgo: Literal["Alto", "Medio", "Bajo"]
    encharcamientos_activos: int
    nivel_agua_maximo_activo: str | None
    encharcamientos_historicos_12_meses: int
    ultimo_reporte: FechaLocal
    folios_activos: list[str]
    recomendacion: str


class RiesgoInundacion(BaseModel):
    alerta_lluvia: bool
    datos: list[CalleRiesgo]
    criterio: str
    obtenido_en: FechaLocal
