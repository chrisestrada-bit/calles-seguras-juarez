"""Creación y consulta de reportes: RN-01, RN-03, RN-08, RN-09, HU-02.2, HU-02.3, HU-03.1."""

from datetime import date, timedelta

from sqlalchemy import Float, case, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errores import ErrorAPI, fuera_de_juarez
from app.core.tiempo import ahora_utc
from app.models import (
    ESTADOS_PAVIMENTO_ABIERTOS,
    Colonia,
    EstadoReporte,
    HistorialEstado,
    NivelAgua,
    OrigenCambio,
    ProfundidadBache,
    Reporte,
    Severidad,
    TamanoBache,
    TipoDano,
    Usuario,
)
from app.schemas.comun import ParametrosPagina
from app.schemas.reportes import BacheIn, EncharcamientoIn, ReporteCrear, ReporteEditar
from app.services import geo
from app.services.folios import generar_folio
from app.services.historial import fijar_contexto
from app.services.presentacion import etiqueta_publica
from app.services.sqlutil import (
    error_validacion,
    escapar_like,
    fecha_local_sql,
    parsear_bbox,
    validar_rango_fechas,
)
from app.services.vigencia import VIGENCIA

LIMITE_REPORTES_POR_HORA = 10  # RN-08
VENTANA_LIMITE = timedelta(hours=1)


# --------------------------------------------------------------------------- reglas de dominio


def severidad_bache(tamano: TamanoBache, profundidad: ProfundidadBache) -> Severidad:
    if tamano == TamanoBache.GRANDE or profundidad == ProfundidadBache.MAS_10:
        return Severidad.ALTA
    if tamano == TamanoBache.MEDIANO or profundidad == ProfundidadBache.DE_5_A_10:
        return Severidad.MEDIA
    return Severidad.BAJA


def severidad_encharcamiento(nivel: NivelAgua) -> Severidad:
    if nivel == NivelAgua.INTRANSITABLE:
        return Severidad.ALTA
    if nivel == NivelAgua.A_MEDIA_LLANTA:
        return Severidad.MEDIA
    return Severidad.BAJA


def calcular_severidad(payload: ReporteCrear) -> Severidad:
    """La severidad nunca la envía el cliente (HU-02.2); la alcantarilla sin tapa es siempre Alta."""
    if isinstance(payload, BacheIn):
        return severidad_bache(payload.tamano, payload.profundidad)
    if isinstance(payload, EncharcamientoIn):
        return severidad_encharcamiento(payload.nivel_agua)
    return Severidad.ALTA


def verificar_territorio(latitud: float, longitud: float) -> None:
    if not geo.dentro_de_juarez(latitud, longitud):
        campo = "latitud" if not geo.LAT_MIN <= latitud <= geo.LAT_MAX else "longitud"
        rango = (
            f"Debe estar entre {geo.LAT_MIN:.2f} y {geo.LAT_MAX:.2f}."
            if campo == "latitud"
            else f"Debe estar entre {geo.LON_MIN:.2f} y {geo.LON_MAX:.2f}."
        )
        raise fuera_de_juarez(campo, rango)


def radio_duplicados(tipo: TipoDano) -> int:
    return (
        geo.RADIO_DUPLICADO_ENCHARCAMIENTO_M
        if tipo == TipoDano.ENCHARCAMIENTO
        else geo.RADIO_DUPLICADO_PAVIMENTO_M
    )


def buscar_cercanos(db: Session, tipo: TipoDano, latitud: float, longitud: float) -> list[tuple[Reporte, float]]:
    """Duplicados por Haversine: bache/alcantarilla abierto a ≤ 30 m; encharcamiento vigente a ≤ 50 m."""
    radio = radio_duplicados(tipo)
    lat_min, lat_max, lon_min, lon_max = geo.caja_envolvente(latitud, longitud, radio)
    distancia = func.distancia_haversine_m(Reporte.latitud, Reporte.longitud, latitud, longitud, type_=Float)
    condiciones = [
        Reporte.latitud.between(lat_min, lat_max),  # prefiltro con índice parcial
        Reporte.longitud.between(lon_min, lon_max),
        distancia <= radio,
        Reporte.tipo_dano == tipo,
    ]
    if tipo == TipoDano.ENCHARCAMIENTO:
        condiciones += [Reporte.estado == EstadoReporte.ACTIVO, Reporte.vigente_hasta > ahora_utc()]
    else:
        condiciones.append(Reporte.estado.in_(ESTADOS_PAVIMENTO_ABIERTOS))
    filas = db.execute(select(Reporte, distancia).where(*condiciones).order_by(distancia)).all()
    return [(r, float(d)) for r, d in filas]


