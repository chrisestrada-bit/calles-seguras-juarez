"""Folios únicos e inmutables (RN-03), generados con secuencias de PostgreSQL.

Una secuencia nunca devuelve el mismo valor dos veces, ni siquiera tras un rollback, por lo que un
folio jamás se reutiliza (pueden existir huecos). Es atómico bajo concurrencia.
"""

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.tiempo import a_local
from app.models import TipoDano

_SECUENCIAS = {True: ("seq_folio_enc", "ENC"), False: ("seq_folio_bch", "BCH")}


def generar_folio(db: Session, tipo: TipoDano, creado_en: datetime) -> str:
    secuencia, prefijo = _SECUENCIAS[tipo == TipoDano.ENCHARCAMIENTO]
    numero = db.execute(text(f"SELECT nextval('{secuencia}')")).scalar_one()  # nombre fijo, no entrada
    return f"{prefijo}-{a_local(creado_en).year}-{numero:06d}"
