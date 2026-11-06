"""Lógica de RF-12 (generar notificaciones) y RF-13 (escalar su frecuencia).

Generar ≠ entregar ≠ mostrar (DECISIONES.md §4.1):
1. GENERAR (aquí): el backend calcula el plan de avisos y lo guarda en `notificacion` como PROGRAMADA.
2. ENTREGAR: la app llama a `POST /notificaciones/sincronizar`, recibe los avisos futuros y los programa
   en el dispositivo. Se anota `fecha_sincronizacion`.
3. MOSTRAR: lo hace el sistema operativo a la hora programada. El backend no puede confirmarlo; cuando la
   hora pasa y el aviso estaba sincronizado se registra como ENVIADA (aproximación documentada).

El plan se recalcula de forma idempotente (`replanificar`) cada vez que algo lo afecta: crear, editar,
completar, reabrir o eliminar una tarea; cambiar la preferencia de recordatorios o el idioma; y al
sincronizar. Las llamadas se hacen DENTRO de la transacción de la operación que lo provoca: si la
operación falla, el plan tampoco cambia.
"""
import uuid
from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.tiempo import zona_horaria
from app.modules.historial import tipos as tipos_evento
from app.modules.historial.repository import HistorialRepository
from app.modules.notificaciones import planificador as plan
from app.modules.notificaciones.mensajes import construir_mensaje
from app.modules.notificaciones.models import Notificacion
from app.modules.notificaciones.repository import CANCELADA, ENVIADA, NotificacionRepository
from app.modules.tareas.enums import EstadoTarea
from app.modules.tareas.models import Tarea
from app.modules.usuarios.models import PreferenciaNotificacion, Usuario

PERFIL_POR_DEFECTO = "equilibrado"


def _hora(texto: str) -> time:
    h, m = texto.split(":")
    return time(int(h), int(m))


def parametros_para(perfil: str) -> plan.ParametrosPlan:
    """Traduce la configuración (core/config.py) y el perfil del usuario a parámetros del planificador."""
    s = settings
    perfil = perfil if perfil in s.notif_intervalos_horas else PERFIL_POR_DEFECTO
    return plan.ParametrosPlan(
        intervalos_horas=s.notif_intervalos_horas[perfil],
        maximo_diario=s.notif_maximo_diario.get(perfil, 8),
        dias_correctiva=s.notif_correctiva_dias.get(perfil, 0),
        umbral_critica_horas=s.notif_umbral_critica_horas,
        umbral_urgente_horas=s.notif_umbral_urgente_horas,
        umbral_recordatorio_horas=s.notif_umbral_recordatorio_horas,
        aviso_final_minutos=s.notif_aviso_final_minutos,
        separacion_minima_minutos=s.notif_separacion_minima_minutos,
        silencio_inicio=_hora(s.notif_silencio_inicio),
        silencio_fin=_hora(s.notif_silencio_fin),
        silencio_alternativa=_hora(s.notif_silencio_alternativa),
        correctiva_primera_horas=s.notif_correctiva_primera_horas,
        correctiva_hora_diaria=_hora(s.notif_correctiva_hora_diaria),
        horizonte_horas=s.notif_horizonte_horas,
    )


