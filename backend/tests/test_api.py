"""Pruebas de integración de la API contra PostgreSQL (ver conftest.py)."""

import json
import re
from datetime import timedelta

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import text

from app.core.config import get_settings
from app.core.tiempo import hoy_local
from tests.conftest import (
    motivo_id,
    CONTRASENA,
    crear_cuenta,
    crear_reporte,
    desplazar,
    payload_bache,
    payload_enc,
    punto_unico,
)

API = "/api/v1"
FOLIO_BCH = re.compile(r"^BCH-\d{4}-\d{6}$")
FOLIO_ENC = re.compile(r"^ENC-\d{4}-\d{6}$")
CLAVES_PRIVADAS = {"usuario_id", "autor_id", "actor_id", "correo", "password_hash", "token_version", "motivo_rechazo"}


def claves(obj) -> set[str]:
    if isinstance(obj, dict):
        return set(obj) | {k for v in obj.values() for k in claves(v)}
    if isinstance(obj, list):
        return {k for v in obj for k in claves(v)}
    return set()


# --------------------------------------------------------------------------- auth y roles


def test_salud(client):
    assert client.get("/salud").json() == {"estado": "ok"}


def test_registro_login_y_yo(client):
    correo = "nueva-persona@ejemplo.mx"
    datos = {"nombre": "Nueva Persona", "correo": correo, "contrasena": CONTRASENA, "acepta_aviso_privacidad": True}
    r = client.post(f"{API}/auth/registro", json=datos)
    if r.status_code == 409:  # la prueba ya corrió antes sobre esta base
        assert r.json()["error"]["codigo"] == "CORREO_REGISTRADO"
    else:
        assert r.status_code == 201 and r.json()["rol"] == "ciudadano"
        assert client.post(f"{API}/auth/registro", json=datos).status_code == 409
    assert client.post(f"{API}/auth/registro", json={**datos, "correo": "otra@ejemplo.mx", "contrasena": "soloLetras"}).status_code == 422
    assert client.post(f"{API}/auth/registro", json={**datos, "correo": "otra@ejemplo.mx", "rol": "coordinador"}).status_code == 422
    assert client.post(f"{API}/auth/login", json={"correo": correo, "contrasena": "Incorrecta1"}).status_code == 401
    ok = client.post(f"{API}/auth/login", json={"correo": correo, "contrasena": CONTRASENA})
    assert ok.status_code == 200 and ok.json()["expira_en_segundos"] == 1800
    yo = client.get(f"{API}/auth/yo", headers={"Authorization": f"Bearer {ok.json()['access_token']}"}).json()
    assert yo["correo"] == correo and yo["limite_reportes_hora"] == 10


def test_sin_token_401_y_rol_incorrecto_403(client, ciudadano, moderador):
    assert client.post(f"{API}/reportes", json={}).status_code == 401
    assert client.get(f"{API}/reportes/mios").status_code == 401
    assert client.get(f"{API}/moderacion/reportes").status_code == 401
    assert client.get(f"{API}/auth/yo", headers={"Authorization": "Bearer basura"}).status_code == 401
    assert client.get(f"{API}/moderacion/reportes", headers=ciudadano.h).status_code == 403
    assert client.get(f"{API}/indicadores/moderacion", headers=ciudadano.h).status_code == 403
    assert client.get(f"{API}/admin/usuarios", headers=ciudadano.h).status_code == 403
    assert client.get(f"{API}/admin/usuarios", headers=moderador.h).status_code == 403
    assert client.get(f"{API}/moderacion/reportes", headers=moderador.h).status_code == 200


def test_cerrar_sesion_revoca_token(client):
    cuenta = crear_cuenta(client)
    assert client.post(f"{API}/auth/cerrar-sesion", headers=cuenta.h).status_code == 204
    assert client.get(f"{API}/auth/yo", headers=cuenta.h).status_code == 401


def test_bloqueo_por_intentos_fallidos(client):
    cuenta = crear_cuenta(client)
    for _ in range(5):
        assert client.post(f"{API}/auth/login", json={"correo": cuenta.correo, "contrasena": "Incorrecta1"}).status_code == 401
    bloqueado = client.post(f"{API}/auth/login", json={"correo": cuenta.correo, "contrasena": CONTRASENA})
    assert bloqueado.status_code == 429 and "Retry-After" in bloqueado.headers


