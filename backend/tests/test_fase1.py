"""Fase 1 de requisitos opcionales: HU-02.4 (fotos), HU-04.5 (mapa) y HU-07.3 (exportación CSV/XML + importación XML)."""

import csv
import io
import uuid
from pathlib import Path

import pytest
from lxml import etree

from app.services import exportacion, fotos
from tests.conftest import crear_reporte, desplazar, payload_bache, payload_enc, punto_unico

API = "/api/v1"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


@pytest.fixture(autouse=True)
def _directorio_fotos(tmp_path, monkeypatch):
    monkeypatch.setattr(fotos, "directorio_fotos", lambda: tmp_path)


def subir(client, cuenta, folio, *archivos):
    """archivos: tuplas (nombre, bytes, content_type)."""
    return client.post(
        f"{API}/reportes/{folio}/fotos",
        files=[("archivos", a) for a in archivos],
        headers=cuenta.h if cuenta else {},
    )


def validar(client, moderador, folio):
    r = client.post(
        f"{API}/moderacion/reportes/{folio}/transiciones", json={"estado_nuevo": "Validado"}, headers=moderador.h
    )
    assert r.status_code == 200, r.text


def nuevo_bache(client, cuenta):
    lat, lon = punto_unico()
    return crear_reporte(client, cuenta, payload_bache(client, lat, lon))


# ------------------------------------------------------------------------------ HU-02.4 fotos


def test_foto_valida_jpg_y_png_se_guardan_con_nombre_uuid(client, ciudadano, tmp_path):
    folio = nuevo_bache(client, ciudadano)["folio"]
    r = subir(client, ciudadano, folio, ("a.jpg", JPG, "image/jpeg"), ("b.png", PNG, "image/png"))
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert len(cuerpo["aceptadas"]) == 2 and cuerpo["rechazadas"] == []
    archivos = sorted(p.name for p in tmp_path.iterdir())
    assert len(archivos) == 2
    for nombre in archivos:
        uuid.UUID(Path(nombre).stem)  # nombre impredecible UUIDv4
    assert "usuario_id" not in r.text and ciudadano.id not in r.text  # RN-04


def test_reporte_sin_fotos_sigue_siendo_valido(client, ciudadano):
    folio = nuevo_bache(client, ciudadano)["folio"]
    r = client.get(f"{API}/reportes/{folio}/fotos", headers=ciudadano.h)
    assert r.status_code == 200 and r.json()["datos"] == []


def test_valida_contenido_real_no_extension_ni_content_type(client, ciudadano):
    folio = nuevo_bache(client, ciudadano)["folio"]
    falso = subir(client, ciudadano, folio, ("virus.jpg", b"MZ\x90\x00 no soy imagen", "image/jpeg"))
    assert falso.status_code == 422
    assert "JPG o PNG" in falso.json()["error"]["detalles"][0]["mensaje"]
    gif = subir(client, ciudadano, folio, ("a.png", b"GIF89a" + b"\x00" * 20, "image/png"))
    assert gif.status_code == 422
    vacio = subir(client, ciudadano, folio, ("vacio.png", b"", "image/png"))
    assert vacio.status_code == 422


def test_limite_de_5_mb_exacto_y_5_mb_mas_un_byte(client, ciudadano):
    folio = nuevo_bache(client, ciudadano)["folio"]
    limite = 5 * 1024 * 1024
    justo = PNG + b"\x00" * (limite - len(PNG))
    demasiado = PNG + b"\x00" * (limite + 1 - len(PNG))
    assert len(justo) == limite and len(demasiado) == limite + 1
    ok = subir(client, ciudadano, folio, ("justo.png", justo, "image/png"))
    assert ok.status_code == 201, ok.text
    mal = subir(client, ciudadano, folio, ("grande.png", demasiado, "image/png"))
    assert mal.status_code == 422
    assert "5 MB" in mal.json()["error"]["detalles"][0]["mensaje"]


def test_maximo_3_fotos_y_archivo_invalido_no_pierde_los_validos(client, ciudadano):
    folio = nuevo_bache(client, ciudadano)["folio"]
    r = subir(
        client,
        ciudadano,
        folio,
        ("1.jpg", JPG, "image/jpeg"),
        ("malo.txt", b"texto", "text/plain"),
        ("2.png", PNG, "image/png"),
        ("3.jpg", JPG, "image/jpeg"),
        ("4.jpg", JPG, "image/jpeg"),
    )
    assert r.status_code == 201
    cuerpo = r.json()
    assert len(cuerpo["aceptadas"]) == 3
    motivos = {x["nombre"]: x["motivo"] for x in cuerpo["rechazadas"]}
    assert "JPG o PNG" in motivos["malo.txt"] and "límite de 3" in motivos["4.jpg"]
    de_nuevo = subir(client, ciudadano, folio, ("5.jpg", JPG, "image/jpeg"))
    assert de_nuevo.status_code == 422  # ya tiene 3
    assert len(client.get(f"{API}/reportes/{folio}/fotos", headers=ciudadano.h).json()["datos"]) == 3


