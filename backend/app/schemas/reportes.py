"""Esquemas de reportes. Los esquemas *Publico no contienen datos del ciudadano reportante (RN-04)."""

from datetime import date
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, field_validator, model_serializer

from app.models import (
    CarrilAfectado,
    EstadoReporte,
    NivelAgua,
    ProfundidadBache,
    Severidad,
    TamanoBache,
    TipoConfirmacion,
    TipoDano,
)
from app.schemas.comun import (
    ColoniaRef,
    Esquema,
    FechaLocal,
    Latitud,
    Longitud,
    SectorRef,
    Ubicacion,
)

# --------------------------------------------------------------------------- petición


class _ReporteBase(Esquema):
    latitud: Latitud
    longitud: Longitud
    colonia_id: int = Field(ge=1)
    calle: str = Field(min_length=3, max_length=150)
    referencia: str | None = Field(default=None, max_length=200)
    descripcion: str | None = Field(default=None, max_length=500)  # HU-02.2: máximo 500
    forzar_nuevo: bool = False

    @field_validator("referencia", "descripcion")
    @classmethod
    def _vacio_a_nulo(cls, valor: str | None) -> str | None:
        return valor or None


class BacheIn(_ReporteBase):
    tipo_dano: Literal["Bache"]
    tamano: TamanoBache
    profundidad: ProfundidadBache
    carril_afectado: CarrilAfectado


class AlcantarillaIn(_ReporteBase):
    tipo_dano: Literal["Alcantarilla sin tapa"]
    esta_senalizado: bool


class EncharcamientoIn(_ReporteBase):
    tipo_dano: Literal["Encharcamiento"]
    nivel_agua: NivelAgua
    hay_riesgo_personas_vehiculos: bool | None = Field(default=None, validate_default=True)

    @field_validator("hay_riesgo_personas_vehiculos")
    @classmethod
    def _riesgo_si_intransitable(cls, valor: bool | None, info: Any) -> bool | None:
        nivel = info.data.get("nivel_agua")
        if nivel is None:
            return valor
        if nivel == NivelAgua.INTRANSITABLE and valor is None:
            raise ValueError("Indica si hay riesgo para personas o vehículos.")
        if nivel != NivelAgua.INTRANSITABLE and valor is not None:
            raise ValueError("Sólo aplica cuando el nivel del agua es «intransitable».")
        return valor


ReporteCrear = Annotated[BacheIn | AlcantarillaIn | EncharcamientoIn, Field(discriminator="tipo_dano")]


class ReporteEditar(Esquema):
    """HU-02.5: el autor corrige su reporte mientras está «Recibido».

    Folio, tipo, ubicación y fecha son inmutables (RN-03, RN-10); la severidad la recalcula el servidor.
    """

    colonia_id: int | None = Field(default=None, ge=1)
    calle: str | None = Field(default=None, min_length=3, max_length=150)
    referencia: str | None = Field(default=None, max_length=200)
    descripcion: str | None = Field(default=None, max_length=500)  # HU-02.2: máximo 500
    tamano: TamanoBache | None = None
    profundidad: ProfundidadBache | None = None
    carril_afectado: CarrilAfectado | None = None
    esta_senalizado: bool | None = None

    @field_validator("referencia", "descripcion")
    @classmethod
    def _vacio_a_nulo(cls, valor: str | None) -> str | None:
        return valor or None


class ConfirmacionIn(Esquema):
    tipo: TipoConfirmacion


# --------------------------------------------------------------------------- respuesta pública


class DetalleBache(BaseModel):
    tamano: TamanoBache
    profundidad: ProfundidadBache
    carril_afectado: CarrilAfectado


class DetalleAlcantarilla(BaseModel):
    esta_senalizado: bool


class DetalleEncharcamiento(BaseModel):
    nivel_agua: NivelAgua
    hay_riesgo_personas_vehiculos: bool | None


class Vigencia(BaseModel):
    vigente_hasta: FechaLocal
    sigue_ahi: int
    ya_no_hay_agua: int


class ReporteResumenPublico(BaseModel):
    folio: str
    tipo_dano: TipoDano
    estado: EstadoReporte
    etiqueta_publica: str | None
    severidad: Severidad
    ubicacion: Ubicacion
    calle: str
    colonia: ColoniaRef
    created_at: FechaLocal
    longevidad_dias: int | None
    vigencia: Vigencia | None
    nivel_agua: str | None = None


class ReportePublico(ReporteResumenPublico):
    referencia: str | None
    sector: SectorRef
    descripcion: str | None
    detalle: DetalleBache | DetalleAlcantarilla | DetalleEncharcamiento
    confirmaciones: int
    fecha_programada: date | None
    fecha_reparacion: date | None
    # Sólo con sesión; son booleanos relativos al solicitante, no revelan identidad de terceros.
    es_mio: bool | None = None
    ya_confirmado_por_mi: bool | None = None

    @model_serializer(mode="wrap")
    def _omitir_campos_de_sesion(self, handler: Any) -> dict[str, Any]:
        datos = handler(self)
        for clave in ("es_mio", "ya_confirmado_por_mi"):
            if datos.get(clave) is None:
                datos.pop(clave, None)
        return datos


class HistorialPublicoItem(BaseModel):
    estado_anterior: EstadoReporte | None
    estado_nuevo: EstadoReporte
    origen: str
    fecha: FechaLocal


class HistorialPublico(BaseModel):
    folio: str
    historial: list[HistorialPublicoItem]


class CandidatoDuplicado(BaseModel):
    folio: str
    tipo_dano: TipoDano
    estado: EstadoReporte
    etiqueta_publica: str | None
    severidad: Severidad
    calle: str
    distancia_metros: float
    confirmaciones: int
    ya_confirmado_por_mi: bool
    es_mio: bool
    created_at: FechaLocal


class CercanosRespuesta(BaseModel):
    radio_metros: int
    candidatos: list[CandidatoDuplicado]


class MiReporte(BaseModel):
    """Vista del propio autor: incluye el motivo si fue rechazado."""

    folio: str
    tipo_dano: TipoDano
    estado: EstadoReporte
    etiqueta_publica: str | None
    severidad: Severidad
    calle: str
    colonia: ColoniaRef
    created_at: FechaLocal
    motivo_rechazo: str | None
    longevidad_dias: int | None
    es_mio: Literal[True] = True


class ConfirmacionOut(BaseModel):
    folio: str
    tipo: TipoConfirmacion
    estado_reporte: EstadoReporte
    vigencia: Vigencia | None
    mensaje: str


# --------------------------------------------------------------------------- mapa (HU-04.5)


class MarcadorMapa(BaseModel):
    """Punto público del mapa: sin datos de la persona reportante (RN-04)."""

    folio: str
    tipo_dano: TipoDano
    estado: EstadoReporte
    etiqueta_publica: str | None
    severidad: Severidad
    ubicacion: Ubicacion
    calle: str
    colonia: ColoniaRef
    nivel_agua: str | None = None
    created_at: FechaLocal


class MapaRespuesta(BaseModel):
    total: int
    mostrados: int
    limite: int
    datos: list[MarcadorMapa]