# --------------------------------------------------------------------------- catálogos


def test_catalogos(client):
    assert len(client.get(f"{API}/catalogos/sectores").json()["datos"]) >= 6
    tipos = client.get(f"{API}/catalogos/tipos-dano").json()
    assert tipos["limites_territorio"]["latitud_min"] == 31.45 and tipos["descripcion_max_caracteres"] == 500
    assert {t["prefijo_folio"] for t in tipos["datos"]} == {"BCH", "ENC"}
    estados = client.get(f"{API}/catalogos/estados").json()
    assert estados["pavimento"]["finales"] == ["Reparado", "Rechazado"]


def test_colonias_filtro_por_nombre_y_sector(client):
    por_nombre = client.get(f"{API}/catalogos/colonias", params={"q": "romero"}).json()
    assert any(c["nombre"] == "Partido Romero" for c in por_nombre["datos"])
    sector = por_nombre["datos"][0]["sector"]["id"]
    combinado = client.get(f"{API}/catalogos/colonias", params={"q": "romero", "sector_id": sector}).json()
    assert combinado["datos"] and all(c["sector"]["id"] == sector for c in combinado["datos"])
    typo = client.get(f"{API}/catalogos/colonias", params={"q": "partdo romro"}).json()
    assert typo["datos"][0]["nombre"] == "Partido Romero"
    solo_sector = client.get(f"{API}/catalogos/colonias", params={"sector_id": sector, "por_pagina": 100}).json()
    assert all(c["sector"]["id"] == sector for c in solo_sector["datos"])
    assert client.get(f"{API}/catalogos/colonias", params={"sector_id": 9999}).status_code == 422
    assert client.get(f"{API}/catalogos/colonias", params={"q": "a"}).status_code == 422


# --------------------------------------------------------------------------- creación y validaciones


def test_crear_bache(client, ciudadano):
    lat, lon = punto_unico()
    r = client.post(f"{API}/reportes", json=payload_bache(client, lat, lon), headers=ciudadano.h)
    assert r.status_code == 201
    cuerpo = r.json()
    assert FOLIO_BCH.match(cuerpo["folio"]) and cuerpo["estado"] == "Recibido"
    assert cuerpo["etiqueta_publica"] == "Sin validar" and cuerpo["severidad"] == "Alta"
    assert cuerpo["es_mio"] is True and cuerpo["longevidad_dias"] == 0
    assert r.headers["Location"].endswith(cuerpo["folio"])
    assert re.search(r"[-+]0[67]:00$", cuerpo["created_at"])  # RN-02: hora de Ciudad Juárez


def test_alcantarilla_alta_y_cliente_no_fija_severidad(client, ciudadano):
    lat, lon = punto_unico()
    base = {
        "tipo_dano": "Alcantarilla sin tapa", "latitud": lat, "longitud": lon, "colonia_id": 1,
        "calle": "Calle Mariscal", "esta_senalizado": False,
    }
    r = client.post(f"{API}/reportes", json=base, headers=ciudadano.h)
    assert r.status_code == 201 and r.json()["severidad"] == "Alta"
    assert r.json()["detalle"] == {"esta_senalizado": False}
    assert client.post(f"{API}/reportes", json={**base, "severidad": "Baja"}, headers=ciudadano.h).status_code == 422


@pytest.mark.parametrize("cambio", [{"latitud": 32.1}, {"latitud": 31.44}, {"longitud": -106.2}, {"longitud": -107}])
def test_fuera_de_juarez_422(client, ciudadano, cambio):
    lat, lon = punto_unico()
    r = client.post(f"{API}/reportes", json=payload_bache(client, lat, lon, **cambio), headers=ciudadano.h)
    assert r.status_code == 422 and r.json()["error"]["codigo"] == "FUERA_DE_JUAREZ"
    assert "Ciudad Juárez" in r.json()["error"]["mensaje"]


