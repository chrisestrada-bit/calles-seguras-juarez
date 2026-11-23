"""Esquemas de evidencia fotográfica (HU-02.4). Sin datos de quien subió la imagen (RN-04)."""

import uuid

from pydantic import BaseModel

from app.schemas.comun import FechaLocal


class FotoOut(BaseModel):
    id: uuid.UUID
    url: str
    nombre_original: str
    mime_type: str
    tamano_bytes: int
    created_at: FechaLocal


class FotoRechazadaOut(BaseModel):
    nombre: str
    motivo: str


class FotosSubidas(BaseModel):
    folio: str
    aceptadas: list[FotoOut]
    rechazadas: list[FotoRechazadaOut]
    mensaje: str


class ListaFotos(BaseModel):
    folio: str
    maximo_por_persona: int
    datos: list[FotoOut]
