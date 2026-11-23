"""Datos semilla idempotentes para Calles Seguras Juárez.

Crea usuarios de prueba (ciudadano, moderador, coordinador), sectores y colonias de Ciudad Juárez y un
volumen realista de reportes históricos y activos distribuidos en distintos estados y colonias.

* Idempotente: usuarios, sectores y colonias se insertan sólo si faltan (las colonias existentes sólo
  actualizan su código postal); los reportes se completan hasta la meta de demostración (≥ 500 visibles,
  RNF-09) y, una vez alcanzada, no se vuelven a sembrar.
* Reproducible: el generador aleatorio usa una semilla fija.
* Pasa por los mismos triggers que la aplicación: el historial de estados y los folios (RN-03) los
  genera la base de datos, y las transiciones respetan RN-05 y RN-06.
* La contraseña de las cuentas de prueba sale de SEED_PASSWORD (ver .env.example); no hay valor por
  omisión en el código ni en docker-compose.yml. Sin SEED_PASSWORD las cuentas nuevas reciben una contraseña
  aleatoria no revelada. Con APP_ENV=production se exigen al menos 12 caracteres y se rechazan los valores de
  ejemplo que alguna vez se publicaron en el repositorio (auditoría final, A1).
* Colonias y fraccionamientos reales de Ciudad Juárez agrupados por sector. Los códigos postales
  (32000–32730) provienen del catálogo de SEPOMEX (consultado en micodigopostal.org, 2026-11-22); las
  coordenadas del centro son aproximadas. Samalayuca (32730) y San Isidro Río Grande (32720) quedan fuera
  del recuadro de RN-01 y no se incluyen.

Uso:  python db/seed.py
"""

import logging
import os
import random
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import func, select  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import MENSAJE_CONTRASENA, contrasena_valida, hashear_contrasena  # noqa: E402
from app.core.tiempo import a_local, ahora_utc  # noqa: E402
from app.models import (  # noqa: E402
    AsignacionCuadrilla,
    CatalogoMotivoRechazo,
    CatalogoTipoDano,
    Cuadrilla,
    UsuarioCuadrilla,
    CarrilAfectado,
    Colonia,
    ConfirmacionReporte,
    EstadoReporte,
    NivelAgua,
    OrigenCambio,
    ProfundidadBache,
    Reporte,
    RolUsuario,
    Sector,
    Severidad,
    TamanoBache,
    TipoConfirmacion,
    TipoDano,
    Usuario,
)
from app.services import geo  # noqa: E402
from app.services.folios import generar_folio  # noqa: E402
from app.services.historial import fijar_contexto  # noqa: E402
from app.services.reportes import severidad_bache, severidad_encharcamiento  # noqa: E402
from app.services.vigencia import MOTIVO_DESMENTIDO, MOTIVO_VENCIMIENTO, VIGENCIA  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s seed: %(message)s")
log = logging.getLogger("seed")

SEMILLA_ALEATORIA = 20261121

SECTORES = [
    ("NORPONIENTE", "Norponiente"),
    ("NORORIENTE", "Nororiente"),
    ("CENTRO", "Centro"),
    ("PONIENTE", "Poniente"),
    ("SURORIENTE", "Suroriente"),
    ("SURPONIENTE", "Surponiente"),
]