def test_validaciones_formulario_dinamico(client, ciudadano):
    lat, lon = punto_unico()
    sin_tamano = payload_bache(client, lat, lon)
    sin_tamano.pop("tamano")
    assert client.post(f"{API}/reportes", json=sin_tamano, headers=ciudadano.h).status_code == 422
    r = client.post(f"{API}/reportes", json=payload_enc(client, lat, lon, nivel_agua="intransitable"), headers=ciudadano.h)
    assert r.status_code == 422 and r.json()["error"]["detalles"][0]["campo"] == "hay_riesgo_personas_vehiculos"
    largo = payload_bache(client, lat, lon, descripcion="x" * 501)
    assert client.post(f"{API}/reportes", json=largo, headers=ciudadano.h).status_code == 422
    assert client.post(f"{API}/reportes", json={"tipo_dano": "Otro"}, headers=ciudadano.h).status_code == 422


# --------------------------------------------------------------------------- duplicados


def test_duplicado_bache_30_metros(client, ciudadanos):
    a, b = ciudadanos[:2]
    lat, lon = punto_unico()
    original = crear_reporte(client, a, payload_bache(client, lat, lon))
    cerca = desplazar(lat, lon, 25)
    dup = client.post(f"{API}/reportes", json=payload_bache(client, *cerca), headers=b.h)
    assert dup.status_code == 409 and dup.json()["error"]["codigo"] == "POSIBLE_DUPLICADO"
    assert dup.json()["error"]["detalles"][0]["folio"] == original["folio"]
    cand = client.get(f"{API}/reportes/cercanos", params={"latitud": cerca[0], "longitud": cerca[1], "tipo_dano": "Bache"}, headers=b.h).json()
    assert cand["radio_metros"] == 30 and cand["candidatos"][0]["folio"] == original["folio"]
    lejos = desplazar(lat, lon, 45)  # fuera de los 30 m: no es duplicado
    assert client.post(f"{API}/reportes", json=payload_bache(client, *lejos), headers=b.h).status_code == 201
    forzado = client.post(f"{API}/reportes", json=payload_bache(client, *cerca, forzar_nuevo=True), headers=b.h)
    assert forzado.status_code == 201


def test_duplicado_encharcamiento_50_metros(client, ciudadanos):
    a, b = ciudadanos[:2]
    lat, lon = punto_unico()
    crear_reporte(client, a, payload_enc(client, lat, lon))
    assert client.post(f"{API}/reportes", json=payload_enc(client, *desplazar(lat, lon, 45)), headers=b.h).status_code == 409
    assert client.post(f"{API}/reportes", json=payload_enc(client, *desplazar(lat, lon, 70)), headers=b.h).status_code == 201


# --------------------------------------------------------------------------- confirmaciones y vigencia


def test_confirmar_bache(client, ciudadanos):
    autor, otro = ciudadanos[:2]
    lat, lon = punto_unico()
    folio = crear_reporte(client, autor, payload_bache(client, lat, lon))["folio"]
    url = f"{API}/reportes/{folio}/confirmaciones"
    assert client.post(url, json={"tipo": "confirmacion_dano"}, headers=autor.h).json()["error"]["codigo"] == "AUTOCONFIRMACION_NO_PERMITIDA"
    assert client.post(url, json={"tipo": "sigue_ahi"}, headers=otro.h).json()["error"]["codigo"] == "CONFIRMACION_NO_APLICA"
    assert client.post(url, json={"tipo": "confirmacion_dano"}).status_code == 401
    ok = client.post(url, json={"tipo": "confirmacion_dano"}, headers=otro.h)
    assert ok.status_code == 201
    assert client.post(url, json={"tipo": "confirmacion_dano"}, headers=otro.h).status_code == 409
    assert client.get(f"{API}/reportes/{folio}").json()["confirmaciones"] == 1


