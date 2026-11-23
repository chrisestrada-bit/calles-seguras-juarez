import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import SOLO_COORDINADOR, get_db
from app.models import RolUsuario, Usuario
from app.schemas.admin import (
    ColoniaAdmin,
    ColoniaCrear,
    ColoniaEditar,
    EstadoUsuarioIn,
    EstadoUsuarioOut,
    ImportacionCatalogos,
    RolIn,
    RolOut,
    SectorAdmin,
    SectorCrear,
    SectorEditar,
    UsuarioAdmin,
)
from app.schemas.comun import Pagina, ParametrosPagina, armar_pagina, respuestas
from app.services import admin as servicio
from app.services import catalogos_admin, catalogos_xml
from app.schemas.operacion import (
    ListaMotivos,
    ListaTiposDanoAdmin,
    MotivoCrear,
    MotivoEditar,
    MotivoRechazo,
    TipoDanoAdmin,
    TipoDanoCrear,
    TipoDanoEditar,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _colonia(c) -> ColoniaAdmin:
    return ColoniaAdmin(
        id=c.id,
        nombre=c.nombre,
        codigo_postal=c.codigo_postal,
        sector={"id": c.sector.id, "nombre": c.sector.nombre},
        centro={"latitud": c.latitud_centro, "longitud": c.longitud_centro},
        activo=c.activo,
    )


@router.get(
    "/usuarios",
    response_model=Pagina[UsuarioAdmin],
    summary="Listar usuarios (vista privada del coordinador)",
    responses=respuestas(401, 403, 422),
)
def usuarios(
    rol: RolUsuario | None = None,
    activo: bool | None = None,
    q: Annotated[str | None, Query(min_length=2, max_length=80)] = None,
    pag: ParametrosPagina = Depends(),
    _: Usuario = Depends(SOLO_COORDINADOR),
    db: Session = Depends(get_db),
) -> dict:
    filas, total = servicio.listar_usuarios(db, rol=rol, activo=activo, q=q, pag=pag)
    return armar_pagina(
        [UsuarioAdmin(id=u.id, nombre=u.nombre, correo=u.correo, rol=u.rol, activo=u.activo, created_at=u.created_at) for u in filas],
        total,
        pag,
    )


@router.patch(
    "/usuarios/{usuario_id}/rol",
    response_model=RolOut,
    summary="Cambiar el rol de un usuario",
    responses=respuestas(400, 401, 403, 404, 422),
)
def cambiar_rol(
    usuario_id: uuid.UUID,
    datos: RolIn,
    actor: Usuario = Depends(SOLO_COORDINADOR),
    db: Session = Depends(get_db),
) -> RolOut:
    usuario = servicio.cambiar_rol(db, actor, usuario_id, datos.rol)
    return RolOut(
        id=usuario.id, rol=usuario.rol, mensaje="El rol se actualizó. El usuario deberá iniciar sesión de nuevo."
    )


@router.patch(
    "/usuarios/{usuario_id}/estado",
    response_model=EstadoUsuarioOut,
    summary="Activar o desactivar una cuenta",
    responses=respuestas(400, 401, 403, 404, 422),
)
def cambiar_estado(
    usuario_id: uuid.UUID,
    datos: EstadoUsuarioIn,
    actor: Usuario = Depends(SOLO_COORDINADOR),
    db: Session = Depends(get_db),
) -> EstadoUsuarioOut:
    usuario = servicio.cambiar_estado(db, actor, usuario_id, datos.activo)
    return EstadoUsuarioOut(
        id=usuario.id,
        activo=usuario.activo,
        mensaje="La cuenta fue activada." if usuario.activo else "La cuenta fue desactivada.",
    )


@router.post(
    "/sectores",
    response_model=SectorAdmin,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un sector",
    responses=respuestas(401, 403, 409, 422),
)
def crear_sector(datos: SectorCrear, _: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> SectorAdmin:
    s = servicio.crear_sector(db, datos)
    return SectorAdmin(id=s.id, clave=s.clave, nombre=s.nombre, activo=s.activo)


@router.patch(
    "/sectores/{sector_id}",
    response_model=SectorAdmin,
    summary="Editar un sector (la clave es inmutable)",
    responses=respuestas(401, 403, 404, 409, 422),
)
def editar_sector(
    sector_id: int,
    datos: SectorEditar,
    _: Usuario = Depends(SOLO_COORDINADOR),
    db: Session = Depends(get_db),
) -> SectorAdmin:
    s = servicio.editar_sector(db, sector_id, datos)
    return SectorAdmin(id=s.id, clave=s.clave, nombre=s.nombre, activo=s.activo)


@router.post(
    "/colonias",
    response_model=ColoniaAdmin,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una colonia",
    responses=respuestas(401, 403, 409, 422),
)
def crear_colonia(datos: ColoniaCrear, _: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> ColoniaAdmin:
    return _colonia(servicio.crear_colonia(db, datos))


@router.patch(
    "/colonias/{colonia_id}",
    response_model=ColoniaAdmin,
    summary="Editar una colonia",
    responses=respuestas(401, 403, 404, 409, 422),
)
def editar_colonia(
    colonia_id: int,
    datos: ColoniaEditar,
    _: Usuario = Depends(SOLO_COORDINADOR),
    db: Session = Depends(get_db),
) -> ColoniaAdmin:
    return _colonia(servicio.editar_colonia(db, colonia_id, datos))


@router.post(
    "/catalogos/importar-xml",
    response_model=ImportacionCatalogos,
    summary="Importar o actualizar sectores y colonias desde XML (esquema catalogos_v1.xsd)",
    description=(
        "Sube un archivo XML (máx. 2 MB) validado contra `docs/esquemas/catalogos_v1.xsd`. Es transaccional: "
        "si el XML está mal formado, incumple el esquema o referencia sectores inexistentes, no se importa nada."
    ),
    responses=respuestas(401, 403, 413, 422),
)
def importar_catalogos_xml(
    archivo: Annotated[UploadFile, File(description="Archivo XML de catálogos.")],
    _: Usuario = Depends(SOLO_COORDINADOR),
    db: Session = Depends(get_db),
) -> ImportacionCatalogos:
    contenido = archivo.file.read(catalogos_xml.MAX_BYTES_XML + 1)
    r = catalogos_xml.importar(db, contenido)
    return ImportacionCatalogos(
        sectores_creados=r.sectores_creados,
        sectores_actualizados=r.sectores_actualizados,
        colonias_creadas=r.colonias_creadas,
        colonias_actualizadas=r.colonias_actualizadas,
        mensaje="Catálogos importados correctamente.",
    )


# ------------------------------------------------------------------ HU-06.3 catálogos administrables


def _tipo(t) -> TipoDanoAdmin:
    return TipoDanoAdmin(id=t.id, clave=t.clave, nombre=t.nombre, descripcion=t.descripcion, activo=t.activo)


def _motivo(m) -> MotivoRechazo:
    return MotivoRechazo(id=m.id, nombre=m.nombre, descripcion=m.descripcion, activo=m.activo)


@router.get("/catalogos/tipos-dano", response_model=ListaTiposDanoAdmin, summary="Tipos de daño (activos e inactivos)", responses=respuestas(401, 403))
def listar_tipos(_: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> ListaTiposDanoAdmin:
    return ListaTiposDanoAdmin(datos=[_tipo(t) for t in catalogos_admin.tipos(db, solo_activos=False)])


@router.post(
    "/catalogos/tipos-dano", response_model=TipoDanoAdmin, status_code=status.HTTP_201_CREATED,
    summary="Registrar un tipo de daño soportado por la plataforma", responses=respuestas(401, 403, 409, 422),
)
def crear_tipo(datos: TipoDanoCrear, _: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> TipoDanoAdmin:
    return _tipo(catalogos_admin.crear_tipo(db, datos))


@router.patch(
    "/catalogos/tipos-dano/{tipo_id}", response_model=TipoDanoAdmin,
    summary="Editar o desactivar un tipo de daño (no se borra; los reportes históricos no cambian)",
    responses=respuestas(401, 403, 404, 422),
)
def editar_tipo(tipo_id: int, datos: TipoDanoEditar, _: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> TipoDanoAdmin:
    return _tipo(catalogos_admin.editar_tipo(db, tipo_id, datos))


@router.get("/catalogos/motivos-rechazo", response_model=ListaMotivos, summary="Motivos de rechazo (activos e inactivos)", responses=respuestas(401, 403))
def listar_motivos(_: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> ListaMotivos:
    return ListaMotivos(datos=[_motivo(m) for m in catalogos_admin.motivos(db, solo_activos=False)])


@router.post(
    "/catalogos/motivos-rechazo", response_model=MotivoRechazo, status_code=status.HTTP_201_CREATED,
    summary="Crear un motivo de rechazo", responses=respuestas(401, 403, 409, 422),
)
def crear_motivo(datos: MotivoCrear, _: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> MotivoRechazo:
    return _motivo(catalogos_admin.crear_motivo(db, datos))


@router.patch(
    "/catalogos/motivos-rechazo/{motivo_id}", response_model=MotivoRechazo,
    summary="Editar o desactivar un motivo (no se borra; los rechazos históricos conservan su texto)",
    responses=respuestas(401, 403, 404, 409, 422),
)
def editar_motivo(motivo_id: int, datos: MotivoEditar, _: Usuario = Depends(SOLO_COORDINADOR), db: Session = Depends(get_db)) -> MotivoRechazo:
    return _motivo(catalogos_admin.editar_motivo(db, motivo_id, datos))
