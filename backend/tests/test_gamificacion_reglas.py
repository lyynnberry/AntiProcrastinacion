"""Reglas puras de gamificación (RF-21 a RF-27): sin base de datos ni reloj."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.modules.gamificacion import reglas
from app.modules.gamificacion.reglas import Compromiso, Indicadores

MX = ZoneInfo("America/Mexico_City")
D = date(2030, 3, 10)


def _c(limite, completada=None):
    return Compromiso(object(), limite, completada)


def _fin():
    return reglas.limites_del_dia(D, MX)[1]


# ---- RF-21 ---------------------------------------------------------------------------------------
def test_limites_del_dia_en_zona_del_usuario():
    inicio, fin = reglas.limites_del_dia(D, MX)
    assert inicio == datetime(2030, 3, 10, 6, tzinfo=timezone.utc)  # 00:00 CDMX = 06:00 UTC
    assert fin - inicio == timedelta(days=1)


def test_dia_comprometido_usa_programada_o_dia_local_del_limite():
    limite = datetime(2030, 3, 11, 5, 30, tzinfo=timezone.utc)  # 10 mar 23:30 en CDMX
    assert reglas.dia_comprometido(None, limite, MX) == date(2030, 3, 10)
    assert reglas.dia_comprometido(date(2030, 3, 8), limite, MX) == date(2030, 3, 8)
    assert reglas.dia_comprometido(None, limite, ZoneInfo("Asia/Tokyo")) == date(2030, 3, 11)


def test_cumplida_en_plazo_incluye_exactamente_el_limite():
    limite = datetime(2030, 3, 10, 20, tzinfo=MX)
    assert reglas.cumplida_en_plazo(_c(limite, limite), _fin())
    assert not reglas.cumplida_en_plazo(_c(limite, limite + timedelta(seconds=1)), _fin())
    assert not reglas.cumplida_en_plazo(_c(limite, None), _fin())


def test_tarea_programada_debe_cumplirse_antes_del_fin_del_dia_comprometido():
    limite = datetime(2030, 3, 12, 20, tzinfo=MX)  # límite dos días después
    assert reglas.cumplida_en_plazo(_c(limite, datetime(2030, 3, 10, 23, 59, tzinfo=MX)), _fin())
    assert not reglas.cumplida_en_plazo(_c(limite, datetime(2030, 3, 11, 0, 1, tzinfo=MX)), _fin())


def test_evaluar_dia_cumplido_incumplido_y_sin_compromisos():
    limite = datetime(2030, 3, 10, 20, tzinfo=MX)
    ok, mal = _c(limite, limite - timedelta(hours=1)), _c(limite, None)
    assert reglas.evaluar_dia(4, [ok, ok], _fin()) == reglas.ResultadoDia("CUMPLIDO", 2, 2, 4, 5)
    assert reglas.evaluar_dia(4, [ok, mal], _fin()) == reglas.ResultadoDia("INCUMPLIDO", 2, 1, 4, 0)
    assert reglas.evaluar_dia(4, [], _fin()) == reglas.ResultadoDia("SIN_COMPROMISOS", 0, 0, 4, 4)


def test_dias_pendientes_no_incluye_hoy_ni_dias_previos_al_perfil():
    assert reglas.dias_pendientes(None, D, D) == []
    assert reglas.dias_pendientes(None, D, D + timedelta(days=3)) == [D, D + timedelta(days=1), D + timedelta(days=2)]
    assert reglas.dias_pendientes(D + timedelta(days=1), D, D + timedelta(days=3)) == [D + timedelta(days=2)]
    assert reglas.dias_pendientes(D + timedelta(days=2), D, D + timedelta(days=3)) == []


# ---- RF-22 ---------------------------------------------------------------------------------------
def test_puntos_y_nivel():
    assert reglas.puntos_por_completar(True, 10, 0) == 10
    assert reglas.puntos_por_completar(False, 10, 0) == 0
    assert [reglas.nivel_para(p, 200) for p in (0, 199, 200, 650)] == [1, 1, 2, 4]
    assert reglas.nivel_para(-5, 200) == 1


# ---- RF-23 ---------------------------------------------------------------------------------------
IND = Indicadores(racha_actual=0, racha_maxima=8, puntos_totales=120, tareas_a_tiempo=3, tareas_anticipadas=1)


@pytest.mark.parametrize(
    "tipo,valor,esperado",
    [("DIAS_RACHA", 7, True), ("DIAS_RACHA", 30, False), ("PUNTOS_TOTALES", 100, True),
     ("TAREAS_A_TIEMPO", 10, False), ("TAREAS_ANTICIPADAS", 1, True)],
)
def test_condiciones_de_logros(tipo, valor, esperado):
    assert reglas.condicion_cumplida(tipo, valor, IND) is esperado


def test_logro_de_racha_usa_la_racha_maxima_y_no_se_pierde():
    assert IND.valor_para("DIAS_RACHA") == 8  # aunque la racha actual sea 0


def test_progreso_acotado_al_objetivo():
    assert reglas.progreso("TAREAS_A_TIEMPO", 10, IND) == (30, 3)
    assert reglas.progreso("PUNTOS_TOTALES", 100, IND) == (100, 100)


# ---- RF-27 ---------------------------------------------------------------------------------------
def test_recompensa_por_racha_solo_al_llegar_a_multiplos():
    assert reglas.recompensa_por_racha(7, 6, 7)
    assert reglas.recompensa_por_racha(14, 13, 7)
    assert not reglas.recompensa_por_racha(8, 7, 7)
    assert not reglas.recompensa_por_racha(7, 7, 7)  # protegido/sin compromisos: no "llega" de nuevo
    assert not reglas.recompensa_por_racha(7, 6, 0)


# ---- RF-25 ---------------------------------------------------------------------------------------
def test_resolver_recuperacion():
    assert reglas.resolver_recuperacion(["CUMPLIDO", "INCUMPLIDO"], False, True) == "FALLIDA"
    assert reglas.resolver_recuperacion(["CUMPLIDO"], False, True) is None
    assert reglas.resolver_recuperacion(["CUMPLIDO", "SIN_COMPROMISOS", "CUMPLIDO"], True, True) == "EXITOSA"
    assert reglas.resolver_recuperacion(["CUMPLIDO", "CUMPLIDO", "CUMPLIDO"], True, False) == "FALLIDA"
