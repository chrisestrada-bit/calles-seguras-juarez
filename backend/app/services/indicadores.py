"""Indicadores públicos y de moderación. Históricos y reparados cuentan; los Rechazados se excluyen."""

from datetime import date

from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.core.tiempo import ahora_utc
from app.models import (
    ESTADOS_PAVIMENTO_ABIERTOS,
    TIPOS_PAVIMENTO,
    Colonia,
    EstadoReporte,
    HistorialEstado,
    NivelAgua,
    Reporte,
    Sector,
    TipoDano,
)
from app.core.config import get_settings
from app.schemas.comun import ColoniaRef, SectorRef
from app.services.presentacion import longevidad_dias
from app.services.sqlutil import fecha_local_sql, hoy_local_sql, validar_rango_fechas


def _redondear(valor, decimales: int = 1) -> float | None:
    return round(float(valor), decimales) if valor is not None else None


def _filtros(desde: date | None, hasta: date | None, sector_id: int | None = None) -> list:
    validar_rango_fechas(desde, hasta)
    condiciones = []
    if desde:
        condiciones.append(fecha_local_sql(Reporte.created_at) >= desde)
    if hasta:
        condiciones.append(fecha_local_sql(Reporte.created_at) <= hasta)
    if sector_id:
        condiciones.append(Colonia.sector_id == sector_id)
    return condiciones


def _base(*columnas):
    return select(*columnas).select_from(Reporte).join(Colonia, Reporte.colonia_id == Colonia.id)


def resumen(db: Session, desde: date | None, hasta: date | None, sector_id: int | None) -> dict:
    filtros = _filtros(desde, hasta, sector_id)
    publico = Reporte.estado != EstadoReporte.RECHAZADO

    por_estado = {e.value: 0 for e in (*ESTADOS_PAVIMENTO_ABIERTOS, EstadoReporte.REPARADO)}
    por_tipo = {t.value: 0 for t in TIPOS_PAVIMENTO}
    for estado, tipo, n in db.execute(
        _base(Reporte.estado, Reporte.tipo_dano, func.count())
        .where(publico, Reporte.tipo_dano.in_(TIPOS_PAVIMENTO), *filtros)
        .group_by(Reporte.estado, Reporte.tipo_dano)
    ):
        por_estado[estado.value] += n
        por_tipo[tipo.value] += n

    dias_abierto = hoy_local_sql() - fecha_local_sql(Reporte.created_at)
    long_abiertos = db.scalar(
        _base(func.avg(dias_abierto)).where(
            Reporte.tipo_dano.in_(TIPOS_PAVIMENTO), Reporte.estado.in_(ESTADOS_PAVIMENTO_ABIERTOS), *filtros
        )
    )
    t_reparacion = db.scalar(
        _base(func.avg(Reporte.fecha_reparacion - fecha_local_sql(Reporte.created_at))).where(
            Reporte.tipo_dano.in_(TIPOS_PAVIMENTO), Reporte.estado == EstadoReporte.REPARADO, *filtros
        )
    )

    es_enc = Reporte.tipo_dano == TipoDano.ENCHARCAMIENTO
    enc = db.execute(
        _base(
            func.count(),
            func.count().filter(Reporte.estado == EstadoReporte.ACTIVO, Reporte.vigente_hasta > ahora_utc()),
            func.count().filter(Reporte.estado == EstadoReporte.HISTORICO),
            func.count().filter(Reporte.nivel_agua == NivelAgua.INTRANSITABLE),
        ).where(publico, es_enc, *filtros)
    ).one()

    return {
        "periodo": {"desde": desde, "hasta": hasta, "zona_horaria": get_settings().app_timezone},
        "pavimento": {
            "total": sum(por_estado.values()),
            "por_estado": por_estado,
            "por_tipo": por_tipo,
            "longevidad_promedio_abiertos_dias": _redondear(long_abiertos),
            "tiempo_promedio_reparacion_dias": _redondear(t_reparacion),
        },
        "encharcamientos": {
            "total": enc[0],
            "activos": enc[1],
            "historicos": enc[2],
            "intransitables": enc[3],
        },
        "actualizado_en": ahora_utc(),
    }


