from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import CUALQUIER_ROL, get_db, usuario_opcional
from app.core.errores import ErrorAPI
from app.models import EstadoReporte, TipoDano, Usuario
from app.schemas.comun import Latitud, Longitud, Pagina, ParametrosPagina, armar_pagina, respuestas
from app.schemas.reportes import (
    CandidatoDuplicado,
    CercanosRespuesta,
    ConfirmacionIn,
    ConfirmacionOut,
    HistorialPublico,
    HistorialPublicoItem,
    MiReporte,
    ReporteCrear,
    ReportePublico,
    ReporteResumenPublico,
)
from app.services import confirmaciones, presentacion, reportes
from app.services.vigencia import expirar_vencidos

router = APIRouter(prefix="/reportes", tags=["reportes"])

FolioPath = Annotated[
    str,
    Path(pattern=r"^(BCH|ENC)-[0-9]{4}-[0-9]{6}$", description="Folio público, p. ej. BCH-2026-000418."),
]


@router.get(
    "",
    response_model=Pagina[ReporteResumenPublico],
    summary="Lista pública de reportes (sin «Rechazado»)",
    responses=respuestas(422),
)
def listar(
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
    pag: ParametrosPagina = Depends(),
    db: Session = Depends(get_db),
) -> dict:
    expirar_vencidos(db)
    filas, total = reportes.listar_publicos(
        db,
        tipos=tipo_dano,
        estados=estado,
        solo_vigentes=solo_vigentes,
        colonia_id=colonia_id,
        sector_id=sector_id,
        calle=calle,
        bbox=bbox,
        desde=desde,
        hasta=hasta,
        orden=orden,
        pag=pag,
    )
    conteos = presentacion.conteos_confirmaciones(db, filas)
    return armar_pagina([presentacion.a_resumen(r, conteos) for r in filas], total, pag)


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
        headers={"Allow": "GET, POST"},
    )
