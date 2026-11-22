"""Catálogos: sectores, colonias, formulario dinámico por tipo de daño y estados."""

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    CarrilAfectado,
    Colonia,
    NivelAgua,
    ProfundidadBache,
    Sector,
    TamanoBache,
    TipoDano,
)
from app.schemas.comun import ParametrosPagina
from app.services import geo, transiciones
from app.services.sqlutil import error_validacion, escapar_like
from app.services.vigencia import DESMENTIDOS_PARA_HISTORICO, HORAS_VIGENCIA

SIMILITUD_MINIMA = 0.3


def listar_sectores(db: Session) -> list[Sector]:
    return list(db.scalars(select(Sector).where(Sector.activo).order_by(Sector.nombre)))


def buscar_colonias(
    db: Session, *, q: str | None, sector_id: int | None, limite: int | None = None, pag: ParametrosPagina | None = None
) -> tuple[list[Colonia], int]:
    """Filtro por nombre (ILIKE + similitud por trigramas) y por sector; ambos combinables."""
    condiciones = [Colonia.activo]
    if sector_id is not None:
        if db.get(Sector, sector_id) is None:
            raise error_validacion("sector_id", f"El sector {sector_id} no existe.")
        condiciones.append(Colonia.sector_id == sector_id)
    orden = [Colonia.nombre]
    if q:
        similitud = func.similarity(Colonia.nombre, q)
        condiciones.append(or_(Colonia.nombre.ilike(f"%{escapar_like(q)}%", escape="\\"), similitud > SIMILITUD_MINIMA))
        orden = [case((func.lower(Colonia.nombre) == q.lower(), 0), else_=1), similitud.desc(), Colonia.nombre]

    total = db.scalar(select(func.count()).select_from(Colonia).where(*condiciones)) or 0
    stmt = select(Colonia).where(*condiciones).order_by(*orden, Colonia.id)
    if pag is not None:
        stmt = stmt.limit(pag.por_pagina).offset(pag.offset)
    elif limite is not None:
        stmt = stmt.limit(limite)
    return list(db.scalars(stmt)), total


def tipos_dano() -> dict:
    """Describe el formulario dinámico (HU-02.2 / HU-03.1) y las constantes de negocio."""
    return {
        "limites_territorio": {
            "latitud_min": geo.LAT_MIN,
            "latitud_max": geo.LAT_MAX,
            "longitud_min": geo.LON_MIN,
            "longitud_max": geo.LON_MAX,
        },
        "descripcion_max_caracteres": 500,
        "datos": [
            {
                "tipo_dano": TipoDano.BACHE.value,
                "prefijo_folio": "BCH",
                "radio_duplicados_metros": geo.RADIO_DUPLICADO_PAVIMENTO_M,
                "campos": [
                    {
                        "nombre": "tamano",
                        "etiqueta": "Tamaño",
                        "tipo": "enum",
                        "obligatorio": True,
                        "opciones": [o.value for o in TamanoBache],
                    },
                    {
                        "nombre": "profundidad",
                        "etiqueta": "Profundidad",
                        "tipo": "enum",
                        "obligatorio": True,
                        "opciones": [o.value for o in ProfundidadBache],
                    },
                    {
                        "nombre": "carril_afectado",
                        "etiqueta": "Carril afectado",
                        "tipo": "enum",
                        "obligatorio": True,
                        "opciones": [o.value for o in CarrilAfectado],
                    },
                ],
            },
            {
                "tipo_dano": TipoDano.ALCANTARILLA.value,
                "prefijo_folio": "BCH",
                "radio_duplicados_metros": geo.RADIO_DUPLICADO_PAVIMENTO_M,
                "severidad_fija": "Alta",
                "campos": [
                    {
                        "nombre": "esta_senalizado",
                        "etiqueta": "¿Está señalizada?",
                        "tipo": "booleano",
                        "obligatorio": True,
                    }
                ],
            },
            {
                "tipo_dano": TipoDano.ENCHARCAMIENTO.value,
                "prefijo_folio": "ENC",
                "radio_duplicados_metros": geo.RADIO_DUPLICADO_ENCHARCAMIENTO_M,
                "vigencia_horas": HORAS_VIGENCIA,
                "desmentidos_para_historico": DESMENTIDOS_PARA_HISTORICO,
                "campos": [
                    {
                        "nombre": "nivel_agua",
                        "etiqueta": "Nivel del agua",
                        "tipo": "enum",
                        "obligatorio": True,
                        "opciones": [o.value for o in NivelAgua],
                    },
                    {
                        "nombre": "hay_riesgo_personas_vehiculos",
                        "etiqueta": "¿Hay riesgo para personas o vehículos?",
                        "tipo": "booleano",
                        "obligatorio": True,
                        "visible_si": {"nivel_agua": NivelAgua.INTRANSITABLE.value},
                    },
                ],
            },
        ],
    }


def _transiciones_publicas(tabla: dict) -> list[dict]:
    return [
        {"desde": d.value, "hacia": h.value, "roles": sorted(roles, key=lambda r: (r == "sistema", r))}
        for (d, h), roles in tabla.items()
    ]


def estados() -> dict:
    return {
        "pavimento": {
            "estados": [e.value for e in transiciones.ESTADOS_PAVIMENTO],
            "finales": [e.value for e in transiciones.FINALES_PAVIMENTO],
            "transiciones": _transiciones_publicas(transiciones.TRANSICIONES_PAVIMENTO),
            "etiquetas_publicas": {"Recibido": "Sin validar"},
        },
        "encharcamiento": {
            "estados": [e.value for e in transiciones.ESTADOS_ENCHARCAMIENTO],
            "finales": [e.value for e in transiciones.FINALES_ENCHARCAMIENTO],
            "transiciones": _transiciones_publicas(transiciones.TRANSICIONES_ENCHARCAMIENTO),
        },
    }