class NotificacionService:
    def __init__(self, db: Session):
        self.db = db
        self.notificaciones = NotificacionRepository(db)
        self.historial = HistorialRepository(db)

    # ---- RF-13 regla 5: registrar las enviadas ---------------------------------------------
    def registrar_enviadas(self, usuario: Usuario, ahora: datetime) -> None:
        """Avisos PROGRAMADA cuya hora ya llegó:
        - sincronizados antes de su hora -> ENVIADA (+ evento NOTIFICACION_ENVIADA en el historial);
        - nunca sincronizados -> CANCELADA (no pudieron llegar al teléfono)."""
        for n in self.notificaciones.programadas_vencidas(usuario.id_usuario, ahora):
            if n.fecha_sincronizacion is not None and n.fecha_sincronizacion <= n.fecha_programada:
                n.estado = ENVIADA
                n.fecha_envio = n.fecha_programada
                self.historial.registrar(
                    id_usuario=usuario.id_usuario,
                    id_tarea=n.id_tarea,
                    id_notificacion=n.id_notificacion,
                    tipo_evento=tipos_evento.NOTIFICACION_ENVIADA,
                    datos={"tipo": n.tipo, "nivel_intensidad": n.nivel_intensidad},
                    fecha_evento=n.fecha_programada,
                    origen="SISTEMA",
                )
            else:
                n.estado = CANCELADA
                n.fecha_cancelacion = ahora
        self.db.flush()

    # ---- RF-12 y RF-13: generar / actualizar / cancelar --------------------------------------
    def replanificar(self, usuario: Usuario, ahora: datetime) -> None:
        """Deja en la BD exactamente los avisos futuros que corresponden. Idempotente: ejecutarla dos veces
        seguidas no cambia nada. No hace commit (lo hace quien la llama)."""
        # Bloquea la fila del usuario: dos replanificaciones simultáneas no pueden duplicar avisos.
        self.db.execute(select(Usuario.id_usuario).where(Usuario.id_usuario == usuario.id_usuario).with_for_update())
        self.db.flush()
        self.registrar_enviadas(usuario, ahora)

        zona = zona_horaria(usuario.zona_horaria)
        pref = self.db.get(PreferenciaNotificacion, usuario.id_usuario)
        activas = pref.notificaciones_activas if pref else True
        parametros = parametros_para(pref.perfil_recordatorios if pref else PERFIL_POR_DEFECTO)

        tareas = {t.id_tarea: t for t in self._tareas_abiertas(usuario.id_usuario)}
        deseados: list[plan.Aviso] = []
        if activas:
            deseados = plan.planificar(
                [plan.TareaPlan(t.id_tarea, t.titulo, t.fecha_limite, t.prioridad) for t in tareas.values()],
                ahora,
                zona,
                parametros,
                self._ya_usados(usuario.id_usuario, ahora, zona),
            )

        existentes = {(n.id_tarea, n.fecha_programada): n for n in self.notificaciones.programadas_futuras(usuario.id_usuario, ahora)}
        claves_deseadas = set()
        for aviso in deseados:
            tarea = tareas[aviso.id_tarea]
            clave = (aviso.id_tarea, aviso.fecha_programada)
            claves_deseadas.add(clave)
            mensaje = construir_mensaje(aviso.tipo, aviso.es_aviso_final, tarea.titulo, tarea.fecha_limite, zona, usuario.idioma)
            actual = existentes.get(clave)
            if actual is None:
                self.notificaciones.agregar(
                    Notificacion(
                        id_usuario=usuario.id_usuario,
                        id_tarea=aviso.id_tarea,
                        tipo=aviso.tipo,
                        nivel_intensidad=aviso.nivel,
                        mensaje=mensaje,
                        requiere_accion=False,  # lo definirá RF-14 (acciones desde la notificación)
                        es_aviso_final=aviso.es_aviso_final,
                        estado="PROGRAMADA",
                        fecha_generacion=ahora,
                        fecha_programada=aviso.fecha_programada,
                    )
                )
            elif (actual.tipo, actual.mensaje, actual.es_aviso_final) != (aviso.tipo, mensaje, aviso.es_aviso_final):
                actual.tipo = aviso.tipo
                actual.nivel_intensidad = aviso.nivel
                actual.mensaje = mensaje
                actual.es_aviso_final = aviso.es_aviso_final
                actual.fecha_sincronizacion = None  # el teléfono tiene una versión vieja: debe volver a sincronizar

        # RF-13 regla 4: lo que ya no corresponde (tarea completada/eliminada, fecha cambiada, preferencias) se cancela.
        for clave, n in existentes.items():
            if clave not in claves_deseadas:
                n.estado = CANCELADA
                n.fecha_cancelacion = ahora
        self.db.flush()

    def sincronizar(self, usuario: Usuario, ahora: datetime) -> list[Notificacion]:
        """Entrega al dispositivo el plan vigente. La app reemplaza TODOS sus avisos locales por esta lista."""
        self.replanificar(usuario, ahora)
        vigentes = sorted(self.notificaciones.programadas_futuras(usuario.id_usuario, ahora), key=lambda n: n.fecha_programada)
        for n in vigentes:
            n.fecha_sincronizacion = ahora
        self.db.commit()
        return vigentes

    def listar(self, usuario: Usuario, estado: str | None, id_tarea: uuid.UUID | None, limite: int) -> list[Notificacion]:
        return self.notificaciones.listar(usuario.id_usuario, estado, id_tarea, limite)

    # ---- auxiliares ----------------------------------------------------------------------
    def _tareas_abiertas(self, id_usuario: uuid.UUID) -> list[Tarea]:
        # RF-12 reglas 1 y 4: solo tareas no completadas; RF-06 regla 6: ni eliminadas.
        return list(
            self.db.scalars(
                select(Tarea).where(
                    Tarea.id_usuario == id_usuario,
                    Tarea.fecha_eliminacion.is_(None),
                    Tarea.estado != EstadoTarea.COMPLETADA.value,
                )
            )
        )

    def _ya_usados(self, id_usuario: uuid.UUID, ahora: datetime, zona) -> dict[date, int]:
        """Avisos de HOY (día local) cuya hora ya pasó y no se cancelaron: ocupan cupo del máximo diario."""
        inicio_dia = datetime.combine(ahora.astimezone(zona).date(), time.min, tzinfo=zona)
        usados: dict[date, int] = {}
        for n in self.notificaciones.no_canceladas_entre(id_usuario, inicio_dia, ahora):
            dia = n.fecha_programada.astimezone(zona).date()
            usados[dia] = usados.get(dia, 0) + 1
        return usados


def procesar_todos(db: Session, ahora: datetime) -> int:
    """Proceso programado (DECISIONES §10): registra enviadas y extiende el plan de todos los usuarios activos.
    Idempotente. Se ejecuta con `python -m app.modules.notificaciones.procesos`."""
    usuarios = list(db.scalars(select(Usuario).where(Usuario.activo.is_(True))))
    servicio = NotificacionService(db)
    for usuario in usuarios:
        servicio.replanificar(usuario, ahora)
        db.commit()
    return len(usuarios)

