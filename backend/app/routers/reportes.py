from datetime import date
from typing import Annotated, Literal

import uuid

from fastapi import APIRouter, Depends, File, Path, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.dependencies import CUALQUIER_ROL, MODERACION, get_db, usuario_opcional
from app.core.errores import ErrorAPI
from app.models import EstadoReporte, TipoDano, Usuario
from app.schemas.comun import Latitud, Longitud, Pagina, ParametrosPagina, armar_pagina, respuestas
from app.schemas.fotos import FotoOut, FotoRechazadaOut, FotosSubidas, ListaFotos
from app.schemas.reportes import (
    CandidatoDuplicado,
    CercanosRespuesta,
    ConfirmacionIn,
    ConfirmacionOut,
    HistorialPublico,
    HistorialPublicoItem,
    MapaRespuesta,
    MarcadorMapa,
    MiReporte,
    ReporteCrear,
    ReporteEditar,
    ReportePublico,
    ReporteResumenPublico,
)
from app.services import confirmaciones, exportacion, fotos, presentacion, reportes
from app.services.vigencia import expirar_vencidos

router = APIRouter(prefix="/reportes", tags=["reportes"])

FolioPath = Annotated[
    str,
    Path(pattern=r"^(BCH|ENC)-[0-9]{4}-[0-9]{6}$", description="Folio público, p. ej. BCH-2026-000418."),
]


LIMITE_MAPA = 2000


class FiltrosReportes:
    """Filtros de consulta de HU-04.2, compartidos por la lista, el mapa y la exportación."""

    def __init__(
        self,
        tipo_dano: Annotated[list[TipoDano] | None, Query()] = None,
        estado: Annotated[list[EstadoReporte] | None, Query()] = None,
        solo_vigentes: bool = False,
        colonia_id: Annotated[int | None, Query(ge=1)] = None,
        sector_id: Annotated[int | None, Query(ge=1)] = None,
        calle: Annotated[str | None, Query(min_length=3, max_length=100)] = None,
        bbox: Annotated[str | None, Query(description="lon_min,lat_min,lon_max,lat_max")] = None,
        desde: date | None = None,
        hasta: date | None = None,
        orden: Literal["recientes", "longevidad", "severidad"] = "recientes",
    ) -> None:
        self.orden = orden
        self.filtros = {
            "tipos": tipo_dano,
            "estados": estado,
            "solo_vigentes": solo_vigentes,
            "colonia_id": colonia_id,
            "sector_id": sector_id,
            "calle": calle,
            "bbox": bbox,
            "desde": desde,
            "hasta": hasta,
        }


@router.get(
    "",
    response_model=Pagina[ReporteResumenPublico],
    summary="Lista pública de reportes (sin «Rechazado»)",
    responses=respuestas(422),
)
def listar(
    f: FiltrosReportes = Depends(),
    pag: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
) -> dict:
    expirar_vencidos(db)
    filas, total = reportes.listar_publicos(db, orden=f.orden, pag=pag, **f.filtros)
    conteos = presentacion.conteos_confirmaciones(db, filas)
    return armar_pagina([presentacion.a_resumen(r, conteos) for r in filas], total, pag)


@router.get(
    "/mapa",
    response_model=MapaRespuesta,
    summary="Reportes públicos con coordenadas para el mapa interactivo (HU-04.5)",
    description="Acepta exactamente los mismos filtros que `GET /reportes`. Devuelve hasta 2000 puntos, sin datos personales.",
    responses=respuestas(422),
)
def mapa(f: FiltrosReportes = Depends(), db: Session = Depends(get_db)) -> MapaRespuesta:
    expirar_vencidos(db)
    filas, total = reportes.listar_sin_paginar(db, orden=f.orden, limite=LIMITE_MAPA, **f.filtros)
    return MapaRespuesta(
        total=total,
        mostrados=len(filas),
        limite=LIMITE_MAPA,
        datos=[
            MarcadorMapa(
                folio=r.folio,
                tipo_dano=r.tipo_dano,
                estado=r.estado,
                etiqueta_publica=presentacion.etiqueta_publica(r),
                severidad=r.severidad,
                ubicacion={"latitud": r.latitud, "longitud": r.longitud},
                calle=r.calle,
                colonia={"id": r.colonia.id, "nombre": r.colonia.nombre},
                nivel_agua=r.nivel_agua.value if r.tipo_dano == TipoDano.ENCHARCAMIENTO and r.nivel_agua else None,
                created_at=r.created_at,
            )
            for r in filas
        ],
    )


