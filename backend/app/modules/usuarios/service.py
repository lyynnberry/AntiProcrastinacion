"""Perfil del usuario autenticado: nombre, idioma, preferencia de recordatorios, foto y flujo de primer uso.

Todas las operaciones reciben al `Usuario` ya autenticado y solo tocan SUS datos: no existe ningún
parámetro de id de otro usuario, así que no hay forma de editar el perfil ajeno.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.errors import NoEncontrado
from app.modules.usuarios.imagen import TIPO_SALIDA, procesar_foto
from app.modules.usuarios.models import FotoPerfil, PreferenciaNotificacion, Usuario
from app.modules.usuarios.repository import UsuarioRepository
from app.modules.usuarios.schemas import PerfilActualizar, PreferenciaEntrada

PREFERENCIA_POR_DEFECTO = ("equilibrado", True)


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


class PerfilService:
    def __init__(self, db: Session):
        self.db = db
        self.usuarios = UsuarioRepository(db)

    def actualizar(self, usuario: Usuario, datos: PerfilActualizar) -> Usuario:
        campos = datos.model_fields_set
        if "nombre" in campos:
            usuario.nombre = datos.nombre  # None borra el nombre; el esquema ya lo normalizó
        if "idioma" in campos and datos.idioma is not None:
            usuario.idioma = datos.idioma
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    # --- Preferencia de recordatorios / configuración inicial ---
    def obtener_preferencia(self, usuario: Usuario) -> PreferenciaNotificacion:
        pref = self.usuarios.obtener_preferencia(usuario.id_usuario)
        if pref is None:  # aún no eligió: se devuelve el valor por defecto sin crear fila
            return PreferenciaNotificacion(
                id_usuario=usuario.id_usuario,
                perfil_recordatorios=PREFERENCIA_POR_DEFECTO[0],
                notificaciones_activas=PREFERENCIA_POR_DEFECTO[1],
            )
        return pref

    def guardar_preferencia(self, usuario: Usuario, datos: PreferenciaEntrada) -> PreferenciaNotificacion:
        """Guarda la preferencia y, si es la primera vez, marca completa la personalización inicial."""
        pref = self.usuarios.guardar_preferencia(
            usuario.id_usuario, datos.perfil_recordatorios, datos.notificaciones_activas
        )
        if usuario.personalizacion_completada_en is None:
            usuario.personalizacion_completada_en = _ahora()
        self.db.commit()
        self.db.refresh(pref)
        return pref

    def completar_tutorial(self, usuario: Usuario) -> Usuario:
        if usuario.tutorial_completado_en is None:  # idempotente: no se sobrescribe la primera fecha
            usuario.tutorial_completado_en = _ahora()
            self.db.commit()
            self.db.refresh(usuario)
        return usuario

    # --- Foto ---
    def guardar_foto(self, usuario: Usuario, datos: bytes) -> Usuario:
        jpeg = procesar_foto(datos)  # lanza ErrorDominio si no es una imagen válida
        self.usuarios.guardar_foto(usuario.id_usuario, jpeg, TIPO_SALIDA)
        usuario.foto_actualizada_en = _ahora()
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def obtener_foto(self, usuario: Usuario) -> FotoPerfil:
        foto = self.usuarios.obtener_foto(usuario.id_usuario)
        if foto is None:
            raise NoEncontrado("No tienes foto de perfil.", "FOTO_NO_ENCONTRADA")
        return foto

    def borrar_foto(self, usuario: Usuario) -> Usuario:
        self.usuarios.borrar_foto(usuario.id_usuario)
        usuario.foto_actualizada_en = None
        self.db.commit()
        self.db.refresh(usuario)
        return usuario
