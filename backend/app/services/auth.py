"""Registro, inicio de sesión y revocación de tokens."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errores import ErrorAPI
from app.core.security import (
    HASH_RELLENO,
    crear_token,
    hashear_contrasena,
    verificar_contrasena,
)
from app.core.tiempo import ahora_utc
from app.models import RolUsuario, Usuario
from app.schemas.auth import LoginIn, RegistroIn, TokenOut, UsuarioSesion

MAX_INTENTOS_FALLIDOS = 5
BLOQUEO = timedelta(minutes=15)


def registrar(db: Session, datos: RegistroIn) -> Usuario:
    correo = datos.correo.lower()
    if db.scalar(select(Usuario.id).where(Usuario.correo == correo)) is not None:
        raise ErrorAPI(409, "CORREO_REGISTRADO", "Ya existe una cuenta con ese correo.")
    usuario = Usuario(
        nombre=datos.nombre,
        correo=correo,
        password_hash=hashear_contrasena(datos.contrasena),
        rol=RolUsuario.CIUDADANO,  # el cliente nunca elige su rol
        aviso_privacidad_aceptado_at=ahora_utc(),  # HU-01.2: constancia del consentimiento
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErrorAPI(409, "CORREO_REGISTRADO", "Ya existe una cuenta con ese correo.") from None
    return usuario


def _credenciales_invalidas() -> ErrorAPI:
    return ErrorAPI(401, "CREDENCIALES_INVALIDAS", "Correo o contraseña incorrectos.")


def emitir_token(usuario: Usuario) -> TokenOut:
    token, segundos = crear_token(usuario.id, usuario.rol.value, usuario.token_version)
    return TokenOut(
        access_token=token,
        expira_en_segundos=segundos,
        usuario=UsuarioSesion(id=usuario.id, nombre=usuario.nombre, rol=usuario.rol),
    )


def iniciar_sesion(db: Session, datos: LoginIn) -> TokenOut:
    usuario = db.scalar(select(Usuario).where(Usuario.correo == datos.correo.lower()))
    ahora = ahora_utc()

    if usuario is not None and usuario.bloqueado_hasta and usuario.bloqueado_hasta > ahora:
        espera = int((usuario.bloqueado_hasta - ahora).total_seconds()) + 1
        raise ErrorAPI(
            429,
            "DEMASIADOS_INTENTOS",
            "Demasiados intentos fallidos. Intenta de nuevo en unos minutos.",
            headers={"Retry-After": str(espera)},
        )

    hash_guardado = usuario.password_hash if usuario else HASH_RELLENO  # iguala tiempos de respuesta
    correcta = verificar_contrasena(datos.contrasena, hash_guardado)
    if usuario is None or not correcta:
        if usuario is not None:
            usuario.intentos_fallidos += 1
            if usuario.intentos_fallidos >= MAX_INTENTOS_FALLIDOS:
                usuario.bloqueado_hasta = ahora + BLOQUEO
                usuario.intentos_fallidos = 0
            db.commit()
        raise _credenciales_invalidas()
    if not usuario.activo:
        raise _credenciales_invalidas()  # mensaje genérico: no revela el estado de la cuenta

    if usuario.intentos_fallidos or usuario.bloqueado_hasta:
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        db.commit()
    return emitir_token(usuario)


def cerrar_sesion(db: Session, usuario: Usuario) -> None:
    usuario.token_version += 1  # invalida todos los tokens emitidos
    db.commit()
