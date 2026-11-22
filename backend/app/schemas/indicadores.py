from datetime import date

from pydantic import BaseModel

from app.models import EstadoReporte, Severidad, TipoDano
from app.schemas.comun import ColoniaRef, FechaLocal, SectorRef


class Periodo(BaseModel):
    desde: date | None
    hasta: date | None
    zona_horaria: str


class ResumenPavimento(BaseModel):
    total: int
    por_estado: dict[str, int]
    por_tipo: dict[str, int]
    longevidad_promedio_abiertos_dias: float | None
    tiempo_promedio_reparacion_dias: float | None


class ResumenEncharcamientos(BaseModel):
    total: int
    activos: int
    historicos: int
    intransitables: int


class IndicadoresResumen(BaseModel):
    periodo: Periodo
    pavimento: ResumenPavimento
    encharcamientos: ResumenEncharcamientos
    actualizado_en: FechaLocal


class IndicadorSector(BaseModel):
    sector: SectorRef
    baches_abiertos: int
    reparados: int
    longevidad_promedio_abiertos_dias: float | None
    encharcamientos_total: int
    encharcamientos_activos: int


class IndicadoresSectores(BaseModel):
    datos: list[IndicadorSector]


class LongevidadItem(BaseModel):
    folio: str
    tipo_dano: TipoDano
    estado: EstadoReporte
    severidad: Severidad
    calle: str
    colonia: ColoniaRef
    created_at: FechaLocal
    longevidad_dias: int


class IndicadoresLongevidad(BaseModel):
    datos: list[LongevidadItem]


class IndicadoresModeracion(BaseModel):
    pendientes_validacion: int
    antiguedad_max_pendiente_horas: float | None
    tiempo_promedio_validacion_horas: float | None
    rechazados_periodo: int
    tasa_rechazo_pct: float
    reportes_forzados_como_nuevos: int
    encharcamientos_rechazados: int
