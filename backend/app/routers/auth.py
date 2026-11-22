from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import CUALQUIER_ROL, get_db
from app.models import Usuario
from app.schemas.auth import LoginIn, RegistroIn, RegistroOut, TokenOut, YoOut
from app.schemas.comun import respuestas
from app.services import auth as servicio
from app.services.reportes import LIMITE_REPORTES_POR_HORA, contar_reportes_ultima_hora

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/registro",
    response_model=RegistroOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una cuenta de ciudadano",
    responses=respuestas(409, 422),
)
def registro(datos: RegistroIn, db: Session = Depends(get_db)) -> RegistroOut:
    usuario = servicio.registrar(db, datos)
    return RegistroOut(id=usuario.id, nombre=usuario.nombre, rol=usuario.rol, created_at=usuario.created_at)


@router.post(
    "/login",
    response_model=TokenOut,
    summary="Iniciar sesión y obtener un JWT (30 min de inactividad)",
    responses=respuestas(401, 422, 429),
)
def login(datos: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    return servicio.iniciar_sesion(db, datos)


@router.post(
    "/renovar",
    response_model=TokenOut,
    summary="Renovar el token (sesión deslizante)",
    responses=respuestas(401),
)
def renovar(usuario: Usuario = Depends(CUALQUIER_ROL)) -> TokenOut:
    return servicio.emitir_token(usuario)


@router.post(
    "/cerrar-sesion",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión e invalidar los tokens emitidos",
    responses=respuestas(401),
)
def cerrar_sesion(usuario: Usuario = Depends(CUALQUIER_ROL), db: Session = Depends(get_db)) -> Response:
    servicio.cerrar_sesion(db, usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/yo", response_model=YoOut, summary="Datos de la propia cuenta", responses=respuestas(401))
def yo(usuario: Usuario = Depends(CUALQUIER_ROL), db: Session = Depends(get_db)) -> YoOut:
    return YoOut(
        id=usuario.id,
        nombre=usuario.nombre,
        correo=usuario.correo,
        rol=usuario.rol,
        reportes_ultima_hora=contar_reportes_ultima_hora(db, usuario.id),
        limite_reportes_hora=LIMITE_REPORTES_POR_HORA,
    )