def contar_reportes_ultima_hora(db: Session, usuario_id) -> int:
    return db.scalar(
        select(func.count()).where(
            Reporte.usuario_id == usuario_id, Reporte.created_at > ahora_utc() - VENTANA_LIMITE
        )
    ) or 0


def _verificar_limite_por_hora(db: Session, usuario: Usuario) -> None:
    """RN-08. El candado asesor serializa solicitudes concurrentes de la misma cuenta."""
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:u))"), {"u": str(usuario.id)})
    ahora = ahora_utc()
    recientes = db.scalars(
        select(Reporte.created_at)
        .where(Reporte.usuario_id == usuario.id, Reporte.created_at > ahora - VENTANA_LIMITE)
        .order_by(Reporte.created_at.desc())
        .limit(LIMITE_REPORTES_POR_HORA)
    ).all()
    if len(recientes) >= LIMITE_REPORTES_POR_HORA:
        espera = max(1, int((recientes[-1] + VENTANA_LIMITE - ahora).total_seconds()) + 1)
        db.rollback()
        raise ErrorAPI(
            429,
            "LIMITE_REPORTES",
            "Alcanzaste el máximo de 10 reportes por hora. Intenta de nuevo más tarde.",
            headers={"Retry-After": str(espera)},
        )


# --------------------------------------------------------------------------- creación


def _por_clave(db: Session, usuario: Usuario, clave) -> Reporte | None:
    if clave is None:
        return None
    return db.scalar(select(Reporte).where(Reporte.usuario_id == usuario.id, Reporte.idempotency_key == clave))


def crear_reporte(db: Session, usuario: Usuario, payload: ReporteCrear) -> Reporte:
    # HU-08.4: reenviar el mismo borrador offline devuelve el reporte ya creado (sin folio nuevo ni tope RN-08).
    previo = _por_clave(db, usuario, payload.idempotency_key)
    if previo is not None:
        previo._reutilizado = True  # type: ignore[attr-defined]
        return previo
    tipo = TipoDano(payload.tipo_dano)
    verificar_territorio(payload.latitud, payload.longitud)  # RN-01 (defensa en profundidad)

    colonia = db.get(Colonia, payload.colonia_id)
    if colonia is None or not colonia.activo:
        raise error_validacion("colonia_id", "La colonia seleccionada no existe o no está activa.")

    _verificar_limite_por_hora(db, usuario)  # RN-08

    if not payload.forzar_nuevo:  # HU-02.3 / HU-03.1
        candidatos = buscar_cercanos(db, tipo, payload.latitud, payload.longitud)
        if candidatos:
            db.rollback()
            raise ErrorAPI(
                409,
                "POSIBLE_DUPLICADO",
                "Ya existe un reporte abierto muy cerca de este punto. "
                "Confírmalo o indica que se trata de un daño distinto.",
                [
                    {
                        "folio": c.folio,
                        "tipo_dano": c.tipo_dano.value,
                        "etiqueta_publica": etiqueta_publica(c),
                        "distancia_metros": round(d, 1),
                        "calle": c.calle,
                    }
                    for c, d in candidatos
                ],
            )

    creado = ahora_utc()
    es_enc = tipo == TipoDano.ENCHARCAMIENTO
    reporte = Reporte(
        folio=generar_folio(db, tipo, creado),  # RN-03
        tipo_dano=tipo,
        estado=EstadoReporte.ACTIVO if es_enc else EstadoReporte.RECIBIDO,  # RN-06: nace Activo
        severidad=calcular_severidad(payload),
        usuario_id=usuario.id,
        colonia=colonia,
        latitud=payload.latitud,
        longitud=payload.longitud,
        calle=payload.calle,
        referencia=payload.referencia,
        descripcion=payload.descripcion,
        tamano=getattr(payload, "tamano", None),
        profundidad=getattr(payload, "profundidad", None),
        carril_afectado=getattr(payload, "carril_afectado", None),
        esta_senalizado=getattr(payload, "esta_senalizado", None),
        nivel_agua=getattr(payload, "nivel_agua", None),
        hay_riesgo_personas_vehiculos=getattr(payload, "hay_riesgo_personas_vehiculos", None),
        vigencia_inicio=creado if es_enc else None,
        vigente_hasta=creado + VIGENCIA if es_enc else None,
        ciclo_vigencia=0,
        forzado_como_nuevo=payload.forzar_nuevo,
        idempotency_key=payload.idempotency_key,
        created_at=creado,  # RN-10: inmutable desde aquí
        updated_at=creado,
    )
    fijar_contexto(db, usuario_id=usuario.id, origen=OrigenCambio.CIUDADANO, fecha_evento=creado)
    db.add(reporte)
    try:
        db.flush()
        db.commit()
    except IntegrityError:
        db.rollback()
        carrera = _por_clave(db, usuario, payload.idempotency_key)  # dos envíos simultáneos del mismo borrador
        if carrera is None:
            raise
        carrera._reutilizado = True  # type: ignore[attr-defined]
        return carrera
    return reporte