def test_encharcamiento_tres_desmentidos_lo_pasan_a_historico(client, ciudadanos):
    autor, c1, c2, c3, c4 = ciudadanos
    lat, lon = punto_unico()
    creado = crear_reporte(client, autor, payload_enc(client, lat, lon))
    folio = creado["folio"]
    assert FOLIO_ENC.match(folio) and creado["estado"] == "Activo"  # nace Activo, sin validación
    url = f"{API}/reportes/{folio}/confirmaciones"
    no = {"tipo": "ya_no_hay_agua"}
    assert client.post(url, json=no, headers=autor.h).json()["error"]["codigo"] == "AUTOCONFIRMACION_NO_PERMITIDA"
    assert client.post(url, json=no, headers=c1.h).json()["vigencia"]["ya_no_hay_agua"] == 1
    assert client.post(url, json=no, headers=c1.h).status_code == 409  # un voto por usuario y vigencia
    assert client.post(url, json=no, headers=c2.h).json()["estado_reporte"] == "Activo"
    cierre = client.post(url, json=no, headers=c3.h)
    assert cierre.status_code == 201 and cierre.json()["estado_reporte"] == "Histórico"
    assert client.get(f"{API}/reportes/{folio}").json()["estado"] == "Histórico"
    assert client.post(url, json={"tipo": "sigue_ahi"}, headers=c4.h).json()["error"]["codigo"] == "REPORTE_NO_CONFIRMABLE"
    historial = client.get(f"{API}/reportes/{folio}/historial").json()["historial"]
    assert [h["estado_nuevo"] for h in historial] == ["Activo", "Histórico"]
    assert historial[-1]["origen"] == "sistema"


def test_sigue_ahi_reinicia_6_horas_y_votos(client, ciudadanos):
    autor, c1, c2, c3, _ = ciudadanos
    lat, lon = punto_unico()
    folio = crear_reporte(client, autor, payload_enc(client, lat, lon))["folio"]
    url = f"{API}/reportes/{folio}/confirmaciones"
    antes = client.get(f"{API}/reportes/{folio}").json()["vigencia"]["vigente_hasta"]
    client.post(url, json={"tipo": "ya_no_hay_agua"}, headers=c1.h)
    client.post(url, json={"tipo": "ya_no_hay_agua"}, headers=c2.h)
    r = client.post(url, json={"tipo": "sigue_ahi"}, headers=c3.h).json()
    assert r["vigencia"]["sigue_ahi"] == 1 and r["vigencia"]["ya_no_hay_agua"] == 0  # los votos previos ya no cuentan
    assert r["vigencia"]["vigente_hasta"] > antes
    # c1 ya votó en la vigencia anterior; en la nueva puede volver a votar y no se acumulan con los anteriores
    assert client.post(url, json={"tipo": "ya_no_hay_agua"}, headers=c1.h).json()["estado_reporte"] == "Activo"
    assert client.post(url, json={"tipo": "sigue_ahi"}, headers=c3.h).status_code == 409


def test_vencimiento_a_las_6_horas_se_evalua_en_consulta(client, ciudadano, db):
    lat, lon = punto_unico()
    folio = crear_reporte(client, ciudadano, payload_enc(client, lat, lon))["folio"]
    db.execute(
        text("UPDATE reportes SET vigencia_inicio = now() - interval '7 hours', vigente_hasta = now() - interval '1 hour' WHERE folio = :f"),
        {"f": folio},
    )
    db.commit()
    detalle = client.get(f"{API}/reportes/{folio}").json()
    assert detalle["estado"] == "Histórico"
    historial = client.get(f"{API}/reportes/{folio}/historial").json()["historial"]
    cierre = [h for h in historial if h["estado_nuevo"] == "Histórico"]
    assert len(cierre) == 1 and cierre[0]["origen"] == "sistema"
    # El historial registra el instante real del vencimiento (vigente_hasta), no la hora de la consulta.
    fila = db.execute(text("SELECT h.created_at = r.vigente_hasta FROM historial_estados h JOIN reportes r ON r.id = h.reporte_id WHERE r.folio = :f AND h.estado_nuevo = 'Histórico'"), {"f": folio}).scalar_one()
    assert fila is True
    vigentes = client.get(f"{API}/reportes", params={"solo_vigentes": "true", "por_pagina": 100}).json()["datos"]
    assert folio not in {r["folio"] for r in vigentes}


# --------------------------------------------------------------------------- moderación, RN-05, RN-07


def transicionar(client, cuenta, folio, **cuerpo):
    return client.post(f"{API}/moderacion/reportes/{folio}/transiciones", json=cuerpo, headers=cuenta.h)


