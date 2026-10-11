from enum import Enum


class Prioridad(str, Enum):
    """RF-09: solo estos tres niveles."""

    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"


# En la BD la prioridad se guarda como número (documento §4.2): 1 = Baja, 2 = Media, 3 = Alta.
PRIORIDAD_A_NUMERO = {Prioridad.BAJA: 1, Prioridad.MEDIA: 2, Prioridad.ALTA: 3}
NUMERO_A_PRIORIDAD = {numero: prioridad for prioridad, numero in PRIORIDAD_A_NUMERO.items()}


class EstadoTarea(str, Enum):
    """Los cuatro estados permitidos (RF-05 regla 3)."""

    PENDIENTE = "PENDIENTE"
    EN_PROGRESO = "EN_PROGRESO"
    COMPLETADA = "COMPLETADA"
    VENCIDA = "VENCIDA"  # solo se calcula; el usuario no puede establecerla
