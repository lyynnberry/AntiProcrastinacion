"""Acceso a datos de MATERIA.

Regla de seguridad: TODAS las consultas reciben `id_usuario` y filtran por él. Así es imposible
leer una materia ajena por descuido en un servicio.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.materias.models import Materia


class MateriaRepository:
    def __init__(self, db: Session):
        self.db = db

    def obtener_activa(self, id_materia: uuid.UUID, id_usuario: uuid.UUID) -> Materia | None:
        return self.db.scalar(
            select(Materia).where(
                Materia.id_materia == id_materia,
                Materia.id_usuario == id_usuario,
                Materia.activa.is_(True),
            )
        )

    def obtener_activa_por_nombre(self, id_usuario: uuid.UUID, nombre_normalizado: str) -> Materia | None:
        return self.db.scalar(
            select(Materia).where(
                Materia.id_usuario == id_usuario,
                Materia.nombre_normalizado == nombre_normalizado,
                Materia.activa.is_(True),
            )
        )

    def listar_activas(self, id_usuario: uuid.UUID) -> list[Materia]:
        # Sin ORDER BY a propósito: el orden alfabético lo aplica el servicio (ver MateriaService.listar).
        return list(
            self.db.scalars(
                select(Materia).where(Materia.id_usuario == id_usuario, Materia.activa.is_(True))
            )
        )

    def crear(self, id_usuario: uuid.UUID, nombre: str, nombre_normalizado: str) -> Materia:
        materia = Materia(id_usuario=id_usuario, nombre=nombre, nombre_normalizado=nombre_normalizado)
        self.db.add(materia)
        self.db.flush()
        return materia
