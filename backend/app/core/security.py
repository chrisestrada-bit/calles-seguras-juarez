"""Contraseñas (Argon2id) y tokens JWT."""

import re
import uuid
from datetime import timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings
from app.core.tiempo import ahora_utc

_hasher = PasswordHasher()
# Hash de relleno para igualar el tiempo de respuesta cuando el correo no existe.
HASH_RELLENO = _hasher.hash("relleno-para-igualar-tiempos-1")

MENSAJE_CONTRASENA = "La contraseña debe tener al menos 8 caracteres e incluir letras y números."


def contrasena_valida(contrasena: str) -> bool:
    return (
        len(contrasena) >= 8
        and len(contrasena) <= 128
        and re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", contrasena) is not None
        and re.search(r"\d", contrasena) is not None
    )


def hashear_contrasena(contrasena: str) -> str:
    return _hasher.hash(contrasena)


def verificar_contrasena(contrasena: str, hash_guardado: str) -> bool:
    try:
        return _hasher.verify(hash_guardado, contrasena)
    except (VerificationError, InvalidHashError):
        return False


def crear_token(usuario_id: uuid.UUID, rol: str, token_version: int) -> tuple[str, int]:
    """Devuelve (token, segundos de vigencia). Expira a los 30 min de inactividad (renovable)."""
    s = get_settings()
    ahora = ahora_utc()
    vigencia = timedelta(minutes=s.access_token_expire_minutes)
    carga = {
        "sub": str(usuario_id),
        "rol": rol,
        "ver": token_version,
        "iat": ahora,
        "exp": ahora + vigencia,
    }
    token = jwt.encode(carga, s.jwt_secret_key.get_secret_value(), algorithm=s.jwt_algorithm)
    return token, int(vigencia.total_seconds())


def decodificar_token(token: str) -> dict[str, Any] | None:
    s = get_settings()
    try:
        return jwt.decode(
            token,
            s.jwt_secret_key.get_secret_value(),
            algorithms=[s.jwt_algorithm],
            options={"require": ["exp", "sub", "ver"]},
        )
    except jwt.PyJWTError:
        return None
