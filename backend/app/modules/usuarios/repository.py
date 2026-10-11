"""Acceso a datos de USUARIO. Solo consultas; las reglas de negocio viven en los servicios."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.usuarios.models import Usuario


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
