"""Enumeraciones del dominio. Los valores coinciden con los ENUM de PostgreSQL y con la API."""

import enum


class RolUsuario(enum.StrEnum):
    CIUDADANO = "ciudadano"
    MODERADOR = "moderador"
    COORDINADOR = "coordinador"
    ENLACE_MUNICIPAL = "enlace_municipal"  # HU-05.5: autoridad que reporta el avance de sus cuadrillas


class TipoDano(enum.StrEnum):
    BACHE = "Bache"
    ALCANTARILLA = "Alcantarilla sin tapa"
    ENCHARCAMIENTO = "Encharcamiento"


class EstadoReporte(enum.StrEnum):
    RECIBIDO = "Recibido"
    VALIDADO = "Validado"
    PROGRAMADO = "Programado"
    EN_REPARACION = "En reparación"
    REPARADO = "Reparado"
    RECHAZADO = "Rechazado"
    ACTIVO = "Activo"
    HISTORICO = "Histórico"


class Severidad(enum.StrEnum):
    BAJA = "Baja"
    MEDIA = "Media"
    ALTA = "Alta"


class TamanoBache(enum.StrEnum):
    CHICO = "chico"
    MEDIANO = "mediano"
    GRANDE = "grande"


class ProfundidadBache(enum.StrEnum):
    MENOS_5 = "menos de 5 cm"
    DE_5_A_10 = "5 a 10 cm"
    MAS_10 = "más de 10 cm"


class CarrilAfectado(enum.StrEnum):
    DERECHO = "carril derecho"
    CENTRAL = "carril central"
    IZQUIERDO = "carril izquierdo"
    VARIOS = "varios carriles"
    ACOTAMIENTO = "acotamiento"


class NivelAgua(enum.StrEnum):
    A_UN_LADO = "a un lado de la calle"
    CUBRE_CARRIL = "cubre un carril"
    A_MEDIA_LLANTA = "a media llanta"
    INTRANSITABLE = "intransitable"


class TipoConfirmacion(enum.StrEnum):
    CONFIRMACION_DANO = "confirmacion_dano"
    SIGUE_AHI = "sigue_ahi"
    YA_NO_HAY_AGUA = "ya_no_hay_agua"


class OrigenCambio(enum.StrEnum):
    CIUDADANO = "ciudadano"
    MODERACION = "moderacion"
    SISTEMA = "sistema"


ESTADOS_PAVIMENTO_ABIERTOS = (
    EstadoReporte.RECIBIDO,
    EstadoReporte.VALIDADO,
    EstadoReporte.PROGRAMADO,
    EstadoReporte.EN_REPARACION,
)
TIPOS_PAVIMENTO = (TipoDano.BACHE, TipoDano.ALCANTARILLA)