# --------------------------------------------------------------------------- consultas


def obtener_visible(db: Session, folio: str) -> Reporte:
    """Detalle público: los Rechazados no se muestran ni revelan su existencia (RN-09)."""
    reporte = db.scalar(
        select(Reporte).where(Reporte.folio == folio, Reporte.estado != EstadoReporte.RECHAZADO)
    )
    if reporte is None:
        raise ErrorAPI(404, "NO_ENCONTRADO", f"No existe un reporte con el folio {folio}.")
    return reporte


def obtener_por_folio(db: Session, folio: str) -> Reporte:
    """Búsqueda sin filtro de visibilidad: el llamador decide quién puede ver el reporte (p. ej. fotos)."""
    reporte = db.scalar(select(Reporte).where(Reporte.folio == folio))
    if reporte is None:
        raise ErrorAPI(404, "NO_ENCONTRADO", f"No existe un reporte con el folio {folio}.")
    return reporte


def historial_publico(db: Session, reporte: Reporte) -> list[HistorialEstado]:
    return list(
        db.scalars(
            select(HistorialEstado)
            .where(HistorialEstado.reporte_id == reporte.id)
            .order_by(HistorialEstado.created_at, HistorialEstado.id)
        )
    )


_RANGO_SEVERIDAD = case({Severidad.ALTA: 3, Severidad.MEDIA: 2}, value=Reporte.severidad, else_=1)


def condiciones_publicas(
    *,
    tipos: list[TipoDano] | None,
    estados: list[EstadoReporte] | None,
    solo_vigentes: bool,
    colonia_id: int | None,
    sector_id: int | None,
    calle: str | None,
    bbox: str | None,
    desde: date | None,
    hasta: date | None,
) -> list:
    """Filtros de HU-04.2 compartidos por la lista, el mapa (HU-04.5) y la exportación (HU-07.3)."""
    if estados and EstadoReporte.RECHAZADO in estados:
        raise error_validacion("estado", "El estado «Rechazado» no está disponible en consultas públicas.")
    validar_rango_fechas(desde, hasta)

    condiciones = [Reporte.estado != EstadoReporte.RECHAZADO]  # RN-09
    if tipos:
        condiciones.append(Reporte.tipo_dano.in_(tipos))
    if estados:
        condiciones.append(Reporte.estado.in_(estados))
    if solo_vigentes:
        condiciones += [
            Reporte.tipo_dano == TipoDano.ENCHARCAMIENTO,
            Reporte.estado == EstadoReporte.ACTIVO,
            Reporte.vigente_hasta > ahora_utc(),
        ]
    if colonia_id:
        condiciones.append(Reporte.colonia_id == colonia_id)
    if sector_id:
        condiciones.append(Colonia.sector_id == sector_id)
    if calle:
        condiciones.append(Reporte.calle.ilike(f"%{escapar_like(calle)}%", escape="\\"))
    if bbox:
        lon_min, lat_min, lon_max, lat_max = parsear_bbox(bbox)
        condiciones += [
            Reporte.latitud.between(lat_min, lat_max),
            Reporte.longitud.between(lon_min, lon_max),
        ]
    if desde:
        condiciones.append(fecha_local_sql(Reporte.created_at) >= desde)
    if hasta:
        condiciones.append(fecha_local_sql(Reporte.created_at) <= hasta)
    return condiciones


_ORDENES = {
    "recientes": lambda: [Reporte.created_at.desc()],
    "longevidad": lambda: [Reporte.created_at.asc()],
    "severidad": lambda: [_RANGO_SEVERIDAD.desc(), Reporte.created_at.desc()],
}


def listar_publicos(
    db: Session,
    *,
    orden: str,
    pag: ParametrosPagina,
    **filtros,
) -> tuple[list[Reporte], int]:
    condiciones = condiciones_publicas(**filtros)
    total = db.scalar(
        select(func.count()).select_from(Reporte).join(Colonia, Reporte.colonia_id == Colonia.id).where(*condiciones)
    ) or 0
    filas = db.scalars(
        select(Reporte)
        .join(Colonia, Reporte.colonia_id == Colonia.id)
        .where(*condiciones)
        .order_by(*_ORDENES[orden](), Reporte.id.desc())
        .limit(pag.por_pagina)
        .offset(pag.offset)
    ).all()
    return list(filas), total


