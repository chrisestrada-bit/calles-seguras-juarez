"""Fase 3 de requisitos opcionales: HU-05.3 (fusión), HU-05.4 (cuadrillas), HU-05.5 (enlace municipal),
HU-06.3 (catálogos), HU-01.4 (colonias favoritas), HU-04.6 (trayecto) y HU-07.2 (resumen por colonia)."""

import math
import uuid
from datetime import timedelta

import pytest

from app.core.tiempo import hoy_local
from app.services import fusion, trayecto
from tests.conftest import (
    crear_cuenta,
    crear_reporte,
    desplazar,
    motivo_id,
    payload_bache,
    payload_enc,
    punto_unico,
)

API = "/api/v1"
HOY = hoy_local().isoformat()


def transicionar(client, cuenta, folio, **cuerpo):
    return client.post(f"{API}/moderacion/reportes/{folio}/transiciones", json=cuerpo, headers=cuenta.h)


def validar(client, moderador, folio):
    r = transicionar(client, moderador, folio, estado_nuevo="Validado")
    assert r.status_code == 200, r.text


def bache(client, cuenta, **extra):
    lat, lon = punto_unico()
    return crear_reporte(client, cuenta, payload_bache(client, lat, lon, **extra))["folio"]


def confirmaciones_de(client, folio, cuenta=None):
    return client.get(f"{API}/reportes/{folio}", headers=cuenta.h if cuenta else {}).json()["confirmaciones"]


def confirmar(client, cuenta, folio):
    r = client.post(f"{API}/reportes/{folio}/confirmaciones", json={"tipo": "confirmacion_dano"}, headers=cuenta.h)
    assert r.status_code == 201, r.text


def fusionar(client, cuenta, principal, secundario):
    return client.post(
        f"{API}/moderacion/reportes/fusionar",
        json={"folio_principal": principal, "folio_secundario": secundario},
        headers=cuenta.h,
    )


def par_duplicado(client, autor_a, autor_b):
    """Dos baches a 10 m: el segundo se fuerza como nuevo (lo que la fusión corrige después)."""
    lat, lon = punto_unico()
    principal = crear_reporte(client, autor_a, payload_bache(client, lat, lon))["folio"]
    lat2, lon2 = desplazar(lat, lon, 10)
    secundario = crear_reporte(client, autor_b, payload_bache(client, lat2, lon2, forzar_nuevo=True))["folio"]
    return principal, secundario


# ============================================================================ HU-05.3 fusión


def test_fusion_suma_confirmaciones_sin_doble_conteo(client, ciudadanos, moderador):
    a, b, c, d = ciudadanos[:4]
    principal, secundario = par_duplicado(client, a, b)
    confirmar(client, c, principal)
    confirmar(client, c, secundario)  # C confirmó ambos: cuenta una sola vez
    confirmar(client, d, secundario)  # D sólo el secundario: se transfiere
    confirmar(client, a, secundario)  # A es autor del principal: nunca se transfiere (no confirma lo propio)
    antes = confirmaciones_de(client, principal)
    r = fusionar(client, moderador, principal, secundario)
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["confirmaciones_transferidas"] == 2  # D y el autor del secundario (B)
    assert confirmaciones_de(client, principal) == antes + 2 == cuerpo["confirmaciones_principal"]

    det = client.get(f"{API}/moderacion/reportes/{secundario}", headers=moderador.h).json()
    assert det["estado"] == "Rechazado" and det["motivo_rechazo"] == f"Duplicado de {principal}"
    assert det["folio"] == secundario and det["folio_principal"] == principal  # conserva su folio y enlaza
    assert any(h["estado_nuevo"] == "Rechazado" and h["motivo"] == f"Duplicado de {principal}" for h in det["historial"])
    mios = client.get(f"{API}/reportes/mios", headers=b.h).json()["datos"]
    assert next(x for x in mios if x["folio"] == secundario)["folio_principal"] == principal
    aviso = client.get(f"{API}/notificaciones", headers=b.h).json()["datos"][0]
    assert principal in aviso["mensaje"] and aviso["folio"] == secundario
    assert client.get(f"{API}/reportes/{secundario}").status_code == 404  # RN-09: el rechazado no es público


