"""Esquemas de la Fase 3: fusión, cuadrillas, enlace municipal, catálogos, colonias favoritas, trayecto y resumen."""

import re
import uuid
from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.models import EstadoReporte, NivelAgua, TipoDano
from app.schemas.comun import ColoniaRef, Esquema, FechaLocal, SectorRef, Ubicacion

FOLIO = r"^(BCH|ENC)-[0-9]{4}-[0-9]{6}$"


# ------------------------------------------------------------------------------- fusión (HU-05.3)


class FusionIn(Esquema):
    folio_principal: str = Field(pattern=FOLIO)
    folio_secundario: str = Field(pattern=FOLIO)


class FusionOut(BaseModel):
    folio_principal: str
    folio_secundario: str
    estado_secundario: EstadoReporte
    confirmaciones_transferidas: int
    confirmaciones_principal: int
    registrado_en: FechaLocal
    mensaje: str


# ------------------------------------------------------------------------------- cuadrillas (HU-05.4)


class _CuadrillaCampos(Esquema):
    @field_validator("telefono_contacto", check_fields=False)
    @classmethod
    def _telefono(cls, valor: str | None) -> str | None:
        if valor is not None and not re.fullmatch(r"[0-9 +()-]{7,20}", valor):
            raise ValueError("Teléfono no válido: usa de 7 a 20 dígitos, espacios, +, ( ) o guiones.")
        return valor


class CuadrillaCrear(_CuadrillaCampos):
    nombre: str = Field(min_length=3, max_length=120)
    responsable: str = Field(min_length=3, max_length=120)
    telefono_contacto: str


class CuadrillaEditar(_CuadrillaCampos):
    nombre: str | None = Field(default=None, min_length=3, max_length=120)
    responsable: str | None = Field(default=None, min_length=3, max_length=120)
    telefono_contacto: str | None = None
    activa: bool | None = None


class CuadrillaOut(BaseModel):
    id: int
    nombre: str
    responsable: str
    telefono_contacto: str
    activa: bool
    pendientes: int
    created_at: FechaLocal


class ListaCuadrillas(BaseModel):
    datos: list[CuadrillaOut]


class AsignacionIn(Esquema):
    folio: str = Field(pattern=FOLIO)
    fecha_programada: date


class BacheAsignado(BaseModel):
    """Vista operativa: sin datos del ciudadano que reportó (RN-04)."""

    asignacion_id: int
    folio: str
    tipo_dano: TipoDano
    estado: EstadoReporte
    calle: str
    referencia: str | None
    colonia: ColoniaRef
    ubicacion: Ubicacion
    fecha_programada: date
    fecha_reparacion: date | None
    cuadrilla: str
    asignacion_activa: bool
    asignado_en: FechaLocal
    transiciones_disponibles: list[EstadoReporte] = []


class EnlaceRef(BaseModel):
    id: uuid.UUID
    nombre: str
    activo: bool


class CuadrillaDetalle(CuadrillaOut):
    enlaces: list[EnlaceRef]
    baches: list[BacheAsignado]


class EnlaceIn(Esquema):
    usuario_id: uuid.UUID


# ------------------------------------------------------------------------------- enlace municipal (HU-05.5)


class CuadrillaRef(BaseModel):
    id: int
    nombre: str
    activa: bool


class MisAsignaciones(BaseModel):
    cuadrillas: list[CuadrillaRef]
    datos: list[BacheAsignado]


class AvanceIn(Esquema):
    estado_nuevo: EstadoReporte
    fecha_reparacion: date | None = None


class AvanceOut(BaseModel):
    folio: str
    estado_anterior: EstadoReporte
    estado: EstadoReporte
    fecha_reparacion: date | None
    mensaje: str


# ------------------------------------------------------------------------------- catálogos (HU-06.3)


class TipoDanoAdmin(BaseModel):
    id: int
    clave: TipoDano
    nombre: str
    descripcion: str | None
    activo: bool


class TipoDanoCrear(Esquema):
    clave: TipoDano
    nombre: str = Field(min_length=3, max_length=80)
    descripcion: str | None = Field(default=None, max_length=300)


class TipoDanoEditar(Esquema):
    nombre: str | None = Field(default=None, min_length=3, max_length=80)
    descripcion: str | None = Field(default=None, max_length=300)
    activo: bool | None = None


class MotivoRechazo(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    activo: bool


class MotivoCrear(Esquema):
    nombre: str = Field(min_length=3, max_length=120)
    descripcion: str | None = Field(default=None, max_length=300)


class MotivoEditar(Esquema):
    nombre: str | None = Field(default=None, min_length=3, max_length=120)
    descripcion: str | None = Field(default=None, max_length=300)
    activo: bool | None = None


class ListaTiposDanoAdmin(BaseModel):
    datos: list[TipoDanoAdmin]


class ListaMotivos(BaseModel):
    datos: list[MotivoRechazo]


# ------------------------------------------------------------------------------- colonias favoritas (HU-01.4)


class ColoniaFavoritaOut(BaseModel):
    colonia: ColoniaRef
    sector: SectorRef
    codigo_postal: str | None
    activa: bool
    agregada_en: FechaLocal


class ListaFavoritas(BaseModel):
    maximo: int
    datos: list[ColoniaFavoritaOut]


class FavoritaIn(Esquema):
    colonia_id: int = Field(ge=1)


# ------------------------------------------------------------------------------- trayecto (HU-04.6)


class RutaOut(BaseModel):
    fuente: str
    degradado: bool
    mensaje: str | None
    distancia_metros: float
    duracion_segundos: float | None
    puntos: list[tuple[float, float]]


class EncharcamientoEnTrayecto(BaseModel):
    folio: str
    calle: str
    colonia: ColoniaRef
    ubicacion: Ubicacion
    nivel_agua: NivelAgua
    es_intransitable: bool
    hay_riesgo_personas_vehiculos: bool | None
    distancia_metros: float
    vigente_hasta: FechaLocal


class TrayectoOut(BaseModel):
    origen: Ubicacion
    destino: Ubicacion
    radio_metros: int
    ruta: RutaOut
    total: int
    datos: list[EncharcamientoEnTrayecto]
    mensaje: str | None


# ------------------------------------------------------------------------------- resumen por colonia (HU-07.2)


class CriteriosResumen(BaseModel):
    abiertos: str
    tiempo_promedio_reparacion: str


class ResumenColonia(BaseModel):
    colonia: ColoniaRef
    sector: SectorRef
    codigo_postal: str | None
    activa: bool
    abiertos: int
    abiertos_por_estado: dict[str, int]
    reparados: int
    tiempo_promedio_reparacion_dias: float | None
    encharcamientos_activos: int
    criterios: CriteriosResumen
    actualizado_en: FechaLocal
