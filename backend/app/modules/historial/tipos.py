"""Catálogo de tipos de evento del historial.

V6 §4.2 menciona un "catálogo de eventos" sin listarlo. Los nombres siguen el formato acordado en
DECISIONES.md §11 (`TAREA_*`, `NOTIFICACION_*`).

RF-32 (eventos mínimos de una tarea) -> tipo:
- creación ............ TAREA_CREADA
- modificación ........ TAREA_EDITADA (todos los campos cambiados, con valores antes/después)
- cambio de estado .... TAREA_ESTADO_CAMBIADO (Pendiente <-> En progreso) y TAREA_REABIERTA
- finalización ........ TAREA_COMPLETADA (indica si fue a tiempo o con retraso, RF-12 regla 5 / RF-13 reglas 6-7)
- reprogramación ...... TAREA_POSPUESTA (fecha posterior en una tarea abierta y no vencida, DECISIONES §5.1)
                        o TAREA_REPROGRAMADA (cualquier otro cambio de fecha límite)
- eliminación ......... TAREA_ELIMINADA

Una operación genera como máximo un evento de cada tipo. Una edición que cambia el estado o la fecha
genera TAREA_EDITADA más el evento específico (así lo fija DECISIONES §5.1 punto 5).

RF-13 regla 5: NOTIFICACION_ENVIADA (origen SISTEMA).
"""
TAREA_CREADA = "TAREA_CREADA"
TAREA_EDITADA = "TAREA_EDITADA"
TAREA_ESTADO_CAMBIADO = "TAREA_ESTADO_CAMBIADO"
TAREA_COMPLETADA = "TAREA_COMPLETADA"
TAREA_REABIERTA = "TAREA_REABIERTA"
TAREA_POSPUESTA = "TAREA_POSPUESTA"
TAREA_REPROGRAMADA = "TAREA_REPROGRAMADA"
TAREA_ELIMINADA = "TAREA_ELIMINADA"
NOTIFICACION_ENVIADA = "NOTIFICACION_ENVIADA"
