"""Evidencia fotográfica (HU-02.4): validación por contenido real, almacenamiento y control de acceso."""

import logging
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errores import ErrorAPI
from app.models import ConfirmacionReporte, EstadoReporte, ReporteFoto, Reporte, RolUsuario, Usuario

logger = logging.getLogger("calles_seguras")

MAX_FOTOS_POR_PERSONA = 3
MAX_BYTES = 5 * 1024 * 1024  # 5 MB exactos: 5 MB se acepta, 5 MB + 1 byte se rechaza
_FIRMA_JPEG = b"\xff\xd8\xff"
_FIRMA_PNG = b"\x89PNG\r\n\x1a\n"
_EXTENSION = {"image/jpeg": ".jpg", "image/png": ".png"}


@dataclass
class FotoRechazada:
    nombre: str
    motivo: str


def tipo_por_contenido(contenido: bytes) -> str | None:
    """Detecta JPEG/PNG por su encabezado binario; ignora extensión y Content-Type del cliente."""
    if contenido.startswith(_FIRMA_JPEG):
        return "image/jpeg"
    if contenido.startswith(_FIRMA_PNG):
        return "image/png"
    return None


def directorio_fotos() -> Path:
    ruta = Path(get_settings().uploads_dir)
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def _nombre_seguro(nombre: str | None) -> str:
    base = os.path.basename((nombre or "foto").replace("\\", "/")).strip() or "foto"
    base = "".join(c for c in base if c.isprintable() and c not in '<>"')
    return base[:150] or "foto"


def validar_archivo(nombre: str | None, flujo: BinaryIO) -> tuple[bytes, str] | FotoRechazada:
    """Devuelve (contenido, mime) o el motivo de rechazo en español."""
    etiqueta = _nombre_seguro(nombre)
    contenido = flujo.read(MAX_BYTES + 1)
    if len(contenido) == 0:
        return FotoRechazada(etiqueta, "El archivo está vacío.")
    if len(contenido) > MAX_BYTES:
        return FotoRechazada(etiqueta, "La imagen supera el tamaño máximo de 5 MB.")
    mime = tipo_por_contenido(contenido)
    if mime is None:
        return FotoRechazada(etiqueta, "Formato no permitido: sólo se aceptan imágenes JPG o PNG.")
    return contenido, mime


def puede_subir(db: Session, reporte: Reporte, usuario: Usuario) -> bool:
    """Autor del reporte o persona que lo confirmó (HU-02.3)."""
    if reporte.usuario_id == usuario.id:
        return True
    return (
        db.scalar(
            select(func.count()).where(
                ConfirmacionReporte.reporte_id == reporte.id, ConfirmacionReporte.usuario_id == usuario.id
            )
        )
        or 0
    ) > 0


def contar_de_usuario(db: Session, reporte: Reporte, usuario: Usuario) -> int:
    return (
        db.scalar(
            select(func.count()).where(ReporteFoto.reporte_id == reporte.id, ReporteFoto.usuario_id == usuario.id)
        )
        or 0
    )