def test_fusion_bloquea_casos_invalidos(client, ciudadanos, ciudadano, moderador):
    a, b = ciudadanos[:2]
    principal, secundario = par_duplicado(client, a, b)
    assert fusionar(client, moderador, principal, principal).status_code == 422
    assert fusionar(client, ciudadano, principal, secundario).status_code == 403
    assert fusionar(client, moderador, principal, "BCH-2099-999999").status_code == 404
    validar(client, moderador, secundario)
    assert fusionar(client, moderador, principal, secundario).json()["error"]["codigo"] == "SECUNDARIO_NO_FUSIONABLE"

    p2, s2 = par_duplicado(client, a, b)
    assert transicionar(client, moderador, p2, estado_nuevo="Rechazado", motivo_id=motivo_id(client)).status_code == 200
    assert fusionar(client, moderador, p2, s2).json()["error"]["codigo"] == "PRINCIPAL_NO_VALIDO"

    lat, lon = punto_unico()
    enc = crear_reporte(client, a, payload_enc(client, lat, lon))["folio"]
    assert fusionar(client, moderador, enc, bache(client, b)).status_code == 422


def test_fusion_hace_rollback_si_algo_falla(client, ciudadanos, moderador, monkeypatch):
    a, b, d = ciudadanos[0], ciudadanos[1], ciudadanos[3]
    principal, secundario = par_duplicado(client, a, b)
    confirmar(client, d, secundario)
    antes = confirmaciones_de(client, principal)

    def falla(*_args, **_kwargs):
        raise RuntimeError("falla simulada después de mover confirmaciones y cambiar el estado")

    monkeypatch.setattr(fusion.notificaciones, "notificar", falla)
    with pytest.raises(RuntimeError):
        fusionar(client, moderador, principal, secundario)
    monkeypatch.undo()
    det = client.get(f"{API}/moderacion/reportes/{secundario}", headers=moderador.h).json()
    assert det["estado"] == "Recibido" and det["folio_principal"] is None
    assert confirmaciones_de(client, principal) == antes  # ninguna confirmación quedó a medias
    assert fusionar(client, moderador, principal, secundario).status_code == 200  # y luego sí se puede


# ============================================================================ HU-05.4 cuadrillas


def nueva_cuadrilla(client, coordinador, **extra):
    datos = {"nombre": f"Cuadrilla prueba {uuid.uuid4().hex[:6]}", "responsable": "Jefatura de prueba", "telefono_contacto": "656 000 0000", **extra}
    r = client.post(f"{API}/cuadrillas", json=datos, headers=coordinador.h)
    assert r.status_code == 201, r.text
    return r.json()


def asignar(client, coordinador, cuadrilla_id, folio, fecha=HOY):
    return client.post(f"{API}/cuadrillas/{cuadrilla_id}/asignaciones", json={"folio": folio, "fecha_programada": fecha}, headers=coordinador.h)


def test_cuadrillas_solo_coordinacion_y_validaciones(client, moderador, coordinador):
    assert client.get(f"{API}/cuadrillas", headers=moderador.h).status_code == 403
    assert client.get(f"{API}/cuadrillas").status_code == 401
    c = nueva_cuadrilla(client, coordinador)
    repetida = client.post(f"{API}/cuadrillas", json={"nombre": c["nombre"].upper(), "responsable": "Otra", "telefono_contacto": "6560000000"}, headers=coordinador.h)
    assert repetida.status_code == 409
    malo = client.post(f"{API}/cuadrillas", json={"nombre": "Otra cuadrilla", "responsable": "Alguien", "telefono_contacto": "abc"}, headers=coordinador.h)
    assert malo.status_code == 422


