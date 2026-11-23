"""Regresiones de la auditoría final (docs/auditoria-final/03-hallazgos.md): A2, A3, A4, M1, M2 y M3.

Cada prueba reproduce el sondeo que confirmó el hallazgo y verifica la corrección.
"""

import struct

import pytest
from starlette.requests import Request

from app.core.config import get_settings
from app.core.red import ip_cliente
from app.services import auth as servicio_auth
from app.services import fotos
from app.services.imagenes import ImagenInvalida, _orientacion_exif, limpiar_metadatos
from tests.conftest import CONTRASENA, crear_cuenta, crear_reporte, payload_bache, punto_unico
from tests.test_fase1 import JPG, PNG, subir, validar
from tests.test_fase3 import fusionar, par_duplicado

API = "/api/v1"


@pytest.fixture(autouse=True)
def _directorio_fotos(tmp_path, monkeypatch):
    monkeypatch.setattr(fotos, "directorio_fotos", lambda: tmp_path)


@pytest.fixture
def ip_por_cabecera(monkeypatch):
    """Simula un despliegue detrás de un proxy de confianza que escribe la IP real en X-Real-IP."""
    monkeypatch.setattr(get_settings(), "client_ip_header", "X-Real-IP")


def _jpeg_con_exif(orientacion: int = 6) -> bytes:
    tiff = b"MM\x00*" + struct.pack(">I", 8) + struct.pack(">H", 1)
    tiff += struct.pack(">HHIHH", 0x0112, 3, 1, orientacion, 0) + struct.pack(">I", 0)
    app1 = b"Exif\x00\x00" + tiff + b"GPS 31.7398N 106.4870W Juan Perez iPhone"
    segmento = b"\xff\xe1" + struct.pack(">H", len(app1) + 2) + app1
    comentario = b"\xff\xfe" + struct.pack(">H", 2 + 12) + b"Juan Perez!!"
    return JPG[:20] + segmento + comentario + JPG[20:] + b"<script>oculto</script>"


# =============================================================================== A2: sesión del enlace municipal


def test_enlace_municipal_consulta_renueva_y_cierra_sesion(client):
    enlace = crear_cuenta(client, "enlace_municipal")
    assert client.get(f"{API}/auth/yo", headers=enlace.h).status_code == 200
    renovado = client.post(f"{API}/auth/renovar", headers=enlace.h)
    assert renovado.status_code == 200
    h = {"Authorization": f"Bearer {renovado.json()['access_token']}"}
    assert client.post(f"{API}/auth/cerrar-sesion", headers=h).status_code == 204
    # El token queda revocado en el servidor (antes seguía sirviendo tras «cerrar sesión»).
    assert client.get(f"{API}/enlace/reportes", headers=h).status_code == 401


# =============================================================================== A3: metadatos de fotografías


def test_quita_exif_comentarios_y_datos_tras_el_fin_conservando_orientacion():
    limpia = limpiar_metadatos(_jpeg_con_exif(6), "image/jpeg")
    assert b"GPS" not in limpia and b"Juan" not in limpia and b"script" not in limpia
    assert limpia.endswith(b"\xff\xd9") and limpia.startswith(b"\xff\xd8\xff\xe0")
    inicio = limpia.find(b"Exif\x00\x00")
    assert inicio > limpia.find(b"JFIF") > 0  # APP0 sigue primero
    assert _orientacion_exif(limpia[inicio:]) == 6
    assert limpiar_metadatos(limpia, "image/jpeg") == limpia  # idempotente
    assert limpiar_metadatos(JPG, "image/jpeg") == JPG and limpiar_metadatos(PNG, "image/png") == PNG


def test_png_sin_fragmentos_de_texto_ni_datos_ocultos():
    def fragmento(tipo: bytes, datos: bytes) -> bytes:
        return struct.pack(">I", len(datos)) + tipo + datos + b"\x00\x00\x00\x00"

    ihdr_fin = 8 + 25
    png = PNG[:ihdr_fin] + fragmento(b"tEXt", b"Author\x00Juan Perez") + fragmento(b"eXIf", b"GPS") + PNG[ihdr_fin:]
    limpia = limpiar_metadatos(png + b"ZIP-OCULTO", "image/png")
    assert limpia == PNG


