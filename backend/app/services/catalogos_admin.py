"""Catálogos administrables de tipos de daño y motivos de rechazo (HU-06.3).

* Nunca se borran registros: se desactivan (los reportes y rechazos históricos conservan su texto y su tipo).
* Los tipos de daño corresponden a los tres comportamientos que la plataforma sabe validar (formulario dinámico,
  severidad y vigencia). El catálogo controla si cada uno está disponible para reportes nuevos y su texto visible.
"""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errores import ErrorAPI
from app.models import CatalogoMotivoRechazo, CatalogoTipoDano, TipoDano
from app.services.sqlutil import error_validacion


# ------------------------------------------------------------------------------- tipos de daño


def tipos(db: Session, *, solo_activos: bool) -> list[CatalogoTipoDano]:
    stmt = select(CatalogoTipoDano).order_by(CatalogoTipoDano.id)
    if solo_activos:
        stmt = stmt.where(CatalogoTipoDano.activo)
    return list(db.scalars(stmt))


def tipo_activo(db: Session, tipo: TipoDano) -> bool:
    return bool(db.scalar(select(CatalogoTipoDano.activo).where(CatalogoTipoDano.clave == tipo)))


def exigir_tipo_activo(db: Session, tipo: TipoDano) -> None:
    if not tipo_activo(db, tipo):
        raise error_validacion("tipo_dano", f"El tipo de daño «{tipo.value}» no está disponible por ahora.")


def crear_tipo(db: Session, datos) -> CatalogoTipoDano:
    if db.scalar(select(CatalogoTipoDano.id).where(CatalogoTipoDano.clave == datos.clave)) is not None:
        raise ErrorAPI(409, "TIPO_DUPLICADO", "Ese tipo de daño ya está en el catálogo; edítalo o reactívalo.")
    t = CatalogoTipoDano(clave=datos.clave, nombre=datos.nombre, descripcion=datos.descripcion)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def editar_tipo(db: Session, tipo_id: int, datos) -> CatalogoTipoDano:
    t = db.get(CatalogoTipoDano, tipo_id)
    if t is None:
        raise ErrorAPI(404, "NO_ENCONTRADO", "El tipo de daño no existe en el catálogo.")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        if valor is None and campo != "descripcion":
            raise error_validacion(campo, "Este campo no admite valores nulos.")
        setattr(t, campo, valor)
    db.commit()
    db.refresh(t)
    return t


# ------------------------------------------------------------------------------- motivos de rechazo


def motivos(db: Session, *, solo_activos: bool) -> list[CatalogoMotivoRechazo]:
    stmt = select(CatalogoMotivoRechazo).order_by(CatalogoMotivoRechazo.nombre)
    if solo_activos:
        stmt = stmt.where(CatalogoMotivoRechazo.activo)
    return list(db.scalars(stmt))


def motivo_autorizado(db: Session, motivo_id: int | None) -> CatalogoMotivoRechazo:
    m = db.get(CatalogoMotivoRechazo, motivo_id) if motivo_id is not None else None
    if m is None or not m.activo:
        raise ErrorAPI(
            422, "MOTIVO_NO_AUTORIZADO", "Elige un motivo de rechazo activo del catálogo.",
            [{"campo": "motivo_id", "mensaje": "El motivo no existe o está desactivado."}],
        )
    return m


def _nombre_repetido(db: Session, nombre: str, excluir: int | None = None) -> bool:
    stmt = select(CatalogoMotivoRechazo.id).where(func.lower(CatalogoMotivoRechazo.nombre) == nombre.lower())
    if excluir is not None:
        stmt = stmt.where(CatalogoMotivoRechazo.id != excluir)
    return db.scalar(stmt) is not None


def _guardar(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErrorAPI(409, "MOTIVO_DUPLICADO", "Ya existe un motivo con ese nombre.") from None


def crear_motivo(db: Session, datos) -> CatalogoMotivoRechazo:
    if _nombre_repetido(db, datos.nombre):
        raise ErrorAPI(409, "MOTIVO_DUPLICADO", "Ya existe un motivo con ese nombre.")
    m = CatalogoMotivoRechazo(nombre=datos.nombre, descripcion=datos.descripcion)
    db.add(m)
    _guardar(db)
    db.refresh(m)
    return m


def editar_motivo(db: Session, motivo_id: int, datos) -> CatalogoMotivoRechazo:
    m = db.get(CatalogoMotivoRechazo, motivo_id)
    if m is None:
        raise ErrorAPI(404, "NO_ENCONTRADO", "El motivo no existe.")
    cambios = datos.model_dump(exclude_unset=True)
    if cambios.get("nombre") and _nombre_repetido(db, cambios["nombre"], m.id):
        raise ErrorAPI(409, "MOTIVO_DUPLICADO", "Ya existe un motivo con ese nombre.")
    for campo, valor in cambios.items():
        if valor is None and campo != "descripcion":
            raise error_validacion(campo, "Este campo no admite valores nulos.")
        setattr(m, campo, valor)
    _guardar(db)
    db.refresh(m)
    return m
