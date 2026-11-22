"""Moderación: cola de trabajo y transiciones de estado (RN-05, RN-07, RN-10)."""

from datetime import date, timedelta
import uuid

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.errores import ErrorAPI
from app.core.tiempo import ahora_utc, fecha_local, hoy_local
from app.models import (
    Colonia,
    ConfirmacionReporte,
    EstadoReporte,
    HistorialEstado,
    OrigenCambio,
    Reporte,
    Severidad,
    TipoConfirmacion,
    TipoDano,
    Usuario,
)
from app.schemas.comun import ColoniaRef, ParametrosPagina, SectorRef, Ubicacion
from app.schemas.moderacion import (
    HistorialModeracionItem,
    ReporteModeracion,
    ReporteModeracionItem,
    TransicionIn,
    TransicionOut,
)
from app.services import transiciones
from app.services.historial import fijar_contexto
from app.services.presentacion import conteos_confirmaciones, detalle_de, longevidad_dias
from app.services.sqlutil import error_validacion, fecha_local_sql, validar_rango_fechas

_RANGO_SEVERIDAD = case({Severidad.ALTA: 3, Severidad.MEDIA: 2}, value=Reporte.severidad, else_=1)


def _reportes_por_autor_24h(db: Session, autores: set[uuid.UUID]) -> dict[uuid.UUID, int]:
    if not autores:
        return {}
    filas = db.execute(
        select(Reporte.usuario_id, func.count())
        .where(Reporte.usuario_id.in_(autores), Reporte.created_at > ahora_utc() - timedelta(hours=24))
        .group_by(Reporte.usuario_id)
    ).all()
    return {uid: n for uid, n in filas}


def _item(r: Reporte, rol, conteos, por_autor) -> dict:
    return {
        "folio": r.folio,
        "tipo_dano": r.tipo_dano,
        "estado": r.estado,
        "severidad": r.severidad,
        "calle": r.calle,
        "colonia": ColoniaRef(id=r.colonia.id, nombre=r.colonia.nombre),
        "sector": SectorRef(id=r.colonia.sector.id, nombre=r.colonia.sector.nombre),
        "confirmaciones": conteos.get(r.id, (0, 0))[0],
        "forzado_como_nuevo": r.forzado_como_nuevo,
        "autor_id": r.usuario_id,  # sólo UUID: nunca nombre ni correo
        "reportes_autor_ultimas_24h": por_autor.get(r.usuario_id, 0),
        "created_at": r.created_at,
        "transiciones_disponibles": transiciones.disponibles(r.tipo_dano, r.estado, rol),
    }


def listar_cola(
    db: Session,
    usuario: Usuario,
    *,
    estados: list[EstadoReporte] | None,
    tipo: TipoDano | None,
    sector_id: int | None,
    colonia_id: int | None,
    severidad: Severidad | None,
    desde: date | None,
    hasta: date | None,
    autor_id: uuid.UUID | None,
    orden: str,
    pag: ParametrosPagina,
) -> tuple[list[ReporteModeracionItem], int]:
    validar_rango_fechas(desde, hasta)
    condiciones = [Reporte.estado.in_(estados or [EstadoReporte.RECIBIDO])]
    if tipo:
        condiciones.append(Reporte.tipo_dano == tipo)
    if sector_id:
        condiciones.append(Colonia.sector_id == sector_id)
    if colonia_id:
        condiciones.append(Reporte.colonia_id == colonia_id)
    if severidad:
        condiciones.append(Reporte.severidad == severidad)
    if autor_id:
        condiciones.append(Reporte.usuario_id == autor_id)
    if desde:
        condiciones.append(fecha_local_sql(Reporte.created_at) >= desde)
    if hasta:
        condiciones.append(fecha_local_sql(Reporte.created_at) <= hasta)

    confirmaciones = (
        select(func.count())
        .where(
            ConfirmacionReporte.reporte_id == Reporte.id,
            ConfirmacionReporte.tipo.in_([TipoConfirmacion.CONFIRMACION_DANO, TipoConfirmacion.SIGUE_AHI]),
        )
        .correlate(Reporte)
        .scalar_subquery()
    )
    ordenes = {
        "antiguos": [Reporte.created_at.asc()],
        "recientes": [Reporte.created_at.desc()],
        "severidad": [_RANGO_SEVERIDAD.desc(), Reporte.created_at.asc()],
        "confirmaciones": [confirmaciones.desc(), Reporte.created_at.asc()],
    }
    total = db.scalar(
        select(func.count()).select_from(Reporte).join(Colonia, Reporte.colonia_id == Colonia.id).where(*condiciones)
    ) or 0
    filas = list(
        db.scalars(
            select(Reporte)
            .join(Colonia, Reporte.colonia_id == Colonia.id)
            .where(*condiciones)
            .order_by(*ordenes.get(orden, ordenes["antiguos"]), Reporte.id)
            .limit(pag.por_pagina)
            .offset(pag.offset)
        )
    )
    conteos = conteos_confirmaciones(db, filas)
    por_autor = _reportes_por_autor_24h(db, {r.usuario_id for r in filas})
    return [ReporteModeracionItem(**_item(r, usuario.rol, conteos, por_autor)) for r in filas], total


