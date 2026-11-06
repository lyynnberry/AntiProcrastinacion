"""RF-12 / RF-13: reglas PURAS del planificador (sin BD ni reloj real)."""
import uuid
from dataclasses import replace
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.modules.notificaciones import planificador as plan
from app.modules.notificaciones.service import parametros_para

UTC = timezone.utc
ZONA_UTC = ZoneInfo("UTC")
MEXICO = ZoneInfo("America/Mexico_City")
LIMITE = datetime(2027, 3, 10, 12, 0, tzinfo=UTC)  # miércoles 12:00 UTC
MUCHO_ANTES = LIMITE - timedelta(days=30)


def _params(perfil="equilibrado", **cambios):
    p = replace(parametros_para(perfil), horizonte_horas=100_000)  # plan completo, sin horizonte
    return replace(p, **cambios)


def _sin_silencio(perfil="equilibrado", **cambios):
    return _params(perfil, silencio_inicio=time(0, 0), silencio_fin=time(0, 0), **cambios)


def _tarea(limite=LIMITE, titulo="Ensayo", prioridad=2, id_tarea=None):
    return plan.TareaPlan(id_tarea or uuid.uuid4(), titulo, limite, prioridad)


def _restantes_horas(avisos, tipo):
    return sorted(((LIMITE - a.fecha_programada).total_seconds() / 3600 for a in avisos if a.tipo == tipo and not a.es_aviso_final), reverse=True)


# ---- niveles e intervalos (RF-13 reglas 1 y 2) -------------------------------------------------
def test_niveles_segun_tiempo_restante():
    p = _params()
    assert plan.nivel_para(timedelta(days=8), p) is None  # más de 7 días: todavía nada
    assert plan.nivel_para(timedelta(days=7), p) == plan.RECORDATORIO
    assert plan.nivel_para(timedelta(hours=72), p) == plan.URGENTE
    assert plan.nivel_para(timedelta(hours=24), p) == plan.CRITICA
    assert plan.nivel_para(timedelta(minutes=1), p) == plan.CRITICA
    assert plan.nivel_para(timedelta(0), p) == plan.CORRECTIVA


def test_equilibrado_respeta_los_intervalos_definidos():
    avisos = plan.avisos_de_tarea(_tarea(), MUCHO_ANTES, ZONA_UTC, _sin_silencio())
    assert _restantes_horas(avisos, plan.RECORDATORIO) == [168, 144, 120, 96]  # cada 24 h
    assert _restantes_horas(avisos, plan.URGENTE) == [72, 60, 48, 36]  # cada 12 h
    assert _restantes_horas(avisos, plan.CRITICA) == [24, 20, 16, 12, 8, 4]  # cada 4 h
    final = [a for a in avisos if a.es_aviso_final]
    assert len(final) == 1 and final[0].fecha_programada == LIMITE - timedelta(hours=1)
    assert final[0].tipo == plan.CRITICA


def test_la_frecuencia_aumenta_al_acercarse_la_fecha_limite():
    avisos = [a for a in plan.avisos_de_tarea(_tarea(), MUCHO_ANTES, ZONA_UTC, _sin_silencio()) if a.tipo != plan.CORRECTIVA]
    separaciones = [(b.fecha_programada - a.fecha_programada) for a, b in zip(avisos, avisos[1:])]
    assert separaciones == sorted(separaciones, reverse=True)  # nunca se alargan
    niveles = [a.nivel for a in avisos]
    assert niveles == sorted(niveles)  # el nivel nunca baja


def test_perfiles_cambian_la_cantidad_de_avisos():
    cuantos = {
        perfil: len([a for a in plan.avisos_de_tarea(_tarea(), MUCHO_ANTES, ZONA_UTC, _sin_silencio(perfil)) if a.tipo != plan.CORRECTIVA])
        for perfil in ("tranquilo", "equilibrado", "insistente")
    }
    assert cuantos["tranquilo"] < cuantos["equilibrado"] < cuantos["insistente"]
    tranquilo = plan.avisos_de_tarea(_tarea(), MUCHO_ANTES, ZONA_UTC, _sin_silencio("tranquilo"))
    assert _restantes_horas(tranquilo, plan.CRITICA) == [24, 16, 8]  # cada 8 h


def test_correctiva_despues_de_vencer():
    avisos = plan.avisos_de_tarea(_tarea(), MUCHO_ANTES, ZONA_UTC, _sin_silencio())
    correctivas = [a.fecha_programada for a in avisos if a.tipo == plan.CORRECTIVA]
    assert correctivas == [
        LIMITE + timedelta(hours=1),
        LIMITE.replace(hour=19),
        LIMITE.replace(hour=19) + timedelta(days=1),
        LIMITE.replace(hour=19) + timedelta(days=2),
    ]
    tranquilo = plan.avisos_de_tarea(_tarea(), MUCHO_ANTES, ZONA_UTC, _sin_silencio("tranquilo"))
    assert [a.fecha_programada for a in tranquilo if a.tipo == plan.CORRECTIVA] == [LIMITE + timedelta(hours=1)]


# ---- solo avisos futuros y dentro del horizonte ------------------------------------------------
def test_no_se_planifican_avisos_pasados():
    ahora = LIMITE - timedelta(hours=10)
    avisos = plan.avisos_de_tarea(_tarea(), ahora, ZONA_UTC, _sin_silencio())
    assert avisos and all(a.fecha_programada > ahora for a in avisos)


