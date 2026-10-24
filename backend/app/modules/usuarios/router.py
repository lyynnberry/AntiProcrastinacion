from typing import Annotated

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.errors import ErrorValidacion
from app.modules.auth.dependencies import get_usuario_actual
from app.modules.usuarios.imagen import TAMANO_MAX_BYTES, ArchivoDemasiadoGrande
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.schemas import (
    PerfilActualizar,
    PreferenciaEntrada,
    PreferenciaSalida,
    UsuarioSalida,
)
from app.modules.usuarios.service import PerfilService

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

UsuarioActual = Annotated[Usuario, Depends(get_usuario_actual)]
Db = Annotated[Session, Depends(get_db)]


@router.get("/me", response_model=UsuarioSalida)
def perfil_actual(usuario: UsuarioActual):
    """Perfil del usuario autenticado, con el estado del flujo de primer uso."""
    return usuario


@router.patch("/me", response_model=UsuarioSalida)
def actualizar_perfil(datos: PerfilActualizar, usuario: UsuarioActual, db: Db):
    """Edita nombre e idioma del propio perfil. El correo no es editable."""
    return PerfilService(db).actualizar(usuario, datos)


@router.get("/me/preferencia-notificacion", response_model=PreferenciaSalida)
def obtener_preferencia(usuario: UsuarioActual, db: Db):
    return PerfilService(db).obtener_preferencia(usuario)


@router.put("/me/preferencia-notificacion", response_model=PreferenciaSalida)
def guardar_preferencia(datos: PreferenciaEntrada, usuario: UsuarioActual, db: Db):
    """Guarda la preferencia de recordatorios; la primera vez completa la personalización inicial."""
    return PerfilService(db).guardar_preferencia(usuario, datos)


@router.post("/me/tutorial/completar", response_model=UsuarioSalida)
def completar_tutorial(usuario: UsuarioActual, db: Db):
    """Marca el tutorial como visto (también al omitirlo). Idempotente."""
    return PerfilService(db).completar_tutorial(usuario)


@router.put("/me/foto", response_model=UsuarioSalida)
async def subir_foto(usuario: UsuarioActual, db: Db, archivo: Annotated[UploadFile, File()]):
    """Sube o reemplaza la foto de perfil (JPG/PNG/WebP, máx. 5 MB). Se valida y re-codifica en el servidor."""
    datos = await archivo.read(TAMANO_MAX_BYTES + 1)  # nunca se lee más del límite en memoria
    if len(datos) > TAMANO_MAX_BYTES:
        raise ArchivoDemasiadoGrande("La imagen supera el máximo de 5 MB.")
    if not datos:
        raise ErrorValidacion("El archivo está vacío.", "FOTO_INVALIDA")
    return PerfilService(db).guardar_foto(usuario, datos)


@router.get("/me/foto")
def obtener_foto(usuario: UsuarioActual, db: Db):
    """Devuelve la foto SOLO a su dueño (requiere sesión; no hay URL pública)."""
    foto = PerfilService(db).obtener_foto(usuario)
    return Response(
        content=foto.contenido,
        media_type=foto.tipo_mime,
        headers={"Cache-Control": "private, max-age=0, must-revalidate", "X-Content-Type-Options": "nosniff"},
    )


@router.delete("/me/foto", response_model=UsuarioSalida)
def borrar_foto(usuario: UsuarioActual, db: Db):
    return PerfilService(db).borrar_foto(usuario)
