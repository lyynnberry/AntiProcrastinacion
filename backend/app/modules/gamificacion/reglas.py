"""Reglas PURAS de gamificación (sin BD ni reloj): fáciles de probar y reutilizables.

Fuentes: V6 RF-21 a RF-27 y DECISIONES.md (§7 de RF-12 a RF-21 y la sección de gamificación).
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

# Resultados de un día (V6 §4.2 DIA_RACHA)
CUMPLIDO = "CUMPLIDO"
INCUMPLIDO = "INCUMPLIDO"
PROTEGIDO = "PROTEGIDO"
SIN_COMPROMISOS = "SIN_COMPROMISOS"


# ---- RF-21: tareas comprometidas y evaluación de un día ---------------------------------------
@dataclass(frozen=True)
class Compromiso:
    """Una tarea comprometida con un día, y el límite que debe cumplir ese día."""

    id_tarea: object
    limite: datetime  # fecha límite que cuenta para ese día
    fecha_completada: datetime | None  # None si no está completada


def limites_del_dia(dia: date, zona) -> tuple[datetime, datetime]:
    """[00:00 del día, 00:00 del día siguiente) en la zona del usuario."""
    inicio = datetime.combine(dia, time.min, tzinfo=zona)
    return inicio, datetime.combine(dia + timedelta(days=1), time.min, tzinfo=zona)


def dia_comprometido(fecha_programada: date | None, fecha_limite: datetime, zona) -> date:
    """§7 regla 3: el día de `fecha_programada` si existe; si no, el día local de la fecha límite."""
    return fecha_programada if fecha_programada is not None else fecha_limite.astimezone(zona).date()


def cumplida_en_plazo(c: Compromiso, fin_del_dia: datetime) -> bool:
    """RF-21 regla 2: completada dentro de su plazo. El plazo es su fecha límite y, para una tarea programada,
    además el fin del día comprometido [PROPUESTA §12 aprobada]. Exactamente en el límite cuenta (RF-12 r5)."""
    if c.fecha_completada is None:
        return False
    return c.fecha_completada <= c.limite and c.fecha_completada < fin_del_dia


@dataclass(frozen=True)
class ResultadoDia:
    resultado: str
    comprometidas: int
    cumplidas: int
    racha_previa: int
    racha_resultante: int


def evaluar_dia(racha_previa: int, compromisos: list[Compromiso], fin_del_dia: datetime) -> ResultadoDia:
    """RF-21 reglas 2 a 7."""
    total = len(compromisos)
    cumplidas = sum(1 for c in compromisos if cumplida_en_plazo(c, fin_del_dia))
    if total == 0:
        return ResultadoDia(SIN_COMPROMISOS, 0, 0, racha_previa, racha_previa)  # ni sube ni rompe
    if cumplidas == total:
        return ResultadoDia(CUMPLIDO, total, cumplidas, racha_previa, racha_previa + 1)
    return ResultadoDia(INCUMPLIDO, total, cumplidas, racha_previa, 0)  # rompe (salvo protección, RF-24)


def dias_pendientes(ultima_evaluada: date | None, primer_dia: date, hoy: date) -> list[date]:
    """§7 regla 12 (puesta al día): todos los días cerrados aún sin evaluar, en orden. Hoy no se evalúa
    porque todavía pueden agregarse compromisos (§7 regla 8)."""
    desde = max(primer_dia, ultima_evaluada + timedelta(days=1)) if ultima_evaluada else primer_dia
    return [desde + timedelta(days=i) for i in range((hoy - desde).days)] if desde < hoy else []


# ---- RF-22 -------------------------------------------------------------------------------------
def puntos_por_completar(a_tiempo: bool, puntos_a_tiempo: int, puntos_con_retraso: int) -> int:
    """RF-22 reglas 2 y 3: la tarea con retraso no recibe la misma recompensa."""
    return puntos_a_tiempo if a_tiempo else puntos_con_retraso


def nivel_para(puntos: int, puntos_por_nivel: int) -> int:
    return 1 + max(puntos, 0) // max(puntos_por_nivel, 1)


# ---- RF-23 -------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Indicadores:
    """Valores actuales con los que se comparan las condiciones de logros y recompensas."""

    racha_actual: int
    racha_maxima: int
    puntos_totales: int
    tareas_a_tiempo: int
    tareas_anticipadas: int

    def valor_para(self, tipo_condicion: str) -> int:
        # DIAS_RACHA usa la racha MÁXIMA: un logro de racha alcanzado no se "pierde" ni se revalida.
        return {
            "DIAS_RACHA": self.racha_maxima,
            "PUNTOS_TOTALES": self.puntos_totales,
            "TAREAS_A_TIEMPO": self.tareas_a_tiempo,
            "TAREAS_ANTICIPADAS": self.tareas_anticipadas,
        }[tipo_condicion]


def condicion_cumplida(tipo_condicion: str, valor_condicion: int, ind: Indicadores) -> bool:
    return ind.valor_para(tipo_condicion) >= valor_condicion


def progreso(tipo_condicion: str, valor_condicion: int, ind: Indicadores) -> tuple[int, int]:
    """(porcentaje 0-100, valor actual acotado al objetivo) para mostrar logros pendientes (RF-23 regla 6)."""
    actual = min(ind.valor_para(tipo_condicion), valor_condicion)
    return (actual * 100) // valor_condicion, actual


# ---- RF-27 -------------------------------------------------------------------------------------
def recompensa_por_racha(racha_resultante: int, racha_previa: int, cada_dias: int) -> bool:
    """+1 protección cada vez que un día CUMPLIDO lleva la racha a un múltiplo de `cada_dias`."""
    return cada_dias > 0 and racha_resultante > racha_previa and racha_resultante % cada_dias == 0


# ---- RF-25 -------------------------------------------------------------------------------------
def resolver_recuperacion(
    resultados_periodo: list[str], periodo_terminado: bool, atrasadas_completadas: bool
) -> str | None:
    """Estado al que pasa una recuperación ACTIVA, o None si sigue ACTIVA.
    - Un día INCUMPLIDO dentro del periodo la hace FALLIDA de inmediato (RF-25 regla 5).
    - Al terminar el periodo: EXITOSA si las tareas atrasadas se completaron; si no, FALLIDA."""
    if INCUMPLIDO in resultados_periodo:
        return "FALLIDA"
    if not periodo_terminado:
        return None
    return "EXITOSA" if atrasadas_completadas else "FALLIDA"