@pytest.mark.parametrize(
    ("contenido", "mime"),
    [
        (b"\x89PNG\r\n\x1a\n" + b"\x00" * 64, "image/png"),
        (b"\xff\xd8\xff\xe0" + b"\x00" * 64, "image/jpeg"),
        (JPG[:-2], "image/jpeg"),  # sin fin de imagen
    ],
)
def test_estructura_invalida_se_rechaza(contenido, mime):
    with pytest.raises(ImagenInvalida):
        limpiar_metadatos(contenido, mime)


def test_foto_publica_sin_exif_y_sin_nombre_original(client, ciudadano, moderador):
    lat, lon = punto_unico()
    folio = crear_reporte(client, ciudadano, payload_bache(client, lat, lon))["folio"]
    subida = subir(client, ciudadano, folio, ("Juan_Perez_Calle_Falsa_123.jpg", _jpeg_con_exif(), "image/jpeg"))
    assert subida.status_code == 201, subida.text
    validar(client, moderador, folio)

    publica = client.get(f"{API}/reportes/{folio}/fotos").json()["datos"][0]
    assert publica["nombre_original"] == "fotografia-1.jpg"
    contenido = client.get(publica["url"]).content
    assert b"GPS" not in contenido and b"Juan" not in contenido
    assert publica["tamano_bytes"] == len(contenido)

    del_autor = client.get(f"{API}/reportes/{folio}/fotos", headers=ciudadano.h).json()["datos"][0]
    assert del_autor["nombre_original"] == "Juan_Perez_Calle_Falsa_123.jpg"


