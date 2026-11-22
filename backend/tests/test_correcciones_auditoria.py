"""Pruebas de regresión de los defectos de docs/AUDITORIA_OBLIGATORIA.md §8 y del catálogo de códigos postales."""

import uuid

from pydantic import SecretStr
from sqlalchemy import text

from app.core.config import Settings, get_settings
from app.services import geo
from tests.conftest import CONTRASENA, crear_reporte, payload_bache, payload_enc, punto_unico

API = "/api/v1"


def _limpiar_limitador_geocoding() -> None:
    from app.routers import geocoding as router_geo

    router_geo._limitador._eventos.clear()


# --------------------------------------------------------------------------- D-06 · HU-01.2


def test_registro_exige_aceptar_aviso_de_privacidad(client, db):
    base = {"nombre": "Persona Privacidad", "contrasena": CONTRASENA}
    sin_campo = client.post(f"{API}/auth/registro", json={**base, "correo": "sin-consentimiento@ejemplo.mx"})
    assert sin_campo.status_code == 422
    assert any(d["campo"] == "acepta_aviso_privacidad" for d in sin_campo.json()["error"]["detalles"])
    rechazado = client.post(
        f"{API}/auth/registro",
        json={**base, "correo": "no-acepta@ejemplo.mx", "acepta_aviso_privacidad": False},
    )
    assert rechazado.status_code == 422
    assert "aviso de privacidad" in rechazado.text

    correo = f"acepta-{uuid.uuid4().hex[:12]}@ejemplo.mx"
    ok = client.post(f"{API}/auth/registro", json={**base, "correo": correo, "acepta_aviso_privacidad": True})
    assert ok.status_code == 201, ok.text
    fecha = db.execute(
        text("SELECT aviso_privacidad_aceptado_at FROM usuarios WHERE correo = :c"), {"c": correo}
    ).scalar_one()
    assert fecha is not None  # constancia del consentimiento (LFPDPPP)


# --------------------------------------------------------------------------- catálogo de colonias y CP


def test_catalogo_de_colonias_ampliado_con_codigos_postales(client):
    primera = client.get(f"{API}/catalogos/colonias", params={"por_pagina": 100}).json()
    assert 80 <= primera["paginacion"]["total"] <= 200
    colonias = primera["datos"]
    for pagina in range(2, primera["paginacion"]["total_paginas"] + 1):
        colonias += client.get(f"{API}/catalogos/colonias", params={"por_pagina": 100, "pagina": pagina}).json()["datos"]
    cps = [c["codigo_postal"] for c in colonias if c["codigo_postal"]]
    assert len(cps) >= 80
    assert all(geo.CP_MIN <= cp <= geo.CP_MAX for cp in cps)
    assert {c["sector"]["nombre"] for c in colonias} >= {"Centro", "Norponiente", "Suroriente", "Surponiente"}


def test_buscar_colonias_por_codigo_postal(client):
    exacto = client.get(f"{API}/catalogos/colonias", params={"q": "32310"}).json()["datos"]
    assert exacto and all(c["codigo_postal"] == "32310" for c in exacto)
    assert "Monumental" in {c["nombre"] for c in exacto}
    prefijo = client.get(f"{API}/catalogos/colonias", params={"q": "325", "por_pagina": 100}).json()["datos"]
    assert prefijo and all(c["codigo_postal"].startswith("325") for c in prefijo)
    assert [c["codigo_postal"] for c in prefijo] == sorted(c["codigo_postal"] for c in prefijo)
    # El nombre sigue funcionando igual.
    assert any(c["nombre"] == "Partido Romero" for c in client.get(f"{API}/catalogos/colonias", params={"q": "romero"}).json()["datos"])


