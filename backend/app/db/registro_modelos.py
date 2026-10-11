"""Importa todos los modelos para que Alembic los detecte.

Al agregar un módulo nuevo con tablas (por ejemplo notificaciones), se importa aquí.
"""
from app.modules.auth.models import SesionAutenticacion  # noqa: F401
from app.modules.historial.models import HistorialEvento  # noqa: F401
from app.modules.materias.models import Materia  # noqa: F401
from app.modules.tareas.models import Tarea  # noqa: F401
from app.modules.usuarios.models import Usuario  # noqa: F401