def _obtener(db: Session, folio: str, *, bloquear: bool = False) -> Reporte:
    stmt = select(Reporte).where(Reporte.folio == folio)
    if bloquear:
        stmt = stmt.with_for_update(of=Reporte)
    reporte = db.scalar(stmt)
    if reporte is None:
        raise ErrorAPI(404, "NO_ENCONTRADO", f"No existe un reporte con el folio {folio}.")
    return reporte


def detalle(db: Session, usuario: Usuario, folio: str) -> ReporteModeracion:
    r = _obtener(db, folio)
    conteos = conteos_confirmaciones(db, [r])
    por_autor = _reportes_por_autor_24h(db, {r.usuario_id})
    filas = db.execute(
        select(HistorialEstado, Usuario.rol)
        .outerjoin(Usuario, Usuario.id == HistorialEstado.usuario_id)
        .where(HistorialEstado.reporte_id == r.id)
        .order_by(HistorialEstado.created_at, HistorialEstado.id)
    ).all()
    historial = [
        HistorialModeracionItem(
            estado_anterior=h.estado_anterior,
            estado_nuevo=h.estado_nuevo,
            origen=h.origen.value,
            actor_id=h.usuario_id,
            actor_rol=rol,
            motivo=h.motivo,
            fecha=h.created_at,
        )
        for h, rol in filas
    ]
    return ReporteModeracion(
        **_item(r, usuario.rol, conteos, por_autor),
        ubicacion=Ubicacion(latitud=r.latitud, longitud=r.longitud),
        referencia=r.referencia,
        descripcion=r.descripcion,
        detalle=detalle_de(r),
        motivo_rechazo=r.motivo_rechazo,
        fecha_programada=r.fecha_programada,
        fecha_reparacion=r.fecha_reparacion,
        historial=historial,
    )


def transicionar(db: Session, usuario: Usuario, folio: str, datos: TransicionIn) -> TransicionOut:
    reporte = _obtener(db, folio, bloquear=True)
    anterior, nuevo = reporte.estado, datos.estado_nuevo
    transiciones.validar_transicion(reporte.tipo_dano, anterior, nuevo, usuario.rol)  # RN-05: 400 / 403

    if nuevo == EstadoReporte.REPARADO:
        inicio = fecha_local(reporte.created_at)
        if datos.fecha_reparacion is None:
            raise error_validacion("fecha_reparacion", "La fecha de reparación es obligatoria.")
        if not inicio <= datos.fecha_reparacion <= hoy_local():
            raise ErrorAPI(
                422,
                "FECHA_REPARACION_INVALIDA",
                "La fecha de reparación debe ser igual o posterior a la fecha del reporte y no puede ser futura.",
                [
                    {
                        "campo": "fecha_reparacion",
                        "mensaje": f"La fecha {datos.fecha_reparacion.isoformat()} debe estar entre "
                        f"{inicio.isoformat()} y {hoy_local().isoformat()}.",
                    }
                ],
            )
        reporte.fecha_reparacion = datos.fecha_reparacion
    elif datos.fecha_reparacion is not None:
        raise error_validacion("fecha_reparacion", "Sólo se indica al pasar a «Reparado».")

    if nuevo == EstadoReporte.PROGRAMADO and datos.fecha_programada is not None:
        if datos.fecha_programada < hoy_local():
            raise error_validacion("fecha_programada", "La fecha programada no puede ser anterior a hoy.")
        reporte.fecha_programada = datos.fecha_programada
    elif nuevo != EstadoReporte.PROGRAMADO and datos.fecha_programada is not None:
        raise error_validacion("fecha_programada", "Sólo se indica al pasar a «Programado».")

    if nuevo == EstadoReporte.RECHAZADO:
        reporte.motivo_rechazo = datos.motivo  # RN-07: motivo obligatorio (validado en el esquema)

    ahora = ahora_utc()
    fijar_contexto(db, usuario_id=usuario.id, origen=OrigenCambio.MODERACION, motivo=datos.motivo, fecha_evento=ahora)
    reporte.estado = nuevo
    db.flush()
    resultado = TransicionOut(
        folio=reporte.folio,
        estado_anterior=anterior,
        estado=nuevo,
        fecha_reparacion=reporte.fecha_reparacion,
        longevidad_dias=longevidad_dias(reporte),
        registrado_en=ahora,
        mensaje=f'El reporte {reporte.folio} cambió a "{nuevo.value}".',
    )
    db.commit()
    return resultado