def test_maquina_de_estados_completa(client, ciudadano, moderador, coordinador):
    lat, lon = punto_unico()
    folio = crear_reporte(client, ciudadano, payload_bache(client, lat, lon))["folio"]
    assert transicionar(client, moderador, folio, estado_nuevo="Programado").status_code == 400
    assert transicionar(client, moderador, folio, estado_nuevo="Reparado", fecha_reparacion=str(hoy_local())).status_code == 400
    assert transicionar(client, coordinador, folio, estado_nuevo="Validado").status_code == 403
    assert transicionar(client, ciudadano, folio, estado_nuevo="Validado").status_code == 403
    assert transicionar(client, moderador, folio, estado_nuevo="Validado").status_code == 200
    assert transicionar(client, coordinador, folio, estado_nuevo="En reparación").status_code == 200
    assert transicionar(client, moderador, folio, estado_nuevo="Reparado").json()["error"]["detalles"][0]["campo"] == "fecha_reparacion"
    futura = transicionar(client, moderador, folio, estado_nuevo="Reparado", fecha_reparacion=str(hoy_local() + timedelta(days=2)))
    assert futura.status_code == 422 and futura.json()["error"]["codigo"] == "FECHA_REPARACION_INVALIDA"
    pasada = transicionar(client, moderador, folio, estado_nuevo="Reparado", fecha_reparacion=str(hoy_local() - timedelta(days=3)))
    assert pasada.status_code == 422  # anterior a la fecha del reporte
    hecho = transicionar(client, coordinador, folio, estado_nuevo="Reparado", fecha_reparacion=str(hoy_local()))
    assert hecho.status_code == 200 and hecho.json()["longevidad_dias"] == 0
    assert transicionar(client, moderador, folio, estado_nuevo="En reparación").status_code == 400  # estado final
    historial = client.get(f"{API}/reportes/{folio}/historial").json()["historial"]
    assert [h["estado_nuevo"] for h in historial] == ["Recibido", "Validado", "En reparación", "Reparado"]
    detalle = client.get(f"{API}/moderacion/reportes/{folio}", headers=moderador.h).json()
    assert detalle["historial"][1]["actor_rol"] == "moderador" and "correo" not in claves(detalle)


def test_rechazo_exige_motivo_y_oculta_el_reporte(client, ciudadano, moderador):
    lat, lon = punto_unico()
    folio = crear_reporte(client, ciudadano, payload_bache(client, lat, lon))["folio"]
    assert transicionar(client, moderador, folio, estado_nuevo="Rechazado").status_code == 422
    assert transicionar(client, moderador, folio, estado_nuevo="Rechazado", motivo="El punto está en un predio privado.").status_code == 422  # sin motivo del catálogo (HU-06.3)
    ok = transicionar(client, moderador, folio, estado_nuevo="Rechazado", motivo_id=motivo_id(client), motivo="El punto está en un predio privado.")
    assert ok.status_code == 200
    assert client.get(f"{API}/reportes/{folio}").status_code == 404  # RN-09
    assert client.get(f"{API}/reportes/{folio}/historial").status_code == 404
    todos = client.get(f"{API}/reportes", params={"por_pagina": 100}).json()["datos"]
    assert folio not in {r["folio"] for r in todos}
    mios = client.get(f"{API}/reportes/mios", headers=ciudadano.h).json()["datos"]
    assert mios[0]["folio"] == folio and mios[0]["motivo_rechazo"] == "Información insuficiente: El punto está en un predio privado."
    assert client.get(f"{API}/reportes", params={"estado": "Rechazado"}).status_code == 422
    cola = client.get(f"{API}/moderacion/reportes", params={"estado": "Rechazado", "autor_id": ciudadano.id}, headers=moderador.h).json()
    assert cola["datos"][0]["transiciones_disponibles"] == []


