"""Endpoints de autenticación (RF-01, RF-02, RF-03). Solo traducen HTTP <-> servicio."""
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.auth.dependencies import get_contexto_autenticacion
from app.modules.auth.schemas import LoginEntrada, RefreshEntrada, RegistroEntrada, TokensSalida
from app.modules.auth.service import AuthService, ContextoAutenticacion
from app.modules.usuarios.schemas import UsuarioSalida

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/registro", response_model=UsuarioSalida, status_code=status.HTTP_201_CREATED)
def registrar(datos: RegistroEntrada, db: Annotated[Session, Depends(get_db)]):
    """RF-01. Crea la cuenta. Para obtener tokens hay que iniciar sesión después."""
    return AuthService(db).registrar(datos)


@router.post("/login", response_model=TokensSalida)
def iniciar_sesion(
    datos: LoginEntrada,
    db: Annotated[Session, Depends(get_db)],
    user_agent: Annotated[str | None, Header()] = None,
):
    """RF-02."""
    return AuthService(db).iniciar_sesion(datos, dispositivo=user_agent)


@router.post("/refresh", response_model=TokensSalida)
def renovar_sesion(datos: RefreshEntrada, db: Annotated[Session, Depends(get_db)]):
    """RF-03. Obtiene un nuevo access token sin volver a pedir la contraseña."""
    return AuthService(db).renovar_sesion(datos.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def cerrar_sesion(
    contexto: Annotated[ContextoAutenticacion, Depends(get_contexto_autenticacion)],
    db: Annotated[Session, Depends(get_db)],
):
    """RF-03. Invalida la sesión actual."""
    AuthService(db).cerrar_sesion(contexto.sesion)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