def test_geocoding_por_codigo_postal(client, monkeypatch):
    _limpiar_limitador_geocoding()
    monkeypatch.setattr(get_settings(), "geocoding_api_key", SecretStr("llave-que-no-debe-usarse"))
    from app.services import geocoding as servicio

    def no_llamar(*_args, **_kwargs):
        raise AssertionError("Un código postal se resuelve con el catálogo local, sin llamar al proveedor.")

    monkeypatch.setattr(servicio, "_consultar_locationiq", no_llamar)
    r = client.get(f"{API}/geocoding/buscar", params={"q": "32000"})
    cuerpo = r.json()
    assert r.status_code == 200 and cuerpo["fuente"] == "catalogo_local" and cuerpo["degradado"] is False
    assert cuerpo["datos"] and cuerpo["datos"][0]["colonia_sugerida"]["codigo_postal"] == "32000"
    assert cuerpo["datos"][0]["precision"] == "colonia" and "C.P. 32000" in cuerpo["datos"][0]["etiqueta"]
    for d in cuerpo["datos"]:
        assert geo.dentro_de_juarez(d["ubicacion"]["latitud"], d["ubicacion"]["longitud"])

    fuera = client.get(f"{API}/geocoding/buscar", params={"q": "31000"})
    assert fuera.status_code == 422 and "no pertenece a Ciudad Juárez" in fuera.text
    sin_colonias = client.get(f"{API}/geocoding/buscar", params={"q": "32720"}).json()
    assert sin_colonias["datos"] == [] and sin_colonias["mensaje"]
    _limpiar_limitador_geocoding()


def test_geocoding_inversa_dentro_de_juarez(client, monkeypatch):
    _limpiar_limitador_geocoding()
    monkeypatch.setattr(get_settings(), "geocoding_api_key", SecretStr(""))
    r = client.get(f"{API}/geocoding/inversa", params={"latitud": 31.7330, "longitud": -106.4630})
    cuerpo = r.json()
    assert r.status_code == 200 and cuerpo["fuente"] == "catalogo_local"
    assert cuerpo["colonia_sugerida"]["nombre"] == "Partido Romero"
    assert cuerpo["colonia_sugerida"]["codigo_postal"] == "32030"
    distancias = [c["distancia_metros"] for c in cuerpo["colonias_cercanas"]]
    assert distancias == sorted(distancias) and len(distancias) == 3
    assert "mapa" not in (cuerpo["mensaje"] or "")

    fuera = client.get(f"{API}/geocoding/inversa", params={"latitud": 32.5, "longitud": -106.4})
    assert fuera.status_code == 422 and fuera.json()["error"]["codigo"] == "FUERA_DE_JUAREZ"
    fuera_lon = client.get(f"{API}/geocoding/inversa", params={"latitud": 31.7, "longitud": -107.0})
    assert fuera_lon.status_code == 422 and fuera_lon.json()["error"]["codigo"] == "FUERA_DE_JUAREZ"
    _limpiar_limitador_geocoding()


def test_geocoding_inversa_con_proveedor_y_sin_exponer_llave(client, monkeypatch):
    from app.services import geocoding as servicio

    _limpiar_limitador_geocoding()
    centinela = "llave-centinela-inversa"
    monkeypatch.setattr(get_settings(), "geocoding_api_key", SecretStr(centinela))
    monkeypatch.setattr(
        servicio,
        "_consultar_locationiq_inversa",
        lambda lat, lon: {"address": {"road": "Avenida Tecnológico", "neighbourhood": "Partido Romero"}},
    )
    r = client.get(f"{API}/geocoding/inversa", params={"latitud": 31.7330, "longitud": -106.4630})
    cuerpo = r.json()
    assert r.status_code == 200 and cuerpo["fuente"] == "locationiq" and cuerpo["calle"] == "Avenida Tecnológico"
    assert cuerpo["colonia_sugerida"]["nombre"] == "Partido Romero" and centinela not in r.text

    def falla(lat, lon):
        raise servicio._ProveedorNoDisponible

    monkeypatch.setattr(servicio, "_consultar_locationiq_inversa", falla)
    caido = client.get(f"{API}/geocoding/inversa", params={"latitud": 31.7330, "longitud": -106.4630}).json()
    assert caido["fuente"] == "catalogo_local" and caido["degradado"] is True
    _limpiar_limitador_geocoding()


def test_fallback_de_geocoding_no_remite_a_un_mapa(client, monkeypatch):
    _limpiar_limitador_geocoding()
    monkeypatch.setattr(get_settings(), "geocoding_api_key", SecretStr(""))
    cuerpo = client.get(f"{API}/geocoding/buscar", params={"q": "romero"}).json()
    assert cuerpo["degradado"] is True and "mapa" not in cuerpo["mensaje"]  # D-13
    _limpiar_limitador_geocoding()