def por_sector(db: Session, desde: date | None, hasta: date | None) -> list[dict]:
    filtros = _filtros(desde, hasta)
    publico = Reporte.estado != EstadoReporte.RECHAZADO
    es_bache = Reporte.tipo_dano == TipoDano.BACHE
    dias_abierto = hoy_local_sql() - fecha_local_sql(Reporte.created_at)
    abierto = (es_bache, Reporte.estado.in_(ESTADOS_PAVIMENTO_ABIERTOS))
    filas = {
        sid: fila
        for sid, *fila in db.execute(
            _base(
                Colonia.sector_id,
                func.count().filter(*abierto),
                func.count().filter(es_bache, Reporte.estado == EstadoReporte.REPARADO),
                func.avg(dias_abierto).filter(*abierto),
                func.count().filter(Reporte.tipo_dano == TipoDano.ENCHARCAMIENTO),
                func.count().filter(
                    Reporte.tipo_dano == TipoDano.ENCHARCAMIENTO,
                    Reporte.estado == EstadoReporte.ACTIVO,
                    Reporte.vigente_hasta > ahora_utc(),
                ),
            )
            .where(publico, *filtros)
            .group_by(Colonia.sector_id)
        )
    }
    resultado = []
    for sector in db.scalars(select(Sector).where(Sector.activo).order_by(Sector.nombre)):
        ab, rep, prom, enc_total, enc_act = filas.get(sector.id, (0, 0, None, 0, 0))
        resultado.append(
            {
                "sector": SectorRef(id=sector.id, nombre=sector.nombre),
                "baches_abiertos": ab,
                "reparados": rep,
                "longevidad_promedio_abiertos_dias": _redondear(prom),
                "encharcamientos_total": enc_total,
                "encharcamientos_activos": enc_act,
            }
        )
    resultado.sort(key=lambda f: (-f["baches_abiertos"], f["sector"].nombre))
    return resultado


def mas_antiguos(db: Session, sector_id: int | None, limite: int) -> list[dict]:
    condiciones = [Reporte.tipo_dano.in_(TIPOS_PAVIMENTO), Reporte.estado.in_(ESTADOS_PAVIMENTO_ABIERTOS)]
    if sector_id:
        condiciones.append(Colonia.sector_id == sector_id)
    reportes = db.scalars(
        select(Reporte)
        .join(Colonia, Reporte.colonia_id == Colonia.id)
        .where(*condiciones)
        .order_by(Reporte.created_at.asc(), Reporte.id)
        .limit(limite)
    ).all()
    return [
        {
            "folio": r.folio,
            "tipo_dano": r.tipo_dano,
            "estado": r.estado,
            "severidad": r.severidad,
            "calle": r.calle,
            "colonia": ColoniaRef(id=r.colonia.id, nombre=r.colonia.nombre),
            "created_at": r.created_at,
            "longevidad_dias": longevidad_dias(r) or 0,
        }
        for r in reportes
    ]


def moderacion(db: Session, desde: date | None, hasta: date | None) -> dict:
    filtros = _filtros(desde, hasta)
    ahora = ahora_utc()
    pendientes, mas_viejo = db.execute(
        select(func.count(), func.min(Reporte.created_at)).where(Reporte.estado == EstadoReporte.RECIBIDO)
    ).one()
    horas_validacion = db.scalar(
        select(func.avg(extract("epoch", HistorialEstado.created_at - Reporte.created_at) / 3600))
        .select_from(HistorialEstado)
        .join(Reporte, Reporte.id == HistorialEstado.reporte_id)
        .where(HistorialEstado.estado_nuevo == EstadoReporte.VALIDADO, *filtros)
    )
    total, rechazados, forzados, enc_rechazados = db.execute(
        select(
            func.count(),
            func.count().filter(Reporte.estado == EstadoReporte.RECHAZADO),
            func.count().filter(Reporte.forzado_como_nuevo),
            func.count().filter(
                Reporte.estado == EstadoReporte.RECHAZADO, Reporte.tipo_dano == TipoDano.ENCHARCAMIENTO
            ),
        )
        .select_from(Reporte)
        .where(*filtros)
    ).one()
    return {
        "pendientes_validacion": pendientes,
        "antiguedad_max_pendiente_horas": _redondear((ahora - mas_viejo).total_seconds() / 3600) if mas_viejo else None,
        "tiempo_promedio_validacion_horas": _redondear(horas_validacion),
        "rechazados_periodo": rechazados,
        "tasa_rechazo_pct": round(100 * rechazados / total, 1) if total else 0.0,
        "reportes_forzados_como_nuevos": forzados,
        "encharcamientos_rechazados": enc_rechazados,
    }

