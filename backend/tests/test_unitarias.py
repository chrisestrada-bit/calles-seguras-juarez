"""Pruebas sin base de datos: geografía, esquemas, severidad y máquina de estados."""

import os

os.environ.setdefault("JWT_SECRET_KEY", "clave-de-pruebas-clave-de-pruebas-1234567890")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres@127.0.0.1:5432/calles_seguras_test")

import pytest
from pydantic import TypeAdapter, ValidationError

from app.core.errores import ErrorAPI, _traducir_validacion
from app.core.security import contrasena_valida
from app.models import EstadoReporte as E
from app.models import NivelAgua, RolUsuario, Severidad, TipoDano
from app.schemas.reportes import ReporteCrear
from app.services import geo, transiciones
from app.services.reportes import calcular_severidad, severidad_bache
from app.models import ProfundidadBache, TamanoBache

adaptador = TypeAdapter(ReporteCrear)
BASE = {"latitud": 31.7, "longitud": -106.4, "colonia_id": 1, "calle": "Av. Juárez"}


def test_haversine_30_metros():
    d = geo.haversine_m(31.7, -106.4, 31.7 + 30 / 111_320, -106.4)
    assert d == pytest.approx(30, abs=0.1)


def test_limites_de_juarez():
    assert geo.dentro_de_juarez(31.45, -106.65) and geo.dentro_de_juarez(31.80, -106.25)
    assert not geo.dentro_de_juarez(31.44, -106.4)
    assert not geo.dentro_de_juarez(31.7, -106.24)
    assert not geo.dentro_de_juarez(31.7, -106.66)


@pytest.mark.parametrize("campo,valor", [("latitud", 32.5), ("longitud", -107.0)])
def test_fuera_de_juarez_se_rechaza(campo, valor):
    datos = {**BASE, "tipo_dano": "Alcantarilla sin tapa", "esta_senalizado": True, campo: valor}
    with pytest.raises(ValidationError) as exc:
        adaptador.validate_python(datos)
    codigo, _, detalles = _traducir_validacion(exc.value.errors())
    assert codigo == "FUERA_DE_JUAREZ"
    assert detalles[0]["campo"] == campo


def test_bache_exige_campos_condicionales():
    with pytest.raises(ValidationError) as exc:
        adaptador.validate_python({**BASE, "tipo_dano": "Bache"})
    campos = {e["loc"][-1] for e in exc.value.errors()}
    assert {"tamano", "profundidad", "carril_afectado"} <= campos


def test_encharcamiento_intransitable_exige_riesgo():
    with pytest.raises(ValidationError):
        adaptador.validate_python({**BASE, "tipo_dano": "Encharcamiento", "nivel_agua": "intransitable"})
    ok = adaptador.validate_python(
        {**BASE, "tipo_dano": "Encharcamiento", "nivel_agua": "intransitable", "hay_riesgo_personas_vehiculos": True}
    )
    assert ok.hay_riesgo_personas_vehiculos is True


def test_encharcamiento_no_intransitable_rechaza_riesgo():
    with pytest.raises(ValidationError):
        adaptador.validate_python(
            {**BASE, "tipo_dano": "Encharcamiento", "nivel_agua": "a un lado de la calle", "hay_riesgo_personas_vehiculos": False}
        )


def test_descripcion_maximo_500_y_campos_extra():
    datos = {**BASE, "tipo_dano": "Alcantarilla sin tapa", "esta_senalizado": False}
    assert adaptador.validate_python({**datos, "descripcion": "a" * 500})
    with pytest.raises(ValidationError):
        adaptador.validate_python({**datos, "descripcion": "a" * 501})
    with pytest.raises(ValidationError):  # el cliente no puede fijar severidad ni folio
        adaptador.validate_python({**datos, "severidad": "Baja"})
    with pytest.raises(ValidationError):
        adaptador.validate_python({**datos, "folio": "BCH-2026-000001"})


def test_alcantarilla_siempre_alta():
    r = adaptador.validate_python({**BASE, "tipo_dano": "Alcantarilla sin tapa", "esta_senalizado": True})
    assert calcular_severidad(r) == Severidad.ALTA


def test_severidad_bache():
    assert severidad_bache(TamanoBache.GRANDE, ProfundidadBache.MENOS_5) == Severidad.ALTA
    assert severidad_bache(TamanoBache.CHICO, ProfundidadBache.MAS_10) == Severidad.ALTA
    assert severidad_bache(TamanoBache.MEDIANO, ProfundidadBache.MENOS_5) == Severidad.MEDIA
    assert severidad_bache(TamanoBache.CHICO, ProfundidadBache.DE_5_A_10) == Severidad.MEDIA
    assert severidad_bache(TamanoBache.CHICO, ProfundidadBache.MENOS_5) == Severidad.BAJA


PERMITIDAS = {
    (E.RECIBIDO, E.VALIDADO, "moderador"), (E.RECIBIDO, E.RECHAZADO, "moderador"),
    (E.VALIDADO, E.PROGRAMADO, "moderador"), (E.VALIDADO, E.PROGRAMADO, "coordinador"),
    (E.VALIDADO, E.EN_REPARACION, "moderador"), (E.VALIDADO, E.EN_REPARACION, "coordinador"),
    (E.PROGRAMADO, E.EN_REPARACION, "moderador"), (E.PROGRAMADO, E.EN_REPARACION, "coordinador"),
    (E.EN_REPARACION, E.REPARADO, "moderador"), (E.EN_REPARACION, E.REPARADO, "coordinador"),
}


def _resultado(desde, hacia, rol):
    try:
        transiciones.validar_transicion(TipoDano.BACHE, desde, hacia, RolUsuario(rol))
    except ErrorAPI as e:
        return e.status
    return 200


@pytest.mark.parametrize("desde", [E.RECIBIDO, E.VALIDADO, E.PROGRAMADO, E.EN_REPARACION, E.REPARADO, E.RECHAZADO])
@pytest.mark.parametrize("hacia", [E.RECIBIDO, E.VALIDADO, E.PROGRAMADO, E.EN_REPARACION, E.REPARADO, E.RECHAZADO])
@pytest.mark.parametrize("rol", ["moderador", "coordinador"])
def test_matriz_completa_rn05(desde, hacia, rol):
    r = _resultado(desde, hacia, rol)
    if (desde, hacia, rol) in PERMITIDAS:
        assert r == 200
    elif any(d == desde and h == hacia for d, h, _ in PERMITIDAS):
        assert r == 403  # transición válida pero el rol no puede ejecutarla
    else:
        assert r == 400  # transición inexistente (incluye estados finales)


def test_encharcamiento_activo_a_historico_no_es_manual():
    with pytest.raises(ErrorAPI) as exc:
        transiciones.validar_transicion(TipoDano.ENCHARCAMIENTO, E.ACTIVO, E.HISTORICO, RolUsuario.MODERADOR)
    assert exc.value.status == 400
    transiciones.validar_transicion(TipoDano.ENCHARCAMIENTO, E.ACTIVO, E.RECHAZADO, RolUsuario.MODERADOR)


def test_politica_de_contrasena():
    assert contrasena_valida("Abcdef12")
    assert not contrasena_valida("abcdefgh")  # sin números
    assert not contrasena_valida("12345678")  # sin letras
    assert not contrasena_valida("Ab1")  # muy corta


def test_nivel_agua_valores():
    assert [n.value for n in NivelAgua] == [
        "a un lado de la calle", "cubre un carril", "a media llanta", "intransitable",
    ]
