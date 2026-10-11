"""Dependencias de FastAPI para proteger endpoints.

Uso en un router:   usuario: Usuario = Depends(get_usuario_actual)
Con ello el endpoint exige un access token válido y recibe al usuario autenticado.
"""
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.errors import NoAutenticado
from app.modules.auth.service import AuthService, ContextoAutenticacion
from app.modules.usuarios.models import Usuario

# auto_error=False para responder con nuestro formato de error en lugar del predeterminado.
_esquema_bearer = HTTPBearer(auto_error=False)


def get_contexto_autenticacion(
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_esquema_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> ContextoAutenticacion:
    if credenciales is None:
        raise NoAutenticado("Se requiere autenticación.", "NO_AUTENTICADO")
    return AuthService(db).autenticar(credenciales.credentials)


def get_usuario_actual(
    contexto: Annotated[ContextoAutenticacion, Depends(get_contexto_autenticacion)],
) -> Usuario:
    return contexto.usuario
