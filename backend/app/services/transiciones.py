"""Máquina de estados (RN-05 y RN-06). Respaldada también por el trigger trg_reportes_transicion."""

from app.core.errores import ErrorAPI
from app.models import EstadoReporte as E
from app.models import RolUsuario, TipoDano

SISTEMA = "sistema"
_M, _C = RolUsuario.MODERADOR.value, RolUsuario.COORDINADOR.value
_E = RolUsuario.ENLACE_MUNICIPAL.value  # HU-05.5: sólo sobre baches de sus cuadrillas (se valida en el servicio)

# (desde, hacia) -> roles que pueden ejecutarla.
TRANSICIONES_PAVIMENTO: dict[tuple[E, E], frozenset[str]] = {
    (E.RECIBIDO, E.VALIDADO): frozenset({_M}),
    (E.RECIBIDO, E.RECHAZADO): frozenset({_M}),
    (E.VALIDADO, E.PROGRAMADO): frozenset({_M, _C}),
    (E.VALIDADO, E.EN_REPARACION): frozenset({_M, _C}),
    (E.PROGRAMADO, E.EN_REPARACION): frozenset({_M, _C, _E}),
    (E.EN_REPARACION, E.REPARADO): frozenset({_M, _C, _E}),
}

TRANSICIONES_ENCHARCAMIENTO: dict[tuple[E, E], frozenset[str]] = {
    (E.ACTIVO, E.HISTORICO): frozenset({SISTEMA}),
    (E.ACTIVO, E.RECHAZADO): frozenset({_M}),
}

ESTADOS_PAVIMENTO = [E.RECIBIDO, E.VALIDADO, E.PROGRAMADO, E.EN_REPARACION, E.REPARADO, E.RECHAZADO]
ESTADOS_ENCHARCAMIENTO = [E.ACTIVO, E.HISTORICO, E.RECHAZADO]
FINALES_PAVIMENTO = [E.REPARADO, E.RECHAZADO]
FINALES_ENCHARCAMIENTO = [E.HISTORICO, E.RECHAZADO]


def tabla(tipo: TipoDano) -> dict[tuple[E, E], frozenset[str]]:
    return TRANSICIONES_ENCHARCAMIENTO if tipo == TipoDano.ENCHARCAMIENTO else TRANSICIONES_PAVIMENTO


def disponibles(tipo: TipoDano, desde: E, rol: RolUsuario) -> list[E]:
    """Estados a los que el rol puede mover manualmente el reporte."""
    return [h for (d, h), roles in tabla(tipo).items() if d == desde and rol.value in roles]


def validar_transicion(tipo: TipoDano, desde: E, hacia: E, rol: RolUsuario) -> None:
    roles = tabla(tipo).get((desde, hacia))
    manuales = (roles or frozenset()) - {SISTEMA}
    if not manuales:
        raise ErrorAPI(
            400,
            "TRANSICION_INVALIDA",
            f'No es posible cambiar el estado de "{desde.value}" a "{hacia.value}".',
        )
    if rol.value not in manuales:
        raise ErrorAPI(403, "ROL_NO_AUTORIZADO", "Tu rol no tiene permiso para realizar esta acción.")
