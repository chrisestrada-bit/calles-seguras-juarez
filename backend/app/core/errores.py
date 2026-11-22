"""Errores de la API con envoltura uniforme y mensajes en español de México."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("calles_seguras")

MENSAJE_FUERA_DE_JUAREZ = (
    "La ubicación está fuera de los límites de Ciudad Juárez, Chihuahua. "
    "Selecciona un punto dentro del municipio."
)
MARCA_FUERA_DE_JUAREZ = "FUERA_DE_JUAREZ|"


class ErrorAPI(Exception):
    """Error de negocio que se serializa como {"error": {codigo, mensaje, detalles}}."""

    def __init__(
        self,
        status: int,
        codigo: str,
        mensaje: str,
        detalles: list[Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(mensaje)
        self.status = status
        self.codigo = codigo
        self.mensaje = mensaje
        self.detalles = detalles or []
        self.headers = headers or {}


def fuera_de_juarez(campo: str, detalle: str) -> ErrorAPI:
    return ErrorAPI(
        422,
        "FUERA_DE_JUAREZ",
        MENSAJE_FUERA_DE_JUAREZ,
        [{"campo": campo, "mensaje": detalle}],
    )


def _cuerpo(codigo: str, mensaje: str, detalles: list[Any] | None = None) -> dict[str, Any]:
    return {"error": {"codigo": codigo, "mensaje": mensaje, "detalles": detalles or []}}


_TRADUCCIONES = {
    "missing": lambda c: "Este campo es obligatorio.",
    "string_too_short": lambda c: f"Debe tener al menos {c.get('min_length')} caracteres.",
    "string_too_long": lambda c: f"Debe tener máximo {c.get('max_length')} caracteres.",
    "string_type": lambda c: "Debe ser texto.",
    "greater_than_equal": lambda c: f"Debe ser mayor o igual a {c.get('ge')}.",
    "less_than_equal": lambda c: f"Debe ser menor o igual a {c.get('le')}.",
    "greater_than": lambda c: f"Debe ser mayor que {c.get('gt')}.",
    "less_than": lambda c: f"Debe ser menor que {c.get('lt')}.",
    "int_parsing": lambda c: "Debe ser un número entero.",
    "int_type": lambda c: "Debe ser un número entero.",
    "float_parsing": lambda c: "Debe ser un número.",
    "float_type": lambda c: "Debe ser un número.",
    "bool_parsing": lambda c: "Debe ser verdadero o falso.",
    "bool_type": lambda c: "Debe ser verdadero o falso.",
    "enum": lambda c: f"Valor no permitido. Opciones: {c.get('expected')}.",
    "literal_error": lambda c: f"Valor no permitido. Opciones: {c.get('expected')}.",
    "extra_forbidden": lambda c: "Campo no permitido.",
    "string_pattern_mismatch": lambda c: "El formato no es válido.",
    "date_parsing": lambda c: "Fecha inválida; usa el formato AAAA-MM-DD.",
    "date_type": lambda c: "Fecha inválida; usa el formato AAAA-MM-DD.",
    "date_from_datetime_parsing": lambda c: "Fecha inválida; usa el formato AAAA-MM-DD.",
    "uuid_parsing": lambda c: "El identificador no es válido.",
    "json_invalid": lambda c: "El cuerpo de la petición no es un JSON válido.",
    "union_tag_invalid": lambda c: "El tipo de daño no es válido.",
    "union_tag_not_found": lambda c: "Indica el tipo de daño (tipo_dano).",
    "model_attributes_type": lambda c: "El cuerpo de la petición no es válido.",
    "dict_type": lambda c: "El cuerpo de la petición no es válido.",
    "value_error": lambda c: "El valor no es válido.",
}


def _campo(loc: tuple[Any, ...]) -> str | None:
    for parte in reversed(loc):
        if isinstance(parte, str) and parte not in {"body", "query", "path"}:
            return parte
    return None


def _traducir_validacion(errores: list[dict[str, Any]]) -> tuple[str, str, list[dict[str, Any]]]:
    codigo, mensaje = "VALIDACION", "Revisa los datos marcados."
    detalles: list[dict[str, Any]] = []
    for e in errores:
        campo = _campo(tuple(e.get("loc", ())))
        texto = str(e.get("msg", ""))
        if texto.startswith("Value error, "):
            texto = texto.removeprefix("Value error, ")
        if texto.startswith(MARCA_FUERA_DE_JUAREZ):
            texto = texto.removeprefix(MARCA_FUERA_DE_JUAREZ)
            codigo, mensaje = "FUERA_DE_JUAREZ", MENSAJE_FUERA_DE_JUAREZ
        elif e.get("type") == "value_error":
            pass  # ya viene en español desde el validador
        else:
            traductor = _TRADUCCIONES.get(e.get("type", ""))
            texto = traductor(e.get("ctx") or {}) if traductor else "El valor no es válido."
        detalles.append({"campo": campo, "mensaje": texto})
    return codigo, mensaje, detalles


_ESTANDAR_HTTP = {
    401: ("NO_AUTENTICADO", "Necesitas iniciar sesión para continuar."),
    403: ("ROL_NO_AUTORIZADO", "Tu rol no tiene permiso para realizar esta acción."),
    404: ("NO_ENCONTRADO", "El recurso solicitado no existe."),
    405: ("METODO_NO_PERMITIDO", "Este método no está permitido para el recurso."),
}


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorAPI)
    async def _error_api(_: Request, exc: ErrorAPI) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status,
            content=_cuerpo(exc.codigo, exc.mensaje, exc.detalles),
            headers=exc.headers or None,
        )

    @app.exception_handler(RequestValidationError)
    async def _validacion(_: Request, exc: RequestValidationError) -> JSONResponse:
        codigo, mensaje, detalles = _traducir_validacion(list(exc.errors()))
        return JSONResponse(status_code=422, content=_cuerpo(codigo, mensaje, detalles))

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        codigo, mensaje = _ESTANDAR_HTTP.get(
            exc.status_code, ("ERROR_HTTP", "No fue posible procesar la solicitud.")
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_cuerpo(codigo, mensaje),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _inesperado(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Error no controlado: %s", type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content=_cuerpo("ERROR_INTERNO", "Ocurrió un error inesperado. Intenta de nuevo más tarde."),
        )