def test_delete_prohibido_y_base_de_datos_inmutable(client, ciudadano, db):
    lat, lon = punto_unico()
    folio = crear_reporte(client, ciudadano, payload_bache(client, lat, lon))["folio"]
    for cuenta in (None, ciudadano):
        r = client.delete(f"{API}/reportes/{folio}", headers=cuenta.h if cuenta else {})
        assert r.status_code == 405
    for sentencia in (
        "DELETE FROM reportes WHERE folio = :f",
        "UPDATE reportes SET created_at = created_at - interval '1 day' WHERE folio = :f",
        "UPDATE reportes SET folio = 'BCH-2026-999999' WHERE folio = :f",
        "UPDATE reportes SET estado = 'Reparado', fecha_reparacion = current_date WHERE folio = :f",
        "UPDATE historial_estados SET motivo = 'x' WHERE reporte_id = (SELECT id FROM reportes WHERE folio = :f)",
        "DELETE FROM historial_estados WHERE reporte_id = (SELECT id FROM reportes WHERE folio = :f)",
    ):
        with pytest.raises(Exception):
            db.execute(text(sentencia), {"f": folio})
        db.rollback()
    with pytest.raises(Exception):  # cambio de estado sin contexto de historial
        db.execute(text("UPDATE reportes SET estado = 'Validado' WHERE folio = :f"), {"f": folio})
    db.rollback()


# --------------------------------------------------------------------------- RN-08


def test_limite_de_10_reportes_por_hora(client):
    cuenta = crear_cuenta(client)
    for _ in range(10):
        lat, lon = punto_unico()
        assert client.post(f"{API}/reportes", json=payload_bache(client, lat, lon), headers=cuenta.h).status_code == 201
    lat, lon = punto_unico()
    r = client.post(f"{API}/reportes", json=payload_bache(client, lat, lon), headers=cuenta.h)
    assert r.status_code == 429 and r.json()["error"]["codigo"] == "LIMITE_REPORTES"
    assert 1 <= int(r.headers["Retry-After"]) <= 3600
    assert client.get(f"{API}/auth/yo", headers=cuenta.h).json()["reportes_ultima_hora"] == 10


# --------------------------------------------------------------------------- privacidad (RN-04)


def test_respuestas_publicas_sin_datos_personales(client, db, ciudadano):
    lat, lon = punto_unico()
    folio = crear_reporte(client, ciudadano, payload_bache(client, lat, lon))["folio"]
    rutas = [
        f"{API}/reportes?por_pagina=100", f"{API}/reportes/{folio}", f"{API}/reportes/{folio}/historial",
        f"{API}/reportes/{folio}?x=1", f"{API}/catalogos/sectores", f"{API}/catalogos/colonias?por_pagina=100",
        f"{API}/catalogos/tipos-dano", f"{API}/catalogos/estados", f"{API}/indicadores/resumen",
        f"{API}/indicadores/sectores", f"{API}/indicadores/longevidad", f"{API}/clima/riesgo-inundacion",
    ]
    personales = [fila[0] for fila in db.execute(text("SELECT nombre FROM usuarios UNION SELECT correo::text FROM usuarios"))]
    for ruta in rutas:
        r = client.get(ruta)
        assert r.status_code == 200, (ruta, r.text)
        assert not claves(r.json()) & CLAVES_PRIVADAS, ruta
        cuerpo = json.dumps(r.json(), ensure_ascii=False)
        assert not [p for p in personales if p in cuerpo], ruta


# --------------------------------------------------------------------------- listados, indicadores, admin


def test_listado_publico_y_filtros(client):
    r = client.get(f"{API}/reportes", params={"tipo_dano": "Bache", "estado": "Reparado", "por_pagina": 5}).json()
    assert r["paginacion"]["por_pagina"] == 5 and r["datos"]
    assert all(x["tipo_dano"] == "Bache" and x["estado"] == "Reparado" for x in r["datos"])
    assert all(x["longevidad_dias"] is not None for x in r["datos"])
    recibidos = client.get(f"{API}/reportes", params={"estado": "Recibido", "por_pagina": 100}).json()["datos"]
    assert recibidos and all(x["etiqueta_publica"] == "Sin validar" for x in recibidos)
    assert client.get(f"{API}/reportes", params={"bbox": "-106.5,31.6,-106.4,31.7"}).status_code == 200
    assert client.get(f"{API}/reportes", params={"bbox": "mal"}).status_code == 422
    assert client.get(f"{API}/reportes/BCH-2026-00001").status_code == 422  # folio con formato inválido
    assert client.get(f"{API}/reportes/BCH-2026-999998").status_code == 404