# Catálogo territorial agrupado por sector: (nombre, código postal o None, latitud, longitud del centro).
# Las 46 colonias originales conservan su sector y coordenadas (los reportes ya sembrados apuntan a ellas);
# se corrigen sus códigos postales cuando SEPOMEX los confirma. None = código postal sin verificar.
COLONIAS_POR_SECTOR: dict[str, list[tuple[str, str | None, float, float]]] = {
    "CENTRO": [
        ("Centro", "32000", 31.7390, -106.4870),
        ("Cuauhtémoc", "32010", 31.7350, -106.4930),
        ("Monumento", "32020", 31.7280, -106.4700),
        ("Partido Romero", "32030", 31.7330, -106.4630),
        ("El Barreal", "32040", 31.7370, -106.4570),
        ("Obrera", "32050", 31.7300, -106.4800),
        ("Chaveña", "32060", 31.7470, -106.4960),
        ("Monterrey", "32070", 31.7260, -106.4740),
        ("Corregidora", "32080", 31.7230, -106.4800),
        ("Altavista", "32120", 31.7220, -106.4900),
        ("Bellavista", "32130", 31.7300, -106.4850),
        ("Barrio Alto", "32160", 31.7450, -106.4930),
        ("Chamizal", "32300", 31.7560, -106.4590),
        ("Hidalgo", "32300", 31.7350, -106.4780),
        ("Margaritas", "32300", 31.7270, -106.4510),
        ("Monumental", "32310", 31.7340, -106.4500),
        ("Progresista", "32310", 31.7300, -106.4470),
        ("Los Álamos", "32310", 31.7270, -106.4420),
        ("Pronaf", "32315", 31.7440, -106.4720),
        ("Panamericana", "32320", 31.7230, -106.4380),
        ("Burócrata", "32330", 31.7170, -106.4410),
    ],
    "NORPONIENTE": [
        ("Felipe Ángeles", "32100", 31.7443, -106.5012),
        ("La Mesita", "32100", 31.7520, -106.5180),
        ("Anapra", "32107", 31.7868, -106.5470),
        ("Lomas de Poleo", "32107", 31.7925, -106.5620),
        ("Rancho Anapra", "32107", 31.7840, -106.5520),
        ("La Conquista", "32107", 31.7760, -106.5390),
        ("Ladrillera Juárez", "32108", 31.7680, -106.5300),
        ("Popular", "32110", 31.7480, -106.5080),
        ("Niños Héroes", "32130", 31.7360, -106.5000),
        ("Arroyo Colorado", "32140", 31.7330, -106.5080),
        ("Insurgentes", "32150", 31.7250, -106.5060),
        ("Lázaro Cárdenas", "32150", 31.7220, -106.5110),
        ("Durango", "32160", 31.7410, -106.5010),
        ("Francisco I. Madero", "32170", 31.7380, -106.5130),
        ("Fronteriza", "32180", 31.7420, -106.5200),
        ("Vicente Guerrero", "32190", 31.7350, -106.5250),
        ("Plutarco Elías Calles", "32217", 31.7340, -106.5030),
        ("Mariano Escobedo", "32230", 31.7480, -106.5120),
        ("Azteca", "32280", 31.7270, -106.5100),
    ],
    "PONIENTE": [
        ("Francisco Villa", "32110", 31.7110, -106.4940),
        ("16 de Septiembre", "32210", 31.7250, -106.5200),
        ("Adolfo López Mateos", "32220", 31.7200, -106.5100),
        ("Álvaro Obregón", "32220", 31.7170, -106.5050),
        ("Hermenegildo Galeana", "32230", 31.7150, -106.5000),
        ("San Antonio", "32250", 31.7180, -106.4960),
        ("Constitución", "32260", 31.7100, -106.4930),
        ("Industrial", "32270", 31.7080, -106.4880),
        ("Libertad", "32290", 31.7060, -106.4990),
        ("Ricardo Flores Magón", "32290", 31.7030, -106.4950),
        ("Vista Hermosa", "32295", 31.6980, -106.5000),
        ("Los Nogales", "32340", 31.7090, -106.4720),
        ("Satélite", "32543", 31.7050, -106.4560),
        ("Infonavit Casas Grandes", "32600", 31.7182, -106.4529),
        ("Hacienda de las Torres", None, 31.7160, -106.4380),
        ("Paseo de la Victoria", None, 31.7000, -106.4470),
        ("Villa Colonial", None, 31.7020, -106.4820),
        ("Mezquital", None, 31.6930, -106.4780),
        ("Morelos", None, 31.6900, -106.4660),
    ],
    "NORORIENTE": [
        ("Aurora", "32350", 31.7090, -106.4300),
        ("La Raza", "32360", 31.7070, -106.4350),
        ("Olimpia", "32370", 31.7020, -106.4400),
        ("Jardines de San José", "32390", 31.6950, -106.4200),
        ("Alameda", "32400", 31.6930, -106.4370),
        ("Infonavit San Lorenzo", "32420", 31.7050, -106.4100),
        ("Villas San Marcos", "32450", 31.6830, -106.4120),
        ("Campos Elíseos", "32472", 31.7230, -106.4110),
        ("Fuentes del Valle", "32500", 31.6980, -106.4180),
        ("Villahermosa", "32510", 31.7080, -106.4050),
        ("Hacienda de San Pedro", "32520", 31.7020, -106.3980),
        ("Partido Senecu", "32545", 31.7150, -106.4000),
        ("Valle del Sol", "32546", 31.7050, -106.4020),
        ("Jardines de San Patricio", "32546", 31.6930, -106.3850),
        ("Ciudad Río Bravo", "32550", 31.6890, -106.3750),
        ("Waterfill Río Bravo", "32553", 31.6870, -106.3650),
        ("Zaragoza", "32560", 31.6890, -106.3870),
        ("Senderos de San Isidro", None, 31.6790, -106.3700),
        ("Misión de los Lagos", None, 31.7210, -106.4180),
        ("Oasis Revolución", None, 31.7120, -106.3950),
    ],
    "SURORIENTE": [
        ("Las Flores", "32560", 31.6850, -106.3800),
        ("San Pablo", "32560", 31.6800, -106.3600),
        ("Jardines del Valle", "32563", 31.6760, -106.3750),
        ("Morelos I", "32573", 31.6620, -106.3920),
        ("Prados de Salvárcar", "32573", 31.6600, -106.3800),
        ("Carlos Castillo Peraza", "32575", 31.6400, -106.3900),
        ("Manuel J. Clouthier", "32575", 31.6450, -106.3960),
        ("Terranova", "32576", 31.6350, -106.4000),
        ("Salvárcar", "32580", 31.6550, -106.3650),
        ("Lucio Blanco", "32583", 31.6600, -106.3500),
        ("Buenos Aires", "32590", 31.6700, -106.3500),
        ("Águilas de Zaragoza", "32599", 31.6650, -106.3400),
        ("Parajes del Sur", None, 31.6340, -106.3920),
        ("Riberas del Bravo", None, 31.6350, -106.3500),
        ("Villas de Salvárcar", None, 31.6420, -106.3650),
        ("Lote Bravo", None, 31.6270, -106.3800),
        ("Parajes de San Isidro", None, 31.6190, -106.3550),
        ("Tierra Nueva", None, 31.6040, -106.3700),
        ("San Lorenzo", None, 31.6130, -106.3330),
        ("Praderas del Sur", None, 31.6250, -106.3980),
        ("Ejido Salvárcar", None, 31.6480, -106.3400),
    ],
    "SURPONIENTE": [
        ("Campestre", "32460", 31.6650, -106.4300),
        ("Infonavit Mil Cumbres", "32600", 31.6900, -106.4560),
        ("Floresta", "32617", 31.6850, -106.4520),
        ("Acacias", "32630", 31.6800, -106.4620),
        ("México 68", "32640", 31.6750, -106.4750),
        ("Andrés Figueroa", "32650", 31.6700, -106.4800),
        ("Del Real", "32660", 31.6600, -106.4720),
        ("1 de Mayo", "32670", 31.6620, -106.4560),
        ("Ciudad Moderna", "32670", 31.6580, -106.4610),
        ("Colinas de Juárez", "32680", 31.6560, -106.4440),
        ("Lomas de San José", "32680", 31.6500, -106.4700),
        ("Aeropuerto", "32690", 31.6380, -106.4300),
        ("Kilómetro 20", "32695", 31.6200, -106.4500),
        ("15 de Enero", "32696", 31.6300, -106.4880),
        ("Sierra Vista", None, 31.6700, -106.4500),
        ("Lomas del Rey", None, 31.6600, -106.4680),
        ("Cerradas de Cumbres", None, 31.6480, -106.4600),
        ("Torres del Sur", None, 31.6420, -106.4300),
        ("Real del Sur", None, 31.6380, -106.4170),
    ],
}

