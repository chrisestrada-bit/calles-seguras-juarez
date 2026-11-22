import uuid

from pydantic import EmailStr, Field, field_validator

from app.core.security import MENSAJE_CONTRASENA, contrasena_valida
from app.models import RolUsuario
from app.schemas.comun import Esquema, FechaLocal
from pydantic import BaseModel


class RegistroIn(Esquema):
    nombre: str = Field(min_length=2, max_length=120)
    correo: EmailStr = Field(max_length=254)
    contrasena: str = Field(max_length=128)
    # HU-01.2: el consentimiento se exige también en el servidor, no sólo en el formulario.
    acepta_aviso_privacidad: bool

    @field_validator("acepta_aviso_privacidad")
    @classmethod
    def _consentimiento(cls, valor: bool) -> bool:
        if valor is not True:
            raise ValueError("Debes aceptar el aviso de privacidad para crear tu cuenta.")
        return valor

    @field_validator("contrasena")
    @classmethod
    def _politica(cls, valor: str) -> str:
        if not contrasena_valida(valor):
            raise ValueError(MENSAJE_CONTRASENA)
        return valor


class LoginIn(Esquema):
    correo: EmailStr
    contrasena: str = Field(min_length=1, max_length=128)


class RegistroOut(BaseModel):
    id: uuid.UUID
    nombre: str
    rol: RolUsuario
    created_at: FechaLocal


class UsuarioSesion(BaseModel):
    id: uuid.UUID
    nombre: str
    rol: RolUsuario


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en_segundos: int
    usuario: UsuarioSesion


class YoOut(BaseModel):
    """Vista privada: sólo los datos de la propia cuenta."""

    id: uuid.UUID
    nombre: str
    correo: str
    rol: RolUsuario
    reportes_ultima_hora: int
    limite_reportes_hora: int
