"""Registro, inicio de sesión y revocación de tokens."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
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
from app.services.limitador import LimitadorVentana

# Respaldo distribuido en BD: tras 20 fallos (desde cualquier IP) la cuenta se bloquea 15 min. El umbral es alto a
# propósito: el bloqueo fino (5 fallos) es por cuenta + IP, para que un tercero no pueda bloquear a la víctima
# desde su propia IP con sólo 5 intentos (auditoría final, M2).
MAX_INTENTOS_FALLIDOS = 20
BLOQUEO = timedelta(minutes=15)
_VENTANA_LOGIN_S = BLOQUEO.total_seconds()

_s = get_settings()
limitador_registro = LimitadorVentana(_s.limite_registros_por_hora_ip, 3600)  # M1
limitador_login_ip = LimitadorVentana(_s.limite_login_fallidos_por_ip, _VENTANA_LOGIN_S)  # M2
limitador_login_cuenta_ip = LimitadorVentana(_s.limite_login_fallidos_por_cuenta_ip, _VENTANA_LOGIN_S)  # M2


def _demasiados_intentos(espera: int) -> ErrorAPI:
    return ErrorAPI(
        429,
        "DEMASIADOS_INTENTOS",
        "Demasiados intentos fallidos. Intenta de nuevo en unos minutos.",
        headers={"Retry-After": str(espera)},
    )


def registrar(db: Session, datos: RegistroIn, ip: str) -> Usuario:
    espera = limitador_registro.intentar(ip)  # M1: también frena la enumeración de correos (409)
    if espera is not None:
        raise ErrorAPI(
            429,
            "LIMITE_REGISTROS",
            "Se crearon demasiadas cuentas desde esta conexión. Intenta de nuevo más tarde.",
            headers={"Retry-After": str(espera)},
        )
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


def iniciar_sesion(db: Session, datos: LoginIn, ip: str) -> TokenOut:
    correo = datos.correo.lower()
    clave_cuenta = f"{correo}|{ip}"
    for limitador, clave in ((limitador_login_ip, ip), (limitador_login_cuenta_ip, clave_cuenta)):
        espera = limitador.consultar(clave)
        if espera is not None:
            raise _demasiados_intentos(espera)

    usuario = db.scalar(select(Usuario).where(Usuario.correo == correo))
    ahora = ahora_utc()

    if usuario is not None and usuario.bloqueado_hasta and usuario.bloqueado_hasta > ahora:
        raise _demasiados_intentos(int((usuario.bloqueado_hasta - ahora).total_seconds()) + 1)

    hash_guardado = usuario.password_hash if usuario else HASH_RELLENO  # iguala tiempos de respuesta
    correcta = verificar_contrasena(datos.contrasena, hash_guardado)
    if usuario is None or not correcta:
        limitador_login_ip.registrar(ip)
        limitador_login_cuenta_ip.registrar(clave_cuenta)
        if usuario is not None:
            usuario.intentos_fallidos += 1
            if usuario.intentos_fallidos >= MAX_INTENTOS_FALLIDOS:
                usuario.bloqueado_hasta = ahora + BLOQUEO
                usuario.intentos_fallidos = 0
            db.commit()
        raise _credenciales_invalidas()
    if not usuario.activo:
        raise _credenciales_invalidas()  # mensaje genérico: no revela el estado de la cuenta

    limitador_login_cuenta_ip.olvidar(clave_cuenta)
    if usuario.intentos_fallidos or usuario.bloqueado_hasta:
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        db.commit()
    return emitir_token(usuario)


def cerrar_sesion(db: Session, usuario: Usuario) -> None:
    usuario.token_version += 1  # invalida todos los tokens emitidos
    db.commit()