def listar_sin_paginar(db: Session, *, orden: str, limite: int, **filtros) -> tuple[list[Reporte], int]:
    """Todos los reportes que cumplen los filtros (hasta `limite`) y el total real. Para mapa y exportación."""
    condiciones = condiciones_publicas(**filtros)
    total = db.scalar(
        select(func.count()).select_from(Reporte).join(Colonia, Reporte.colonia_id == Colonia.id).where(*condiciones)
    ) or 0
    filas = db.scalars(
        select(Reporte)
        .join(Colonia, Reporte.colonia_id == Colonia.id)
        .where(*condiciones)
        .order_by(*_ORDENES[orden](), Reporte.id.desc())
        .limit(limite)
    ).all()
    return list(filas), total


def listar_mios(
    db: Session,
    usuario: Usuario,
    *,
    estado: EstadoReporte | None,
    tipo: TipoDano | None,
    pag: ParametrosPagina,
) -> tuple[list[Reporte], int]:
    condiciones = [Reporte.usuario_id == usuario.id]
    if estado:
        condiciones.append(Reporte.estado == estado)
    if tipo:
        condiciones.append(Reporte.tipo_dano == tipo)
    total = db.scalar(select(func.count()).select_from(Reporte).where(*condiciones)) or 0
    filas = db.scalars(
        select(Reporte).where(*condiciones).order_by(Reporte.created_at.desc()).limit(pag.por_pagina).offset(pag.offset)
    ).all()
    return list(filas), total


__all__ = [
    "LIMITE_REPORTES_POR_HORA",
    "buscar_cercanos",
    "calcular_severidad",
    "contar_reportes_ultima_hora",
    "crear_reporte",
    "historial_publico",
    "listar_mios",
    "condiciones_publicas",
    "listar_publicos",
    "listar_sin_paginar",
    "obtener_por_folio",
    "obtener_visible",
    "radio_duplicados",
    "verificar_territorio",
]


# --------------------------------------------------------------------------- edición (HU-02.5)

_CAMPOS_BACHE = {"tamano", "profundidad", "carril_afectado"}
_CAMPOS_ALCANTARILLA = {"esta_senalizado"}


def editar_reporte(db: Session, usuario: Usuario, folio: str, datos: ReporteEditar) -> Reporte:
    """Sólo el autor y sólo en «Recibido». No cambia estado, por lo que no genera historial."""
    reporte = db.scalar(select(Reporte).where(Reporte.folio == folio).with_for_update())
    if reporte is None:
        raise ErrorAPI(404, "NO_ENCONTRADO", f"No existe un reporte con el folio {folio}.")
    if reporte.usuario_id != usuario.id:
        raise ErrorAPI(403, "SIN_PERMISO", "Sólo la persona que creó el reporte puede editarlo.")
    if reporte.estado != EstadoReporte.RECIBIDO:
        raise ErrorAPI(
            409,
            "REPORTE_NO_EDITABLE",
            "Sólo puedes editar un reporte mientras está en estado «Recibido» (sin validar).",
        )

    cambios = datos.model_dump(include=datos.model_fields_set)
    if not cambios:
        raise error_validacion("cuerpo", "Indica al menos un campo para actualizar.")
    no_aplican = (_CAMPOS_ALCANTARILLA if reporte.tipo_dano == TipoDano.BACHE else _CAMPOS_BACHE) & cambios.keys()
    for campo in sorted(no_aplican):
        raise error_validacion(campo, f"Este campo no aplica a un reporte de tipo «{reporte.tipo_dano.value}».")
    for campo in ("calle", *_CAMPOS_BACHE, *_CAMPOS_ALCANTARILLA):
        if campo in cambios and cambios[campo] is None:
            raise error_validacion(campo, "Este campo no puede quedar vacío.")

    if "colonia_id" in cambios:
        colonia = db.get(Colonia, cambios.pop("colonia_id"))
        if colonia is None or not colonia.activo:
            raise error_validacion("colonia_id", "La colonia seleccionada no existe o no está activa.")
        reporte.colonia = colonia
    for campo, valor in cambios.items():
        setattr(reporte, campo, valor)
    if reporte.tipo_dano == TipoDano.BACHE:
        reporte.severidad = severidad_bache(reporte.tamano, reporte.profundidad)  # type: ignore[arg-type]
    db.commit()
    db.refresh(reporte)
    return reporte