def agregar_fotos(
    db: Session, reporte: Reporte, usuario: Usuario, archivos: list[tuple[str | None, BinaryIO]]
) -> tuple[list[ReporteFoto], list[FotoRechazada]]:
    """Guarda las imágenes válidas y rechaza las inválidas sin afectar a las demás ni al reporte."""
    if reporte.estado == EstadoReporte.RECHAZADO:
        raise ErrorAPI(409, "REPORTE_NO_ACEPTA_FOTOS", "Un reporte rechazado ya no admite fotografías.")
    if not puede_subir(db, reporte, usuario):
        raise ErrorAPI(
            403, "SIN_PERMISO", "Sólo quien creó o confirmó el reporte puede adjuntar fotografías."
        )
    # El candado de fila evita que dos solicitudes simultáneas superen el límite de 3.
    db.execute(select(Reporte.id).where(Reporte.id == reporte.id).with_for_update())
    disponibles = MAX_FOTOS_POR_PERSONA - contar_de_usuario(db, reporte, usuario)

    guardadas: list[ReporteFoto] = []
    rechazadas: list[FotoRechazada] = []
    rutas_escritas: list[Path] = []
    carpeta = directorio_fotos()
    for nombre, flujo in archivos:
        if disponibles <= 0:
            rechazadas.append(
                FotoRechazada(_nombre_seguro(nombre), "Se alcanzó el límite de 3 fotografías por reporte.")
            )
            continue
        resultado = validar_archivo(nombre, flujo)
        if isinstance(resultado, FotoRechazada):
            rechazadas.append(resultado)
            continue
        contenido, mime = resultado
        archivo = f"{uuid.uuid4()}{_EXTENSION[mime]}"  # nombre impredecible (UUIDv4)
        destino = carpeta / archivo
        destino.write_bytes(contenido)
        rutas_escritas.append(destino)
        foto = ReporteFoto(
            reporte_id=reporte.id,
            usuario_id=usuario.id,
            ruta_almacenamiento=archivo,
            nombre_original=_nombre_seguro(nombre),
            mime_type=mime,
            tamano_bytes=len(contenido),
        )
        db.add(foto)
        guardadas.append(foto)
        disponibles -= 1
    try:
        db.commit()
    except Exception:
        db.rollback()
        for ruta in rutas_escritas:  # no dejar archivos huérfanos
            ruta.unlink(missing_ok=True)
        raise
    for foto in guardadas:
        db.refresh(foto)
    return guardadas, rechazadas


def autorizado_a_ver(reporte: Reporte, usuario: Usuario | None) -> bool:
    """Visible para autor, moderador y coordinador siempre; para el público sólo tras salir de «Recibido»."""
    if usuario is not None and (
        usuario.id == reporte.usuario_id or usuario.rol in (RolUsuario.MODERADOR, RolUsuario.COORDINADOR)
    ):
        return True
    return reporte.estado not in (EstadoReporte.RECIBIDO, EstadoReporte.RECHAZADO)


def exigir_acceso(reporte: Reporte, usuario: Usuario | None) -> None:
    if autorizado_a_ver(reporte, usuario):
        return
    if reporte.estado == EstadoReporte.RECHAZADO:  # RN-09: un rechazado no revela su existencia
        raise ErrorAPI(404, "NO_ENCONTRADO", f"No existe un reporte con el folio {reporte.folio}.")
    raise ErrorAPI(
        403,
        "FOTO_NO_DISPONIBLE",
        "Las fotografías se publican cuando el reporte es validado por moderación.",
    )


def listar(db: Session, reporte: Reporte) -> list[ReporteFoto]:
    return list(
        db.scalars(
            select(ReporteFoto).where(ReporteFoto.reporte_id == reporte.id).order_by(ReporteFoto.created_at, ReporteFoto.id)
        )
    )


def obtener(db: Session, reporte: Reporte, foto_id: uuid.UUID) -> ReporteFoto:
    foto = db.scalar(select(ReporteFoto).where(ReporteFoto.id == foto_id, ReporteFoto.reporte_id == reporte.id))
    if foto is None:
        raise ErrorAPI(404, "NO_ENCONTRADO", "La fotografía no existe.")
    return foto


def ruta_de(foto: ReporteFoto) -> Path:
    ruta = (directorio_fotos() / foto.ruta_almacenamiento).resolve()
    if directorio_fotos().resolve() not in ruta.parents:  # defensa contra recorrido de directorios
        raise ErrorAPI(404, "NO_ENCONTRADO", "La fotografía no existe.")
    if not ruta.is_file():
        logger.error("Archivo de foto ausente en disco: %s", foto.id)
        raise ErrorAPI(404, "NO_ENCONTRADO", "La fotografía no está disponible.")
    return ruta