# Vista plana (clave de sector, nombre, código postal, latitud, longitud).
COLONIAS = [
    (clave, nombre, cp, lat, lon) for clave, filas in COLONIAS_POR_SECTOR.items() for nombre, cp, lat, lon in filas
]

CALLES = [
    "Av. Tecnológico", "Av. de las Torres", "Av. Ejército Nacional", "Av. 16 de Septiembre",
    "Blvd. Independencia", "Av. Manuel J. Clouthier", "Av. Plutarco Elías Calles", "Av. Hermanos Escobar",
    "Blvd. Gómez Morín", "Av. Paseo Triunfo de la República", "Calle Mariscal", "Av. Juárez",
    "Av. Vicente Guerrero", "Blvd. Zaragoza", "Av. Rafael Pérez Serna", "Av. Ramón Rayón",
    "Av. de la Raza", "Av. Teófilo Borunda", "Av. Waterfill", "Av. Jilotepec",
    "Av. Heroico Colegio Militar", "Av. López Mateos", "Blvd. Juan Pablo II", "Av. Valentín Fuentes",
    "Av. Insurgentes", "Calle Ignacio Mejía", "Av. Lerdo", "Av. Abraham Lincoln",
    "Av. Miguel de la Madrid", "Av. Ricardo Flores Magón",
]

NOMBRES = [
    "María Fernanda López", "José Luis Carrasco", "Ana Lucía Ramírez", "Carlos Eduardo Ortega",
    "Gabriela Contreras", "Luis Ángel Mendoza", "Daniela Villalobos", "Jorge Alberto Chávez",
    "Patricia Domínguez", "Ricardo Salazar", "Alejandra Reyes", "Miguel Ángel Holguín",
]

MOTIVOS_RECHAZO = [
    "La ubicación corresponde a una obra en proceso ya señalizada por el municipio.",
    "El reporte duplica otro ya registrado en el mismo punto; se pidió confirmar el existente.",
    "La fotografía y la descripción no corresponden a un daño en la vía pública.",
    "El punto señalado está dentro de un predio privado, fuera de la vía pública.",
]