def test_asignar_validado_pasa_a_programado_con_historial(client, ciudadano, moderador, coordinador):
    c1, c2 = nueva_cuadrilla(client, coordinador), nueva_cuadrilla(client, coordinador)
    folio = bache(client, ciudadano)
    assert asignar(client, coordinador, c1["id"], folio).json()["error"]["codigo"] == "ASIGNACION_INVALIDA"  # aún Recibido
    validar(client, moderador, folio)
    ayer = (hoy_local() - timedelta(days=1)).isoformat()
    assert asignar(client, coordinador, c1["id"], folio, ayer).status_code == 422
    assert asignar(client, moderador, c1["id"], folio).status_code == 403
    r = asignar(client, coordinador, c1["id"], folio)
    assert r.status_code == 201, r.text
    assert r.json()["estado"] == "Programado" and r.json()["cuadrilla"] == c1["nombre"]
    det = client.get(f"{API}/moderacion/reportes/{folio}", headers=moderador.h).json()
    paso = det["historial"][-1]
    assert paso["estado_nuevo"] == "Programado" and paso["actor_rol"] == "coordinador" and c1["nombre"] in paso["motivo"]
    assert det["fecha_programada"] == HOY
    assert "programada" in client.get(f"{API}/notificaciones", headers=ciudadano.h).json()["datos"][0]["mensaje"]
    # Reasignar conserva el historial de ambas cuadrillas.
    assert asignar(client, coordinador, c2["id"], folio).status_code == 201
    hist1 = client.get(f"{API}/cuadrillas/{c1['id']}", headers=coordinador.h).json()["baches"]
    hist2 = client.get(f"{API}/cuadrillas/{c2['id']}", headers=coordinador.h).json()["baches"]
    assert [b["asignacion_activa"] for b in hist1 if b["folio"] == folio] == [False]
    assert [b["asignacion_activa"] for b in hist2 if b["folio"] == folio] == [True]
    assert "autor" not in str(hist2) and ciudadano.correo not in str(hist2)


def test_no_se_elimina_cuadrilla_con_pendientes_pero_si_se_desactiva(client, ciudadano, moderador, coordinador):
    c = nueva_cuadrilla(client, coordinador)
    folio = bache(client, ciudadano)
    validar(client, moderador, folio)
    asignar(client, coordinador, c["id"], folio)
    r = client.delete(f"{API}/cuadrillas/{c['id']}", headers=coordinador.h)
    assert r.status_code == 409 and r.json()["error"]["codigo"] == "CUADRILLA_CON_PENDIENTES"
    off = client.patch(f"{API}/cuadrillas/{c['id']}", json={"activa": False}, headers=coordinador.h)
    assert off.status_code == 200 and off.json()["activa"] is False and off.json()["pendientes"] == 1
    otro = bache(client, ciudadano)
    validar(client, moderador, otro)
    assert asignar(client, coordinador, c["id"], otro).json()["error"]["codigo"] == "CUADRILLA_INACTIVA"
    vacia = nueva_cuadrilla(client, coordinador)
    assert client.delete(f"{API}/cuadrillas/{vacia['id']}", headers=coordinador.h).status_code == 204


# ============================================================================ HU-05.5 enlace municipal


@pytest.fixture
def escenario_enlace(client, ciudadano, moderador, coordinador):
    enlace = crear_cuenta(client, "enlace_municipal")
    mia, ajena = nueva_cuadrilla(client, coordinador), nueva_cuadrilla(client, coordinador)
    assert client.post(f"{API}/cuadrillas/{mia['id']}/enlaces", json={"usuario_id": enlace.id}, headers=coordinador.h).status_code == 204
    propio, otro = bache(client, ciudadano), bache(client, ciudadano)
    for folio, cuadrilla in ((propio, mia), (otro, ajena)):
        validar(client, moderador, folio)
        assert asignar(client, coordinador, cuadrilla["id"], folio).status_code == 201
    return enlace, mia, propio, otro


def avance(client, cuenta, folio, **cuerpo):
    return client.post(f"{API}/enlace/reportes/{folio}/avance", json=cuerpo, headers=cuenta.h)


