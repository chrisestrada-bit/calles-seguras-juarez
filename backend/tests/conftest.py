"""Fixtures de pruebas.

Las pruebas de integración necesitan PostgreSQL con migraciones aplicadas y la semilla cargada
(alembic -c db/alembic.ini upgrade head && python db/seed.py). Para no ensuciar datos reales sólo se
ejecutan si el nombre de la base de datos termina en «_test».
"""

import itertools
import os
import sys
import uuid
from pathlib import Path

import pytest

os.environ.setdefault("JWT_SECRET_KEY", "clave-de-pruebas-clave-de-pruebas-1234567890")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres@127.0.0.1:5432/calles_seguras_test")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402

CONTRASENA = "Prueba2026"
_celdas = itertools.count(0)
_PASO = 0.003  # ≈ 333 m entre celdas: ni los radios de 30 m / 50 m ni los desplazamientos de prueba se cruzan


def punto_unico() -> tuple[float, float]:
    """Coordenada del extremo suroeste de Juárez sin ningún reporte cerca (sin duplicados accidentales)."""
    while True:
        i = next(_celdas)
        lat = round(31.451 + (i % 110) * _PASO, 6)
        lon = round(-106.649 + ((i // 110) % 130) * _PASO, 6)
        with SessionLocal() as s:
            ocupada = s.execute(
                text("SELECT 1 FROM reportes WHERE latitud BETWEEN :a AND :b AND longitud BETWEEN :c AND :d LIMIT 1"),
                {"a": lat - 0.0015, "b": lat + 0.0035, "c": lon - 0.0015, "d": lon + 0.0035},
            ).first()
        if ocupada is None:
            return lat, lon


def desplazar(lat: float, lon: float, metros_norte: float) -> tuple[float, float]:
    return round(lat + metros_norte / 111_320, 6), lon


@pytest.fixture(scope="session")
def client():
    if not (engine.url.database or "").endswith("_test"):
        pytest.skip("Las pruebas de integración requieren una base de datos cuyo nombre termine en _test.")
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        pytest.skip("PostgreSQL no está disponible para las pruebas de integración.")
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    with SessionLocal() as sesion:
        yield sesion


class Cuenta:
    def __init__(self, client: TestClient, correo: str, usuario_id: str, token: str) -> None:
        self.client, self.correo, self.id, self.token = client, correo, usuario_id, token

    @property
    def h(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


def crear_cuenta(client: TestClient, rol: str = "ciudadano") -> Cuenta:
    correo = f"prueba-{uuid.uuid4().hex[:12]}@ejemplo.mx"
    r = client.post("/api/v1/auth/registro", json={"nombre": "Persona de Prueba", "correo": correo, "contrasena": CONTRASENA})
    assert r.status_code == 201, r.text
    usuario_id = r.json()["id"]
    if rol != "ciudadano":
        with SessionLocal() as s:
            s.execute(text("UPDATE usuarios SET rol = :r WHERE id = :i"), {"r": rol, "i": usuario_id})
            s.commit()
    login = client.post("/api/v1/auth/login", json={"correo": correo, "contrasena": CONTRASENA})
    assert login.status_code == 200, login.text
    return Cuenta(client, correo, usuario_id, login.json()["access_token"])


@pytest.fixture
def ciudadano(client):
    return crear_cuenta(client)


@pytest.fixture
def ciudadanos(client):
    return [crear_cuenta(client) for _ in range(5)]


@pytest.fixture
def moderador(client):
    return crear_cuenta(client, "moderador")


@pytest.fixture
def coordinador(client):
    return crear_cuenta(client, "coordinador")


def primera_colonia(client: TestClient) -> int:
    return client.get("/api/v1/catalogos/colonias").json()["datos"][0]["id"]


def payload_bache(client: TestClient, lat: float, lon: float, **extra) -> dict:
    base = {
        "tipo_dano": "Bache", "latitud": lat, "longitud": lon, "colonia_id": primera_colonia(client),
        "calle": "Av. Tecnológico", "tamano": "grande", "profundidad": "más de 10 cm",
        "carril_afectado": "carril derecho",
    }
    return {**base, **extra}


def payload_enc(client: TestClient, lat: float, lon: float, **extra) -> dict:
    base = {
        "tipo_dano": "Encharcamiento", "latitud": lat, "longitud": lon, "colonia_id": primera_colonia(client),
        "calle": "Av. de las Torres", "nivel_agua": "cubre un carril",
    }
    return {**base, **extra}


def crear_reporte(client: TestClient, cuenta: Cuenta, payload: dict) -> dict:
    r = client.post("/api/v1/reportes", json=payload, headers=cuenta.h)
    assert r.status_code == 201, r.text
    return r.json()