# RNF-09: ≥ 500 reportes públicos (los «Rechazado» no cuentan). Con las proporciones de destino de
# Generador (≈ 8 % de pavimento y ≈ 4 % de encharcamientos rechazados) quedan ≈ 540 visibles.
N_PAVIMENTO = 420
N_ENCHARCAMIENTOS = 160
PESO_MES_PAVIMENTO = [3, 3, 3, 3, 4, 4, 5, 5, 5, 4, 3]  # enero–noviembre
PESO_MES_LLUVIA = [1, 1, 1, 1, 2, 3, 10, 14, 10, 4, 2]  # temporada de lluvias: jul–sep


# --------------------------------------------------------------------------- catálogos y usuarios


# Valores que aparecieron en el repositorio o en su documentación: cualquiera puede conocerlos.
CONTRASENAS_PUBLICADAS = {"juarez2026", "cambiaresto2026", "elijeuna2026", "pruebasci2026", "prueba2026"}


def sembrar_usuarios(db) -> dict[str, list[Usuario]]:
    contrasena = os.environ.get("SEED_PASSWORD", "").strip()
    if not contrasena:
        # Sin valor por omisión en el código (OWASP A02): la contraseña aleatoria no se muestra ni se registra.
        log.warning(
            "SEED_PASSWORD no está definida: las cuentas de prueba nuevas reciben una contraseña aleatoria "
            "no revelada. Defínela en .env (ver .env.example) para poder iniciar sesión con ellas."
        )
        contrasena = f"{secrets.token_urlsafe(24)}a1"
    elif not contrasena_valida(contrasena):
        raise SystemExit(f"SEED_PASSWORD no cumple la política de contraseñas: {MENSAJE_CONTRASENA}")
    elif os.environ.get("APP_ENV", "").lower() == "production" and (
        contrasena.lower() in CONTRASENAS_PUBLICADAS or len(contrasena) < 12
    ):
        raise SystemExit(
            "SEED_PASSWORD es un valor de ejemplo publicado o tiene menos de 12 caracteres: no se usa en producción. "
            "Genera una con `python -c \"import secrets; print(secrets.token_urlsafe(18) + 'a1')\"`."
        )
    hash_comun = hashear_contrasena(contrasena)
    definiciones = [
        ("Coordinación Calles Seguras", "coordinador@ejemplo.mx", RolUsuario.COORDINADOR),
        ("Moderación Uno", "moderador@ejemplo.mx", RolUsuario.MODERADOR),
        ("Moderación Dos", "moderador2@ejemplo.mx", RolUsuario.MODERADOR),
        # HU-05.5: cuenta de prueba del rol enlace municipal (vinculada a dos cuadrillas en sembrar_operacion).
        ("Enlace Municipal de Prueba", "enlace@ejemplo.mx", RolUsuario.ENLACE_MUNICIPAL),
    ] + [
        (NOMBRES[i % len(NOMBRES)], f"ciudadano{i + 1:02d}@ejemplo.mx", RolUsuario.CIUDADANO) for i in range(12)
    ]
    creados = 0
    for nombre, correo, rol in definiciones:
        if db.scalar(select(Usuario.id).where(Usuario.correo == correo)) is None:
            db.add(Usuario(nombre=nombre, correo=correo, password_hash=hash_comun, rol=rol))
            creados += 1
    db.commit()
    por_rol: dict[str, list[Usuario]] = {r.value: [] for r in RolUsuario}
    for u in db.scalars(select(Usuario).where(Usuario.correo.like("%@ejemplo.mx")).order_by(Usuario.correo)):
        por_rol[u.rol.value].append(u)
    log.info("Usuarios de prueba: %s nuevos (%s en total)", creados, sum(len(v) for v in por_rol.values()))
    return por_rol


def sembrar_territorio(db) -> list[Colonia]:
    for clave, nombre in SECTORES:
        if db.scalar(select(Sector.id).where(Sector.clave == clave)) is None:
            db.add(Sector(clave=clave, nombre=nombre))
    db.commit()
    sectores = {s.clave: s for s in db.scalars(select(Sector))}
    nuevas = actualizadas = 0
    for clave, nombre, cp, lat, lon in COLONIAS:
        # Se identifica por nombre (sin distinguir mayúsculas) en cualquier sector: si el coordinador ya la
        # movió de sector o la editó, la semilla no la duplica ni pisa sus datos, sólo completa el código postal.
        existente = db.scalar(select(Colonia).where(func.lower(Colonia.nombre) == nombre.lower()).limit(1))
        if existente is None:
            db.add(
                Colonia(
                    sector_id=sectores[clave].id, nombre=nombre, codigo_postal=cp,
                    latitud_centro=lat, longitud_centro=lon,
                )
            )
            nuevas += 1
        elif cp is not None and existente.codigo_postal != cp:
            existente.codigo_postal = cp
            actualizadas += 1
    db.commit()
    colonias = list(db.scalars(select(Colonia).where(Colonia.activo).order_by(Colonia.id)))
    log.info(
        "Territorio: %s sectores, %s colonias activas (%s nuevas, %s con código postal actualizado)",
        len(sectores), len(colonias), nuevas, actualizadas,
    )
    return colonias


