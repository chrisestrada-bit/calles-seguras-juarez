"""Routers de la Fase 3: cuadrillas, enlace municipal, perfil, trayecto y resumen público por colonia."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import CUALQUIER_ROL, SOLO_COORDINADOR, SOLO_ENLACE, get_db
from app.models import EstadoReporte, NivelAgua, Usuario
from app.schemas.comun import Latitud, Longitud, respuestas
from app.schemas.operacion import (
    AsignacionIn,
    AvanceIn,
    AvanceOut,
    BacheAsignado,
    ColoniaFavoritaOut,
    CuadrillaCrear,
    CuadrillaDetalle,
    CuadrillaEditar,
    CuadrillaOut,
    CuadrillaRef,
    EnlaceIn,
    EnlaceRef,
    EncharcamientoEnTrayecto,
    FavoritaIn,
    ListaCuadrillas,
    ListaFavoritas,
    MisAsignaciones,
    ResumenColonia,
    RutaOut,
    TrayectoOut,
)
from app.services import cuadrillas as svc_cuadrillas
from app.services import perfil_publico, transiciones, trayecto
from app.services.vigencia import expirar_vencidos

FolioPath = Annotated[str, Path(pattern=r"^(BCH|ENC)-[0-9]{4}-[0-9]{6}$")]


def _bache(a, r, *, rol=None) -> BacheAsignado:
    return BacheAsignado(
        asignacion_id=a.id,
        folio=r.folio,
        tipo_dano=r.tipo_dano,
        estado=r.estado,
        calle=r.calle,
        referencia=r.referencia,
        colonia={"id": r.colonia.id, "nombre": r.colonia.nombre},
        ubicacion={"latitud": r.latitud, "longitud": r.longitud},
        fecha_programada=a.fecha_programada,
        fecha_reparacion=r.fecha_reparacion,
        cuadrilla=a.cuadrilla.nombre,
        asignacion_activa=a.activa,
        asignado_en=a.created_at,
        transiciones_disponibles=transiciones.disponibles(r.tipo_dano, r.estado, rol) if rol is not None else [],
    )


def _cuadrilla(c, pendientes: dict[int, int]) -> CuadrillaOut:
    return CuadrillaOut(
        id=c.id, nombre=c.nombre, responsable=c.responsable, telefono_contacto=c.telefono_contacto,
        activa=c.activa, pendientes=pendientes.get(c.id, 0), created_at=c.created_at,
    )


# =============================================================================== cuadrillas (HU-05.4)

cuadrillas = APIRouter(prefix="/cuadrillas", tags=["cuadrillas"])


@cuadrillas.get("", response_model=ListaCuadrillas, summary="Cuadrillas (coordinación)", responses=respuestas(401, 403))
def listar_cuadrillas(solo_activas: bool = False, _: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> ListaCuadrillas:
    filas = svc_cuadrillas.listar(db, solo_activas=solo_activas)
    pendientes = svc_cuadrillas.pendientes_por_cuadrilla(db)
    return ListaCuadrillas(datos=[_cuadrilla(c, pendientes) for c in filas])


@cuadrillas.post("", response_model=CuadrillaOut, status_code=status.HTTP_201_CREATED, summary="Crear cuadrilla", responses=respuestas(401, 403, 409, 422))
def crear_cuadrilla(datos: CuadrillaCrear, _: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> CuadrillaOut:
    return _cuadrilla(svc_cuadrillas.crear(db, datos), {})


def _detalle(db: Session, c) -> CuadrillaDetalle:
    pendientes = svc_cuadrillas.pendientes_por_cuadrilla(db, [c.id])
    base = _cuadrilla(c, pendientes).model_dump()
    return CuadrillaDetalle(
        **base,
        enlaces=[EnlaceRef(id=u.id, nombre=u.nombre, activo=u.activo) for u in svc_cuadrillas.enlaces_de(db, c.id)],
        baches=[_bache(a, r) for a, r in svc_cuadrillas.asignaciones(db, c.id, solo_activas=False)],
    )


@cuadrillas.get("/{cuadrilla_id}", response_model=CuadrillaDetalle, summary="Detalle con baches asignados e historial", responses=respuestas(401, 403, 404))
def detalle_cuadrilla(cuadrilla_id: int, _: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> CuadrillaDetalle:
    return _detalle(db, svc_cuadrillas.obtener(db, cuadrilla_id))


@cuadrillas.patch("/{cuadrilla_id}", response_model=CuadrillaOut, summary="Editar o desactivar una cuadrilla", responses=respuestas(401, 403, 404, 409, 422))
def editar_cuadrilla(cuadrilla_id: int, datos: CuadrillaEditar, _: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> CuadrillaOut:
    c = svc_cuadrillas.editar(db, cuadrilla_id, datos)
    return _cuadrilla(c, svc_cuadrillas.pendientes_por_cuadrilla(db, [c.id]))


@cuadrillas.delete(
    "/{cuadrilla_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una cuadrilla sin trabajo pendiente ni historial (si no, 409: desactívala)",
    responses=respuestas(401, 403, 404, 409),
)
def eliminar_cuadrilla(cuadrilla_id: int, _: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> Response:
    svc_cuadrillas.eliminar(db, cuadrilla_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@cuadrillas.post(
    "/{cuadrilla_id}/asignaciones", response_model=BacheAsignado, status_code=status.HTTP_201_CREATED,
    summary="Asignar un bache «Validado» (pasa a «Programado») o reasignar uno «Programado»",
    responses=respuestas(400, 401, 403, 404, 409, 422),
)
def asignar(cuadrilla_id: int, datos: AsignacionIn, actor: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> BacheAsignado:
    a, r = svc_cuadrillas.asignar(db, actor, cuadrilla_id, datos.folio, datos.fecha_programada)
    return _bache(a, r)


@cuadrillas.post("/{cuadrilla_id}/enlaces", status_code=status.HTTP_204_NO_CONTENT, summary="Vincular una cuenta de enlace municipal", responses=respuestas(401, 403, 404, 422))
def vincular(cuadrilla_id: int, datos: EnlaceIn, _: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> Response:
    svc_cuadrillas.vincular_enlace(db, cuadrilla_id, datos.usuario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@cuadrillas.delete("/{cuadrilla_id}/enlaces/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desvincular un enlace municipal", responses=respuestas(401, 403, 404))
def desvincular(cuadrilla_id: int, usuario_id: uuid.UUID, _: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> Response:
    svc_cuadrillas.desvincular_enlace(db, cuadrilla_id, usuario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =============================================================================== enlace municipal (HU-05.5)

enlace = APIRouter(prefix="/enlace", tags=["enlace municipal"])


@enlace.get("/reportes", response_model=MisAsignaciones, summary="Baches asignados a mis cuadrillas", responses=respuestas(401, 403))
def mis_baches(incluir_reparados: bool = False, usuario: Usuario = Depends(SOLO_ENLACE), db: Session = Depends(get_db)) -> MisAsignaciones:
    return MisAsignaciones(
        cuadrillas=[CuadrillaRef(id=c.id, nombre=c.nombre, activa=c.activa) for c in svc_cuadrillas.cuadrillas_de_enlace(db, usuario)],
        datos=[_bache(a, r, rol=usuario.rol) for a, r in svc_cuadrillas.listar_del_enlace(db, usuario, incluir_reparados=incluir_reparados)],
    )


@enlace.get("/reportes/{folio}", response_model=BacheAsignado, summary="Detalle de un bache de mis cuadrillas (403 si es ajeno)", responses=respuestas(401, 403, 422))
def mi_bache(folio: FolioPath, usuario: Usuario = Depends(SOLO_ENLACE), db: Session = Depends(get_db)) -> BacheAsignado:
    a, r = svc_cuadrillas.reporte_del_enlace(db, usuario, folio)
    return _bache(a, r, rol=usuario.rol)


@enlace.post(
    "/reportes/{folio}/avance", response_model=AvanceOut,
    summary="Avanzar «Programado → En reparación → Reparado» (sólo baches de mis cuadrillas)",
    responses=respuestas(400, 401, 403, 422),
)
def avanzar(folio: FolioPath, datos: AvanceIn, usuario: Usuario = Depends(SOLO_ENLACE), db: Session = Depends(get_db)) -> AvanceOut:
    _, r, anterior = svc_cuadrillas.avanzar(db, usuario, folio, datos.estado_nuevo, datos.fecha_reparacion)
    return AvanceOut(
        folio=r.folio, estado_anterior=anterior, estado=r.estado, fecha_reparacion=r.fecha_reparacion,
        mensaje=f'El bache {r.folio} cambió a "{r.estado.value}".',
    )


# =============================================================================== perfil (HU-01.4)

perfil = APIRouter(prefix="/perfil", tags=["perfil"])


def _favorita(f) -> ColoniaFavoritaOut:
    c = f.colonia
    return ColoniaFavoritaOut(
        colonia={"id": c.id, "nombre": c.nombre}, sector={"id": c.sector.id, "nombre": c.sector.nombre},
        codigo_postal=c.codigo_postal, activa=c.activo, agregada_en=f.created_at,
    )


@perfil.get("/colonias-favoritas", response_model=ListaFavoritas, summary="Mis colonias de interés", responses=respuestas(401))
def mis_colonias(usuario: Usuario = Depends(CUALQUIER_ROL), db: Session = Depends(get_db)) -> ListaFavoritas:
    return ListaFavoritas(maximo=perfil_publico.MAX_FAVORITAS, datos=[_favorita(f) for f in perfil_publico.favoritas(db, usuario)])


@perfil.post(
    "/colonias-favoritas", response_model=ColoniaFavoritaOut, status_code=status.HTTP_201_CREATED,
    summary="Agregar una colonia activa a mis colonias de interés (200 si ya estaba)", responses=respuestas(401, 422),
)
def agregar_colonia(datos: FavoritaIn, response: Response, usuario: Usuario = Depends(CUALQUIER_ROL), db: Session = Depends(get_db)) -> ColoniaFavoritaOut:
    fav, creada = perfil_publico.agregar(db, usuario, datos.colonia_id)
    if not creada:
        response.status_code = status.HTTP_200_OK
    return _favorita(fav)


@perfil.delete("/colonias-favoritas/{colonia_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Quitar una colonia de interés", responses=respuestas(401, 404))
def quitar_colonia(colonia_id: int, usuario: Usuario = Depends(CUALQUIER_ROL), db: Session = Depends(get_db)) -> Response:
    perfil_publico.quitar(db, usuario, colonia_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =============================================================================== trayecto (HU-04.6)

ruta_trayecto = APIRouter(prefix="/trayecto", tags=["trayecto"])


@ruta_trayecto.get(
    "/revisar", response_model=TrayectoOut,
    summary="Encharcamientos vigentes a <= 100 m de la ruta entre dos puntos de Ciudad Juárez",
    description="Ruta de OSRM con respaldo a línea recta si el proveedor falla. Primero los «intransitable». Sin datos personales.",
    responses=respuestas(422),
)
def revisar_trayecto(
    origen_latitud: Annotated[Latitud, Query()],
    origen_longitud: Annotated[Longitud, Query()],
    destino_latitud: Annotated[Latitud, Query()],
    destino_longitud: Annotated[Longitud, Query()],
    db: Session = Depends(get_db),
) -> TrayectoOut:
    expirar_vencidos(db)
    origen, destino = (origen_latitud, origen_longitud), (destino_latitud, destino_longitud)
    ruta = trayecto.obtener_ruta(origen, destino)
    cercanos = trayecto.encharcamientos_cercanos(db, ruta)
    return TrayectoOut(
        origen={"latitud": origen[0], "longitud": origen[1]},
        destino={"latitud": destino[0], "longitud": destino[1]},
        radio_metros=trayecto.RADIO_TRAYECTO_M,
        ruta=RutaOut(
            fuente=ruta.fuente, degradado=ruta.degradado, mensaje=ruta.mensaje,
            distancia_metros=round(ruta.distancia_metros, 1), duracion_segundos=ruta.duracion_segundos, puntos=ruta.puntos,
        ),
        total=len(cercanos),
        datos=[
            EncharcamientoEnTrayecto(
                folio=r.folio, calle=r.calle, colonia={"id": r.colonia.id, "nombre": r.colonia.nombre},
                ubicacion={"latitud": r.latitud, "longitud": r.longitud}, nivel_agua=r.nivel_agua,
                es_intransitable=r.nivel_agua == NivelAgua.INTRANSITABLE,
                hay_riesgo_personas_vehiculos=r.hay_riesgo_personas_vehiculos,
                distancia_metros=round(d, 1), vigente_hasta=r.vigente_hasta,
            )
            for r, d in cercanos
        ],
        mensaje=None if cercanos else "No hay encharcamientos reportados cerca del trayecto",
    )


# =============================================================================== resumen público (HU-07.2)

publico = APIRouter(prefix="/publico", tags=["público"])


@publico.get(
    "/colonias/{colonia_id}/resumen", response_model=ResumenColonia,
    summary="Resumen público de una colonia: abiertos, reparados y tiempo promedio de reparación",
    responses=respuestas(404, 422),
)
def resumen_colonia(colonia_id: Annotated[int, Path(ge=1)], db: Session = Depends(get_db)) -> dict:
    expirar_vencidos(db)
    return perfil_publico.resumen_colonia(db, colonia_id)


__all__ = ["cuadrillas", "enlace", "perfil", "publico", "ruta_trayecto", "EstadoReporte"]
