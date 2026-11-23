"""Colonias de interés (HU-01.4) y resumen público por colonia (HU-07.2)."""

from sqlalchemy import Float, cast, func, select
from sqlalchemy.orm import Session

from app.core.errores import ErrorAPI
from app.core.tiempo import ahora_utc
from app.models import (
    ESTADOS_PAVIMENTO_ABIERTOS,
    TIPOS_PAVIMENTO,
    Colonia,
    ColoniaFavorita,
    EstadoReporte,
    Reporte,
    TipoDano,
    Usuario,
)
from app.services.sqlutil import error_validacion, fecha_local_sql

MAX_FAVORITAS = 20


# ------------------------------------------------------------------------------- colonias favoritas (HU-01.4)


def favoritas(db: Session, usuario: Usuario) -> list[ColoniaFavorita]:
    return list(
        db.scalars(
            select(ColoniaFavorita).join(Colonia, Colonia.id == ColoniaFavorita.colonia_id)
            .where(ColoniaFavorita.usuario_id == usuario.id).order_by(Colonia.nombre)
        )
    )


def ids_favoritas(db: Session, usuario: Usuario | None) -> list[int]:
    if usuario is None:
        return []
    return list(db.scalars(select(ColoniaFavorita.colonia_id).where(ColoniaFavorita.usuario_id == usuario.id)))


def agregar(db: Session, usuario: Usuario, colonia_id: int) -> tuple[ColoniaFavorita, bool]:
    """Devuelve (favorita, creada). Sólo se agregan colonias activas; si ya estaba, no se duplica."""
    existente = db.get(ColoniaFavorita, (usuario.id, colonia_id))
    if existente is not None:
        return existente, False
    colonia = db.get(Colonia, colonia_id)
    if colonia is None or not colonia.activo:
        raise error_validacion("colonia_id", "La colonia no existe o no está activa.")
    if len(ids_favoritas(db, usuario)) >= MAX_FAVORITAS:
        raise error_validacion("colonia_id", f"Puedes elegir hasta {MAX_FAVORITAS} colonias de interés.")
    fav = ColoniaFavorita(usuario_id=usuario.id, colonia_id=colonia_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav, True


def quitar(db: Session, usuario: Usuario, colonia_id: int) -> None:
    fav = db.get(ColoniaFavorita, (usuario.id, colonia_id))
    if fav is None:
        raise ErrorAPI(404, "NO_ENCONTRADO", "Esa colonia no está entre tus colonias de interés.")
    db.delete(fav)
    db.commit()


# ------------------------------------------------------------------------------- resumen por colonia (HU-07.2)


def resumen_colonia(db: Session, colonia_id: int) -> dict:
    """Métricas públicas de una colonia, sin datos personales (RN-04).

    * Abiertos: baches y alcantarillas en Recibido, Validado, Programado o En reparación (los «Recibido» cuentan
      porque son públicos como «Sin validar», RN-09). Nunca cuenta «Rechazado».
    * Tiempo promedio de reparación: días entre la fecha local del reporte y `fecha_reparacion` (RN-10) de todos los
      reparados de la colonia, histórico completo. `null` si aún no hay reparados.
    """
    colonia = db.get(Colonia, colonia_id)
    if colonia is None:
        raise ErrorAPI(404, "NO_ENCONTRADO", "La colonia no existe.")
    pavimento = [Reporte.colonia_id == colonia_id, Reporte.tipo_dano.in_(TIPOS_PAVIMENTO)]
    por_estado = dict(
        db.execute(
            select(Reporte.estado, func.count()).where(*pavimento, Reporte.estado.in_(ESTADOS_PAVIMENTO_ABIERTOS))
            .group_by(Reporte.estado)
        ).all()
    )
    reparados, promedio = db.execute(
        select(
            func.count(),
            func.avg(cast(Reporte.fecha_reparacion - fecha_local_sql(Reporte.created_at), Float)),
        ).where(*pavimento, Reporte.estado == EstadoReporte.REPARADO)
    ).one()
    encharcamientos_activos = db.scalar(
        select(func.count()).where(
            Reporte.colonia_id == colonia_id,
            Reporte.tipo_dano == TipoDano.ENCHARCAMIENTO,
            Reporte.estado == EstadoReporte.ACTIVO,
            Reporte.vigente_hasta > ahora_utc(),
        )
    ) or 0
    return {
        "colonia": {"id": colonia.id, "nombre": colonia.nombre},
        "sector": {"id": colonia.sector.id, "nombre": colonia.sector.nombre},
        "codigo_postal": colonia.codigo_postal,
        "activa": colonia.activo,
        "abiertos": sum(por_estado.values()),
        "abiertos_por_estado": {e.value: por_estado.get(e, 0) for e in ESTADOS_PAVIMENTO_ABIERTOS},
        "reparados": reparados or 0,
        "tiempo_promedio_reparacion_dias": round(float(promedio), 1) if promedio is not None else None,
        "encharcamientos_activos": encharcamientos_activos,
        "criterios": {
            "abiertos": "Baches y alcantarillas en Recibido (Sin validar), Validado, Programado o En reparación.",
            "tiempo_promedio_reparacion": "Promedio de días entre la fecha del reporte y la fecha de reparación, "
            "de todos los reportes reparados de la colonia (histórico completo, hora de Ciudad Juárez).",
        },
        "actualizado_en": ahora_utc(),
    }
