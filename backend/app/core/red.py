"""IP del cliente para los límites anti-abuso (auditoría final, A4).

Detrás de un proxy (Render, Cloudflare, Nginx) `request.client.host` es la IP del proxy: todas las personas
compartirían una sola cubeta. Pero confiar ciegamente en `X-Forwarded-For` permite falsificar la IP. Por eso
sólo se lee una cabecera cuando el despliegue declara explícitamente cuál escribe su proxy de confianza.
"""

import ipaddress

from starlette.requests import HTTPConnection

from app.core.config import get_settings

DESCONOCIDA = "desconocida"


def _valida(valor: str | None) -> str | None:
    if not valor:
        return None
    try:
        return str(ipaddress.ip_address(valor.strip()))
    except ValueError:
        return None


def ip_cliente(request: HTTPConnection) -> str:
    """Sirve para peticiones HTTP y WebSocket."""
    s = get_settings()
    if s.client_ip_header:
        ip = _valida(request.headers.get(s.client_ip_header))
        if ip:
            return ip
    if s.trusted_proxy_hops > 0:
        cadena = [p for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
        if len(cadena) >= s.trusted_proxy_hops:
            ip = _valida(cadena[-s.trusted_proxy_hops])
            if ip:
                return ip
    return request.client.host if request.client else DESCONOCIDA