def test_indicadores(client, moderador):
    res = client.get(f"{API}/indicadores/resumen").json()
    assert res["pavimento"]["total"] > 0 and res["encharcamientos"]["historicos"] > 0
    assert res["periodo"]["zona_horaria"] == "America/Ciudad_Juarez"
    assert len(client.get(f"{API}/indicadores/sectores").json()["datos"]) >= 6
    ant = client.get(f"{API}/indicadores/longevidad", params={"limite": 3}).json()["datos"]
    assert len(ant) == 3 and ant[0]["longevidad_dias"] >= ant[-1]["longevidad_dias"]
    mod = client.get(f"{API}/indicadores/moderacion", headers=moderador.h).json()
    assert mod["pendientes_validacion"] >= 1 and 0 <= mod["tasa_rechazo_pct"] <= 100


def test_admin(client, coordinador, moderador):
    clave = f"ZONA-{coordinador.id[:6].upper()}"
    r = client.post(f"{API}/admin/sectores", json={"clave": clave, "nombre": f"Sector {clave}"}, headers=coordinador.h)
    assert r.status_code == 201
    sector_id = r.json()["id"]
    assert client.post(f"{API}/admin/sectores", json={"clave": clave, "nombre": "Otro"}, headers=coordinador.h).status_code == 409
    nueva = {"sector_id": sector_id, "nombre": "Colonia de Prueba", "codigo_postal": "32599", "latitud_centro": 31.5, "longitud_centro": -106.5}
    cp_ajeno = client.post(f"{API}/admin/colonias", json={**nueva, "codigo_postal": "32999"}, headers=coordinador.h)
    assert cp_ajeno.status_code == 422  # fuera del rango de Juárez (32000–32730)
    assert client.post(f"{API}/admin/colonias", json=nueva, headers=coordinador.h).status_code == 201
    fuera = client.post(f"{API}/admin/colonias", json={**nueva, "nombre": "Fuera", "latitud_centro": 35}, headers=coordinador.h)
    assert fuera.status_code == 422 and fuera.json()["error"]["codigo"] == "FUERA_DE_JUAREZ"
    assert client.post(f"{API}/admin/colonias", json=nueva, headers=coordinador.h).status_code == 409
    assert client.post(f"{API}/admin/sectores", json={"clave": "X1", "nombre": "Y1"}, headers=moderador.h).status_code == 403
    cambio = client.patch(f"{API}/admin/usuarios/{moderador.id}/rol", json={"rol": "ciudadano"}, headers=coordinador.h)
    assert cambio.status_code == 200
    assert client.get(f"{API}/auth/yo", headers=moderador.h).status_code == 401  # sesión revocada al cambiar rol
    assert client.patch(f"{API}/admin/usuarios/{coordinador.id}/rol", json={"rol": "ciudadano"}, headers=coordinador.h).status_code == 400
    assert client.patch(f"{API}/admin/usuarios/{moderador.id}/estado", json={"activo": False}, headers=coordinador.h).status_code == 200
    login = client.post(f"{API}/auth/login", json={"correo": moderador.correo, "contrasena": CONTRASENA})
    assert login.status_code == 401
    usuarios = client.get(f"{API}/admin/usuarios", params={"rol": "coordinador"}, headers=coordinador.h).json()
    assert usuarios["datos"] and "correo" in usuarios["datos"][0]


# --------------------------------------------------------------------------- geocodificación y clima


def test_geocoding_fallback_sin_llave(client, monkeypatch):
    from app.routers import geocoding as router_geo

    router_geo._limitador._eventos.clear()
    monkeypatch.setattr(get_settings(), "geocoding_api_key", SecretStr(""))
    r = client.get(f"{API}/geocoding/buscar", params={"q": "romero"})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["fuente"] == "catalogo_local" and cuerpo["degradado"] is True and cuerpo["mensaje"]
    assert any(d["colonia_sugerida"]["nombre"] == "Partido Romero" for d in cuerpo["datos"])
    assert client.get(f"{API}/geocoding/buscar", params={"q": "ab"}).status_code == 422