def test_enlace_solo_ve_y_avanza_baches_de_sus_cuadrillas(client, escenario_enlace, ciudadano):
    enlace, mia, propio, otro = escenario_enlace
    lista = client.get(f"{API}/enlace/reportes", headers=enlace.h).json()
    assert [c["id"] for c in lista["cuadrillas"]] == [mia["id"]]
    folios = {b["folio"] for b in lista["datos"]}
    assert propio in folios and otro not in folios
    assert client.get(f"{API}/enlace/reportes/{otro}", headers=enlace.h).status_code == 403
    assert avance(client, enlace, otro, estado_nuevo="En reparación").status_code == 403
    assert client.get(f"{API}/enlace/reportes/BCH-2099-999999", headers=enlace.h).status_code == 403  # no revela

    assert avance(client, enlace, propio, estado_nuevo="Reparado", fecha_reparacion=HOY).status_code == 400  # se salta un paso
    r = avance(client, enlace, propio, estado_nuevo="En reparación")
    assert r.status_code == 200 and r.json()["estado"] == "En reparación"
    assert avance(client, enlace, propio, estado_nuevo="Reparado").status_code == 422  # falta fecha
    manana = (hoy_local() + timedelta(days=1)).isoformat()
    assert avance(client, enlace, propio, estado_nuevo="Reparado", fecha_reparacion=manana).status_code == 422
    fin = avance(client, enlace, propio, estado_nuevo="Reparado", fecha_reparacion=HOY)
    assert fin.status_code == 200 and fin.json()["fecha_reparacion"] == HOY
    historial = client.get(f"{API}/reportes/{propio}/historial").json()["historial"]
    assert [h["estado_nuevo"] for h in historial][-2:] == ["En reparación", "Reparado"]
    assert "reparado" in client.get(f"{API}/notificaciones", headers=ciudadano.h).json()["datos"][0]["mensaje"]


def test_enlace_no_entra_a_otras_areas_y_otros_no_entran_a_la_suya(client, escenario_enlace, ciudadano, moderador):
    enlace, _, propio, _ = escenario_enlace
    assert client.get(f"{API}/moderacion/reportes", headers=enlace.h).status_code == 403
    assert client.get(f"{API}/cuadrillas", headers=enlace.h).status_code == 403
    lat, lon = punto_unico()
    assert client.post(f"{API}/reportes", json=payload_bache(client, lat, lon), headers=enlace.h).status_code == 403
    assert client.get(f"{API}/enlace/reportes", headers=ciudadano.h).status_code == 403
    assert client.get(f"{API}/enlace/reportes", headers=moderador.h).status_code == 403
    assert transicionar(client, enlace, propio, estado_nuevo="En reparación").status_code == 403


def test_enlace_suspendido_o_desvinculado_recibe_403(client, escenario_enlace, coordinador):
    enlace, mia, propio, _ = escenario_enlace
    assert client.delete(f"{API}/cuadrillas/{mia['id']}/enlaces/{enlace.id}", headers=coordinador.h).status_code == 204
    assert client.get(f"{API}/enlace/reportes/{propio}", headers=enlace.h).status_code == 403
    assert client.patch(f"{API}/admin/usuarios/{enlace.id}/estado", json={"activo": False}, headers=coordinador.h).status_code == 200
    r = client.get(f"{API}/enlace/reportes", headers=enlace.h)
    assert r.status_code == 403 and r.json()["error"]["codigo"] == "CUENTA_SUSPENDIDA"


def test_solo_se_vinculan_cuentas_de_enlace(client, ciudadano, coordinador):
    c = nueva_cuadrilla(client, coordinador)
    r = client.post(f"{API}/cuadrillas/{c['id']}/enlaces", json={"usuario_id": ciudadano.id}, headers=coordinador.h)
    assert r.status_code == 422 and r.json()["error"]["codigo"] == "ROL_INCOMPATIBLE"


# ============================================================================ HU-06.3 catálogos