def test_imagen_danada_se_rechaza_con_mensaje(client, ciudadano):
    lat, lon = punto_unico()
    folio = crear_reporte(client, ciudadano, payload_bache(client, lat, lon))["folio"]
    r = subir(client, ciudadano, folio, ("rota.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 64, "image/jpeg"))
    assert r.status_code == 422
    assert "dañada" in r.json()["error"]["detalles"][0]["mensaje"]


# =============================================================================== A4: IP real del cliente


def _peticion(cabeceras: dict[str, str], host: str = "10.0.0.1") -> Request:
    return Request({
        "type": "http",
        "headers": [(k.lower().encode(), v.encode()) for k, v in cabeceras.items()],
        "client": (host, 1234),
    })


def test_ip_cliente_solo_confia_en_cabeceras_declaradas(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "client_ip_header", "")
    monkeypatch.setattr(s, "trusted_proxy_hops", 0)
    falsa = {"X-Forwarded-For": "1.2.3.4", "CF-Connecting-IP": "5.6.7.8"}
    assert ip_cliente(_peticion(falsa)) == "10.0.0.1"  # sin configuración, nada se falsifica

    monkeypatch.setattr(s, "client_ip_header", "CF-Connecting-IP")
    assert ip_cliente(_peticion(falsa)) == "5.6.7.8"
    assert ip_cliente(_peticion({"CF-Connecting-IP": "no-es-ip"})) == "10.0.0.1"

    monkeypatch.setattr(s, "client_ip_header", "")
    monkeypatch.setattr(s, "trusted_proxy_hops", 1)
    # El cliente puede anteponer lo que quiera; sólo cuenta lo que agregó el proxy de confianza (último salto).
    assert ip_cliente(_peticion({"X-Forwarded-For": "1.1.1.1, 203.0.113.9"})) == "203.0.113.9"


# =============================================================================== M1 / M2: registro e inicio de sesión


def test_registro_limitado_por_ip(client, monkeypatch, ip_por_cabecera):
    monkeypatch.setattr(servicio_auth.limitador_registro, "maximo", 3)
    servicio_auth.limitador_registro.limpiar()
    try:
        h = {"X-Real-IP": "198.51.100.20"}
        codigos = [
            client.post(
                f"{API}/auth/registro",
                json={"nombre": "Bot", "correo": f"bot-reg-{i}-{id(h)}@ejemplo.mx", "contrasena": CONTRASENA, "acepta_aviso_privacidad": True},
                headers=h,
            )
            for i in range(4)
        ]
        assert [r.status_code for r in codigos] == [201, 201, 201, 429]
        assert codigos[-1].json()["error"]["codigo"] == "LIMITE_REGISTROS" and "Retry-After" in codigos[-1].headers
        otra_ip = client.post(
            f"{API}/auth/registro",
            json={"nombre": "Persona", "correo": f"otra-{id(h)}@ejemplo.mx", "contrasena": CONTRASENA, "acepta_aviso_privacidad": True},
            headers={"X-Real-IP": "198.51.100.21"},
        )
        assert otra_ip.status_code == 201
    finally:
        servicio_auth.limitador_registro.limpiar()


def test_un_tercero_no_puede_bloquear_la_cuenta_de_otra_persona(client, ip_por_cabecera):
    victima = crear_cuenta(client)
    atacante = {"X-Real-IP": "203.0.113.66"}
    for _ in range(5):
        client.post(f"{API}/auth/login", json={"correo": victima.correo, "contrasena": "Incorrecta123"}, headers=atacante)
    bloqueado = client.post(f"{API}/auth/login", json={"correo": victima.correo, "contrasena": CONTRASENA}, headers=atacante)
    assert bloqueado.status_code == 429 and "Retry-After" in bloqueado.headers
    propia = client.post(f"{API}/auth/login", json={"correo": victima.correo, "contrasena": CONTRASENA}, headers={"X-Real-IP": "198.51.100.7"})
    assert propia.status_code == 200, propia.text


def test_limite_de_fallos_por_ip_frena_el_relleno_de_credenciales(client, monkeypatch, ip_por_cabecera):
    monkeypatch.setattr(servicio_auth.limitador_login_ip, "maximo", 4)
    servicio_auth.limitador_login_ip.limpiar()
    try:
        h = {"X-Real-IP": "203.0.113.77"}
        for i in range(4):
            r = client.post(f"{API}/auth/login", json={"correo": f"nadie{i}@ejemplo.mx", "contrasena": "Incorrecta123"}, headers=h)
            assert r.status_code == 401
        r = client.post(f"{API}/auth/login", json={"correo": "otro@ejemplo.mx", "contrasena": "Incorrecta123"}, headers=h)
        assert r.status_code == 429 and r.json()["error"]["codigo"] == "DEMASIADOS_INTENTOS"
    finally:
        servicio_auth.limitador_login_ip.limpiar()


# =============================================================================== M3: fusión y RN-05


def test_coordinacion_no_rechaza_via_fusion(client, ciudadanos, coordinador, moderador):
    principal, secundario = par_duplicado(client, ciudadanos[0], ciudadanos[1])
    r = fusionar(client, coordinador, principal, secundario)
    assert r.status_code == 403 and r.json()["error"]["codigo"] == "ROL_NO_AUTORIZADO"
    detalle = client.get(f"{API}/moderacion/reportes/{secundario}", headers=moderador.h).json()
    assert detalle["estado"] == "Recibido"  # nada cambió (transacción revertida)
    assert fusionar(client, moderador, principal, secundario).status_code == 200


# =============================================================================== M5 / M6 / M7: perímetro de la API


def test_cabeceras_de_seguridad_de_la_api(client):
    h = client.get(f"{API}/catalogos/sectores").headers
    assert h["x-frame-options"] == "DENY" and h["referrer-policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in h["content-security-policy"] and h["x-content-type-options"] == "nosniff"


def test_cuerpo_demasiado_grande_responde_413_sin_procesarlo(client, ciudadano):
    lat, lon = punto_unico()
    folio = crear_reporte(client, ciudadano, payload_bache(client, lat, lon))["folio"]
    enorme = b"\x00" * (get_settings().max_cuerpo_bytes + 1)
    r = subir(client, ciudadano, folio, ("a.png", enorme, "image/png"))
    assert r.status_code == 413 and r.json()["error"]["codigo"] == "CUERPO_DEMASIADO_GRANDE"
    assert client.get(f"{API}/reportes/{folio}/fotos", headers=ciudadano.h).json()["datos"] == []


def test_websocket_respeta_el_tope_de_conexiones_por_ip(client, monkeypatch):
    from starlette.websockets import WebSocketDisconnect

    monkeypatch.setattr(get_settings(), "ws_max_conexiones_por_ip", 1)
    with client.websocket_connect(f"{API}/ws/encharcamientos") as primera:
        assert primera.receive_json()["tipo"] == "hola"
        with pytest.raises(WebSocketDisconnect) as cierre:
            with client.websocket_connect(f"{API}/ws/encharcamientos") as segunda:
                segunda.receive_json()
        assert cierre.value.code == 1013
