import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

NombreMateria = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class MateriaCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: NombreMateria


class MateriaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_materia: uuid.UUID
    nombre: str
    activa: bool
    fecha_creacion: datetime
