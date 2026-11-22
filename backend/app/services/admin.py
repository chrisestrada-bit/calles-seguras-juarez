"""Administración de usuarios, sectores y colonias (rol coordinador)."""

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errores import ErrorAPI
from app.models import Colonia, RolUsuario, Sector, Usuario
from app.schemas.admin import ColoniaCrear, ColoniaEditar, SectorCrear, SectorEditar
from app.schemas.comun import ParametrosPagina
from app.services.sqlutil import error_validacion, escapar_like

# ------------------------------------------------------------------------------- usuarios


def listar_usuarios(
    db: Session, *, rol: RolUsuario | None, activo: bool | None, q: str | None, pag: ParametrosPagina
) -> tuple[list[Usuario], int]:
    condiciones = []
    if rol:
        condiciones.append(Usuario.rol == rol)
    if activo is not None:
        condiciones.append(Usuario.activo == activo)
    if q:
        patron = f"%{escapar_like(q)}%"
        condiciones.append(or_(Usuario.nombre.ilike(patron, escape="\\"), Usuario.correo.ilike(patron, escape="\\")))
    total = db.scalar(select(func.count()).select_from(Usuario).where(*condiciones)) or 0
    filas = db.scalars(
        select(Usuario).where(*condiciones).order_by(Usuario.created_at.desc(), Usuario.id).limit(pag.por_pagina).offset(pag.offset)
    ).all()
    return list(filas), total


def _usuario_o_404(db: Session, usuario_id: uuid.UUID) -> Usuario:
    usuario = db.get(Usuario, usuario_id, with_for_update=True)
    if usuario is None:
        raise ErrorAPI(404, "NO_ENCONTRADO", "El usuario no existe.")
    return usuario


def cambiar_rol(db: Session, actor: Usuario, usuario_id: uuid.UUID, rol: RolUsuario) -> Usuario:
    if usuario_id == actor.id:
        raise ErrorAPI(400, "OPERACION_NO_PERMITIDA", "No puedes cambiar tu propio rol.")
    usuario = _usuario_o_404(db, usuario_id)
    usuario.rol = rol
    usuario.token_version += 1  # obliga a iniciar sesión de nuevo con el rol actualizado
    db.commit()
    return usuario


def cambiar_estado(db: Session, actor: Usuario, usuario_id: uuid.UUID, activo: bool) -> Usuario:
    if usuario_id == actor.id and not activo:
        raise ErrorAPI(400, "OPERACION_NO_PERMITIDA", "No puedes desactivar tu propia cuenta.")
    usuario = _usuario_o_404(db, usuario_id)
    usuario.activo = activo
    if not activo:
        usuario.token_version += 1
    db.commit()
    return usuario


# ------------------------------------------------------------------------------- sectores


def crear_sector(db: Session, datos: SectorCrear) -> Sector:
    existe = db.scalar(select(Sector.id).where(or_(Sector.clave == datos.clave, Sector.nombre == datos.nombre)))
    if existe is not None:
        raise ErrorAPI(409, "SECTOR_DUPLICADO", "Ya existe un sector con esa clave o nombre.")
    sector = Sector(clave=datos.clave, nombre=datos.nombre)
    db.add(sector)
    _confirmar(db, "SECTOR_DUPLICADO", "Ya existe un sector con esa clave o nombre.")
    return sector


def editar_sector(db: Session, sector_id: int, datos: SectorEditar) -> Sector:
    sector = db.get(Sector, sector_id)
    if sector is None:
        raise ErrorAPI(404, "NO_ENCONTRADO", "El sector no existe.")
    cambios = datos.model_dump(exclude_unset=True)
    if "nombre" in cambios and cambios["nombre"] is not None:
        repetido = db.scalar(select(Sector.id).where(Sector.nombre == cambios["nombre"], Sector.id != sector_id))
        if repetido is not None:
            raise ErrorAPI(409, "SECTOR_DUPLICADO", "Ya existe un sector con ese nombre.")
        sector.nombre = cambios["nombre"]
    if cambios.get("activo") is not None:
        sector.activo = cambios["activo"]
    _confirmar(db, "SECTOR_DUPLICADO", "Ya existe un sector con ese nombre.")
    return sector


# ------------------------------------------------------------------------------- colonias


def _exigir_sector(db: Session, sector_id: int) -> None:
    if db.get(Sector, sector_id) is None:
        raise error_validacion("sector_id", f"El sector {sector_id} no existe.")


def _nombre_repetido(db: Session, sector_id: int, nombre: str, excluir: int | None = None) -> bool:
    stmt = select(Colonia.id).where(Colonia.sector_id == sector_id, func.lower(Colonia.nombre) == nombre.lower())
    if excluir is not None:
        stmt = stmt.where(Colonia.id != excluir)
    return db.scalar(stmt) is not None


def crear_colonia(db: Session, datos: ColoniaCrear) -> Colonia:
    _exigir_sector(db, datos.sector_id)
    if _nombre_repetido(db, datos.sector_id, datos.nombre):
        raise ErrorAPI(409, "COLONIA_DUPLICADA", "Ya existe una colonia con ese nombre en el sector.")
    colonia = Colonia(
        sector_id=datos.sector_id,
        nombre=datos.nombre,
        codigo_postal=datos.codigo_postal,
        latitud_centro=datos.latitud_centro,
        longitud_centro=datos.longitud_centro,
    )
    db.add(colonia)
    _confirmar(db, "COLONIA_DUPLICADA", "Ya existe una colonia con ese nombre en el sector.")
    db.refresh(colonia)
    return colonia


def editar_colonia(db: Session, colonia_id: int, datos: ColoniaEditar) -> Colonia:
    colonia = db.get(Colonia, colonia_id)
    if colonia is None:
        raise ErrorAPI(404, "NO_ENCONTRADO", "La colonia no existe.")
    cambios = datos.model_dump(exclude_unset=True)
    for campo in ("nombre", "sector_id", "latitud_centro", "longitud_centro", "activo"):
        if campo in cambios and cambios[campo] is None:
            raise error_validacion(campo, "Este campo no admite valores nulos.")
    sector_id = cambios.get("sector_id", colonia.sector_id)
    nombre = cambios.get("nombre", colonia.nombre)
    if "sector_id" in cambios:
        _exigir_sector(db, sector_id)
    if ("sector_id" in cambios or "nombre" in cambios) and _nombre_repetido(db, sector_id, nombre, colonia_id):
        raise ErrorAPI(409, "COLONIA_DUPLICADA", "Ya existe una colonia con ese nombre en el sector.")
    for campo, valor in cambios.items():
        setattr(colonia, campo, valor)
    _confirmar(db, "COLONIA_DUPLICADA", "Ya existe una colonia con ese nombre en el sector.")
    db.refresh(colonia)
    return colonia


def _confirmar(db: Session, codigo: str, mensaje: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErrorAPI(409, codigo, mensaje) from None