def test_fotos_al_confirmar_un_reporte_existente(client, ciudadano, ciudadanos):
    folio = nuevo_bache(client, ciudadano)["folio"]
    otra = ciudadanos[0]
    assert subir(client, otra, folio, ("x.jpg", JPG, "image/jpeg")).status_code == 403  # sin confirmar
    assert client.post(f"{API}/reportes/{folio}/confirmaciones", json={"tipo": "confirmacion_dano"}, headers=otra.h).status_code == 201
    assert subir(client, otra, folio, ("x.jpg", JPG, "image/jpeg")).status_code == 201


def test_fotos_en_recibido_solo_autor_y_moderacion_luego_publicas(client, ciudadano, ciudadanos, moderador):
    folio = nuevo_bache(client, ciudadano)["folio"]
    foto = subir(client, ciudadano, folio, ("x.jpg", JPG, "image/jpeg")).json()["aceptadas"][0]
    url = f"{API}/reportes/{folio}/fotos/{foto['id']}"
    assert client.get(url).status_code == 403  # visitante
    assert client.get(f"{API}/reportes/{folio}/fotos").status_code == 403
    assert client.get(url, headers=ciudadanos[1].h).status_code == 403  # otro ciudadano
    assert client.get(url, headers=ciudadano.h).status_code == 200  # autor
    propia = client.get(url, headers=moderador.h)
    assert propia.status_code == 200 and propia.headers["content-type"] == "image/jpeg"
    validar(client, moderador, folio)
    publica = client.get(url)
    assert publica.status_code == 200 and publica.content == JPG
    assert client.get(f"{API}/reportes/{folio}/fotos/{uuid.uuid4()}").status_code == 404


def test_fotos_de_reporte_rechazado_no_se_revelan(client, ciudadano, ciudadanos, moderador):
    folio = nuevo_bache(client, ciudadano)["folio"]
    foto = subir(client, ciudadano, folio, ("x.jpg", JPG, "image/jpeg")).json()["aceptadas"][0]
    r = client.post(
        f"{API}/moderacion/reportes/{folio}/transiciones",
        json={"estado_nuevo": "Rechazado", "motivo": "Foto sin relación con el reporte"},
        headers=moderador.h,
    )
    assert r.status_code == 200, r.text
    assert client.get(f"{API}/reportes/{folio}/fotos/{foto['id']}").status_code == 404
    assert client.get(f"{API}/reportes/{folio}/fotos/{foto['id']}", headers=ciudadanos[0].h).status_code == 404
    assert subir(client, ciudadano, folio, ("y.jpg", JPG, "image/jpeg")).status_code == 409


def test_subir_fotos_requiere_autenticacion(client, ciudadano):
    folio = nuevo_bache(client, ciudadano)["folio"]
    assert subir(client, None, folio, ("x.jpg", JPG, "image/jpeg")).status_code == 401


# ------------------------------------------------------------------------------ HU-04.5 mapa


def test_mapa_publico_sin_datos_personales_y_mismos_filtros(client, ciudadano, moderador):
    lat, lon = punto_unico()
    bache = crear_reporte(client, ciudadano, payload_bache(client, lat, lon))
    lat2, lon2 = punto_unico()
    enc = crear_reporte(client, ciudadano, payload_enc(client, lat2, lon2))
    r = client.get(f"{API}/reportes/mapa", params={"bbox": f"{lon - 0.001},{lat - 0.001},{lon + 0.001},{lat + 0.001}"})
    assert r.status_code == 200
    cuerpo = r.json()
    assert [m["folio"] for m in cuerpo["datos"]] == [bache["folio"]]
    marcador = cuerpo["datos"][0]
    assert marcador["etiqueta_publica"] == "Sin validar"
    for prohibido in ("usuario", "correo", "Persona de Prueba", ciudadano.id, ciudadano.correo):
        assert prohibido not in r.text
    # mismos filtros que la lista
    filtros = {"tipo_dano": "Encharcamiento", "solo_vigentes": "true"}
    lista = client.get(f"{API}/reportes", params={**filtros, "por_pagina": 100}).json()
    mapa = client.get(f"{API}/reportes/mapa", params=filtros).json()
    assert {x["folio"] for x in lista["datos"]} == {x["folio"] for x in mapa["datos"]}
    assert enc["folio"] in {x["folio"] for x in mapa["datos"]}
    assert mapa["total"] == lista["paginacion"]["total"]


