"""Esquemas de administración (vista privada del coordinador)."""

import re
import uuid

from pydantic import BaseModel, Field, field_validator

from app.models import RolUsuario
from app.schemas.comun import Esquema, FechaLocal, Latitud, Longitud, SectorRef
from app.schemas.catalogos import Centro


class UsuarioAdmin(BaseModel):
    id: uuid.UUID
    nombre: str
    correo: str
    rol: RolUsuario
    activo: bool
    created_at: FechaLocal


class RolIn(Esquema):
    rol: RolUsuario


class RolOut(BaseModel):
    id: uuid.UUID
    rol: RolUsuario
    mensaje: str


class EstadoUsuarioIn(Esquema):
    activo: bool


class EstadoUsuarioOut(BaseModel):
    id: uuid.UUID
    activo: bool
    mensaje: str


class SectorCrear(Esquema):
    clave: str = Field(min_length=2, max_length=20)
    nombre: str = Field(min_length=2, max_length=80)

    @field_validator("clave")
    @classmethod
    def _formato_clave(cls, valor: str) -> str:
        valor = valor.upper()
        if not re.fullmatch(r"[A-Z0-9-]{2,20}", valor):
            raise ValueError("La clave sólo admite letras mayúsculas, números y guiones.")
        return valor


class SectorEditar(Esquema):
    nombre: str | None = Field(default=None, min_length=2, max_length=80)
    activo: bool | None = None


class SectorAdmin(BaseModel):
    id: int
    clave: str
    nombre: str
    activo: bool


class _ColoniaBase(Esquema):
    @field_validator("codigo_postal", check_fields=False)
    @classmethod
    def _cp(cls, valor: str | None) -> str | None:
        if valor is not None and not re.fullmatch(r"32[0-9]{3}", valor):
            raise ValueError("El código postal debe tener 5 dígitos y comenzar con 32.")
        return valor


class ColoniaCrear(_ColoniaBase):
    sector_id: int = Field(ge=1)
    nombre: str = Field(min_length=2, max_length=120)
    codigo_postal: str | None = None
    latitud_centro: Latitud
    longitud_centro: Longitud


class ColoniaEditar(_ColoniaBase):
    sector_id: int | None = Field(default=None, ge=1)
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    codigo_postal: str | None = None
    latitud_centro: Latitud | None = None
    longitud_centro: Longitud | None = None
    activo: bool | None = None


class ColoniaAdmin(BaseModel):
    id: int
    nombre: str
    codigo_postal: str | None
    sector: SectorRef
    centro: Centro
    activo: bool