def test_motivos_inactivos_no_se_pueden_usar_y_el_historico_se_conserva(client, ciudadano, moderador, coordinador):
    nombre = f"Motivo de prueba {uuid.uuid4().hex[:6]}"
    assert client.post(f"{API}/admin/catalogos/motivos-rechazo", json={"nombre": nombre}, headers=moderador.h).status_code == 403
    m = client.post(f"{API}/admin/catalogos/motivos-rechazo", json={"nombre": nombre, "descripcion": "Para pruebas"}, headers=coordinador.h).json()
    assert client.post(f"{API}/admin/catalogos/motivos-rechazo", json={"nombre": nombre.lower()}, headers=coordinador.h).status_code == 409
    folio = bache(client, ciudadano)
    assert transicionar(client, moderador, folio, estado_nuevo="Rechazado", motivo_id=m["id"]).status_code == 200
    client.patch(f"{API}/admin/catalogos/motivos-rechazo/{m['id']}", json={"nombre": nombre + " editado", "activo": False}, headers=coordinador.h)
    publicos = [x["id"] for x in client.get(f"{API}/catalogos/motivos-rechazo").json()["datos"]]
    assert m["id"] not in publicos
    todos = client.get(f"{API}/admin/catalogos/motivos-rechazo", headers=coordinador.h).json()["datos"]
    assert any(x["id"] == m["id"] and x["activo"] is False for x in todos)  # no se borra
    otro = bache(client, ciudadano)
    r = transicionar(client, moderador, otro, estado_nuevo="Rechazado", motivo_id=m["id"])
    assert r.status_code == 422 and r.json()["error"]["codigo"] == "MOTIVO_NO_AUTORIZADO"
    assert transicionar(client, moderador, otro, estado_nuevo="Rechazado", motivo_id=999999).status_code == 422
    # El rechazo anterior conserva el texto con el que se hizo.
    det = client.get(f"{API}/moderacion/reportes/{folio}", headers=moderador.h).json()
    assert det["motivo_rechazo"] == nombre


def test_tipo_de_dano_inactivo_no_admite_reportes_nuevos(client, ciudadano, coordinador):
    tipos = client.get(f"{API}/admin/catalogos/tipos-dano", headers=coordinador.h).json()["datos"]
    alcantarilla = next(t for t in tipos if t["clave"] == "Alcantarilla sin tapa")
    assert client.post(f"{API}/admin/catalogos/tipos-dano", json={"clave": "Bache", "nombre": "Bache"}, headers=coordinador.h).status_code == 409
    lat, lon = punto_unico()
    cuerpo = {"tipo_dano": "Alcantarilla sin tapa", "latitud": lat, "longitud": lon, "colonia_id": payload_bache(client, lat, lon)["colonia_id"], "calle": "Calle de prueba", "esta_senalizado": False}
    try:
        off = client.patch(f"{API}/admin/catalogos/tipos-dano/{alcantarilla['id']}", json={"activo": False, "nombre": "Alcantarilla sin tapa"}, headers=coordinador.h)
        assert off.status_code == 200
        visibles = [t["tipo_dano"] for t in client.get(f"{API}/catalogos/tipos-dano").json()["datos"]]
        assert "Alcantarilla sin tapa" not in visibles and "Bache" in visibles
        r = client.post(f"{API}/reportes", json=cuerpo, headers=ciudadano.h)
        assert r.status_code == 422 and "no está disponible" in r.json()["error"]["detalles"][0]["mensaje"]
    finally:
        client.patch(f"{API}/admin/catalogos/tipos-dano/{alcantarilla['id']}", json={"activo": True}, headers=coordinador.h)
    assert client.post(f"{API}/reportes", json=cuerpo, headers=ciudadano.h).status_code == 201


# ============================================================================ HU-01.4 colonias favoritas


def nueva_colonia(client, coordinador) -> int:
    sector = client.get(f"{API}/catalogos/sectores").json()["datos"][0]["id"]
    datos = {"sector_id": sector, "nombre": f"Colonia prueba {uuid.uuid4().hex[:6]}", "latitud_centro": 31.7, "longitud_centro": -106.45}
    r = client.post(f"{API}/admin/colonias", json=datos, headers=coordinador.h)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_colonias_favoritas_crud_y_desactivacion(client, ciudadano, coordinador):
    url = f"{API}/perfil/colonias-favoritas"
    assert client.get(url).status_code == 401
    assert client.get(url, headers=ciudadano.h).json()["datos"] == []
    cid = nueva_colonia(client, coordinador)
    assert client.post(url, json={"colonia_id": cid}, headers=ciudadano.h).status_code == 201
    assert client.post(url, json={"colonia_id": cid}, headers=ciudadano.h).status_code == 200  # sin duplicar
    assert len(client.get(url, headers=ciudadano.h).json()["datos"]) == 1
    client.patch(f"{API}/admin/colonias/{cid}", json={"activo": False}, headers=coordinador.h)
    guardada = client.get(url, headers=ciudadano.h).json()["datos"]
    assert guardada[0]["colonia"]["id"] == cid and guardada[0]["activa"] is False  # se conserva
    otra = nueva_colonia(client, coordinador)
    client.patch(f"{API}/admin/colonias/{otra}", json={"activo": False}, headers=coordinador.h)
    assert client.post(url, json={"colonia_id": otra}, headers=ciudadano.h).status_code == 422  # inactiva
    assert client.delete(f"{url}/{cid}", headers=ciudadano.h).status_code == 204
    assert client.delete(f"{url}/{cid}", headers=ciudadano.h).status_code == 404


