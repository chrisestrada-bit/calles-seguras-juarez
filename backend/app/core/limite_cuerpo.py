"""Tope de tamaño del cuerpo de las peticiones (auditoría final, M7).

Sin él, Starlette guarda en disco temporal cualquier multipart, de cualquier tamaño y con cualquier número de
partes, antes de que el servicio de fotos aplique su cupo de 3 × 5 MB. Se corta tanto por `Content-Length`
declarado como por los bytes que realmente llegan (cuerpos *chunked* sin longitud).
"""

import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_CUERPO_413 = json.dumps(
    {
        "error": {
            "codigo": "CUERPO_DEMASIADO_GRANDE",
            "mensaje": "La solicitud es demasiado grande. Envía como máximo 3 imágenes de 5 MB cada una.",
            "detalles": [],
        }
    },
    ensure_ascii=False,
).encode()


class _Excedido(Exception):
    pass


class LimiteCuerpo:
    def __init__(self, app: ASGIApp, maximo_bytes: int) -> None:
        self.app = app
        self.maximo = maximo_bytes

    async def _responder_413(self, send: Send) -> None:
        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [(b"content-type", b"application/json; charset=utf-8"), (b"content-length", str(len(_CUERPO_413)).encode())],
        })
        await send({"type": "http.response.body", "body": _CUERPO_413})

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        for nombre, valor in scope.get("headers", []):
            if nombre == b"content-length":
                try:
                    if int(valor) > self.maximo:
                        await self._responder_413(send)
                        return
                except ValueError:
                    pass
        recibidos = 0
        iniciada = False

        async def recibir_contado() -> Message:
            nonlocal recibidos
            mensaje = await receive()
            if mensaje["type"] == "http.request":
                recibidos += len(mensaje.get("body", b""))
                if recibidos > self.maximo:
                    raise _Excedido
            return mensaje

        async def enviar_vigilado(mensaje: Message) -> None:
            nonlocal iniciada
            if mensaje["type"] == "http.response.start":
                iniciada = True
            await send(mensaje)

        try:
            await self.app(scope, recibir_contado, enviar_vigilado)
        except _Excedido:
            if not iniciada:
                await self._responder_413(send)