def test_tarea_a_mas_de_7_dias_no_recibe_avisos_hasta_entrar_al_horizonte():
    p = replace(parametros_para("equilibrado"), silencio_inicio=time(0, 0), silencio_fin=time(0, 0))
    lejana = LIMITE + timedelta(days=30)
    assert plan.avisos_de_tarea(_tarea(lejana), MUCHO_ANTES, ZONA_UTC, p) == []
    # 8 días antes de su fecha límite ya entra el primer recordatorio (T - 7 días) en el horizonte.
    assert plan.avisos_de_tarea(_tarea(lejana), lejana - timedelta(days=8), ZONA_UTC, p)


# ---- horario de silencio y zonas horarias ------------------------------------------------------
def test_ningun_aviso_cae_en_horario_de_silencio_en_la_zona_del_usuario():
    limite = datetime(2027, 3, 10, 14, 0, tzinfo=UTC)  # 08:00 en Ciudad de México (UTC-6)
    avisos = plan.avisos_de_tarea(_tarea(limite), limite - timedelta(days=30), MEXICO, _params())
    assert avisos
    for a in avisos:
        hora = a.fecha_programada.astimezone(MEXICO).time()
        assert time(7, 0) <= hora < time(22, 0), a


def test_aviso_en_silencio_se_mueve_a_las_7():
    p = _params()
    momento = datetime(2027, 3, 9, 3, 0, tzinfo=MEXICO)  # 03:00 local
    limite = datetime(2027, 3, 10, 12, 0, tzinfo=MEXICO)
    assert plan.reubicar_por_silencio(momento, limite, MEXICO, p) == datetime(2027, 3, 9, 7, 0, tzinfo=MEXICO)
    # 23:00 -> 07:00 del día siguiente
    momento = datetime(2027, 3, 8, 23, 0, tzinfo=MEXICO)
    assert plan.reubicar_por_silencio(momento, limite, MEXICO, p) == datetime(2027, 3, 9, 7, 0, tzinfo=MEXICO)


def test_si_las_7_ya_es_tarde_el_aviso_se_adelanta_a_las_2130():
    p = _params()
    limite = datetime(2027, 3, 10, 6, 30, tzinfo=MEXICO)  # vence antes de terminar el silencio
    momento = datetime(2027, 3, 10, 5, 30, tzinfo=MEXICO)  # T - 1 h, dentro del silencio
    assert plan.reubicar_por_silencio(momento, limite, MEXICO, p) == datetime(2027, 3, 9, 21, 30, tzinfo=MEXICO)


def test_zona_horaria_cambia_el_resultado():
    """El mismo instante UTC cae en silencio para un usuario y no para otro."""
    p = _params()
    momento = datetime(2027, 3, 10, 5, 0, tzinfo=UTC)  # 05:00 UTC = 23:00 del día anterior en CDMX
    assert plan.reubicar_por_silencio(momento, None, ZONA_UTC, p) != momento
    assert plan.reubicar_por_silencio(datetime(2027, 3, 10, 15, 0, tzinfo=UTC), None, MEXICO, p) == datetime(2027, 3, 10, 15, 0, tzinfo=UTC)


# ---- duplicados y separación mínima -----------------------------------------------------------
def test_avisos_de_una_tarea_nunca_quedan_a_menos_de_15_minutos():
    for perfil in ("tranquilo", "equilibrado", "insistente"):
        avisos = plan.avisos_de_tarea(_tarea(), MUCHO_ANTES, MEXICO, _params(perfil))
        momentos = [a.fecha_programada for a in avisos]
        assert len(momentos) == len(set(momentos))  # sin duplicados exactos
        assert all(b - a >= timedelta(minutes=15) for a, b in zip(momentos, momentos[1:]))


def test_al_chocar_dos_avisos_se_conserva_el_de_mayor_nivel():
    p = _sin_silencio()
    t = uuid.uuid4()
    a = plan.Aviso(t, plan.URGENTE, LIMITE)
    b = plan.Aviso(t, plan.CRITICA, LIMITE + timedelta(minutes=5))
    assert [x.tipo for x in plan._sin_avisos_cercanos([a, b], p)] == [plan.CRITICA]


def test_planificar_dos_veces_da_el_mismo_resultado():
    tareas = [_tarea(LIMITE + timedelta(hours=i * 7)) for i in range(3)]
    uno = plan.planificar(tareas, MUCHO_ANTES, MEXICO, _params())
    dos = plan.planificar(tareas, MUCHO_ANTES, MEXICO, _params())
    assert [(a.id_tarea, a.fecha_programada, a.tipo) for a in uno] == [(a.id_tarea, a.fecha_programada, a.tipo) for a in dos]


# ---- máximo diario ----------------------------------------------------------------------------
def test_maximo_diario_por_usuario_conserva_el_aviso_final_y_los_de_mayor_nivel():
    p = _sin_silencio("tranquilo")  # máximo 4 por día
    tareas = [_tarea(LIMITE + timedelta(minutes=30 * i), titulo=f"T{i}", id_tarea=uuid.uuid4()) for i in range(5)]
    avisos = plan.planificar(tareas, LIMITE - timedelta(hours=3), ZONA_UTC, p)
    por_dia = {}
    for a in avisos:
        por_dia.setdefault(a.fecha_programada.date(), []).append(a)
    assert all(len(lista) <= 4 for lista in por_dia.values())
    # Los cuatro conservados del día son avisos finales (prioritarios), de las fechas límite más cercanas.
    hoy = por_dia[LIMITE.date()]
    assert all(a.es_aviso_final for a in hoy)
    assert sorted(a.fecha_limite for a in hoy) == [t.fecha_limite for t in tareas[:4]]


def test_avisos_ya_usados_del_dia_ocupan_cupo():
    p = _sin_silencio("tranquilo")
    avisos = plan.planificar([_tarea()], LIMITE - timedelta(hours=10), ZONA_UTC, p, {LIMITE.date(): 4})
    assert [a for a in avisos if a.fecha_programada.date() == LIMITE.date()] == []
