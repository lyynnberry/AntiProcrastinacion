"""Lógica de negocio de materias: RF-10 (crear materia)."""
import unicodedata

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import Conflicto
from app.modules.materias.models import Materia
from app.modules.materias.repository import MateriaRepository
from app.modules.materias.schemas import MateriaCrear
from app.modules.usuarios.models import Usuario


def normalizar_nombre(nombre: str) -> str:
    """Para comparar nombres: espacios colapsados y sin distinguir mayúsculas.
    'Cálculo  I' y 'cálculo i' son la misma materia (RF-10 regla 5). Los acentos sí cuentan."""
    return " ".join(nombre.split()).casefold()


class MateriaService:
    def __init__(self, db: Session):
        self.db = db
        self.materias = MateriaRepository(db)

    def crear(self, usuario: Usuario, datos: MateriaCrear) -> Materia:
        nombre = " ".join(datos.nombre.split())  # se guarda sin espacios sobrantes
        normalizado = normalizar_nombre(nombre)

        if self.materias.obtener_activa_por_nombre(usuario.id_usuario, normalizado):
            raise _materia_duplicada()
        try:
            materia = self.materias.crear(usuario.id_usuario, nombre, normalizado)
            self.db.commit()
        except IntegrityError:
            # Respaldo ante dos peticiones simultáneas: la restricción única de la BD decide.
            self.db.rollback()
            raise _materia_duplicada()
        return materia

    def listar(self, usuario: Usuario) -> list[Materia]:
        # Orden alfabético en español (sin distinguir acentos ni mayúsculas). Se hace aquí y no en SQL
        # porque el orden de PostgreSQL depende de la "collation" configurada y puede dejar
        # "Álgebra" después de "Física".
        return sorted(
            self.materias.listar_activas(usuario.id_usuario), key=lambda m: _clave_orden(m.nombre)
        )


def _clave_orden(nombre: str) -> str:
    sin_acentos = unicodedata.normalize("NFD", nombre)
    return "".join(c for c in sin_acentos if not unicodedata.combining(c)).casefold()


def _materia_duplicada() -> Conflicto:
    return Conflicto("Ya tienes una materia con ese nombre.", "MATERIA_DUPLICADA")
