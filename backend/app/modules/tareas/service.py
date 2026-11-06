"""Lógica de negocio de tareas: RF-04 (crear), RF-05 (editar), RF-06 (eliminar), RF-07 (consultar/filtrar),
RF-08 (fecha límite), RF-09 (prioridad) y RF-11 (asociar con materia).

RF-32: cada operación escribe sus eventos de historial en la MISMA transacción que el cambio; si algo falla
no queda ni el cambio ni el evento. RF-12/RF-13: al final de cada operación se recalcula el plan de avisos
del usuario, también dentro de la transacción.
"""
import uuid
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ErrorValidacion, NoEncontrado
from app.core.tiempo import ahora_utc, zona_horaria
from app.modules.gamificacion.service import GamificacionService
from app.modules.historial import tipos as tipos_evento
from app.modules.historial.repository import HistorialRepository
from app.modules.materias.repository import MateriaRepository
from app.modules.notificaciones.service import NotificacionService
from app.modules.tareas.enums import PRIORIDAD_A_NUMERO, EstadoTarea, Prioridad
from app.modules.tareas.models import Tarea
from app.modules.tareas.reglas import estado_efectivo, validar_fecha_limite_futura
from app.modules.tareas.repository import FiltrosTarea, TareaRepository
from app.modules.tareas.schemas import TareaActualizar, TareaCrear
from app.modules.usuarios.models import Usuario


def _tarea_no_encontrada() -> NoEncontrado:
    # Mismo error si la tarea no existe, fue eliminada o es de otro usuario: no se revela cuál.
    return NoEncontrado("Tarea no encontrada.", "TAREA_NO_ENCONTRADA")


def _materia_no_encontrada() -> NoEncontrado:
    return NoEncontrado("Materia no encontrada.", "MATERIA_NO_ENCONTRADA")


def _limpiar_descripcion(descripcion: str | None) -> str | None:
    return descripcion or None  # el esquema ya recortó espacios; "" se guarda como NULL


def _a_json(valor: Any) -> Any:
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, uuid.UUID):
        return str(valor)
    return valor


def _zona_del_usuario(usuario: Usuario) -> ZoneInfo:
    return zona_horaria(usuario.zona_horaria)


def _validar_fecha_programada(programada: date | None, fecha_limite: datetime, ahora: datetime, zona: ZoneInfo) -> None:
    """RF-21 (DECISIONES, gamificación): el día al que se compromete una tarea va de hoy (local) al día local
    de su fecha límite. No se puede comprometer un día pasado ni uno posterior a la entrega."""
    if programada is None:
        return
    hoy = ahora.astimezone(zona).date()
    if programada < hoy or programada > fecha_limite.astimezone(zona).date():
        raise ErrorValidacion(
            "La fecha programada debe estar entre hoy y el día de la fecha límite.", "FECHA_PROGRAMADA_INVALIDA"
        )


