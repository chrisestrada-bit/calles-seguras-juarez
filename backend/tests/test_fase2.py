"""Fase 2 de requisitos opcionales: HU-03.4 (puntos recurrentes), HU-08.2 (notificaciones),
HU-08.3 (WebSocket en vivo) y HU-08.4 (idempotencia para envíos sin conexión)."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from starlette.websockets import WebSocketDisconnect

from app.core.tiempo import hoy_local
from app.models import EstadoReporte, OrigenCambio, Reporte, Severidad, TipoDano
from app.services import tiempo_real
from app.services.folios import generar_folio
from app.services.historial import fijar_contexto
from tests.conftest import (
    crear_reporte,
    desplazar,
    payload_bache,
    payload_enc,
    primera_colonia,
    punto_unico,
)

API = "/api/v1"
ANIO = hoy_local().year


def sembrar_enc(db, client, autor_id, lat, lon, creado: datetime, estado=EstadoReporte.HISTORICO) -> str:
    """Inserta un encharcamiento con fecha controlada (la API siempre usa «ahora»)."""
    motivo = "Reporte de prueba" if estado == EstadoReporte.RECHAZADO else None
    fijar_contexto(db, usuario_id=autor_id, origen=OrigenCambio.CIUDADANO, motivo=motivo, fecha_evento=creado)
    r = Reporte(
        folio=generar_folio(db, TipoDano.ENCHARCAMIENTO, creado),
        tipo_dano=TipoDano.ENCHARCAMIENTO,
        estado=estado,
        severidad=Severidad.BAJA,
        usuario_id=autor_id,
        colonia_id=primera_colonia(client),
        latitud=lat,
        longitud=lon,
        calle="Av. de las Torres",
        nivel_agua="cubre un carril",
        vigencia_inicio=creado,
        vigente_hasta=creado + timedelta(hours=6),  # ck_vigencia_6h
        ciclo_vigencia=0,
        motivo_rechazo=motivo,
        created_at=creado,
        updated_at=creado,
    )
    db.add(r)
    db.commit()
    return r.folio


def utc(mes: int, dia: int, hora: int = 18, minuto: int = 0, anio: int = ANIO) -> datetime:
    return datetime(anio, mes, dia, hora, minuto, tzinfo=timezone.utc)


def detalle(client, folio):
    r = client.get(f"{API}/reportes/{folio}")
    assert r.status_code == 200, r.text
    return r.json()


# ============================================================================ HU-03.4 puntos recurrentes


def test_tres_dias_distintos_es_punto_recurrente(client, db, ciudadano):
    lat, lon = punto_unico()
    f1 = sembrar_enc(db, client, ciudadano.id, lat, lon, utc(1, 10))
    sembrar_enc(db, client, ciudadano.id, *desplazar(lat, lon, 20), utc(1, 15))
    sembrar_enc(db, client, ciudadano.id, *desplazar(lat, lon, 40), utc(1, 20))
    d = detalle(client, f1)
    assert d["es_punto_recurrente"] is True
    assert d["dias_distintos_anio"] == 3
    assert d["ultima_ocurrencia"].startswith(f"{ANIO}-01-20")
    en_lista = [x for x in client.get(f"{API}/reportes", params={"bbox": f"{lon - 0.001},{lat - 0.001},{lon + 0.001},{lat + 0.001}", "tipo_dano": "Encharcamiento", "estado": "Histórico"}).json()["datos"] if x["folio"] == f1]
    assert en_lista and en_lista[0]["es_punto_recurrente"] is True


def test_varios_reportes_el_mismo_dia_cuentan_como_un_dia(client, db, ciudadano):
    lat, lon = punto_unico()
    f1 = sembrar_enc(db, client, ciudadano.id, lat, lon, utc(2, 3, 16))
    sembrar_enc(db, client, ciudadano.id, lat, lon, utc(2, 3, 18))
    sembrar_enc(db, client, ciudadano.id, lat, lon, utc(2, 3, 20))
    sembrar_enc(db, client, ciudadano.id, lat, lon, utc(2, 9, 18))
    d = detalle(client, f1)
    assert d["dias_distintos_anio"] == 2 and d["es_punto_recurrente"] is False


def test_dia_se_cuenta_en_hora_de_ciudad_juarez_no_en_utc(client, db, ciudadano):
    """06:30 UTC es el día anterior en Juárez (UTC-7 en enero); 07:30 UTC ya es el día siguiente: 2 días, no 1."""
    lat, lon = punto_unico()
    f1 = sembrar_enc(db, client, ciudadano.id, lat, lon, utc(1, 10, 6, 30))
    sembrar_enc(db, client, ciudadano.id, lat, lon, utc(1, 10, 7, 30))
    assert detalle(client, f1)["dias_distintos_anio"] == 2
    sembrar_enc(db, client, ciudadano.id, lat, lon, utc(1, 25, 18))
    assert detalle(client, f1)["es_punto_recurrente"] is True


def test_radio_exacto_de_50_metros(client, db, ciudadano):
    lat, lon = punto_unico()
    f1 = sembrar_enc(db, client, ciudadano.id, lat, lon, utc(3, 1))
    sembrar_enc(db, client, ciudadano.id, *desplazar(lat, lon, 45), utc(3, 2))  # dentro (≈45 m)
    sembrar_enc(db, client, ciudadano.id, *desplazar(lat, lon, 56), utc(3, 3))  # fuera (≈56 m)
    assert detalle(client, f1)["dias_distintos_anio"] == 2


def test_no_cuenta_otro_anio_ni_rechazados_ni_pavimento(client, db, ciudadano):
    lat, lon = punto_unico()
    f1 = sembrar_enc(db, client, ciudadano.id, lat, lon, utc(4, 1))
    sembrar_enc(db, client, ciudadano.id, lat, lon, utc(12, 31, 18, anio=ANIO - 1))  # año anterior
    sembrar_enc(db, client, ciudadano.id, lat, lon, utc(4, 5), estado=EstadoReporte.RECHAZADO)
    crear_reporte(client, ciudadano, payload_bache(client, lat, lon))
    assert detalle(client, f1)["dias_distintos_anio"] == 1


def test_pavimento_no_lleva_datos_de_recurrencia(client, ciudadano):
    lat, lon = punto_unico()
    folio = crear_reporte(client, ciudadano, payload_bache(client, lat, lon))["folio"]
    d = detalle(client, folio)
    assert d["es_punto_recurrente"] is None and d["dias_distintos_anio"] is None


def test_vista_de_coordinador_lista_puntos_recurrentes(client, db, ciudadano, moderador, coordinador):
    lat, lon = punto_unico()
    for dia in (5, 12, 19):
        sembrar_enc(db, client, ciudadano.id, lat, lon, utc(5, dia))
    url = f"{API}/indicadores/puntos-recurrentes"
    assert client.get(url).status_code == 401
    assert client.get(url, headers=moderador.h).status_code == 403
    r = client.get(url, headers=coordinador.h)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["anio"] == ANIO and cuerpo["radio_metros"] == 50 and cuerpo["minimo_dias"] == 3
    cerca = [p for p in cuerpo["datos"] if abs(p["ubicacion"]["latitud"] - lat) < 0.0005 and abs(p["ubicacion"]["longitud"] - lon) < 0.0005]
    assert len(cerca) == 1 and cerca[0]["dias_distintos_anio"] == 3 and cerca[0]["total_reportes"] == 3
    assert "usuario" not in r.text and ciudadano.correo not in r.text


# ============================================================================ HU-08.2 notificaciones


def transicionar(client, cuenta, folio, **cuerpo):
    r = client.post(f"{API}/moderacion/reportes/{folio}/transiciones", json=cuerpo, headers=cuenta.h)
    assert r.status_code == 200, r.text
    return r.json()


def avisos(client, cuenta, **params):
    r = client.get(f"{API}/notificaciones", params=params, headers=cuenta.h)
    assert r.status_code == 200, r.text
    return r.json()


def nuevo_bache(client, cuenta):
    lat, lon = punto_unico()
    return crear_reporte(client, cuenta, payload_bache(client, lat, lon))["folio"]


def test_notificaciones_requieren_sesion(client):
    assert client.get(f"{API}/notificaciones").status_code == 401
    assert client.patch(f"{API}/notificaciones/leer-todas").status_code == 401
    assert client.patch(f"{API}/notificaciones/{uuid.uuid4()}/leer").status_code == 401


def test_cada_cambio_de_estado_avisa_al_autor(client, ciudadano, moderador, coordinador):
    folio = nuevo_bache(client, ciudadano)
    assert avisos(client, ciudadano)["no_leidas"] == 0
    transicionar(client, moderador, folio, estado_nuevo="Validado")
    transicionar(client, coordinador, folio, estado_nuevo="Programado", fecha_programada=hoy_local().isoformat())
    transicionar(client, coordinador, folio, estado_nuevo="En reparación")
    transicionar(client, coordinador, folio, estado_nuevo="Reparado", fecha_reparacion=hoy_local().isoformat())
    cuerpo = avisos(client, ciudadano)
    assert cuerpo["no_leidas"] == 4 and cuerpo["paginacion"]["total"] == 4
    textos = [n["mensaje"] for n in cuerpo["datos"]]
    assert all(folio in t for t in textos)
    assert any("validado" in t for t in textos) and any("programada" in t for t in textos)
    assert any("en reparación" in t for t in textos) and any("reparado" in t for t in textos)
    assert all(n["leida"] is False and n["folio"] == folio for n in cuerpo["datos"])
    # el mensaje más reciente va primero
    assert "reparado" in textos[0]


def test_rechazo_avisa_con_motivo(client, ciudadano, moderador):
    folio = nuevo_bache(client, ciudadano)
    transicionar(client, moderador, folio, estado_nuevo="Rechazado", motivo="Foto sin relación con el daño")
    n = avisos(client, ciudadano)["datos"][0]
    assert "rechazado" in n["mensaje"] and "Foto sin relación con el daño" in n["mensaje"]


def test_quien_cambia_el_estado_no_se_notifica_a_si_mismo(client, moderador, coordinador):
    folio = nuevo_bache(client, moderador)  # el moderador es autor y además valida
    transicionar(client, moderador, folio, estado_nuevo="Validado")
    assert avisos(client, moderador)["no_leidas"] == 0


def test_marcar_leida_y_marcar_todas(client, ciudadano, moderador):
    folio1, folio2 = nuevo_bache(client, ciudadano), nuevo_bache(client, ciudadano)
    transicionar(client, moderador, folio1, estado_nuevo="Validado")
    transicionar(client, moderador, folio2, estado_nuevo="Validado")
    lista = avisos(client, ciudadano)
    assert lista["no_leidas"] == 2
    uno = client.patch(f"{API}/notificaciones/{lista['datos'][0]['id']}/leer", headers=ciudadano.h)
    assert uno.status_code == 200 and uno.json()["leida"] is True
    assert avisos(client, ciudadano)["no_leidas"] == 1
    assert len(avisos(client, ciudadano, solo_no_leidas="true")["datos"]) == 1
    todas = client.patch(f"{API}/notificaciones/leer-todas", headers=ciudadano.h)
    assert todas.status_code == 200 and todas.json()["marcadas"] == 1
    assert avisos(client, ciudadano)["no_leidas"] == 0


def test_aislamiento_estricto_entre_usuarios(client, ciudadano, ciudadanos, moderador):
    folio = nuevo_bache(client, ciudadano)
    transicionar(client, moderador, folio, estado_nuevo="Validado")
    ajeno = ciudadanos[0]
    assert avisos(client, ajeno)["datos"] == []
    nid = avisos(client, ciudadano)["datos"][0]["id"]
    assert client.patch(f"{API}/notificaciones/{nid}/leer", headers=ajeno.h).status_code == 404
    assert client.patch(f"{API}/notificaciones/{nid}/leer", headers=moderador.h).status_code == 404
    assert client.patch(f"{API}/notificaciones/{uuid.uuid4()}/leer", headers=ajeno.h).status_code == 404
    # leer-todas de otra persona no toca mis avisos
    client.patch(f"{API}/notificaciones/leer-todas", headers=ajeno.h)
    assert avisos(client, ciudadano)["no_leidas"] == 1


# ============================================================================ HU-08.3 WebSocket

WS = f"{API}/ws/encharcamientos"
PROHIBIDAS = ("usuario", "correo", "autor", "password", "nombre_completo")


def siguiente_evento(ws, tipo_buscado: str, folio: str | None = None, intentos: int = 10) -> dict:
    for _ in range(intentos):
        ev = ws.receive_json()
        if ev["tipo"] == tipo_buscado and (folio is None or ev.get("folio") == folio):
            return ev
    raise AssertionError(f"No llegó el evento {tipo_buscado}")


def test_ws_emite_encharcamiento_nuevo_sin_datos_personales(client, ciudadano):
    lat, lon = punto_unico()
    with client.websocket_connect(WS) as ws:
        assert ws.receive_json()["tipo"] == "hola"
        folio = crear_reporte(client, ciudadano, payload_enc(client, lat, lon))["folio"]
        ev = siguiente_evento(ws, "encharcamiento.creado", folio)
    assert ev["reporte"]["folio"] == folio and ev["reporte"]["estado"] == "Activo"
    assert uuid.UUID(ev["event_id"])
    texto = str(ev).lower()
    assert ciudadano.correo not in texto and ciudadano.id not in texto
    assert not any(clave in texto for clave in PROHIBIDAS), texto


def test_ws_no_difunde_baches_y_si_confirmaciones_y_retiros(client, ciudadano, ciudadanos, moderador):
    lat, lon = punto_unico()
    lat2, lon2 = punto_unico()
    with client.websocket_connect(WS) as ws:
        ws.receive_json()
        crear_reporte(client, ciudadano, payload_bache(client, lat2, lon2))  # no es encharcamiento: sin evento
        folio = crear_reporte(client, ciudadano, payload_enc(client, lat, lon))["folio"]
        assert siguiente_evento(ws, "encharcamiento.creado")["folio"] == folio  # el primero es el encharcamiento
        r = client.post(f"{API}/reportes/{folio}/confirmaciones", json={"tipo": "sigue_ahi"}, headers=ciudadanos[0].h)
        assert r.status_code == 201
        actualizado = siguiente_evento(ws, "encharcamiento.actualizado", folio)
        assert actualizado["reporte"]["vigencia"]["sigue_ahi"] == 1
        transicionar(client, moderador, folio, estado_nuevo="Rechazado", motivo="Reporte falso")
        retirado = siguiente_evento(ws, "encharcamiento.retirado", folio)
        assert retirado["reporte"] is None


def test_ws_avisa_cuando_vence_la_vigencia(client, db, ciudadano):
    from sqlalchemy import text

    lat, lon = punto_unico()
    with client.websocket_connect(WS) as ws:
        ws.receive_json()
        folio = crear_reporte(client, ciudadano, payload_enc(client, lat, lon))["folio"]
        siguiente_evento(ws, "encharcamiento.creado", folio)
        db.execute(text("UPDATE reportes SET vigencia_inicio = now() - interval '361 minutes', vigente_hasta = now() - interval '1 minute' WHERE folio = :f"), {"f": folio})
        db.commit()
        client.get(f"{API}/reportes", params={"tipo_dano": "Encharcamiento"})  # la consulta materializa el vencimiento
        ev = siguiente_evento(ws, "encharcamiento.actualizado", folio)
    assert ev["reporte"]["estado"] == "Histórico"


def test_ws_deduplica_firmas_repetidas():
    tiempo_real.gestor._firmas.clear()
    assert tiempo_real.gestor.es_repetido("x|BCH|Activo||0") is False
    assert tiempo_real.gestor.es_repetido("x|BCH|Activo||0") is True


def test_ws_latido_y_cierre_por_inactividad(client, monkeypatch):
    monkeypatch.setattr(tiempo_real, "HEARTBEAT_SEGUNDOS", 0.2)
    with client.websocket_connect(WS) as ws:
        assert ws.receive_json()["tipo"] == "hola"
        assert ws.receive_json()["tipo"] == "ping"  # latido del servidor
        ws.send_json({"tipo": "pong"})  # responder reinicia el conteo de silencios
        assert ws.receive_json()["tipo"] == "ping"
        with pytest.raises(WebSocketDisconnect):  # sin respuesta, el servidor cierra tras dos latidos
            for _ in range(5):
                ws.receive_json()


def test_ws_rechaza_origen_no_autorizado(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(WS, headers={"origin": "http://sitio-malicioso.example"}) as ws:
            ws.receive_json()


# ============================================================================ HU-08.4 idempotencia


def test_reenviar_el_mismo_borrador_no_duplica_el_folio(client, db, ciudadano):
    from sqlalchemy import func, select

    lat, lon = punto_unico()
    clave = str(uuid.uuid4())
    cuerpo = payload_bache(client, lat, lon, idempotency_key=clave)
    r1 = client.post(f"{API}/reportes", json=cuerpo, headers=ciudadano.h)
    assert r1.status_code == 201, r1.text
    r2 = client.post(f"{API}/reportes", json=cuerpo, headers=ciudadano.h)
    assert r2.status_code == 200, r2.text  # reenvío idempotente
    assert r2.json()["folio"] == r1.json()["folio"]
    assert db.scalar(select(func.count()).select_from(Reporte).where(Reporte.idempotency_key == uuid.UUID(clave))) == 1
    assert "idempotency_key" not in r1.text  # la llave no se expone


def test_la_misma_llave_de_otra_persona_crea_otro_reporte(client, ciudadano, ciudadanos):
    clave = str(uuid.uuid4())
    lat, lon = punto_unico()
    lat2, lon2 = punto_unico()
    a = client.post(f"{API}/reportes", json=payload_bache(client, lat, lon, idempotency_key=clave), headers=ciudadano.h)
    b = client.post(f"{API}/reportes", json=payload_bache(client, lat2, lon2, idempotency_key=clave), headers=ciudadanos[0].h)
    assert a.status_code == b.status_code == 201 and a.json()["folio"] != b.json()["folio"]


def test_llave_invalida_se_rechaza(client, ciudadano):
    lat, lon = punto_unico()
    r = client.post(f"{API}/reportes", json=payload_bache(client, lat, lon, idempotency_key="no-es-uuid"), headers=ciudadano.h)
    assert r.status_code == 422


def test_duplicado_al_reenviar_conserva_el_conflicto_para_explicarlo(client, ciudadano, ciudadanos):
    """Un borrador con otra llave junto a un reporte abierto recibe 409: el cliente lo conserva y lo explica."""
    lat, lon = punto_unico()
    crear_reporte(client, ciudadano, payload_bache(client, lat, lon))
    r = client.post(f"{API}/reportes", json=payload_bache(client, lat, lon, idempotency_key=str(uuid.uuid4())), headers=ciudadanos[0].h)
    assert r.status_code == 409 and r.json()["error"]["codigo"] == "POSIBLE_DUPLICADO"
    fuera = client.post(f"{API}/reportes", json=payload_bache(client, 40.0, -100.0, idempotency_key=str(uuid.uuid4())), headers=ciudadano.h)
    assert fuera.status_code == 422 and fuera.json()["error"]["codigo"] == "FUERA_DE_JUAREZ"