# --------------------------------------------------------------------------- generación de reportes


class Generador:
    def __init__(self, db, rng: random.Random, colonias: list[Colonia], por_rol: dict[str, list[Usuario]]) -> None:
        self.db = db
        self.rng = rng
        self.colonias = colonias
        self.ciudadanos = por_rol[RolUsuario.CIUDADANO.value]
        self.moderadores = por_rol[RolUsuario.MODERADOR.value]
        self.coordinadores = por_rol[RolUsuario.COORDINADOR.value]
        self.ahora = ahora_utc()

    # -- utilidades
    def punto(self, colonia: Colonia) -> tuple[float, float]:
        lat = colonia.latitud_centro + self.rng.uniform(-0.004, 0.004)
        lon = colonia.longitud_centro + self.rng.uniform(-0.004, 0.004)
        return (
            round(min(max(lat, geo.LAT_MIN + 0.001), geo.LAT_MAX - 0.001), 6),
            round(min(max(lon, geo.LON_MIN + 0.001), geo.LON_MAX - 0.001), 6),
        )

    def fecha_en_mes(self, pesos: list[int], maximo: datetime) -> datetime:
        """Fecha aleatoria de 2026 (ponderada por mes) no posterior a `maximo`."""
        for _ in range(200):
            mes = self.rng.choices(range(1, len(pesos) + 1), weights=pesos)[0]
            candidata = datetime(2026, mes, self.rng.randint(1, 28), self.rng.randint(6, 22), self.rng.randint(0, 59), tzinfo=self.ahora.tzinfo)
            if candidata <= maximo:
                return candidata
        return maximo - timedelta(hours=1)

    def actor_moderacion(self, solo_moderador: bool) -> Usuario:
        pool = self.moderadores if solo_moderador else self.moderadores + self.coordinadores
        return self.rng.choice(pool)

    def paso(self, reporte: Reporte, actor: Usuario | None, origen: OrigenCambio, cuando: datetime, motivo: str | None = None) -> None:
        fijar_contexto(self.db, usuario_id=actor.id if actor else None, origen=origen, motivo=motivo, fecha_evento=cuando)

    def nuevo(self, autor: Usuario, tipo: TipoDano, creado: datetime, **campos) -> Reporte:
        colonia = self.rng.choice(self.colonias)
        lat, lon = self.punto(colonia)
        es_enc = tipo == TipoDano.ENCHARCAMIENTO
        reporte = Reporte(
            folio=generar_folio(self.db, tipo, creado),
            tipo_dano=tipo,
            estado=EstadoReporte.ACTIVO if es_enc else EstadoReporte.RECIBIDO,
            usuario_id=autor.id,
            colonia=colonia,
            latitud=lat,
            longitud=lon,
            calle=self.rng.choice(CALLES),
            created_at=creado,
            updated_at=creado,
            ciclo_vigencia=0,
            vigencia_inicio=creado if es_enc else None,
            vigente_hasta=creado + VIGENCIA if es_enc else None,
            forzado_como_nuevo=self.rng.random() < 0.05,
            **campos,
        )
        self.paso(reporte, autor, OrigenCambio.CIUDADANO, creado)
        self.db.add(reporte)
        self.db.flush()
        return reporte

    def confirmar(self, reporte: Reporte, usuario: Usuario, tipo: TipoConfirmacion, cuando: datetime) -> None:
        self.db.add(
            ConfirmacionReporte(
                reporte_id=reporte.id, usuario_id=usuario.id, tipo=tipo,
                ciclo_vigencia=reporte.ciclo_vigencia, created_at=cuando,
            )
        )
        self.db.flush()

    def otros_ciudadanos(self, autor: Usuario, n: int) -> list[Usuario]:
        candidatos = [u for u in self.ciudadanos if u.id != autor.id]
        return self.rng.sample(candidatos, min(n, len(candidatos)))

    # -- pavimento
    def pavimento(self, indice: int) -> None:
        rng = self.rng
        destino = rng.choices(
            ["Recibido", "Validado", "Programado", "En reparación", "Reparado", "Rechazado"],
            weights=[12, 14, 12, 8, 46, 8],
        )[0]
        pasos: list[tuple[EstadoReporte, float]] = []  # (estado, horas desde el paso anterior)
        if destino == "Rechazado":
            pasos = [(EstadoReporte.RECHAZADO, rng.uniform(2, 96))]
        elif destino != "Recibido":
            pasos = [(EstadoReporte.VALIDADO, rng.uniform(2, 72))]
            if destino in ("Programado",) or (destino in ("En reparación", "Reparado") and rng.random() < 0.55):
                pasos.append((EstadoReporte.PROGRAMADO, rng.uniform(24, 240)))
            if destino in ("En reparación", "Reparado"):
                pasos.append((EstadoReporte.EN_REPARACION, rng.uniform(24, 480)))
            if destino == "Reparado":
                pasos.append((EstadoReporte.REPARADO, rng.uniform(12, 240)))
            if destino == "Validado":
                pasos = pasos[:1]
        duracion = sum(h for _, h in pasos)
        if destino == "Recibido":
            creado = self.ahora - timedelta(hours=rng.uniform(0.5, 110))
        else:
            creado = self.fecha_en_mes(PESO_MES_PAVIMENTO, self.ahora - timedelta(hours=duracion + 2))

        autor = rng.choice(self.ciudadanos)
        tipo = rng.choices([TipoDano.BACHE, TipoDano.ALCANTARILLA], weights=[85, 15])[0]
        if tipo == TipoDano.BACHE:
            tamano = rng.choices(list(TamanoBache), weights=[35, 40, 25])[0]
            profundidad = rng.choices(list(ProfundidadBache), weights=[40, 40, 20])[0]
            campos = dict(
                severidad=severidad_bache(tamano, profundidad), tamano=tamano, profundidad=profundidad,
                carril_afectado=rng.choice(list(CarrilAfectado)),
                descripcion=rng.choice([None, "Bache que daña las llantas.", "Hundimiento del pavimento tras la lluvia.", "Se agranda cada semana."]),
            )
        else:
            campos = dict(
                severidad=Severidad.ALTA, esta_senalizado=rng.random() < 0.35,
                descripcion=rng.choice([None, "Registro abierto junto a la banqueta.", "Falta la tapa de la alcantarilla."]),
            )
        reporte = self.nuevo(autor, tipo, creado, **campos)

        if destino != "Rechazado":  # los reportes rechazados no acumulan confirmaciones
            limite = min(self.ahora, creado + timedelta(days=10))
            for votante in self.otros_ciudadanos(autor, rng.choice([0, 0, 1, 2, 3, 4, 6])):
                self.confirmar(
                    reporte, votante, TipoConfirmacion.CONFIRMACION_DANO,
                    creado + (limite - creado) * rng.random(),
                )

        momento = creado
        for estado, horas in pasos:
            momento = momento + timedelta(hours=horas)
            solo_mod = estado in (EstadoReporte.VALIDADO, EstadoReporte.RECHAZADO)
            actor = self.actor_moderacion(solo_mod)
            motivo = None
            if estado == EstadoReporte.RECHAZADO:
                reporte.motivo_rechazo = motivo = rng.choice(MOTIVOS_RECHAZO)
            if estado == EstadoReporte.PROGRAMADO:
                reporte.fecha_programada = a_local(momento).date() + timedelta(days=rng.randint(3, 30))
            if estado == EstadoReporte.REPARADO:
                reporte.fecha_reparacion = a_local(momento).date()
            self.paso(reporte, actor, OrigenCambio.MODERACION, momento, motivo)
            reporte.estado = estado
            self.db.flush()

    # -- encharcamientos
    def encharcamiento(self, indice: int) -> None:
        rng = self.rng
        destino = rng.choices(["Activo", "Vencido", "Desmentido", "Rechazado"], weights=[11, 62, 25, 4])[0]
        autor = rng.choice(self.ciudadanos)
        nivel = rng.choices(list(NivelAgua), weights=[30, 30, 25, 15])[0]
        riesgo = rng.random() < 0.7 if nivel == NivelAgua.INTRANSITABLE else None

        n_sigue = rng.choice([0, 0, 1, 1, 2, 3])
        if destino == "Rechazado":
            n_sigue = 0
        # Instantes (en horas desde la creación) de cada "Sigue ahí", siempre dentro de la vigencia previa.
        sigue: list[float] = []
        fin_vigencia = 6.0
        for _ in range(n_sigue):
            t = (sigue[-1] if sigue else 0.0) + rng.uniform(0.5, 5.0)
            sigue.append(t)
            fin_vigencia = t + 6.0
        inicio_ultima = sigue[-1] if sigue else 0.0

        if destino == "Activo":
            # Todo el recorrido cabe antes de ahora: la vigencia sigue abierta.
            edad_min = max(inicio_ultima + 0.1, rng.uniform(0.2, fin_vigencia - 0.3))
            creado = self.ahora - timedelta(hours=edad_min)
        else:
            extra_horas = 0.0
            if destino == "Vencido":
                extra_horas = fin_vigencia - inicio_ultima  # 6 h tras el último "Sigue ahí"
            elif destino == "Desmentido":
                extra_horas = 2.0
            elif destino == "Rechazado":
                extra_horas = rng.uniform(1, 4)
            creado = self.fecha_en_mes(PESO_MES_LLUVIA, self.ahora - timedelta(hours=inicio_ultima + extra_horas + 1))

        reporte = self.nuevo(
            autor,
            TipoDano.ENCHARCAMIENTO,
            creado,
            severidad=severidad_encharcamiento(nivel),
            nivel_agua=nivel,
            hay_riesgo_personas_vehiculos=riesgo,
            descripcion=rng.choice([None, None, "Se acumula agua cada vez que llueve.", "El agua cubre casi todo el carril."]),
        )

        ultimo_confirmador: Usuario | None = None
        for horas in sigue:  # "Sigue ahí": reinicia 6 h y abre una vigencia nueva
            cuando = creado + timedelta(hours=horas)
            reporte.ciclo_vigencia += 1
            reporte.vigencia_inicio = cuando
            reporte.vigente_hasta = cuando + VIGENCIA
            self.db.flush()
            ultimo_confirmador = rng.choice([u for u in self.ciudadanos if u.id != autor.id])
            self.confirmar(reporte, ultimo_confirmador, TipoConfirmacion.SIGUE_AHI, cuando)

        inicio = creado + timedelta(hours=inicio_ultima)
        if destino == "Vencido":
            self.paso(reporte, None, OrigenCambio.SISTEMA, reporte.vigente_hasta, MOTIVO_VENCIMIENTO)
            reporte.estado = EstadoReporte.HISTORICO
            self.db.flush()
        elif destino == "Desmentido":
            # Una confirmación por usuario y vigencia: quien dijo "Sigue ahí" en este ciclo no vuelve a votar.
            elegibles = [u for u in self.ciudadanos if u.id not in {autor.id, getattr(ultimo_confirmador, "id", None)}]
            votos = rng.sample(elegibles, 3)
            cuando = inicio
            for votante in votos:
                cuando += timedelta(minutes=rng.randint(10, 40))
                self.confirmar(reporte, votante, TipoConfirmacion.YA_NO_HAY_AGUA, cuando)
            self.paso(reporte, None, OrigenCambio.SISTEMA, cuando, MOTIVO_DESMENTIDO)
            reporte.estado = EstadoReporte.HISTORICO
            self.db.flush()
        elif destino == "Rechazado":
            cuando = creado + timedelta(hours=rng.uniform(0.5, 1.5))
            reporte.motivo_rechazo = "Reporte sin evidencia: el punto señalado no presenta acumulación de agua."
            self.paso(reporte, self.actor_moderacion(True), OrigenCambio.MODERACION, cuando, reporte.motivo_rechazo)
            reporte.estado = EstadoReporte.RECHAZADO
            self.db.flush()