def _exportar(f: FiltrosReportes, db: Session, formato: str) -> Response:
    expirar_vencidos(db)
    filas, total = reportes.listar_sin_paginar(db, orden=f.orden, limite=exportacion.LIMITE_EXPORTACION, **f.filtros)
    if formato == "csv":
        cuerpo, tipo = exportacion.generar_csv(filas), "text/csv; charset=utf-8"
    else:
        cuerpo, tipo = exportacion.generar_xml(filas), "application/xml; charset=utf-8"
    return Response(
        cuerpo,
        media_type=tipo,
        headers={
            "Content-Disposition": f'attachment; filename="reportes.{formato}"',
            "X-Total-Registros": str(total),
            "X-Registros-Exportados": str(len(filas)),
            "Cache-Control": "no-store",
        },
    )


@router.get(
    "/exportar/csv",
    summary="Exportar reportes a CSV para hoja de cálculo (moderación y coordinación)",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}, **respuestas(401, 403, 422)},
)
def exportar_csv(
    f: FiltrosReportes = Depends(),
    _: Usuario = Depends(MODERACION),
    db: Session = Depends(get_db),
) -> Response:
    return _exportar(f, db, "csv")


@router.get(
    "/exportar/xml",
    summary="Exportar reportes a XML validado con reportes_v1.xsd (moderación y coordinación)",
    response_class=Response,
    responses={200: {"content": {"application/xml": {}}}, **respuestas(401, 403, 422)},
)
def exportar_xml(
    f: FiltrosReportes = Depends(),
    _: Usuario = Depends(MODERACION),
    db: Session = Depends(get_db),
) -> Response:
    return _exportar(f, db, "xml")


@router.get(
    "/cercanos",
    response_model=CercanosRespuesta,
    summary="Duplicados cercanos antes de reportar (30 m pavimento / 50 m encharcamiento)",
    responses=respuestas(401, 422),
)
def cercanos(
    latitud: Annotated[Latitud, Query()],
    longitud: Annotated[Longitud, Query()],
    tipo_dano: Annotated[TipoDano, Query()],
    usuario: Usuario = Depends(CUALQUIER_ROL),
    db: Session = Depends(get_db),
) -> CercanosRespuesta:
    expirar_vencidos(db)
    encontrados = reportes.buscar_cercanos(db, tipo_dano, latitud, longitud)
    lista = [r for r, _ in encontrados]
    conteos = presentacion.conteos_confirmaciones(db, lista)
    mios = presentacion.confirmados_por_usuario(db, lista, usuario)
    return CercanosRespuesta(
        radio_metros=reportes.radio_duplicados(tipo_dano),
        candidatos=[
            CandidatoDuplicado(
                folio=r.folio,
                tipo_dano=r.tipo_dano,
                estado=r.estado,
                etiqueta_publica=presentacion.etiqueta_publica(r),
                severidad=r.severidad,
                calle=r.calle,
                distancia_metros=round(d, 1),
                confirmaciones=conteos.get(r.id, (0, 0))[0],
                ya_confirmado_por_mi=r.id in mios,
                es_mio=r.usuario_id == usuario.id,
                created_at=r.created_at,
            )
            for r, d in encontrados
        ],
    )


@router.post(
    "",
    response_model=ReportePublico,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un reporte (máx. 10 por hora por cuenta)",
    responses=respuestas(401, 409, 422, 429),
)
def crear(
    payload: ReporteCrear,
    response: Response,
    usuario: Usuario = Depends(CUALQUIER_ROL),
    db: Session = Depends(get_db),
) -> ReportePublico:
    expirar_vencidos(db)
    reporte = reportes.crear_reporte(db, usuario, payload)
    response.headers["Location"] = f"/api/v1/reportes/{reporte.folio}"
    conteos = presentacion.conteos_confirmaciones(db, [reporte])
    return presentacion.a_publico(reporte, conteos, usuario, set())