def test_mapa_excluye_rechazados_y_valida_filtros(client, ciudadano, moderador):
    lat, lon = punto_unico()
    rep = crear_reporte(client, ciudadano, payload_bache(client, lat, lon))
    client.post(
        f"{API}/moderacion/reportes/{rep['folio']}/transiciones",
        json={"estado_nuevo": "Rechazado", "motivo": "No procede"},
        headers=moderador.h,
    )
    folios = {m["folio"] for m in client.get(f"{API}/reportes/mapa").json()["datos"]}
    assert rep["folio"] not in folios
    assert client.get(f"{API}/reportes/mapa", params={"estado": "Rechazado"}).status_code == 422
    assert client.get(f"{API}/reportes/mapa", params={"bbox": "1,2"}).status_code == 422


# ------------------------------------------------------------------------------ HU-07.3 exportación


def test_exportar_exige_rol_de_moderacion(client, ciudadano, moderador, coordinador):
    for formato in ("csv", "xml"):
        url = f"{API}/reportes/exportar/{formato}"
        assert client.get(url).status_code == 401
        assert client.get(url, headers=ciudadano.h).status_code == 403
        assert client.get(url, headers=moderador.h).status_code == 200
        assert client.get(url, headers=coordinador.h).status_code == 200


def test_csv_con_bom_columnas_filtros_y_sin_pii(client, ciudadano, moderador):
    lat, lon = punto_unico()
    rep = crear_reporte(client, ciudadano, payload_bache(client, lat, lon, calle="Calle Peña Nieto"))
    bbox = f"{lon - 0.001},{lat - 0.001},{lon + 0.001},{lat + 0.001}"
    r = client.get(f"{API}/reportes/exportar/csv", params={"bbox": bbox}, headers=moderador.h)
    assert r.status_code == 200
    assert r.content.startswith(b"\xef\xbb\xbf")  # UTF-8 con BOM
    assert "attachment" in r.headers["content-disposition"]
    filas = list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))
    assert filas[0] == ["folio", "tipo_dano", "ubicacion", "colonia", "estado", "fecha_creacion", "fecha_actualizacion"]
    assert len(filas) == 2 and filas[1][0] == rep["folio"] and filas[1][2] == "Calle Peña Nieto"
    assert filas[1][4] == "Recibido"
    assert ciudadano.correo not in r.text and ciudadano.id not in r.text
    vacio = client.get(f"{API}/reportes/exportar/csv", params={"bbox": "-106.64,31.46,-106.6399,31.4601"}, headers=moderador.h)
    assert len(list(csv.reader(io.StringIO(vacio.content.decode("utf-8-sig"))))) == 1  # sólo encabezado


def test_csv_neutraliza_inyeccion_de_formulas():
    class Falso:
        folio, calle = "BCH-2026-000001", "=HYPERLINK(\"http://x\")"
        created_at = updated_at = __import__("datetime").datetime(2026, 1, 1, tzinfo=__import__("datetime").timezone.utc)

        class tipo_dano:
            value = "Bache"

        class estado:
            value = "Recibido"

        class colonia:
            nombre = "+Centro"

    texto = exportacion.generar_csv([Falso()]).decode("utf-8-sig")
    assert "'=HYPERLINK" in texto and "'+Centro" in texto


def test_xml_valido_contra_xsd_con_acentos_y_vacio(client, ciudadano, moderador):
    lat, lon = punto_unico()
    crear_reporte(client, ciudadano, payload_bache(client, lat, lon, calle="Av. Niños Héroes & <Ñandú>"))
    bbox = f"{lon - 0.001},{lat - 0.001},{lon + 0.001},{lat + 0.001}"
    r = client.get(f"{API}/reportes/exportar/xml", params={"bbox": bbox}, headers=moderador.h)
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/xml")
    raiz = etree.fromstring(r.content)
    assert exportacion.cargar_esquema("reportes_v1.xsd").validate(raiz)
    ns = {"r": exportacion.NS_REPORTES}
    assert raiz.get("total") == "1" and raiz.get("zona_horaria") == "America/Ciudad_Juarez"
    assert raiz.find("r:reporte/r:ubicacion", ns).text == "Av. Niños Héroes & <Ñandú>"
    assert ciudadano.correo.encode() not in r.content
    vacio = client.get(f"{API}/reportes/exportar/xml", params={"bbox": "-106.64,31.46,-106.6399,31.4601"}, headers=moderador.h)
    assert exportacion.cargar_esquema("reportes_v1.xsd").validate(etree.fromstring(vacio.content))
    assert etree.fromstring(vacio.content).get("total") == "0"