def sembrar_reportes(db, colonias: list[Colonia], por_rol: dict[str, list[Usuario]]) -> None:
    """Completa la meta de reportes de demostración; si ya se alcanzó, no hace nada (idempotente)."""
    es_enc = Reporte.tipo_dano == TipoDano.ENCHARCAMIENTO
    pavimento = db.scalar(select(func.count()).select_from(Reporte).where(~es_enc)) or 0
    encharcamientos = db.scalar(select(func.count()).select_from(Reporte).where(es_enc)) or 0
    faltan_pav = max(0, N_PAVIMENTO - pavimento)
    faltan_enc = max(0, N_ENCHARCAMIENTOS - encharcamientos)
    if not faltan_pav and not faltan_enc:
        log.info("Ya existen %s reportes: no se vuelven a sembrar (idempotente).", pavimento + encharcamientos)
        return
    # Semilla distinta por punto de partida: una base vacía siempre produce el mismo conjunto.
    gen = Generador(db, random.Random(SEMILLA_ALEATORIA + pavimento + encharcamientos), colonias, por_rol)
    for i in range(faltan_pav):
        gen.pavimento(i)
    for i in range(faltan_enc):
        gen.encharcamiento(i)
    db.commit()
    por_estado = db.execute(select(Reporte.estado, func.count()).group_by(Reporte.estado).order_by(Reporte.estado)).all()
    log.info("Reportes sembrados: %s", ", ".join(f"{e.value}={n}" for e, n in por_estado))


