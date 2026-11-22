"""Conversión de modelos a esquemas de respuesta, longevidad (RN-10) y conteos de confirmaciones."""

from collections.abc import Iterable
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.tiempo import fecha_local, hoy_local
from app.models import (
    ConfirmacionReporte,
    EstadoReporte,
    Reporte,
    TipoConfirmacion,
    TipoDano,
    Usuario,
)
from app.schemas.comun import ColoniaRef, SectorRef, Ubicacion
from app.schemas.reportes import (
    DetalleAlcantarilla,
    DetalleBache,
    DetalleEncharcamiento,
    MiReporte,
    ReportePublico,
    ReporteResumenPublico,
    Vigencia,
)

Conteos = dict[int, tuple[int, int]]  # reporte_id -> (confirmaciones, ya_no_hay_agua de la vigencia actual)


def longevidad_dias(r: Reporte, hoy: date | None = None) -> int | None:
    """RN-10: días desde created_at hasta fecha_reparacion (Reparado) o hasta hoy (abierto)."""
    if r.tipo_dano == TipoDano.ENCHARCAMIENTO or r.estado == EstadoReporte.RECHAZADO:
        return None
    inicio = fecha_local(r.created_at)
    fin = r.fecha_reparacion if r.estado == EstadoReporte.REPARADO else (hoy or hoy_local())
    return max(0, (fin - inicio).days) if fin else None


def etiqueta_publica(r: Reporte) -> str | None:
    """RN-09: «Sin validar» para Recibido; los Rechazados no tienen etiqueta pública."""
    if r.estado == EstadoReporte.RECHAZADO:
        return None
    return "Sin validar" if r.estado == EstadoReporte.RECIBIDO else r.estado.value


def conteos_confirmaciones(db: Session, reportes: Iterable[Reporte]) -> Conteos:
    ids = [r.id for r in reportes]
    if not ids:
        return {}
    filas = db.execute(
        select(
            ConfirmacionReporte.reporte_id,
            func.count().filter(
                ConfirmacionReporte.tipo.in_(
                    [TipoConfirmacion.CONFIRMACION_DANO, TipoConfirmacion.SIGUE_AHI]
                )
            ),
            func.count().filter(
                ConfirmacionReporte.tipo == TipoConfirmacion.YA_NO_HAY_AGUA,
                ConfirmacionReporte.ciclo_vigencia == Reporte.ciclo_vigencia,
            ),
        )
        .join(Reporte, Reporte.id == ConfirmacionReporte.reporte_id)
        .where(ConfirmacionReporte.reporte_id.in_(ids))
        .group_by(ConfirmacionReporte.reporte_id)
    ).all()
    return {rid: (conf, nohay) for rid, conf, nohay in filas}


def confirmados_por_usuario(db: Session, reportes: Iterable[Reporte], usuario: Usuario | None) -> set[int]:
    """Ids de reportes ya confirmados por el usuario (en la vigencia actual para encharcamientos)."""
    ids = [r.id for r in reportes]
    if usuario is None or not ids:
        return set()
    return set(
        db.scalars(
            select(ConfirmacionReporte.reporte_id)
            .join(Reporte, Reporte.id == ConfirmacionReporte.reporte_id)
            .where(
                ConfirmacionReporte.usuario_id == usuario.id,
                ConfirmacionReporte.reporte_id.in_(ids),
                ConfirmacionReporte.ciclo_vigencia == Reporte.ciclo_vigencia,
            )
        )
    )


def vigencia_de(r: Reporte, conteos: Conteos) -> Vigencia | None:
    if r.tipo_dano != TipoDano.ENCHARCAMIENTO or r.vigente_hasta is None:
        return None
    return Vigencia(
        vigente_hasta=r.vigente_hasta,
        sigue_ahi=r.ciclo_vigencia,
        ya_no_hay_agua=conteos.get(r.id, (0, 0))[1],
    )


def detalle_de(r: Reporte) -> DetalleBache | DetalleAlcantarilla | DetalleEncharcamiento:
    if r.tipo_dano == TipoDano.BACHE:
        return DetalleBache(
            tamano=r.tamano, profundidad=r.profundidad, carril_afectado=r.carril_afectado  # type: ignore[arg-type]
        )
    if r.tipo_dano == TipoDano.ALCANTARILLA:
        return DetalleAlcantarilla(esta_senalizado=bool(r.esta_senalizado))
    return DetalleEncharcamiento(
        nivel_agua=r.nivel_agua,  # type: ignore[arg-type]
        hay_riesgo_personas_vehiculos=r.hay_riesgo_personas_vehiculos,
    )


def a_resumen(r: Reporte, conteos: Conteos, hoy: date | None = None) -> ReporteResumenPublico:
    return ReporteResumenPublico(
        folio=r.folio,
        tipo_dano=r.tipo_dano,
        estado=r.estado,
        etiqueta_publica=etiqueta_publica(r),
        severidad=r.severidad,
        ubicacion=Ubicacion(latitud=r.latitud, longitud=r.longitud),
        calle=r.calle,
        colonia=ColoniaRef(id=r.colonia.id, nombre=r.colonia.nombre),
        created_at=r.created_at,
        longevidad_dias=longevidad_dias(r, hoy),
        vigencia=vigencia_de(r, conteos),
    )


def a_publico(
    r: Reporte,
    conteos: Conteos,
    usuario: Usuario | None = None,
    confirmados: set[int] | None = None,
    hoy: date | None = None,
) -> ReportePublico:
    base = a_resumen(r, conteos, hoy).model_dump()
    return ReportePublico(
        **base,
        referencia=r.referencia,
        sector=SectorRef(id=r.colonia.sector.id, nombre=r.colonia.sector.nombre),
        descripcion=r.descripcion,
        detalle=detalle_de(r),
        confirmaciones=conteos.get(r.id, (0, 0))[0],
        fecha_programada=r.fecha_programada,
        fecha_reparacion=r.fecha_reparacion,
        es_mio=(r.usuario_id == usuario.id) if usuario else None,
        ya_confirmado_por_mi=(r.id in (confirmados or set())) if usuario else None,
    )


def a_mi_reporte(r: Reporte, hoy: date | None = None) -> MiReporte:
    return MiReporte(
        folio=r.folio,
        tipo_dano=r.tipo_dano,
        estado=r.estado,
        etiqueta_publica=etiqueta_publica(r),
        severidad=r.severidad,
        calle=r.calle,
        colonia=ColoniaRef(id=r.colonia.id, nombre=r.colonia.nombre),
        created_at=r.created_at,
        motivo_rechazo=r.motivo_rechazo,
        longevidad_dias=longevidad_dias(r, hoy),
    )
