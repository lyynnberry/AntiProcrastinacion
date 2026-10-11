"""Acceso a datos de SESION_AUTENTICACION."""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import SesionAutenticacion


class SesionRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear(
        self,
        id_usuario: uuid.UUID,
        refresh_token_hash: str,
        dispositivo: str | None,
        fecha_emision: datetime,
        fecha_expiracion: datetime,
    ) -> SesionAutenticacion:
        sesion = SesionAutenticacion(
            id_usuario=id_usuario,
            refresh_token_hash=refresh_token_hash,
            dispositivo=dispositivo,
            fecha_emision=fecha_emision,
            fecha_expiracion=fecha_expiracion,
        )
        self.db.add(sesion)
        self.db.flush()
        return sesion

    def obtener_por_id(self, id_sesion: uuid.UUID) -> SesionAutenticacion | None:
        return self.db.get(SesionAutenticacion, id_sesion)

    def obtener_por_refresh_hash(self, refresh_hash: str) -> SesionAutenticacion | None:
        return self.db.scalar(
            select(SesionAutenticacion).where(SesionAutenticacion.refresh_token_hash == refresh_hash)
        )