def test_geocoding_locationiq_filtra_juarez_y_no_expone_la_llave(client, monkeypatch):
    from app.routers import geocoding as router_geo
    from app.services import geocoding as servicio

    router_geo._limitador._eventos.clear()
    centinela = "llave-centinela-no-debe-aparecer"
    monkeypatch.setattr(get_settings(), "geocoding_api_key", SecretStr(centinela))
    crudos = [
        {"lat": "31.7330", "lon": "-106.4630", "display_name": "x", "address": {"road": "Avenida Tecnológico", "neighbourhood": "Partido Romero"}},
        {"lat": "32.5000", "lon": "-106.4000", "display_name": "Fuera de Juárez"},  # fuera del bounding box
        {"lat": "31.6000", "lon": "-106.9000", "display_name": "Fuera en longitud"},
    ]
    monkeypatch.setattr(servicio, "_consultar_locationiq", lambda q, limite: crudos)
    r = client.get(f"{API}/geocoding/buscar", params={"q": "tecnologico"})
    cuerpo = r.json()
    assert r.status_code == 200 and cuerpo["fuente"] == "locationiq" and cuerpo["degradado"] is False
    assert len(cuerpo["datos"]) == 1 and cuerpo["datos"][0]["colonia_sugerida"]["nombre"] == "Partido Romero"
    assert cuerpo["datos"][0]["precision"] == "calle" and "OpenStreetMap" in cuerpo["atribucion"]

    def falla(q, limite):
        raise servicio._ProveedorNoDisponible

    monkeypatch.setattr(servicio, "_consultar_locationiq", falla)
    caido = client.get(f"{API}/geocoding/buscar", params={"q": "romero"})
    assert caido.status_code == 200 and caido.json()["fuente"] == "catalogo_local"
    for resp in (r, caido):
        assert centinela not in resp.text and centinela not in json.dumps(dict(resp.headers))


def test_geocoding_limite_de_busquedas(client, monkeypatch):
    from app.routers import geocoding as router_geo

    router_geo._limitador._eventos.clear()
    monkeypatch.setattr(get_settings(), "geocoding_api_key", SecretStr(""))
    codigos = [client.get(f"{API}/geocoding/buscar", params={"q": "centro"}).status_code for _ in range(31)]
    assert codigos[:30] == [200] * 30 and codigos[30] == 429
    router_geo._limitador._eventos.clear()


def test_clima_cache_y_degradacion(client, db, monkeypatch):
    from app.services import clima

    db.execute(text("DELETE FROM cache_clima"))
    db.commit()
    clima.reiniciar_retroceso()

    def caido():
        raise httpx.ConnectError("sin red")

    monkeypatch.setattr(clima, "_consultar_proveedor", caido)
    sin_cache = client.get(f"{API}/clima/pronostico")
    assert sin_cache.status_code == 503 and sin_cache.json()["error"]["codigo"] == "CLIMA_NO_DISPONIBLE"

    from app.core.tiempo import ahora_utc

    inicio = ahora_utc().replace(minute=0, second=0, microsecond=0)
    horas = [{"hora": (inicio + timedelta(hours=i)).isoformat(), "prob": 80 if i == 1 else 10, "mm": 2.5 if i == 1 else 0} for i in range(0, 10)]
    normalizada = {"actual": {"temperatura_c": 14.2, "precipitacion_mm": 0.0, "descripcion": "Lluvia ligera"}, "horas": horas}
    clima.reiniciar_retroceso()  # el fallo anterior activó el retroceso (D-24)
    monkeypatch.setattr(clima, "_consultar_proveedor", lambda: normalizada)
    ok = client.get(f"{API}/clima/pronostico").json()
    assert ok["alerta_lluvia"] is True and ok["desactualizado"] is False and len(ok["proximas_horas"]) == 6

    monkeypatch.setattr(clima, "_consultar_proveedor", caido)
    assert client.get(f"{API}/clima/pronostico").json()["desactualizado"] is False  # sirve la caché vigente
    db.execute(text("UPDATE cache_clima SET expira_at = now() - interval '1 minute', obtenido_at = now() - interval '2 hours'"))
    db.commit()
    viejo = client.get(f"{API}/clima/pronostico")
    assert viejo.status_code == 200 and viejo.json()["desactualizado"] is True


def test_riesgo_de_inundacion(client):
    r = client.get(f"{API}/clima/riesgo-inundacion", params={"limite": 5}).json()
    assert r["datos"] and r["datos"][0]["nivel_riesgo"] in {"Alto", "Medio", "Bajo"} and r["criterio"]
    assert client.get(f"{API}/clima/riesgo-inundacion", params={"calle": "tecn"}).status_code == 200