class TareaService:
    def __init__(self, db: Session):
        self.db = db
        self.tareas = TareaRepository(db)
        self.materias = MateriaRepository(db)
        self.historial = HistorialRepository(db)
        self.notificaciones = NotificacionService(db)

    # ---- RF-04, RF-08, RF-09, RF-11 -----------------------------------------------------
    def crear(self, usuario: Usuario, datos: TareaCrear) -> Tarea:
        ahora = ahora_utc()
        validar_fecha_limite_futura(datos.fecha_limite, ahora)
        _validar_fecha_programada(datos.fecha_programada, datos.fecha_limite, ahora, _zona_del_usuario(usuario))
        self._exigir_materia_propia(datos.id_materia, usuario)

        tarea = self.tareas.crear(
            id_usuario=usuario.id_usuario,  # siempre el usuario autenticado, nunca un valor del cliente
            id_materia=datos.id_materia,
            titulo=datos.titulo,
            descripcion=_limpiar_descripcion(datos.descripcion),
            prioridad=PRIORIDAD_A_NUMERO[datos.prioridad],
            estado=EstadoTarea.PENDIENTE.value,  # RF-04 regla 5
            fecha_creacion=ahora,
            fecha_limite=datos.fecha_limite,
            fecha_limite_original=datos.fecha_limite,
            fecha_programada=datos.fecha_programada,
            fecha_actualizacion=ahora,
        )
        self.historial.registrar(  # RF-32: creación
            id_usuario=usuario.id_usuario,
            id_tarea=tarea.id_tarea,
            tipo_evento=tipos_evento.TAREA_CREADA,
            datos={
                "titulo": tarea.titulo,
                "prioridad": tarea.prioridad,
                "estado": tarea.estado,
                "fecha_limite": _a_json(tarea.fecha_limite),
                "id_materia": _a_json(tarea.id_materia),
                "fecha_programada": _a_json(tarea.fecha_programada),
            },
            fecha_evento=ahora,
        )
        self.notificaciones.replanificar(usuario, ahora)  # RF-12: primer ciclo de avisos
        self.db.commit()
        return tarea

    # ---- RF-07 -------------------------------------------------------------------------
    def obtener(self, usuario: Usuario, id_tarea: uuid.UUID) -> Tarea:
        tarea = self.tareas.obtener(id_tarea, usuario.id_usuario)
        if tarea is None:
            raise _tarea_no_encontrada()
        return tarea

    def listar(
        self,
        usuario: Usuario,
        estado: EstadoTarea | None,
        prioridad: Prioridad | None,
        id_materia: uuid.UUID | None,
        fecha_desde: date | None,
        fecha_hasta: date | None,
        limite: int,
        desplazamiento: int,
    ) -> list[Tarea]:
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ErrorValidacion("'fecha_desde' no puede ser posterior a 'fecha_hasta'.", "RANGO_INVALIDO")

        # Los días se interpretan en la zona horaria del usuario y ambos extremos son inclusivos.
        zona = _zona_del_usuario(usuario)
        filtros = FiltrosTarea(
            estado=estado,
            prioridad=prioridad,
            id_materia=id_materia,
            limite_desde=datetime.combine(fecha_desde, time.min, tzinfo=zona) if fecha_desde else None,
            limite_hasta=(
                datetime.combine(fecha_hasta + timedelta(days=1), time.min, tzinfo=zona)
                if fecha_hasta
                else None
            ),
        )
        return self.tareas.listar(usuario.id_usuario, filtros, ahora_utc(), limite, desplazamiento)

    # ---- RF-05 -------------------------------------------------------------------------
    def actualizar(self, usuario: Usuario, id_tarea: uuid.UUID, datos: TareaActualizar) -> Tarea:
        tarea = self.obtener(usuario, id_tarea)
        ahora = ahora_utc()
        enviados = datos.model_fields_set
        cambios: dict[str, tuple[Any, Any]] = {}  # campo -> (valor_antes, valor_despues)
        estado_efectivo_antes = estado_efectivo(tarea, ahora)

        # Solo se registran y validan los campos que REALMENTE cambian. Así, editar una tarea
        # vencida sin tocar su fecha límite no obliga a cambiarla (y reenviar el mismo valor tampoco).
        if "titulo" in enviados and datos.titulo != tarea.titulo:
            cambios["titulo"] = (tarea.titulo, datos.titulo)

        if "descripcion" in enviados:
            nueva = _limpiar_descripcion(datos.descripcion)
            if nueva != tarea.descripcion:
                cambios["descripcion"] = (tarea.descripcion, nueva)

        if "prioridad" in enviados:
            nueva = PRIORIDAD_A_NUMERO[datos.prioridad]
            if nueva != tarea.prioridad:
                cambios["prioridad"] = (tarea.prioridad, nueva)

        if "fecha_limite" in enviados and datos.fecha_limite != tarea.fecha_limite:
            validar_fecha_limite_futura(datos.fecha_limite, ahora)  # RF-08: se valida al modificarla
            cambios["fecha_limite"] = (tarea.fecha_limite, datos.fecha_limite)

        if "id_materia" in enviados and datos.id_materia != tarea.id_materia:
            self._exigir_materia_propia(datos.id_materia, usuario)  # None = quitar la materia
            cambios["id_materia"] = (tarea.id_materia, datos.id_materia)

        if "estado" in enviados:
            self._aplicar_estado(tarea, datos.estado, ahora, cambios)

        # RF-21: día comprometido. Una vez que el día programado llegó, ya no se puede mover ni quitar
        # (si no, bastaría con cambiarlo para salvar la racha). Si cambia la fecha límite, se revalida.
        zona = _zona_del_usuario(usuario)
        programada_final = tarea.fecha_programada
        if "fecha_programada" in enviados and datos.fecha_programada != tarea.fecha_programada:
            if tarea.fecha_programada is not None and tarea.fecha_programada <= ahora.astimezone(zona).date():
                raise ErrorValidacion(
                    "El día programado ya llegó: no se puede cambiar.", "FECHA_PROGRAMADA_NO_EDITABLE"
                )
            cambios["fecha_programada"] = (tarea.fecha_programada, datos.fecha_programada)
            programada_final = datos.fecha_programada
        if "fecha_programada" in cambios or "fecha_limite" in cambios:
            limite_final = cambios["fecha_limite"][1] if "fecha_limite" in cambios else tarea.fecha_limite
            if "fecha_programada" in cambios:
                _validar_fecha_programada(programada_final, limite_final, ahora, zona)
            elif programada_final is not None and programada_final > limite_final.astimezone(zona).date():
                raise ErrorValidacion(
                    "La fecha programada debe estar entre hoy y el día de la fecha límite.", "FECHA_PROGRAMADA_INVALIDA"
                )

        # TAR-09 (DECISIONES §5.2, protege RF-13 reglas 6-7): una tarea COMPLETADA no puede cambiar su
        # fecha límite; primero hay que reabrirla. Si no, una entrega con retraso podría volverse "a tiempo".
        estado_final = cambios.get("estado", (None, tarea.estado))[1]
        if "fecha_limite" in cambios and estado_final == EstadoTarea.COMPLETADA.value:
            raise ErrorValidacion(
                "Una tarea completada no puede cambiar su fecha límite. Reábrela primero.",
                "FECHA_TAREA_COMPLETADA",
            )

        if not cambios:
            return tarea  # nada cambió: no se escribe nada ni se llena el historial

        for campo, (_, despues) in cambios.items():
            setattr(tarea, campo, despues)
        tarea.fecha_actualizacion = ahora
        self.historial.registrar(  # RF-05 reglas 5-7
            id_usuario=usuario.id_usuario,
            id_tarea=tarea.id_tarea,
            tipo_evento=tipos_evento.TAREA_EDITADA,
            datos={
                "antes": {c: _a_json(a) for c, (a, _) in cambios.items()},
                "despues": {c: _a_json(d) for c, (_, d) in cambios.items()},
            },
            fecha_evento=ahora,
        )
        self._registrar_eventos_especificos(usuario, tarea, cambios, estado_efectivo_antes, ahora)
        if cambios.get("estado", (None, None))[1] == EstadoTarea.COMPLETADA.value:
            # RF-22: puntos (una sola vez por tarea) y RF-23/RF-27: logros y recompensas, en esta transacción.
            limite = cambios["fecha_limite"][0] if "fecha_limite" in cambios else tarea.fecha_limite
            GamificacionService(self.db).tarea_completada(usuario, tarea.id_tarea, ahora <= limite, ahora)
        self.notificaciones.replanificar(usuario, ahora)  # RF-13: recalcula o cancela los avisos
        self.db.commit()
        return tarea

    def _registrar_eventos_especificos(
        self,
        usuario: Usuario,
        tarea: Tarea,
        cambios: dict[str, tuple[Any, Any]],
        estado_efectivo_antes: EstadoTarea,
        ahora: datetime,
    ) -> None:
        """RF-32: además de TAREA_EDITADA, un evento por cada hecho relevante (como máximo uno de cada tipo)."""

        def registrar(tipo: str, datos: dict) -> None:
            self.historial.registrar(
                id_usuario=usuario.id_usuario,
                id_tarea=tarea.id_tarea,
                tipo_evento=tipo,
                datos=datos,
                fecha_evento=ahora,
            )

        if "fecha_limite" in cambios:
            antes, despues = cambios["fecha_limite"]
            abierta_no_vencida = estado_efectivo_antes in (EstadoTarea.PENDIENTE, EstadoTarea.EN_PROGRESO)
            # DECISIONES §5.1 punto 5: mover a una fecha POSTERIOR una tarea abierta y no vencida es posponerla.
            tipo = tipos_evento.TAREA_POSPUESTA if abierta_no_vencida and despues > antes else tipos_evento.TAREA_REPROGRAMADA
            registrar(
                tipo,
                {
                    "antes": _a_json(antes),
                    "despues": _a_json(despues),
                    "fecha_limite_original": _a_json(tarea.fecha_limite_original),
                    "estaba_vencida": estado_efectivo_antes == EstadoTarea.VENCIDA,
                },
            )

        if "estado" in cambios:
            antes, despues = cambios["estado"]
            if despues == EstadoTarea.COMPLETADA.value:
                # RF-12 regla 5: a tiempo si se completa antes o exactamente en la fecha límite. Se compara con la
                # fecha límite VIGENTE ANTES de esta operación, para que no se pueda mover la fecha y completar a la vez.
                limite = cambios["fecha_limite"][0] if "fecha_limite" in cambios else tarea.fecha_limite
                registrar(
                    tipos_evento.TAREA_COMPLETADA,
                    {
                        "estado_anterior": antes,
                        "fecha_completada": _a_json(ahora),
                        "fecha_limite": _a_json(limite),
                        "a_tiempo": ahora <= limite,  # False = completada con retraso (RF-13 reglas 6-7)
                        # RF-23 (logros VELOCIDAD): completada con al menos N horas de anticipación.
                        "anticipada": ahora <= limite - timedelta(hours=settings.gam_horas_anticipacion),
                    },
                )
            elif antes == EstadoTarea.COMPLETADA.value:
                registrar(tipos_evento.TAREA_REABIERTA, {"antes": antes, "despues": despues})
            else:
                registrar(tipos_evento.TAREA_ESTADO_CAMBIADO, {"antes": antes, "despues": despues})

    @staticmethod
    def _aplicar_estado(
        tarea: Tarea, nuevo: EstadoTarea, ahora: datetime, cambios: dict[str, tuple[Any, Any]]
    ) -> None:
        if nuevo == EstadoTarea.VENCIDA:
            if estado_efectivo(tarea, ahora) == EstadoTarea.VENCIDA:
                return  # el cliente reenvía el estado que recibió: no es un cambio
            raise ErrorValidacion(
                "El estado 'Vencida' no se puede establecer manualmente: se asigna "
                "automáticamente cuando pasa la fecha límite.",
                "ESTADO_NO_EDITABLE",
            )
        if nuevo.value == tarea.estado:
            return
        cambios["estado"] = (tarea.estado, nuevo.value)
        if nuevo == EstadoTarea.COMPLETADA:
            cambios["fecha_completada"] = (tarea.fecha_completada, ahora)  # RF-05 regla 4
        elif tarea.estado == EstadoTarea.COMPLETADA.value:
            cambios["fecha_completada"] = (tarea.fecha_completada, None)  # se reabre la tarea

    # ---- RF-06 -------------------------------------------------------------------------
    def eliminar(self, usuario: Usuario, id_tarea: uuid.UUID) -> None:
        """Eliminación lógica. La confirmación del usuario la pide el frontend (RF-06 regla 2)."""
        tarea = self.obtener(usuario, id_tarea)
        ahora = ahora_utc()
        tarea.fecha_eliminacion = ahora
        tarea.fecha_actualizacion = ahora
        self.historial.registrar(
            id_usuario=usuario.id_usuario,
            id_tarea=tarea.id_tarea,
            tipo_evento=tipos_evento.TAREA_ELIMINADA,
            datos={"titulo": tarea.titulo},
            fecha_evento=ahora,
        )
        self.notificaciones.replanificar(usuario, ahora)  # RF-06 regla 6: sin avisos para tareas eliminadas
        self.db.commit()

    # ---- auxiliar RF-11 ----------------------------------------------------------------
    def _exigir_materia_propia(self, id_materia: uuid.UUID | None, usuario: Usuario) -> None:
        """La materia es opcional; si se indica, debe ser una materia activa del MISMO usuario."""
        if id_materia is None:
            return
        if self.materias.obtener_activa(id_materia, usuario.id_usuario) is None:
            raise _materia_no_encontrada()
