"""Datos semilla idempotentes para Calles Seguras Juárez.

Crea usuarios de prueba (ciudadano, moderador, coordinador), sectores y colonias de Ciudad Juárez y un
volumen realista de reportes históricos y activos distribuidos en distintos estados y colonias.

* Idempotente: usuarios, sectores y colonias se insertan sólo si faltan; los reportes se generan una
  única vez (si ya existe algún reporte, no se vuelve a sembrar).
* Reproducible: el generador aleatorio usa una semilla fija.
* Pasa por los mismos triggers que la aplicación: el historial de estados y los folios (RN-03) los
  genera la base de datos, y las transiciones respetan RN-05 y RN-06.
* La contraseña de las cuentas de prueba sale de SEED_PASSWORD (ver .env.example).
* Las coordenadas y códigos postales de las colonias son aproximados (datos de demostración).

Uso:  python db/seed.py
"""

import logging
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import func, select  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import hashear_contrasena  # noqa: E402
from app.core.tiempo import a_local, ahora_utc  # noqa: E402
from app.models import (  # noqa: E402
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
CONTRASENA_POR_OMISION = "Juarez2026"  # sólo cuentas de prueba locales; cámbiala con SEED_PASSWORD

SECTORES = [
    ("NORPONIENTE", "Norponiente"),
    ("NORORIENTE", "Nororiente"),
    ("CENTRO", "Centro"),
    ("PONIENTE", "Poniente"),
    ("SURORIENTE", "Suroriente"),
    ("SURPONIENTE", "Surponiente"),
]

# (clave de sector, nombre, código postal aproximado, latitud, longitud)
COLONIAS = [
    ("NORPONIENTE", "Anapra", "32100", 31.7868, -106.5470),
    ("NORPONIENTE", "Lomas de Poleo", "32100", 31.7925, -106.5620),
    ("NORPONIENTE", "Felipe Ángeles", "32090", 31.7443, -106.5012),
    ("NORPONIENTE", "Mariano Escobedo", None, 31.7480, -106.5120),
    ("NORPONIENTE", "Plutarco Elías Calles", None, 31.7340, -106.5030),
    ("NORPONIENTE", "Azteca", None, 31.7270, -106.5100),
    ("NORORIENTE", "Fuentes del Valle", "32500", 31.6980, -106.4180),
    ("NORORIENTE", "Zaragoza", "32580", 31.6890, -106.3870),
    ("NORORIENTE", "Senderos de San Isidro", None, 31.6790, -106.3700),
    ("NORORIENTE", "Valle del Sol", "32540", 31.7050, -106.4020),
    ("NORORIENTE", "Misión de los Lagos", None, 31.7210, -106.4180),
    ("NORORIENTE", "Oasis Revolución", None, 31.7120, -106.3950),
    ("CENTRO", "Centro", "32000", 31.7390, -106.4870),
    ("CENTRO", "Chamizal", "32310", 31.7560, -106.4590),
    ("CENTRO", "Pronaf", "32315", 31.7440, -106.4720),
    ("CENTRO", "Partido Romero", "32030", 31.7330, -106.4630),
    ("CENTRO", "Margaritas", None, 31.7270, -106.4510),
    ("CENTRO", "Hidalgo", None, 31.7350, -106.4780),
    ("CENTRO", "Bellavista", None, 31.7300, -106.4850),
    ("CENTRO", "Barrio Alto", None, 31.7450, -106.4930),
    ("CENTRO", "Altavista", None, 31.7220, -106.4900),
    ("PONIENTE", "Infonavit Casas Grandes", "32310", 31.7182, -106.4529),
    ("PONIENTE", "Los Nogales", None, 31.7090, -106.4720),
    ("PONIENTE", "Satélite", None, 31.7050, -106.4560),
    ("PONIENTE", "Hacienda de las Torres", None, 31.7160, -106.4380),
    ("PONIENTE", "Paseo de la Victoria", None, 31.7000, -106.4470),
    ("PONIENTE", "Villa Colonial", None, 31.7020, -106.4820),
    ("PONIENTE", "Mezquital", None, 31.6930, -106.4780),
    ("PONIENTE", "Morelos", None, 31.6900, -106.4660),
    ("PONIENTE", "Francisco Villa", None, 31.7110, -106.4940),
    ("SURORIENTE", "Parajes del Sur", "32575", 31.6340, -106.3920),
    ("SURORIENTE", "Riberas del Bravo", "32474", 31.6350, -106.3500),
    ("SURORIENTE", "Villas de Salvárcar", None, 31.6420, -106.3650),
    ("SURORIENTE", "Lote Bravo", None, 31.6270, -106.3800),
    ("SURORIENTE", "Parajes de San Isidro", None, 31.6190, -106.3550),
    ("SURORIENTE", "Tierra Nueva", None, 31.6040, -106.3700),
    ("SURORIENTE", "San Lorenzo", None, 31.6130, -106.3330),
    ("SURORIENTE", "Praderas del Sur", None, 31.6250, -106.3980),
    ("SURORIENTE", "Ejido Salvárcar", None, 31.6480, -106.3400),
    ("SURPONIENTE", "Sierra Vista", None, 31.6700, -106.4500),
    ("SURPONIENTE", "Colinas de Juárez", None, 31.6560, -106.4440),
    ("SURPONIENTE", "Lomas del Rey", None, 31.6600, -106.4680),
    ("SURPONIENTE", "Cerradas de Cumbres", None, 31.6480, -106.4600),
    ("SURPONIENTE", "Torres del Sur", None, 31.6420, -106.4300),
    ("SURPONIENTE", "Real del Sur", None, 31.6380, -106.4170),
    ("SURPONIENTE", "Campestre", None, 31.6650, -106.4300),
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

N_PAVIMENTO = 170
N_ENCHARCAMIENTOS = 55
PESO_MES_PAVIMENTO = [3, 3, 3, 3, 4, 4, 5, 5, 5, 4, 3]  # enero–noviembre
PESO_MES_LLUVIA = [1, 1, 1, 1, 2, 3, 10, 14, 10, 4, 2]  # temporada de lluvias: jul–sep


# --------------------------------------------------------------------------- catálogos y usuarios


def sembrar_usuarios(db) -> dict[str, list[Usuario]]:
    contrasena = os.environ.get("SEED_PASSWORD", CONTRASENA_POR_OMISION)
    hash_comun = hashear_contrasena(contrasena)
    definiciones = [
        ("Coordinación Calles Seguras", "coordinador@ejemplo.mx", RolUsuario.COORDINADOR),
        ("Moderación Uno", "moderador@ejemplo.mx", RolUsuario.MODERADOR),
        ("Moderación Dos", "moderador2@ejemplo.mx", RolUsuario.MODERADOR),
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
    nuevas = 0
    for clave, nombre, cp, lat, lon in COLONIAS:
        sector = sectores[clave]
        existe = db.scalar(select(Colonia.id).where(Colonia.sector_id == sector.id, Colonia.nombre == nombre))
        if existe is None:
            db.add(
                Colonia(sector_id=sector.id, nombre=nombre, codigo_postal=cp, latitud_centro=lat, longitud_centro=lon)
            )
            nuevas += 1
    db.commit()
    colonias = list(db.scalars(select(Colonia).order_by(Colonia.id)))
    log.info("Territorio: %s sectores, %s colonias (%s nuevas)", len(sectores), len(colonias), nuevas)
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
    if db.scalar(select(func.count()).select_from(Reporte)):
        log.info("Ya existen reportes: no se vuelven a sembrar (idempotente).")
        return
    gen = Generador(db, random.Random(SEMILLA_ALEATORIA), colonias, por_rol)
    for i in range(N_PAVIMENTO):
        gen.pavimento(i)
    for i in range(N_ENCHARCAMIENTOS):
        gen.encharcamiento(i)
    db.commit()
    por_estado = db.execute(select(Reporte.estado, func.count()).group_by(Reporte.estado).order_by(Reporte.estado)).all()
    log.info("Reportes sembrados: %s", ", ".join(f"{e.value}={n}" for e, n in por_estado))


def main() -> None:
    with SessionLocal() as db:
        por_rol = sembrar_usuarios(db)
        colonias = sembrar_territorio(db)
        sembrar_reportes(db, colonias, por_rol)
    log.info("Semilla lista. Cuentas: coordinador@ejemplo.mx, moderador@ejemplo.mx, ciudadano01@ejemplo.mx…")


if __name__ == "__main__":
    main()
