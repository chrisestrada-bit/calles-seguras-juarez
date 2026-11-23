"""Subida insegura de archivos en evidencia fotográfica (HU-02.4, RN-04, OWASP A03/A04).

Complementa test_fase1 y test_auditoria_final: archivos disfrazados de imagen, políglotas, bombas de
descompresión por dimensiones, recorrido de directorios en `ruta_de` y cabeceras seguras en la descarga.
"""

import struct
from types import SimpleNamespace

import pytest

from app.core.errores import ErrorAPI
from app.services import fotos
from app.services.imagenes import MAX_LADO_PX, ImagenInvalida, limpiar_metadatos
from tests.test_fase1 import JPG, PNG, nuevo_bache, subir, validar

API = "/api/v1"


@pytest.fixture(autouse=True)
def _directorio_fotos(tmp_path, monkeypatch):
    monkeypatch.setattr(fotos, "directorio_fotos", lambda: tmp_path)


def _png_de(ancho: int, alto: int) -> bytes:
    # El CRC no se valida (véase imagenes._limpiar_png), así que basta con reescribir ancho y alto del IHDR.
    return PNG[:16] + struct.pack(">II", ancho, alto) + PNG[24:]


def _jpg_de(ancho: int, alto: int) -> bytes:
    sof0 = b"\xff\xc0" + struct.pack(">HBHHB", 11, 8, alto, ancho, 1) + b"\x01\x11\x00"
    corte = JPG.find(b"\xff\xda")
    return JPG[:corte] + sof0 + JPG[corte:]


@pytest.mark.parametrize(
    ("nombre", "contenido", "tipo"),
    [
        ("foto.jpg", b"<!DOCTYPE html><html><script>alert(1)</script></html>", "image/jpeg"),
        ("foto.png", b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>', "image/png"),
        ("foto.jpg", b"texto plano renombrado", "image/jpeg"),
        ("foto.jpg", b"PK\x03\x04 zip renombrado", "image/jpeg"),
        # Políglotas: firma válida seguida de contenido activo, sin estructura de imagen.
        ("poli.jpg", b"\xff\xd8\xff<html><script>alert(1)</script></html>", "image/jpeg"),
        ("poli.png", b"\x89PNG\r\n\x1a\n<html><script>alert(1)</script></html>", "image/png"),
    ],
)
def test_archivo_disfrazado_de_imagen_se_rechaza_y_no_se_guarda(client, ciudadano, tmp_path, nombre, contenido, tipo):
    folio = nuevo_bache(client, ciudadano)["folio"]
    r = subir(client, ciudadano, folio, (nombre, contenido, tipo))
    assert r.status_code == 422, r.text
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("dimensiones", [(65_535, 65_535), (MAX_LADO_PX + 1, 1), (10_000, 10_000), (0, 1)])
def test_dimensiones_anomalas_se_rechazan(dimensiones):
    with pytest.raises(ImagenInvalida):
        limpiar_metadatos(_png_de(*dimensiones), "image/png")
    with pytest.raises(ImagenInvalida):
        limpiar_metadatos(_jpg_de(*dimensiones), "image/jpeg")


def test_dimensiones_de_camara_real_se_aceptan():
    assert limpiar_metadatos(_png_de(8160, 6120), "image/png")
    assert limpiar_metadatos(_jpg_de(4032, 3024), "image/jpeg")


def test_bomba_de_descompresion_se_rechaza_por_api(client, ciudadano, tmp_path):
    folio = nuevo_bache(client, ciudadano)["folio"]
    r = subir(client, ciudadano, folio, ("bomba.png", _png_de(65_535, 65_535), "image/png"))
    assert r.status_code == 422
    assert "dañada" in r.json()["error"]["detalles"][0]["mensaje"]
    assert list(tmp_path.iterdir()) == []


def test_nombre_original_con_recorrido_no_afecta_la_ruta_en_disco(client, ciudadano, tmp_path):
    folio = nuevo_bache(client, ciudadano)["folio"]
    r = subir(client, ciudadano, folio, ("../../etc/passwd.png", PNG, "image/png"))
    assert r.status_code == 201, r.text
    assert [p.parent for p in tmp_path.iterdir()] == [tmp_path]
    assert r.json()["aceptadas"][0]["nombre_original"] == "passwd.png"


@pytest.mark.parametrize("ruta", ["../secreto.txt", "../../etc/passwd", "/etc/passwd", "..\\secreto.txt", "sub/../../x"])
def test_ruta_de_bloquea_recorrido_de_directorios(tmp_path, ruta):
    secreto = tmp_path.parent / "secreto.txt"
    secreto.write_text("no debe servirse", encoding="utf-8")
    foto = SimpleNamespace(id="x", ruta_almacenamiento=ruta)
    with pytest.raises(ErrorAPI) as error:
        fotos.ruta_de(foto)
    assert error.value.status == 404


def test_descarga_con_cabeceras_seguras_y_acceso_controlado(client, ciudadano, moderador):
    folio = nuevo_bache(client, ciudadano)["folio"]
    url = subir(client, ciudadano, folio, ("a.png", PNG, "image/png")).json()["aceptadas"][0]["url"]
    assert client.get(url).status_code == 403  # «Recibido»: el público aún no la ve
    validar(client, moderador, folio)
    r = client.get(url)
    assert r.status_code == 200 and r.content == PNG
    assert r.headers["content-type"] == "image/png"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["content-disposition"] == "inline"
    assert r.headers["x-frame-options"] == "DENY"
