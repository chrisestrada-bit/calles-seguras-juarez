"""Quita metadatos (EXIF/GPS/XMP, comentarios, datos tras el fin de imagen) de fotos subidas antes de la
corrección A3 de la auditoría final (docs/auditoria-final/03-hallazgos.md).

Idempotente: una foto ya limpia queda igual. Actualiza `tamano_bytes` en `reporte_fotos`. No borra nada: si un
archivo tiene estructura inválida sólo se informa.

Uso:  python db/limpiar_fotos.py            (aplica)
      python db/limpiar_fotos.py --simular  (sólo informa)
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import select  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.models import ReporteFoto  # noqa: E402
from app.services.fotos import directorio_fotos  # noqa: E402
from app.services.imagenes import ImagenInvalida, limpiar_metadatos  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")
log = logging.getLogger("limpiar_fotos")


def main(simular: bool) -> None:
    carpeta = directorio_fotos().resolve()
    limpias = cambiadas = invalidas = ausentes = 0
    with SessionLocal() as db:
        for foto in db.scalars(select(ReporteFoto)):
            ruta = (carpeta / foto.ruta_almacenamiento).resolve()
            if carpeta not in ruta.parents or not ruta.is_file():
                ausentes += 1
                continue
            original = ruta.read_bytes()
            try:
                limpia = limpiar_metadatos(original, foto.mime_type)
            except ImagenInvalida:
                invalidas += 1
                log.warning("Estructura inválida, se deja sin cambios: foto %s", foto.id)
                continue
            if limpia == original:
                limpias += 1
                continue
            cambiadas += 1
            if not simular:
                temporal = ruta.with_suffix(ruta.suffix + ".tmp")
                temporal.write_bytes(limpia)
                temporal.replace(ruta)  # reemplazo atómico
                foto.tamano_bytes = len(limpia)
        if not simular:
            db.commit()
    accion = "se limpiarían" if simular else "limpiadas"
    log.info("Fotos ya limpias: %s · %s: %s · inválidas: %s · ausentes en disco: %s", limpias, accion, cambiadas, invalidas, ausentes)


if __name__ == "__main__":
    main(simular="--simular" in sys.argv)