@router.get(
    "/mios",
    response_model=Pagina[MiReporte],
    summary="Mis reportes (incluye rechazados con su motivo)",
    responses=respuestas(401, 422),
)
def mios(
    estado: EstadoReporte | None = None,
    tipo_dano: TipoDano | None = None,
    pag: ParametrosPagina = Depends(),
    usuario: Usuario = Depends(CUALQUIER_ROL),
    db: Session = Depends(get_db),
) -> dict:
    expirar_vencidos(db)
    filas, total = reportes.listar_mios(db, usuario, estado=estado, tipo=tipo_dano, pag=pag)
    return armar_pagina([presentacion.a_mi_reporte(r) for r in filas], total, pag)


@router.get(
    "/{folio}",
    response_model=ReportePublico,
    summary="Detalle público de un reporte",
    responses=respuestas(404, 422),
)
def detalle(
    folio: FolioPath,
    usuario: Usuario | None = Depends(usuario_opcional),
    db: Session = Depends(get_db),
) -> ReportePublico:
    expirar_vencidos(db)
    reporte = reportes.obtener_visible(db, folio)
    conteos = presentacion.conteos_confirmaciones(db, [reporte])
    confirmados = presentacion.confirmados_por_usuario(db, [reporte], usuario)
    return presentacion.a_publico(reporte, conteos, usuario, confirmados)


@router.get(
    "/{folio}/historial",
    response_model=HistorialPublico,
    summary="Línea de tiempo pública de un reporte",
    responses=respuestas(404, 422),
)
def historial(folio: FolioPath, db: Session = Depends(get_db)) -> HistorialPublico:
    expirar_vencidos(db)
    reporte = reportes.obtener_visible(db, folio)
    return HistorialPublico(
        folio=reporte.folio,
        historial=[
            HistorialPublicoItem(
                estado_anterior=h.estado_anterior,
                estado_nuevo=h.estado_nuevo,
                origen=h.origen.value,
                fecha=h.created_at,
            )
            for h in reportes.historial_publico(db, reporte)
        ],
    )


@router.post(
    "/{folio}/confirmaciones",
    response_model=ConfirmacionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Confirmar un daño o indicar «Sigue ahí» / «Ya no hay agua»",
    responses=respuestas(400, 401, 404, 409, 422),
)
def confirmar(
    folio: FolioPath,
    datos: ConfirmacionIn,
    usuario: Usuario = Depends(CUALQUIER_ROL),
    db: Session = Depends(get_db),
) -> ConfirmacionOut:
    return confirmaciones.confirmar(db, folio, usuario, datos.tipo)


@router.patch(
    "/{folio}",
    response_model=ReportePublico,
    summary="Editar mi reporte mientras está «Recibido» (HU-02.5)",
    responses=respuestas(401, 403, 404, 409, 422),
)
def editar(
    folio: FolioPath,
    datos: ReporteEditar,
    usuario: Usuario = Depends(CUALQUIER_ROL),
    db: Session = Depends(get_db),
) -> ReportePublico:
    reporte = reportes.editar_reporte(db, usuario, folio, datos)
    conteos = presentacion.conteos_confirmaciones(db, [reporte])
    confirmados = presentacion.confirmados_por_usuario(db, [reporte], usuario)
    return presentacion.a_publico(reporte, conteos, usuario, confirmados)


def _foto_out(folio: str, f) -> FotoOut:
    return FotoOut(
        id=f.id,
        url=f"/api/v1/reportes/{folio}/fotos/{f.id}",
        nombre_original=f.nombre_original,
        mime_type=f.mime_type,
        tamano_bytes=f.tamano_bytes,
        created_at=f.created_at,
    )