def test_consulta_prioriza_tus_colonias_sin_ocultar_el_resto(client, ciudadano, ciudadanos, coordinador):
    cid = nueva_colonia(client, coordinador)
    lat, lon = punto_unico()
    folio = crear_reporte(client, ciudadanos[0], payload_bache(client, lat, lon, colonia_id=cid))["folio"]
    for _ in range(2):  # reportes más recientes en otras colonias
        bache(client, ciudadanos[1])
    client.post(f"{API}/perfil/colonias-favoritas", json={"colonia_id": cid}, headers=ciudadano.h)
    con = client.get(f"{API}/reportes", params={"por_pagina": 5}, headers=ciudadano.h).json()
    assert con["datos"][0]["folio"] == folio and con["datos"][0]["en_tus_colonias"] is True
    assert all(x["en_tus_colonias"] is False for x in con["datos"][1:])  # el resto sigue visible
    sin = client.get(f"{API}/reportes", params={"por_pagina": 5}).json()
    assert sin["datos"][0]["folio"] != folio and sin["datos"][0]["en_tus_colonias"] is None
    assert con["paginacion"]["total"] == sin["paginacion"]["total"]  # no se oculta nada
    filtrada = client.get(f"{API}/reportes", params={"colonia_id": cid}, headers=ciudadano.h).json()
    assert filtrada["datos"][0]["en_tus_colonias"] is None  # filtro excluyente: sin priorización


# ============================================================================ HU-04.6 trayecto


def este(lat, lon, metros):
    return lat, round(lon + metros / (trayecto._M_POR_GRADO * math.cos(math.radians(lat))), 6)


def ruta_params(o, d):
    return {"origen_latitud": o[0], "origen_longitud": o[1], "destino_latitud": d[0], "destino_longitud": d[1]}


@pytest.fixture
def sin_proveedor(monkeypatch):
    def falla(*_a, **_k):
        raise trayecto.httpx.ConnectError("sin red")

    monkeypatch.setattr(trayecto.httpx, "get", falla)


def test_trayecto_limite_de_100_m_e_intransitables_primero(client, ciudadanos, sin_proveedor):
    lat, lon = punto_unico()
    origen, destino = (lat, lon), (round(lat + 0.0025, 6), lon)  # ≈ 278 m al norte, dentro de la celda libre
    medio_lat = round(lat + 0.00125, 6)
    dentro = crear_reporte(client, ciudadanos[0], payload_enc(client, *este(medio_lat, lon, 95)))["folio"]
    fuera = crear_reporte(client, ciudadanos[1], payload_enc(client, *este(medio_lat, lon, 106), forzar_nuevo=True))["folio"]
    critico = crear_reporte(
        client, ciudadanos[2],
        payload_enc(client, *este(round(lat + 0.0005, 6), lon, -60), nivel_agua="intransitable", hay_riesgo_personas_vehiculos=True),
    )["folio"]
    r = client.get(f"{API}/trayecto/revisar", params=ruta_params(origen, destino))
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["ruta"]["fuente"] == "linea_recta" and cuerpo["ruta"]["degradado"] is True
    folios = [x["folio"] for x in cuerpo["datos"]]
    assert folios == [critico, dentro] and fuera not in folios  # intransitable primero, luego por distancia
    assert 94 <= cuerpo["datos"][1]["distancia_metros"] <= 96
    assert cuerpo["datos"][0]["es_intransitable"] is True
    for clave in ("usuario", "autor", "correo"):
        assert clave not in r.text


