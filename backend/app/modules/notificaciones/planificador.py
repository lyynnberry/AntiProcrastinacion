"""Reglas PURAS de RF-12 y RF-13: qué avisos le corresponden a cada tarea y cuándo.

No accede a la base de datos ni al reloj: recibe `ahora`, las tareas y los parámetros, y devuelve el plan.
Así se prueba sin dispositivo y sin depender de la hora real.

Reglas (fuente entre corchetes):
- Solo tareas no completadas ni eliminadas [V6 RF-12 r1 y r4, RF-13 r3].
- Niveles por tiempo restante T = fecha_limite - momento del aviso [DECISIONES §4.2]:
  RECORDATORIO (1) 72 h < T <= 7 d · URGENTE (2) 24 h < T <= 72 h · CRITICA (3) 0 < T <= 24 h ·
  CORRECTIVA (4) tarea ya vencida.
- Intervalos por perfil y nivel, alineados hacia atrás desde la fecha límite (T - h, T - 2h, ...)
  [DECISIONES §4.3; la alineación es PROPUESTA §12]. Como el intervalo se acorta en cada nivel, la
  frecuencia sube al acercarse la fecha límite [V6 RF-13 r1 y r2].
- Aviso especial T - 1 h, CRITICA, prioritario [DECISIONES §4.3].
- Dos avisos de una misma tarea no pueden quedar a menos de 15 min; se conserva el de mayor nivel.
- Horario de silencio 22:00-07:00 local [DECISIONES §4.5]. Reubicación [PROPUESTA §12]: a las 07:00; si eso
  queda en o después de la fecha límite, a las 21:30 previas; si ya pasó, se descarta.
- Máximo diario por usuario y día local [DECISIONES §4.4], con el orden de conservación definido allí.
- CORRECTIVA [PROPUESTA §12]: 1 h después de vencer y luego a las 19:00 locales, N días (Tranquilo: 0).
- Solo se planifica dentro de un horizonte (7 días): el plan se extiende al volver a sincronizar.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

RECORDATORIO = "RECORDATORIO"
URGENTE = "URGENTE"
CRITICA = "CRITICA"
CORRECTIVA = "CORRECTIVA"
NIVEL = {RECORDATORIO: 1, URGENTE: 2, CRITICA: 3, CORRECTIVA: 4}


@dataclass(frozen=True)
class ParametrosPlan:
    intervalos_horas: dict[str, int]  # tipo -> horas (del perfil elegido)
    maximo_diario: int
    dias_correctiva: int
    umbral_critica_horas: int = 24
    umbral_urgente_horas: int = 72
    umbral_recordatorio_horas: int = 168
    aviso_final_minutos: int = 60
    separacion_minima_minutos: int = 15
    silencio_inicio: time = time(22, 0)
    silencio_fin: time = time(7, 0)
    silencio_alternativa: time = time(21, 30)
    correctiva_primera_horas: int = 1
    correctiva_hora_diaria: time = time(19, 0)
    horizonte_horas: int = 168


@dataclass(frozen=True)
class TareaPlan:
    id_tarea: object
    titulo: str
    fecha_limite: datetime  # con zona horaria
    prioridad: int  # 1 baja .. 3 alta


@dataclass
class Aviso:
    id_tarea: object
    tipo: str
    fecha_programada: datetime
    es_aviso_final: bool = False
    # Datos para ordenar en el máximo diario; no se guardan.
    fecha_limite: datetime | None = field(default=None, compare=False)
    prioridad: int = field(default=2, compare=False)

    @property
    def nivel(self) -> int:
        return NIVEL[self.tipo]


def nivel_para(t_restante: timedelta, p: ParametrosPlan) -> str | None:
    """Tipo que corresponde a un aviso emitido cuando faltan `t_restante` para la fecha límite."""
    horas = t_restante.total_seconds() / 3600
    if horas <= 0:
        return CORRECTIVA
    if horas <= p.umbral_critica_horas:
        return CRITICA
    if horas <= p.umbral_urgente_horas:
        return URGENTE
    if horas <= p.umbral_recordatorio_horas:
        return RECORDATORIO
    return None  # más de 7 días: todavía no corresponde ningún aviso


def _en_silencio(momento: datetime, zona: ZoneInfo, p: ParametrosPlan) -> bool:
    hora = momento.astimezone(zona).time()
    if p.silencio_inicio <= p.silencio_fin:
        return p.silencio_inicio <= hora < p.silencio_fin
    return hora >= p.silencio_inicio or hora < p.silencio_fin


def _local(dia: date, hora: time, zona: ZoneInfo) -> datetime:
    return datetime.combine(dia, hora, tzinfo=zona)


def reubicar_por_silencio(
    momento: datetime, fecha_limite: datetime | None, zona: ZoneInfo, p: ParametrosPlan
) -> datetime | None:
    """Devuelve el momento fuera del horario de silencio, o None si no hay uno útil."""
    if not _en_silencio(momento, zona, p):
        return momento
    local = momento.astimezone(zona)
    # Día en que TERMINA este periodo de silencio (si ya pasó la hora de fin, es mañana).
    dia_fin = local.date() if local.time() < p.silencio_fin else local.date() + timedelta(days=1)
    despues = _local(dia_fin, p.silencio_fin, zona)
    if fecha_limite is None or despues < fecha_limite:
        return despues
    antes = _local(dia_fin - timedelta(days=1), p.silencio_alternativa, zona)
    return antes if antes < fecha_limite else None


def avisos_de_tarea(tarea: TareaPlan, ahora: datetime, zona: ZoneInfo, p: ParametrosPlan) -> list[Aviso]:
    """Plan de una tarea abierta, ya sin silencio y sin avisos a menos de 15 min entre sí."""
    limite = tarea.fecha_limite
    horizonte = ahora + timedelta(hours=p.horizonte_horas)
    crudos: list[Aviso] = []

    def agregar(tipo: str, momento: datetime, final: bool = False):
        crudos.append(Aviso(tarea.id_tarea, tipo, momento, final, limite, tarea.prioridad))

    # Niveles 1-3: múltiplos del intervalo de cada nivel, contados hacia atrás desde la fecha límite.
    for tipo in (RECORDATORIO, URGENTE, CRITICA):
        horas = p.intervalos_horas.get(tipo)
        if not horas or horas <= 0:
            continue
        n = 1
        while True:
            restante = timedelta(hours=horas * n)
            if restante.total_seconds() / 3600 > p.umbral_recordatorio_horas:
                break
            if nivel_para(restante, p) == tipo:
                agregar(tipo, limite - restante)
            n += 1
    agregar(CRITICA, limite - timedelta(minutes=p.aviso_final_minutos), final=True)

    # Nivel 4: tarea vencida y sin completar.
    primera = limite + timedelta(hours=p.correctiva_primera_horas)
    agregar(CORRECTIVA, primera)
    dia = primera.astimezone(zona).date()
    pendientes = p.dias_correctiva
    while pendientes > 0:
        momento = _local(dia, p.correctiva_hora_diaria, zona)
        if momento > primera:
            agregar(CORRECTIVA, momento)
            pendientes -= 1
        dia += timedelta(days=1)

    plan: list[Aviso] = []
    for aviso in crudos:
        tope = None if aviso.tipo == CORRECTIVA else limite
        momento = reubicar_por_silencio(aviso.fecha_programada, tope, zona, p)
        if momento is None or momento <= ahora or momento > horizonte:
            continue
        aviso.fecha_programada = momento.astimezone(ahora.tzinfo)
        plan.append(aviso)
    return _sin_avisos_cercanos(plan, p)


def _sin_avisos_cercanos(avisos: list[Aviso], p: ParametrosPlan) -> list[Aviso]:
    """Si dos avisos de la misma tarea quedan a menos de la separación mínima, se conserva el de mayor nivel
    (en empate, el aviso final y luego el más temprano)."""
    separacion = timedelta(minutes=p.separacion_minima_minutos)
    preferencia = sorted(avisos, key=lambda a: (-a.nivel, not a.es_aviso_final, a.fecha_programada))
    elegidos: list[Aviso] = []
    for aviso in preferencia:
        if all(abs(aviso.fecha_programada - e.fecha_programada) >= separacion for e in elegidos):
            elegidos.append(aviso)
    return sorted(elegidos, key=lambda a: a.fecha_programada)


def aplicar_maximo_diario(
    avisos: list[Aviso], zona: ZoneInfo, p: ParametrosPlan, ya_usados: dict[date, int] | None = None
) -> list[Aviso]:
    """Máximo por usuario y día local. `ya_usados` cuenta avisos de ese día que ya no se replanifican
    (enviados o con hora pasada). Orden de conservación (DECISIONES §4.4): aviso T-1 h, mayor nivel,
    fecha límite más cercana, prioridad más alta."""
    ya_usados = ya_usados or {}
    por_dia: dict[date, list[Aviso]] = {}
    for aviso in avisos:
        por_dia.setdefault(aviso.fecha_programada.astimezone(zona).date(), []).append(aviso)
    resultado: list[Aviso] = []
    for dia, lista in por_dia.items():
        cupo = max(p.maximo_diario - ya_usados.get(dia, 0), 0)
        lista.sort(key=lambda a: (not a.es_aviso_final, -a.nivel, a.fecha_limite, -a.prioridad, a.fecha_programada))
        resultado.extend(lista[:cupo])
    return sorted(resultado, key=lambda a: (a.fecha_programada, str(a.id_tarea)))


def planificar(
    tareas: list[TareaPlan],
    ahora: datetime,
    zona: ZoneInfo,
    p: ParametrosPlan,
    ya_usados: dict[date, int] | None = None,
) -> list[Aviso]:
    """Plan completo de un usuario (todas sus tareas abiertas)."""
    todos: list[Aviso] = []
    for tarea in tareas:
        todos.extend(avisos_de_tarea(tarea, ahora, zona, p))
    return aplicar_maximo_diario(todos, zona, p, ya_usados)
