"""Acceso a datos de USUARIO. Solo consultas; las reglas de negocio viven en los servicios."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.usuarios.models import FotoPerfil, PreferenciaNotificacion, Usuario


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def obtener_por_id(self, id_usuario: uuid.UUID) -> Usuario | None:
        return self.db.get(Usuario, id_usuario)

    def obtener_por_email(self, email_normalizado: str) -> Usuario | None:
        return self.db.scalar(select(Usuario).where(Usuario.email == email_normalizado))

    def crear(self, email_normalizado: str, password_hash: str, nombre: str | None) -> Usuario:
        usuario = Usuario(email=email_normalizado, password_hash=password_hash, nombre=nombre)
        self.db.add(usuario)
        self.db.flush()  # Falla aquí si el correo ya existe (restricción UNIQUE).
        return usuario

    # --- Preferencias de recordatorios ---
    def obtener_preferencia(self, id_usuario: uuid.UUID) -> PreferenciaNotificacion | None:
        return self.db.get(PreferenciaNotificacion, id_usuario)

    def guardar_preferencia(
        self, id_usuario: uuid.UUID, perfil: str, activas: bool
    ) -> PreferenciaNotificacion:
        pref = self.obtener_preferencia(id_usuario)
        if pref is None:
            pref = PreferenciaNotificacion(id_usuario=id_usuario)
            self.db.add(pref)
        pref.perfil_recordatorios = perfil
        pref.notificaciones_activas = activas
        return pref

    # --- Foto de perfil ---
    def obtener_foto(self, id_usuario: uuid.UUID) -> FotoPerfil | None:
        return self.db.get(FotoPerfil, id_usuario)

    def guardar_foto(self, id_usuario: uuid.UUID, contenido: bytes, tipo_mime: str) -> None:
        foto = self.obtener_foto(id_usuario)
        if foto is None:
            foto = FotoPerfil(id_usuario=id_usuario)
            self.db.add(foto)
        foto.contenido = contenido
        foto.tipo_mime = tipo_mime
        foto.tamano_bytes = len(contenido)

    def borrar_foto(self, id_usuario: uuid.UUID) -> None:
        foto = self.obtener_foto(id_usuario)
        if foto is not None:
            self.db.delete(foto)
