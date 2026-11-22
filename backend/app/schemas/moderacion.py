"""Esquemas de moderación. Muestran sólo el UUID del autor (sin nombre ni correo)."""

import uuid
from datetime import date

from pydantic import BaseModel, Field, model_validator

from app.models import EstadoReporte, RolUsuario, Severidad, TipoDano
from app.schemas.comun import ColoniaRef, Esquema, FechaLocal, SectorRef, Ubicacion
from app.schemas.reportes import DetalleAlcantarilla, DetalleBache, DetalleEncharcamiento


class ReporteModeracionItem(BaseModel):
    folio: str
    tipo_dano: TipoDano
    estado: EstadoReporte
    severidad: Severidad
    calle: str
    colonia: ColoniaRef
    sector: SectorRef
    confirmaciones: int
    forzado_como_nuevo: bool
    autor_id: uuid.UUID
    reportes_autor_ultimas_24h: int
    created_at: FechaLocal
    transiciones_disponibles: list[EstadoReporte]


class HistorialModeracionItem(BaseModel):
    estado_anterior: EstadoReporte | None
    estado_nuevo: EstadoReporte
    origen: str
    actor_id: uuid.UUID | None
    actor_rol: RolUsuario | None
    motivo: str | None
    fecha: FechaLocal


class ReporteModeracion(ReporteModeracionItem):
    ubicacion: Ubicacion
    referencia: str | None
    descripcion: str | None
    detalle: DetalleBache | DetalleAlcantarilla | DetalleEncharcamiento
    motivo_rechazo: str | None
    fecha_programada: date | None
    fecha_reparacion: date | None
    historial: list[HistorialModeracionItem]


class TransicionIn(Esquema):
    estado_nuevo: EstadoReporte
    fecha_reparacion: date | None = None
    fecha_programada: date | None = None
    motivo: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _campos_requeridos(self) -> "TransicionIn":
        if self.estado_nuevo == EstadoReporte.RECHAZADO and (
            self.motivo is None or len(self.motivo) < 10
        ):
            raise ValueError("El motivo de rechazo es obligatorio (mínimo 10 caracteres).")
        return self


class TransicionOut(BaseModel):
    folio: str
    estado_anterior: EstadoReporte
    estado: EstadoReporte
    fecha_reparacion: date | None
    longevidad_dias: int | None
    registrado_en: FechaLocal
    mensaje: str