# --------------------------------------------------------------------------- D-08 · HU-02.5


def test_editar_reporte_recibido_solo_autor(client, ciudadano, ciudadanos, moderador):
    lat, lon = punto_unico()
    folio = crear_reporte(client, ciudadano, payload_bache(client, lat, lon))["folio"]
    url = f"{API}/reportes/{folio}"

    assert client.patch(url, json={"calle": "Calle sin sesión"}).status_code == 401
    ajeno = client.patch(url, json={"calle": "Calle ajena"}, headers=ciudadanos[0].h)
    assert ajeno.status_code == 403

    cambios = {"calle": "Av. Tecnológico y Ejército", "tamano": "chico", "profundidad": "menos de 5 cm", "descripcion": "Corregido"}
    r = client.patch(url, json=cambios, headers=ciudadano.h)
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["calle"] == cambios["calle"] and cuerpo["descripcion"] == "Corregido"
    assert cuerpo["severidad"] == "Baja"  # recalculada por el servidor
    assert cuerpo["detalle"]["tamano"] == "chico" and cuerpo["estado"] == "Recibido"
    assert (cuerpo["ubicacion"]["latitud"], cuerpo["ubicacion"]["longitud"]) == (lat, lon)

    # Inmutables y campos ajenos al tipo: 422.
    assert client.patch(url, json={"latitud": lat + 0.001}, headers=ciudadano.h).status_code == 422
    assert client.patch(url, json={"esta_senalizado": True}, headers=ciudadano.h).status_code == 422
    assert client.patch(url, json={}, headers=ciudadano.h).status_code == 422
    assert client.patch(url, json={"descripcion": "x" * 501}, headers=ciudadano.h).status_code == 422

    # Historial sin cambios de estado por la edición.
    historial = client.get(f"{url}/historial").json()["historial"]
    assert [h["estado_nuevo"] for h in historial] == ["Recibido"]

    validar = client.post(f"{API}/moderacion/reportes/{folio}/transiciones", json={"estado_nuevo": "Validado"}, headers=moderador.h)
    assert validar.status_code == 200, validar.text
    tarde = client.patch(url, json={"calle": "Ya no se puede"}, headers=ciudadano.h)
    assert tarde.status_code == 409 and tarde.json()["error"]["codigo"] == "REPORTE_NO_EDITABLE"


def test_encharcamiento_no_es_editable(client, ciudadano):
    lat, lon = punto_unico()
    folio = crear_reporte(client, ciudadano, payload_enc(client, lat, lon))["folio"]
    r = client.patch(f"{API}/reportes/{folio}", json={"calle": "Otra calle"}, headers=ciudadano.h)
    assert r.status_code == 409


def test_delete_sigue_prohibido_y_anuncia_metodos(client, ciudadano):
    lat, lon = punto_unico()
    folio = crear_reporte(client, ciudadano, payload_bache(client, lat, lon))["folio"]
    r = client.delete(f"{API}/reportes/{folio}", headers=ciudadano.h)
    assert r.status_code == 405 and r.headers["Allow"] == "GET, PATCH"


# --------------------------------------------------------------------------- D-12 / D-24 · HU-08.1


def test_ttl_de_clima_es_de_una_hora():
    assert Settings.model_fields["weather_cache_ttl_minutes"].default == 60


def test_clima_no_reintenta_durante_el_retroceso(client, db, monkeypatch):
    import httpx

    from app.services import clima

    db.execute(text("DELETE FROM cache_clima"))
    db.commit()
    clima.reiniciar_retroceso()
    llamadas = []

    def caido():
        llamadas.append(1)
        raise httpx.ConnectTimeout("timeout")

    monkeypatch.setattr(clima, "_consultar_proveedor", caido)
    assert client.get(f"{API}/clima/pronostico").status_code == 503
    assert client.get(f"{API}/clima/pronostico").status_code == 503
    assert len(llamadas) == 1  # el segundo intento no espera otro timeout
    clima.reiniciar_retroceso()


# --------------------------------------------------------------------------- D-05 · RNF-09


def test_volumen_de_datos_de_demostracion(client):
    publicos = client.get(f"{API}/reportes", params={"por_pagina": 1}).json()["paginacion"]["total"]
    assert publicos >= 500