@router.post(
    "/{folio}/fotos",
    response_model=FotosSubidas,
    status_code=status.HTTP_201_CREATED,
    summary="Adjuntar hasta 3 fotografías JPG/PNG de máx. 5 MB (HU-02.4)",
    description=(
        "Para la persona que creó o confirmó el reporte. Las imágenes válidas se guardan aunque otras sean "
        "rechazadas; el motivo de cada rechazo viene en `rechazadas`. Si ninguna es válida responde 422."
    ),
    responses=respuestas(401, 403, 404, 409, 422),
)
def subir_fotos(
    folio: FolioPath,
    archivos: Annotated[list[UploadFile], File(description="Imágenes JPG o PNG (máx. 3, 5 MB cada una).")],
    usuario: Usuario = Depends(CUALQUIER_ROL),
    db: Session = Depends(get_db),
) -> FotosSubidas:
    reporte = reportes.obtener_por_folio(db, folio)
    if reporte.usuario_id != usuario.id and reporte.estado == EstadoReporte.RECHAZADO:
        raise ErrorAPI(404, "NO_ENCONTRADO", f"No existe un reporte con el folio {folio}.")
    guardadas, rechazadas = fotos.agregar_fotos(db, reporte, usuario, [(a.filename, a.file) for a in archivos])
    if not guardadas:
        raise ErrorAPI(
            422,
            "FOTOS_INVALIDAS",
            "Ninguna fotografía cumple los requisitos. Usa imágenes JPG o PNG de máximo 5 MB.",
            [{"campo": r.nombre, "mensaje": r.motivo} for r in rechazadas],
        )
    return FotosSubidas(
        folio=folio,
        aceptadas=[_foto_out(folio, f) for f in guardadas],
        rechazadas=[FotoRechazadaOut(nombre=r.nombre, motivo=r.motivo) for r in rechazadas],
        mensaje=f"Se adjuntaron {len(guardadas)} fotografía(s)."
        + (f" {len(rechazadas)} no se pudieron adjuntar." if rechazadas else ""),
    )


@router.get(
    "/{folio}/fotos",
    response_model=ListaFotos,
    summary="Metadatos de las fotografías de un reporte",
    description="Mientras el reporte esté «Recibido» sólo lo ven su autor, moderación y coordinación (403 para el resto).",
    responses=respuestas(403, 404, 422),
)
def listar_fotos(
    folio: FolioPath,
    usuario: Usuario | None = Depends(usuario_opcional),
    db: Session = Depends(get_db),
) -> ListaFotos:
    reporte = reportes.obtener_por_folio(db, folio)
    fotos.exigir_acceso(reporte, usuario)
    return ListaFotos(
        folio=folio,
        maximo_por_persona=fotos.MAX_FOTOS_POR_PERSONA,
        datos=[_foto_out(folio, f) for f in fotos.listar(db, reporte)],
    )


@router.get(
    "/{folio}/fotos/{foto_id}",
    summary="Descargar una fotografía (acceso controlado)",
    response_class=FileResponse,
    responses={200: {"content": {"image/jpeg": {}, "image/png": {}}}, **respuestas(403, 404, 422)},
)
def descargar_foto(
    folio: FolioPath,
    foto_id: uuid.UUID,
    usuario: Usuario | None = Depends(usuario_opcional),
    db: Session = Depends(get_db),
) -> FileResponse:
    reporte = reportes.obtener_por_folio(db, folio)
    fotos.exigir_acceso(reporte, usuario)
    foto = fotos.obtener(db, reporte, foto_id)
    return FileResponse(
        fotos.ruta_de(foto),
        media_type=foto.mime_type,
        headers={"Cache-Control": "private, max-age=300", "Content-Disposition": "inline"},
    )


@router.delete(
    "/{folio}",
    summary="No disponible: los reportes nunca se eliminan (RN-07)",
    responses=respuestas(405),
    include_in_schema=True,
)
def eliminar(folio: FolioPath) -> None:
    raise ErrorAPI(
        405,
        "METODO_NO_PERMITIDO",
        "Los reportes no se pueden eliminar. Un reporte improcedente se marca como «Rechazado» con su motivo.",
        headers={"Allow": "GET, PATCH"},
    )
