from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.auth.dependencies import get_usuario_actual
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.schemas import UsuarioSalida

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("/me", response_model=UsuarioSalida)
def perfil_actual(usuario: Annotated[Usuario, Depends(get_usuario_actual)]):
    """Perfil básico del usuario autenticado."""
    return usuario