# --------------------------------------------------------------------------- Fase 3: catálogos y cuadrillas

TIPOS_DANO_CATALOGO = [
    (TipoDano.BACHE, "Bache", "Hoyo o hundimiento en el pavimento."),
    (TipoDano.ALCANTARILLA, "Alcantarilla sin tapa", "Registro o pozo de visita sin tapa (severidad Alta fija)."),
    (TipoDano.ENCHARCAMIENTO, "Encharcamiento", "Agua acumulada en la calle."),
]
MOTIVOS_RECHAZO = [
    ("Duplicado", "Ya existe un reporte abierto del mismo daño (se usa al fusionar)."),
    ("Fuera de la vía pública", "El daño está en propiedad privada o fuera de la calle."),
    ("Información insuficiente", "La ubicación o la descripción no permiten identificar el daño."),
    ("No corresponde a un daño", "Lo reportado no es un bache, alcantarilla sin tapa ni encharcamiento."),
    ("Contenido inapropiado", "El reporte contiene lenguaje ofensivo o datos personales."),
    ("Ya fue reparado", "Al revisar el punto, el daño ya estaba reparado."),
    ("Fuera de Ciudad Juárez", "El punto no pertenece al municipio de Juárez."),
]
# Datos ficticios: no corresponden a cuadrillas ni teléfonos reales del municipio.
CUADRILLAS = [
    ("Cuadrilla Norte · Bacheo", "Jefatura de cuadrilla Norte", "656 000 0101"),
    ("Cuadrilla Sur · Bacheo", "Jefatura de cuadrilla Sur", "656 000 0102"),
    ("Cuadrilla Centro · Alcantarillas", "Jefatura de cuadrilla Centro", "656 000 0103"),
]
ASIGNACIONES_DE_EJEMPLO = 8


