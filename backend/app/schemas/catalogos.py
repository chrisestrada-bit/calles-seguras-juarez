from typing import Any

from pydantic import BaseModel

from app.schemas.comun import SectorRef


class SectorCatalogo(BaseModel):
    id: int
    clave: str
    nombre: str


class ListaSectores(BaseModel):
    datos: list[SectorCatalogo]


class Centro(BaseModel):
    latitud: float
    longitud: float


class ColoniaCatalogo(BaseModel):
    id: int
    nombre: str
    codigo_postal: str | None
    sector: SectorRef
    centro: Centro


class CampoFormulario(BaseModel):
    nombre: str
    etiqueta: str
    tipo: str
    obligatorio: bool
    opciones: list[str] | None = None
    visible_si: dict[str, str] | None = None


class TipoDanoCatalogo(BaseModel):
    tipo_dano: str
    prefijo_folio: str
    radio_duplicados_metros: int
    severidad_fija: str | None = None
    vigencia_horas: int | None = None
    desmentidos_para_historico: int | None = None
    campos: list[CampoFormulario]


class LimitesTerritorio(BaseModel):
    latitud_min: float
    latitud_max: float
    longitud_min: float
    longitud_max: float


class CatalogoTiposDano(BaseModel):
    limites_territorio: LimitesTerritorio
    descripcion_max_caracteres: int
    datos: list[TipoDanoCatalogo]


class CatalogoEstados(BaseModel):
    pavimento: dict[str, Any]
    encharcamiento: dict[str, Any]
