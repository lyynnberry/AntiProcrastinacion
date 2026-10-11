import uuid
from datetime import datetime
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, StringConstraints, model_validator

from app.modules.tareas.enums import NUMERO_A_PRIORIDAD, EstadoTarea, Prioridad
from app.modules.tareas.reglas import estado_efectivo

Titulo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
Descripcion = Annotated[str, StringConstraints(strip_whitespace=True, max_length=5000)]


class TareaCrear(BaseModel):
    """RF-04. El estado NO se envía: toda tarea nueva comienza Pendiente (regla 5)."""

    model_config = ConfigDict(extra="forbid")

    titulo: Titulo
    descripcion: Descripcion | None = None
    # AwareDatetime exige zona horaria explícita (ej. 2026-10-20T18:00:00-06:00); evita ambigüedades.
    fecha_limite: AwareDatetime
    prioridad: Prioridad
    id_materia: uuid.UUID | None = None


class TareaActualizar(BaseModel):
    """RF-05. Todos los campos son opcionales: solo se modifican los que se envían.

    - `descripcion` e `id_materia` pueden enviarse como null para vaciarlos / quitar la materia.
    - Los demás campos no admiten null.
    """

    model_config = ConfigDict(extra="forbid")

    titulo: Titulo | None = None
    descripcion: Descripcion | None = None
    fecha_limite: AwareDatetime | None = None
    prioridad: Prioridad | None = None
    estado: EstadoTarea | None = None
    id_materia: uuid.UUID | None = None

    @model_validator(mode="after")
    def validar_campos_enviados(self):
        enviados = self.model_fields_set
        if not enviados:
            raise ValueError("Debes enviar al menos un campo para modificar.")
        for campo in ("titulo", "fecha_limite", "prioridad", "estado"):
            if campo in enviados and getattr(self, campo) is None:
                raise ValueError(f"El campo '{campo}' no puede ser nulo.")
        return self


class TareaSalida(BaseModel):
    id_tarea: uuid.UUID
    titulo: str
    descripcion: str | None
    prioridad: Prioridad
    estado: EstadoTarea  # estado efectivo: incluye VENCIDA calculada
    id_materia: uuid.UUID | None
    fecha_creacion: datetime
    fecha_limite: datetime
    fecha_limite_original: datetime
    fecha_completada: datetime | None
    fecha_actualizacion: datetime

    @classmethod
    def desde_tarea(cls, tarea, ahora: datetime) -> "TareaSalida":
        return cls(
            id_tarea=tarea.id_tarea,
            titulo=tarea.titulo,
            descripcion=tarea.descripcion,
            prioridad=NUMERO_A_PRIORIDAD[tarea.prioridad],
            estado=estado_efectivo(tarea, ahora),
            id_materia=tarea.id_materia,
            fecha_creacion=tarea.fecha_creacion,
            fecha_limite=tarea.fecha_limite,
            fecha_limite_original=tarea.fecha_limite_original,
            fecha_completada=tarea.fecha_completada,
            fecha_actualizacion=tarea.fecha_actualizacion,
        )
