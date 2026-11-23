"""Sondeos de la auditoría final (2026-11-22), ANTES de las correcciones. Se conservan como evidencia.

Sólo se ejecuta contra una base cuyo nombre termine en _test (ver 02-pruebas-y-evidencia.md). Tras las
correcciones, cada sondeo tiene su prueba de regresión en backend/tests/test_auditoria_final.py y aquí
reportarían «no reproducido».

Uso (desde la raíz del repo, con DATABASE_URL/JWT_SECRET_KEY de pruebas). Tras las correcciones, S2 frena al
propio script (límite de registros por IP): para revisar S3–S9 exporta LIMITE_REGISTROS_POR_HORA_IP=1000.
    python docs/auditoria-final/evidencia/sondeo_auditoria.py
"""
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "backend" / "tests"))
sys.path.insert(0, str(REPO / "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from conftest import crear_cuenta, crear_reporte, payload_bache, punto_unico, CONTRASENA  # noqa: E402

assert engine.url.database.endswith("_test")
API = "/api/v1"


def linea(id_, ok, detalle):
    print(f"[{id_}] {'CONFIRMADO' if ok else 'no reproducido'} :: {detalle}")


with TestClient(app) as c:
    # S1: enlace municipal no puede cerrar sesión ni renovar (CUALQUIER_ROL excluye ENLACE_MUNICIPAL)
    enlace = crear_cuenta(c, "enlace_municipal")
    r_logout = c.post(f"{API}/auth/cerrar-sesion", headers=enlace.h)
    r_renov = c.post(f"{API}/auth/renovar", headers=enlace.h)
    r_yo = c.get(f"{API}/auth/yo", headers=enlace.h)
    r_tras = c.get(f"{API}/enlace/reportes", headers=enlace.h)
    linea("S1", r_logout.status_code == 403 and r_tras.status_code == 200,
          f"logout={r_logout.status_code} renovar={r_renov.status_code} yo={r_yo.status_code} "
          f"token tras logout sigue valido -> /enlace/reportes={r_tras.status_code}")

    # S2: registro sin límite de tasa
    codigos = []
    for i in range(25):
        r = c.post(f"{API}/auth/registro", json={"nombre": "Bot", "correo": f"bot{i}-{id(c)}@ejemplo.mx",
                                                 "contrasena": CONTRASENA, "acepta_aviso_privacidad": True})
        codigos.append(r.status_code)
    linea("S2", 429 not in codigos, f"25 registros seguidos desde la misma IP -> {set(codigos)}")

    # S3: bloqueo de cuenta ajena (DoS de login): 5 intentos fallidos bloquean a la víctima 15 min
    victima = crear_cuenta(c)
    for _ in range(5):
        c.post(f"{API}/auth/login", json={"correo": victima.correo, "contrasena": "Incorrecta123"})
    r = c.post(f"{API}/auth/login", json={"correo": victima.correo, "contrasena": CONTRASENA})
    linea("S3", r.status_code == 429, f"login legitimo tras 5 fallos de un tercero -> {r.status_code} Retry-After={r.headers.get('retry-after')}")

    # S4: coordinador rechaza un «Recibido» vía fusión (RN-05: Recibido->Rechazado sólo Moderador)
    autor = crear_cuenta(c)
    coord = crear_cuenta(c, "coordinador")
    lat, lon = punto_unico()
    p = crear_reporte(c, autor, payload_bache(c, lat, lon))
    lat2, lon2 = punto_unico()
    s = crear_reporte(c, crear_cuenta(c), payload_bache(c, lat2, lon2))
    directo = c.post(f"{API}/moderacion/reportes/{s['folio']}/transiciones",
                     json={"estado_nuevo": "Rechazado", "motivo_id": 1}, headers=coord.h)
    fus = c.post(f"{API}/moderacion/reportes/fusionar", json={"folio_principal": p["folio"], "folio_secundario": s["folio"]}, headers=coord.h)
    linea("S4", directo.status_code == 403 and fus.status_code in (200, 201),
          f"coordinador transicion directa Recibido->Rechazado={directo.status_code}; via fusion={fus.status_code} "
          f"(distancia entre reportes ~{abs(lat2-lat)*111000+abs(lon2-lon)*95000:.0f} m)")

    # S5: EXIF conservado y nombre_original público
    jpeg = b"\xff\xd8\xff\xe1" + b"\x00\x40" + b"Exif\x00\x00" + b"GPS-31.7N-106.4W-MARCA-PRIVADA" + b"\x00" * 24 + b"\xff\xd9"
    lat3, lon3 = punto_unico()
    rep = crear_reporte(c, autor, payload_bache(c, lat3, lon3))
    up = c.post(f"{API}/reportes/{rep['folio']}/fotos", headers=autor.h,
                files=[("archivos", ("Juan_Perez_Calle_Falsa_123.jpg", io.BytesIO(jpeg), "image/jpeg"))])
    mod = crear_cuenta(c, "moderador")
    c.post(f"{API}/moderacion/reportes/{rep['folio']}/transiciones", json={"estado_nuevo": "Validado"}, headers=mod.h)
    lista = c.get(f"{API}/reportes/{rep['folio']}/fotos")  # visitante
    if lista.status_code == 200 and lista.json()["datos"]:
        foto = lista.json()["datos"][0]
        bajada = c.get(foto["url"])
        linea("S5", b"MARCA-PRIVADA" in bajada.content,
              f"upload={up.status_code}; visitante ve nombre_original='{foto['nombre_original']}'; "
              f"metadatos EXIF intactos en descarga publica={b'MARCA-PRIVADA' in bajada.content}")
    else:
        linea("S5", False, f"upload={up.status_code} lista={lista.status_code} {lista.text[:200]}")

    # S6: WebSocket sin cabecera Origin se acepta
    try:
        with c.websocket_connect(f"{API}/ws/encharcamientos") as ws:
            linea("S6", ws.receive_json().get("tipo") == "hola", "WS sin Origin aceptado (clientes no navegador sin tope de conexiones)")
    except Exception as e:  # noqa: BLE001
        linea("S6", False, f"WS rechazado: {e}")

    # S7: cabeceras de seguridad de la API
    h = c.get("/salud").headers
    faltan = [k for k in ("strict-transport-security", "x-frame-options", "content-security-policy", "referrer-policy") if k not in h]
    linea("S7", bool(faltan), f"cabeceras ausentes en API: {faltan}")

    # S8: limitador de geocoding por request.client.host (X-Forwarded-For ignorado)
    ok = 0
    for i in range(31):
        r = c.get(f"{API}/geocoding/buscar", params={"q": "32000"}, headers={"X-Forwarded-For": f"10.0.0.{i}"})
        ok += r.status_code == 200
    linea("S8", ok == 30, f"31 busquedas con XFF distinto: {ok} OK, ultima={r.status_code} (todas cuentan como una sola IP: tras proxy, IP compartida)")

    # S9: secuencia de folios con tope 999999 NO CYCLE
    with SessionLocal() as s_:
        mx = s_.execute(text("SELECT max_value FROM pg_sequences WHERE sequencename='seq_folio_bch'")).scalar()
    linea("S9", mx == 999999, f"seq_folio_bch max_value={mx}, global (no se reinicia por año)")