def test_trayecto_usa_la_ruta_del_proveedor_si_responde(client, ciudadanos, monkeypatch):
    lat, lon = punto_unico()
    origen, destino = (lat, lon), (round(lat + 0.0025, 6), lon)
    codo = este(lat, lon, 200)  # la ruta real se desvía 200 m al este

    class Respuesta:
        def raise_for_status(self):
            return None

        def json(self):
            coords = [[lon, lat], [codo[1], codo[0]], [codo[1], destino[0]], [lon, destino[0]]]
            return {"code": "Ok", "routes": [{"distance": 678.0, "duration": 95.0, "geometry": {"coordinates": coords}}]}

    monkeypatch.setattr(trayecto.httpx, "get", lambda *a, **k: Respuesta())
    junto_al_codo = crear_reporte(client, ciudadanos[0], payload_enc(client, *este(round(lat + 0.0012, 6), lon, 180)))["folio"]
    r = client.get(f"{API}/trayecto/revisar", params=ruta_params(origen, destino)).json()
    assert r["ruta"]["fuente"] == "osrm" and r["ruta"]["degradado"] is False and len(r["ruta"]["puntos"]) == 4
    assert [x["folio"] for x in r["datos"]] == [junto_al_codo]  # en línea recta quedaría a 180 m


def test_trayecto_vacio_y_fuera_de_juarez(client, sin_proveedor):
    lat, lon = punto_unico()
    r = client.get(f"{API}/trayecto/revisar", params=ruta_params((lat, lon), (round(lat + 0.0025, 6), lon))).json()
    assert r["total"] == 0 and r["datos"] == []
    assert r["mensaje"] == "No hay encharcamientos reportados cerca del trayecto"
    fuera = client.get(f"{API}/trayecto/revisar", params=ruta_params((lat, lon), (40.0, -100.0)))
    assert fuera.status_code == 422 and fuera.json()["error"]["codigo"] == "FUERA_DE_JUAREZ"


def test_distancia_punto_polilinea():
    puntos = [(31.7, -106.45), (31.701, -106.45)]
    lat, lon = este(31.7005, -106.45, 100)
    assert abs(trayecto.distancia_a_polilinea(lat, lon, puntos) - 100) < 0.5
    # Más allá del extremo: distancia al vértice, no a la recta infinita.
    assert trayecto.distancia_a_polilinea(31.7020, -106.45, puntos) > 100


# ============================================================================ HU-07.2 resumen por colonia


def test_resumen_de_colonia_sin_reportes_y_con_reparados(client, ciudadano, moderador, coordinador):
    cid = nueva_colonia(client, coordinador)
    url = f"{API}/publico/colonias/{cid}/resumen"
    vacio = client.get(url).json()
    assert vacio["abiertos"] == 0 and vacio["reparados"] == 0 and vacio["tiempo_promedio_reparacion_dias"] is None
    assert client.get(f"{API}/publico/colonias/999999/resumen").status_code == 404

    folios = []
    for _ in range(3):
        lat, lon = punto_unico()
        folios.append(crear_reporte(client, ciudadano, payload_bache(client, lat, lon, colonia_id=cid))["folio"])
    reparado, abierto, rechazado = folios
    validar(client, moderador, reparado)
    transicionar(client, moderador, reparado, estado_nuevo="En reparación")
    assert transicionar(client, moderador, reparado, estado_nuevo="Reparado", fecha_reparacion=HOY).status_code == 200
    transicionar(client, moderador, rechazado, estado_nuevo="Rechazado", motivo_id=motivo_id(client))
    r = client.get(url)
    datos = r.json()
    assert datos["abiertos"] == 1 and datos["abiertos_por_estado"]["Recibido"] == 1  # el rechazado no cuenta
    assert datos["reparados"] == 1 and datos["tiempo_promedio_reparacion_dias"] == 0.0
    assert "Recibido" in datos["criterios"]["abiertos"]
    assert ciudadano.correo not in r.text and ciudadano.id not in r.text and abierto not in r.text