def sembrar_operacion(db, por_rol: dict[str, list[Usuario]]) -> None:
    """HU-06.3, HU-05.4 y HU-05.5. Idempotente: sólo agrega lo que falta y nunca pisa cambios de coordinación."""
    for clave, nombre, descripcion in TIPOS_DANO_CATALOGO:
        if db.scalar(select(CatalogoTipoDano.id).where(CatalogoTipoDano.clave == clave)) is None:
            db.add(CatalogoTipoDano(clave=clave, nombre=nombre, descripcion=descripcion))
    for nombre, descripcion in MOTIVOS_RECHAZO:
        if db.scalar(select(CatalogoMotivoRechazo.id).where(func.lower(CatalogoMotivoRechazo.nombre) == nombre.lower())) is None:
            db.add(CatalogoMotivoRechazo(nombre=nombre, descripcion=descripcion))
    for nombre, responsable, telefono in CUADRILLAS:
        if db.scalar(select(Cuadrilla.id).where(func.lower(Cuadrilla.nombre) == nombre.lower())) is None:
            db.add(Cuadrilla(nombre=nombre, responsable=responsable, telefono_contacto=telefono))
    db.commit()

    cuadrillas = [db.scalar(select(Cuadrilla).where(func.lower(Cuadrilla.nombre) == n.lower())) for n, _, _ in CUADRILLAS]
    enlaces = por_rol.get(RolUsuario.ENLACE_MUNICIPAL.value, [])
    for enlace in enlaces:
        for cuadrilla in cuadrillas[:2]:  # el enlace de prueba ve Norte y Sur, nunca Centro
            if db.get(UsuarioCuadrilla, (enlace.id, cuadrilla.id)) is None:
                db.add(UsuarioCuadrilla(usuario_id=enlace.id, cuadrilla_id=cuadrilla.id))
    db.commit()

    coordinador = (por_rol.get(RolUsuario.COORDINADOR.value) or [None])[0]
    ya_hay = db.scalar(select(func.count()).select_from(AsignacionCuadrilla)) or 0
    if coordinador is not None and ya_hay == 0:
        pendientes = db.scalars(
            select(Reporte)
            .where(
                Reporte.estado.in_([EstadoReporte.PROGRAMADO, EstadoReporte.EN_REPARACION]),
                ~select(AsignacionCuadrilla.id).where(AsignacionCuadrilla.reporte_id == Reporte.id, AsignacionCuadrilla.activa).exists(),
            )
            .order_by(Reporte.id)
            .limit(ASIGNACIONES_DE_EJEMPLO)
        ).all()
        for i, reporte in enumerate(pendientes):
            fecha = reporte.fecha_programada or (a_local(reporte.created_at).date() + timedelta(days=3))
            db.add(AsignacionCuadrilla(
                reporte_id=reporte.id, cuadrilla_id=cuadrillas[i % 3].id,
                fecha_programada=fecha, asignado_por_id=coordinador.id,
            ))
        db.commit()
    log.info(
        "Operación: %s tipos de daño, %s motivos de rechazo, %s cuadrillas, %s asignaciones",
        db.scalar(select(func.count()).select_from(CatalogoTipoDano)),
        db.scalar(select(func.count()).select_from(CatalogoMotivoRechazo)),
        db.scalar(select(func.count()).select_from(Cuadrilla)),
        db.scalar(select(func.count()).select_from(AsignacionCuadrilla)),
    )


def main() -> None:
    with SessionLocal() as db:
        por_rol = sembrar_usuarios(db)
        colonias = sembrar_territorio(db)
        sembrar_reportes(db, colonias, por_rol)
        sembrar_operacion(db, por_rol)
    log.info("Semilla lista. Cuentas: coordinador@ejemplo.mx, moderador@ejemplo.mx, enlace@ejemplo.mx, ciudadano01@ejemplo.mx…")


if __name__ == "__main__":
    main()