def test_xml_invalido_no_pasa_el_xsd():
    esquema = exportacion.cargar_esquema("reportes_v1.xsd")
    malo = etree.fromstring(
        f'<reportes xmlns="{exportacion.NS_REPORTES}" version="1" generado="2026-01-01T00:00:00-07:00" '
        'zona_horaria="America/Ciudad_Juarez" total="1"><reporte><folio>XXX</folio></reporte></reportes>'
    )
    assert not esquema.validate(malo)


def test_exportacion_respeta_filtros_de_consulta(client, ciudadano, moderador):
    lat, lon = punto_unico()
    crear_reporte(client, ciudadano, payload_enc(client, lat, lon))
    r = client.get(f"{API}/reportes/exportar/csv", params={"tipo_dano": "Bache", "bbox": f"{lon - 0.001},{lat - 0.001},{lon + 0.001},{lat + 0.001}"}, headers=moderador.h)
    assert len(list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))) == 1
    assert client.get(f"{API}/reportes/exportar/csv", params={"estado": "Rechazado"}, headers=moderador.h).status_code == 422


# ------------------------------------------------------------------------------ importación XML (extra 4.4)

NS_CAT = "https://callesseguras.juarez.mx/esquemas/catalogos/v1"


def xml_catalogo(sector_clave="SEC-IMP", colonia="Colonia Importada", cp="32100", lat="31.70", lon="-106.40", extra=""):
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><catalogos xmlns="{NS_CAT}" version="1">'
        f'<sectores><sector clave="{sector_clave}" nombre="Sector Importado Ñ {sector_clave}"/></sectores>'
        f'<colonias><colonia sector_clave="{sector_clave}" nombre="{colonia}" codigo_postal="{cp}" '
        f'latitud_centro="{lat}" longitud_centro="{lon}"/>{extra}</colonias></catalogos>'
    ).encode()


def importar(client, cuenta, contenido):
    return client.post(
        f"{API}/admin/catalogos/importar-xml", files={"archivo": ("cat.xml", contenido, "application/xml")}, headers=cuenta.h
    )


def test_importar_xml_solo_coordinador(client, ciudadano, moderador, coordinador):
    assert importar(client, ciudadano, xml_catalogo()).status_code == 403
    assert importar(client, moderador, xml_catalogo()).status_code == 403
    assert client.post(f"{API}/admin/catalogos/importar-xml", files={"archivo": ("a.xml", b"<a/>")}).status_code == 401


def test_importar_xml_crea_y_es_idempotente(client, coordinador):
    sufijo = uuid.uuid4().hex[:6].upper()
    contenido = xml_catalogo(sector_clave=f"IMP-{sufijo}", colonia=f"Colonia {sufijo}")
    r = importar(client, coordinador, contenido)
    assert r.status_code == 200, r.text
    assert r.json()["sectores_creados"] == 1 and r.json()["colonias_creadas"] == 1
    r2 = importar(client, coordinador, contenido)
    assert r2.status_code == 200
    assert r2.json()["sectores_creados"] == 0 and r2.json()["colonias_creadas"] == 0 and r2.json()["colonias_actualizadas"] == 1


def test_importar_xml_rechaza_malformado_y_fuera_de_esquema(client, coordinador):
    malo = importar(client, coordinador, b"<catalogos><sectores>")
    assert malo.status_code == 422 and "mal formado" in malo.json()["error"]["mensaje"]
    fuera = importar(client, coordinador, xml_catalogo(lat="40.0"))  # fuera de Juárez (RN-01)
    assert fuera.status_code == 422 and "esquema" in fuera.json()["error"]["mensaje"]
    assert importar(client, coordinador, b"").status_code == 422


def test_importar_xml_rechaza_integridad_referencial_y_no_importa_nada(client, coordinador):
    sufijo = uuid.uuid4().hex[:6].upper()
    huerfana = f'<colonia sector_clave="NO-EXISTE" nombre="Huérfana {sufijo}" latitud_centro="31.6" longitud_centro="-106.4"/>'
    r = importar(client, coordinador, xml_catalogo(sector_clave=f"OK-{sufijo}", colonia=f"Buena {sufijo}", extra=huerfana))
    assert r.status_code == 422
    assert "NO-EXISTE" in r.json()["error"]["detalles"][0]["mensaje"]
    nombres = [c["nombre"] for c in client.get(f"{API}/catalogos/colonias").json()["datos"]]
    assert f"Buena {sufijo}" not in nombres  # transaccional


def test_importar_xml_bloquea_xxe_y_doctype(client, coordinador):
    xxe = (
        b'<?xml version="1.0"?><!DOCTYPE c [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
        b'<catalogos xmlns="' + NS_CAT.encode() + b'" version="1"><sectores><sector clave="A1" nombre="&x;"/></sectores></catalogos>'
    )
    r = importar(client, coordinador, xxe)
    assert r.status_code == 422 and "root:" not in r.text
