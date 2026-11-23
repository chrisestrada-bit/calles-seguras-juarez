"""Dependencias de FastAPI: sesión de BD, autenticación y control de acceso por rol."""

import uuid
from collections.abc import Callable, Iterator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.errores import ErrorAPI
from app.core.security import decodificar_token
from app.models import RolUsuario, Usuario

_esquema = HTTPBearer(auto_error=False, description="JWT obtenido en /api/v1/auth/login")


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _usuario_desde_token(db: Session, cred: HTTPAuthorizationCredentials | None) -> Usuario | None:
    if cred is None:
        return None
    carga = decodificar_token(cred.credentials)
    if carga is None:
        return None
    try:
        usuario_id = uuid.UUID(str(carga["sub"]))
    except ValueError:
        return None
    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo or usuario.token_version != carga.get("ver"):
        return None
    return usuario


def usuario_opcional(
    cred: HTTPAuthorizationCredentials | None = Depends(_esquema),
    db: Session = Depends(get_db),
) -> Usuario | None:
    """Rutas públicas: un token inválido se trata como visitante."""
    return _usuario_desde_token(db, cred)


def _cuenta_suspendida(db: Session, cred: HTTPAuthorizationCredentials | None) -> bool:
    """Token con firma y vigencia válidas, pero de una cuenta desactivada por coordinación."""
    carga = decodificar_token(cred.credentials) if cred else None
    if carga is None:
        return False
    try:
        usuario = db.get(Usuario, uuid.UUID(str(carga["sub"])))
    except ValueError:
        return False
    return usuario is not None and not usuario.activo


def usuario_actual(
    cred: HTTPAuthorizationCredentials | None = Depends(_esquema),
    db: Session = Depends(get_db),
) -> Usuario:
    usuario = _usuario_desde_token(db, cred)
    if usuario is None and _cuenta_suspendida(db, cred):
        raise ErrorAPI(403, "CUENTA_SUSPENDIDA", "Tu cuenta está suspendida. Comunícate con coordinación.")
    if usuario is None:
        raise ErrorAPI(
            401,
            "NO_AUTENTICADO",
            "Tu sesión no es válida o expiró. Inicia sesión de nuevo.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


def requiere_rol(*roles: RolUsuario) -> Callable[..., Usuario]:
    """Devuelve una dependencia que exige alguno de los roles (si no, HTTP 403)."""
    permitidos = frozenset(roles)

    def _dependencia(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
        if usuario.rol not in permitidos:
            raise ErrorAPI(
                403, "ROL_NO_AUTORIZADO", "Tu rol no tiene permiso para realizar esta acción."
            )
        return usuario

    return _dependencia


# Atajos de uso frecuente.
CUALQUIER_ROL = requiere_rol(RolUsuario.CIUDADANO, RolUsuario.MODERADOR, RolUsuario.COORDINADOR)
MODERACION = requiere_rol(RolUsuario.MODERADOR, RolUsuario.COORDINADOR)
SOLO_COORDINADOR = requiere_rol(RolUsuario.COORDINADOR)
SOLO_ENLACE = requiere_rol(RolUsuario.ENLACE_MUNICIPAL)  # HU-05.5
# Gestión de la propia sesión (/auth/yo, /renovar, /cerrar-sesion): cualquier cuenta autenticada, incluido el
# enlace municipal; sin esto su token no se podía revocar ni renovar (auditoría final, A2).
CUALQUIER_SESION = requiere_rol(*RolUsuario)
