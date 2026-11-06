"""RF-21 a RF-27 (gamificación) contra PostgreSQL real.

La mayoría de los escenarios usan el servicio con un reloj fijo (`ahora`) para recorrer varios días; los de
integración con tareas y los de la API usan el reloj real.
"""
import threading
import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.errors import Conflicto, NoEncontrado
from app.modules.gamificacion.models import (
    DiaRacha,
    Logro,
    LogroUsuario,
    PerfilGamificacion,
    RecuperacionRacha,
    TransaccionGamificacion,
)
from app.modules.gamificacion.service import GamificacionService, procesar_todos
from app.modules.historial import tipos
from app.modules.historial.repository import HistorialRepository
from app.modules.usuarios.models import Usuario

MX = ZoneInfo("America/Mexico_City")
D0 = date(2030, 3, 10)


def dia(n: int) -> date:
    return D0 + timedelta(days=n)


def en(n: int, h: int = 12, m: int = 0, zona=MX) -> datetime:
    return datetime.combine(dia(n), time(h, m), tzinfo=zona)


@pytest.fixture
def u(db, usuario_a) -> Usuario:
    usuario = db.get(Usuario, usuario_a.id)
    usuario.zona_horaria = "America/Mexico_City"
    db.commit()
    return usuario


@pytest.fixture
def g(db) -> GamificacionService:
    return GamificacionService(db)


@pytest.fixture
def iniciar(g, u, db):
    """Crea el perfil el día D0: primer día evaluable = D0."""

    def _iniciar(usuario=None):
        g.poner_al_dia(usuario or u, en(0, 7))
        db.commit()

    return _iniciar


@pytest.fixture
def tarea(insertar_tarea, u):
    def _tarea(n, h=20, completada=None, usuario=None, **extra):
        return insertar_tarea(
            (usuario or u).id_usuario,
            fecha_limite=en(n, h),
            estado="COMPLETADA" if completada else "PENDIENTE",
            fecha_completada=completada,
            **extra,
        )

    return _tarea


def evaluar(g, db, usuario, n, h=8):
    perfil = g.poner_al_dia(usuario, en(n, h))
    db.commit()
    return perfil


def dias(db, usuario):
    db.expire_all()
    return {d.fecha: d for d in db.scalars(select(DiaRacha).where(DiaRacha.id_usuario == usuario.id_usuario))}


def movimientos(db, usuario, **filtro):
    db.expire_all()
    q = select(TransaccionGamificacion).where(TransaccionGamificacion.id_usuario == usuario.id_usuario)
    for campo, valor in filtro.items():
        q = q.where(getattr(TransaccionGamificacion, campo) == valor)
    return list(db.scalars(q))


def racha_de(g, db, u, tarea, iniciar, n_dias):
    """Cumple los días 0..n_dias-1 y evalúa en la mañana del día n_dias."""
    iniciar()
    for n in range(n_dias):
        tarea(n, completada=en(n, 10))
    return evaluar(g, db, u, n_dias)


# =========================================================================================== RF-21
class TestRacha:
    def test_dia_sin_compromisos_no_sube_ni_rompe(self, g, db, u, iniciar):
        iniciar()
        perfil = evaluar(g, db, u, 1)
        assert perfil.racha_actual == 0
        assert dias(db, u)[dia(0)].resultado == "SIN_COMPROMISOS"

    def test_dias_cumplidos_consecutivos_aumentan_la_racha(self, g, db, u, iniciar, tarea):
        perfil = racha_de(g, db, u, tarea, iniciar, 3)
        assert (perfil.racha_actual, perfil.racha_maxima) == (3, 3)
        d = dias(db, u)[dia(2)]
        assert (d.resultado, d.tareas_comprometidas, d.tareas_cumplidas_a_tiempo) == ("CUMPLIDO", 1, 1)
        assert (d.racha_previa, d.racha_resultante) == (2, 3)

    def test_una_tarea_sin_cumplir_rompe_la_racha_pero_no_la_maxima(self, g, db, u, iniciar, tarea):
        racha_de(g, db, u, tarea, iniciar, 2)
        tarea(2, completada=en(2, 9))
        tarea(2)  # no completada
        perfil = evaluar(g, db, u, 3)
        assert (perfil.racha_actual, perfil.racha_maxima) == (0, 2)
        d = dias(db, u)[dia(2)]
        assert (d.resultado, d.tareas_comprometidas, d.tareas_cumplidas_a_tiempo, d.racha_previa) == ("INCUMPLIDO", 2, 1, 2)

    def test_completada_tarde_no_cuenta_y_exactamente_en_el_limite_si(self, g, db, u, iniciar, tarea):
        iniciar()
        tarea(0, h=20, completada=en(0, 20))  # exactamente en el límite
        tarea(1, h=20, completada=en(1, 20, 1))  # un minuto tarde
        evaluar(g, db, u, 2)
        assert dias(db, u)[dia(0)].resultado == "CUMPLIDO"
        assert dias(db, u)[dia(1)].resultado == "INCUMPLIDO"

    def test_hoy_no_se_evalua(self, g, db, u, iniciar, tarea):
        iniciar()
        tarea(0)
        evaluar(g, db, u, 0, h=23)
        assert dias(db, u) == {}

    def test_puesta_al_dia_evalua_todos_los_dias_pendientes_en_orden(self, g, db, u, iniciar, tarea):
        iniciar()
        tarea(0, completada=en(0, 9))
        tarea(1, completada=en(1, 9))
        tarea(3)  # incumple el día 3
        perfil = evaluar(g, db, u, 5)
        r = dias(db, u)
        assert [r[dia(i)].resultado for i in range(5)] == ["CUMPLIDO", "CUMPLIDO", "SIN_COMPROMISOS", "INCUMPLIDO", "SIN_COMPROMISOS"]
        assert (perfil.racha_actual, perfil.racha_maxima, perfil.ultima_fecha_evaluada) == (0, 2, dia(4))

    def test_evaluacion_idempotente_y_dias_cerrados_inmutables(self, g, db, u, iniciar, tarea):
        iniciar()
        t = tarea(0)
        evaluar(g, db, u, 1)
        t.estado, t.fecha_completada = "COMPLETADA", en(1, 9)  # se completa después
        db.commit()
        evaluar(g, db, u, 1, h=18)
        evaluar(g, db, u, 1, h=19)
        assert len(dias(db, u)) == 1
        assert dias(db, u)[dia(0)].resultado == "INCUMPLIDO"

    def test_bd_impide_dos_evaluaciones_del_mismo_dia(self, db, u, iniciar):
        iniciar()
        for _ in range(2):
            db.add(DiaRacha(id_usuario=u.id_usuario, fecha=dia(0), resultado="CUMPLIDO", tareas_comprometidas=1,
                            tareas_cumplidas_a_tiempo=1, racha_previa=0, racha_resultante=1))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_no_hay_racha_retroactiva(self, g, db, u, tarea):
        tarea(-2, completada=en(-2, 9))
        tarea(-1)
        g.poner_al_dia(u, en(0, 7))
        db.commit()
        perfil = evaluar(g, db, u, 1)
        assert perfil.primer_dia_evaluable == dia(0)
        assert set(dias(db, u)) == {dia(0)}

    def test_fecha_programada_compromete_ese_dia(self, g, db, u, iniciar, tarea):
        iniciar()
        tarea(3, fecha_programada=dia(1), titulo="Programada")
        tarea(3, completada=en(1, 15), fecha_programada=dia(1))
        perfil = evaluar(g, db, u, 2)
        r = dias(db, u)
        assert (r[dia(1)].resultado, r[dia(1)].tareas_comprometidas, r[dia(1)].tareas_cumplidas_a_tiempo) == ("INCUMPLIDO", 2, 1)
        assert perfil.racha_actual == 0

    def test_tarea_programada_completada_despues_del_dia_no_cumple(self, g, db, u, iniciar, tarea):
        iniciar()
        tarea(3, completada=en(2, 9), fecha_programada=dia(1))  # a tiempo para su límite, tarde para su día
        evaluar(g, db, u, 4)
        r = dias(db, u)
        assert r[dia(1)].resultado == "INCUMPLIDO"
        assert r[dia(3)].resultado == "SIN_COMPROMISOS"  # ya no cuenta para el día de su límite

    def test_antitrampa_posponer_durante_el_dia_no_salva_la_racha(self, g, db, u, iniciar, tarea):
        iniciar()
        t = tarea(1, h=20)
        antes = t.fecha_limite
        t.fecha_limite = en(4, 20)  # se pospone el día 1 a las 15:00
        HistorialRepository(db).registrar(
            id_usuario=u.id_usuario, id_tarea=t.id_tarea, tipo_evento=tipos.TAREA_POSPUESTA,
            datos={"antes": antes.isoformat(), "despues": t.fecha_limite.isoformat()}, fecha_evento=en(1, 15),
        )
        db.commit()
        evaluar(g, db, u, 2)
        assert dias(db, u)[dia(1)].resultado == "INCUMPLIDO"

    def test_posponer_antes_del_dia_si_cambia_el_compromiso(self, g, db, u, iniciar, tarea):
        iniciar()
        t = tarea(2, h=20)
        antes = t.fecha_limite
        t.fecha_limite = en(4, 20)
        HistorialRepository(db).registrar(
            id_usuario=u.id_usuario, id_tarea=t.id_tarea, tipo_evento=tipos.TAREA_POSPUESTA,
            datos={"antes": antes.isoformat(), "despues": t.fecha_limite.isoformat()}, fecha_evento=en(0, 15),
        )
        db.commit()
        evaluar(g, db, u, 3)
        assert dias(db, u)[dia(2)].resultado == "SIN_COMPROMISOS"

    def test_antitrampa_eliminar_durante_el_dia(self, g, db, u, iniciar, tarea):
        iniciar()
        vieja = tarea(1)
        vieja.fecha_eliminacion = en(1, 10)
        duplicado = tarea(2, fecha_creacion=en(2, 9))  # creado por error el mismo día y eliminado
        duplicado.fecha_eliminacion = en(2, 9, 5)
        antigua = tarea(3)
        antigua.fecha_eliminacion = en(0, 10)  # eliminada antes de su día
        db.commit()
        evaluar(g, db, u, 4)
        r = dias(db, u)
        assert r[dia(1)].resultado == "INCUMPLIDO"
        assert r[dia(2)].resultado == "SIN_COMPROMISOS"
        assert r[dia(3)].resultado == "SIN_COMPROMISOS"

    def test_zona_horaria_define_el_dia(self, g, db, u, iniciar, insertar_tarea, crear_usuario):
        iniciar()
        # 10 mar 23:30 en CDMX = 11 mar 05:30 UTC: cuenta para el 10 de marzo del usuario.
        limite = datetime(2030, 3, 11, 5, 30, tzinfo=timezone.utc)
        insertar_tarea(u.id_usuario, fecha_limite=limite, estado="COMPLETADA", fecha_completada=limite - timedelta(minutes=5))
        evaluar(g, db, u, 1, h=1)  # 11 mar 01:00 en CDMX
        assert dias(db, u)[dia(0)].resultado == "CUMPLIDO"

        tokio = db.get(Usuario, crear_usuario().id)
        tokio.zona_horaria = "Asia/Tokyo"
        db.commit()
        g.poner_al_dia(tokio, datetime(2030, 3, 10, 8, tzinfo=ZoneInfo("Asia/Tokyo")))
        insertar_tarea(tokio.id_usuario, fecha_limite=limite)  # 11 mar 14:30 en Tokio
        g.poner_al_dia(tokio, datetime(2030, 3, 12, 8, tzinfo=ZoneInfo("Asia/Tokyo")))
        db.commit()
        r = dias(db, tokio)
        assert r[date(2030, 3, 10)].resultado == "SIN_COMPROMISOS"
        assert r[date(2030, 3, 11)].resultado == "INCUMPLIDO"

    def test_tareas_de_otro_usuario_no_afectan(self, g, db, u, iniciar, tarea, crear_usuario):
        otro = db.get(Usuario, crear_usuario().id)
        iniciar()
        tarea(0, usuario=otro)
        perfil = evaluar(g, db, u, 1)
        assert dias(db, u)[dia(0)].resultado == "SIN_COMPROMISOS"
        assert perfil.racha_actual == 0


# =========================================================================================== RF-22
def _crear_api(client, usuario, **delta):
    limite = (datetime.now(timezone.utc) + timedelta(**(delta or {"days": 3}))).isoformat()
    r = client.post("/tareas", json={"titulo": "Ensayo", "fecha_limite": limite, "prioridad": "ALTA"}, headers=usuario.headers)
    assert r.status_code == 201, r.text
    return r.json()


def _estado(client, usuario, id_tarea, estado):
    r = client.patch(f"/tareas/{id_tarea}", json={"estado": estado}, headers=usuario.headers)
    assert r.status_code == 200, r.text
    return r.json()


def _progreso(client, usuario):
    r = client.get("/gamificacion/progreso", headers=usuario.headers)
    assert r.status_code == 200, r.text
    return r.json()


class TestPuntos:
    def test_completar_a_tiempo_suma_puntos_y_registra_movimiento(self, client, db, usuario_a):
        t = _crear_api(client, usuario_a, hours=5)  # a tiempo pero no anticipada
        _estado(client, usuario_a, t["id_tarea"], "COMPLETADA")
        usuario = db.get(Usuario, usuario_a.id)
        mov = movimientos(db, usuario, motivo="TAREA_A_TIEMPO")
        assert [(m.cantidad, str(m.id_tarea)) for m in mov] == [(10, t["id_tarea"])]
        p = _progreso(client, usuario_a)
        assert p["puntos_totales"] == 10 + 5  # + logro A_TIEMPO_1
        assert p["tareas_a_tiempo"] == 1

    def test_completar_con_retraso_no_da_puntos(self, client, db, usuario_a, insertar_tarea):
        t = insertar_tarea(usuario_a.id, fecha_limite=datetime.now(timezone.utc) - timedelta(hours=2))
        _estado(client, usuario_a, str(t.id_tarea), "COMPLETADA")
        assert movimientos(db, db.get(Usuario, usuario_a.id)) == []
        assert _progreso(client, usuario_a)["puntos_totales"] == 0

    def test_reabrir_y_completar_de_nuevo_no_duplica(self, client, db, usuario_a):
        t = _crear_api(client, usuario_a, hours=5)
        _estado(client, usuario_a, t["id_tarea"], "COMPLETADA")
        _estado(client, usuario_a, t["id_tarea"], "PENDIENTE")
        _estado(client, usuario_a, t["id_tarea"], "COMPLETADA")
        usuario = db.get(Usuario, usuario_a.id)
        assert len(movimientos(db, usuario, motivo="TAREA_A_TIEMPO")) == 1
        assert _progreso(client, usuario_a)["puntos_totales"] == 15  # reabrir no resta

    def test_llamada_repetida_del_servicio_es_idempotente(self, g, db, u, iniciar, tarea):
        iniciar()
        t = tarea(1, completada=en(0, 9))
        for _ in range(3):
            g.tarea_completada(u, t.id_tarea, True, en(0, 9))
        db.commit()
        assert len(movimientos(db, u, motivo="TAREA_A_TIEMPO")) == 1

    def test_bd_rechaza_clave_duplicada(self, db, u, iniciar):
        iniciar()
        for _ in range(2):
            db.add(TransaccionGamificacion(id_usuario=u.id_usuario, recurso="PUNTOS", cantidad=10,
                                           motivo="TAREA_A_TIEMPO", clave_idempotencia="TAREA_A_TIEMPO:x"))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_bd_rechaza_puntos_negativos(self, db, u, iniciar):
        iniciar()
        with pytest.raises(IntegrityError):
            db.execute(text("UPDATE perfil_gamificacion SET puntos_totales = -1"))
        db.rollback()

    def test_servicio_no_deja_puntos_negativos(self, g, db, u, iniciar):
        iniciar()
        perfil = g._perfil(u, en(0, 9))
        assert g._movimiento(u, perfil, "PUNTOS", -5, "RECOMPENSA", "AJUSTE:1", en(0, 9)) is False
        assert perfil.puntos_totales == 0

    def test_nivel_sube_con_los_puntos(self, g, db, u, iniciar):
        iniciar()
        perfil = g._perfil(u, en(0, 9))
        g._movimiento(u, perfil, "PUNTOS", settings.gam_puntos_por_nivel, "RECOMPENSA", "PRUEBA:NIVEL", en(0, 9))
        db.commit()
        assert perfil.nivel == 2

    def test_gamificacion_va_en_la_misma_transaccion_que_la_tarea(self, client, db, usuario_a, monkeypatch):
        from app.modules.notificaciones.service import NotificacionService

        t = _crear_api(client, usuario_a, hours=5)

        def falla(*a, **k):
            raise RuntimeError("fallo simulado")

        monkeypatch.setattr(NotificacionService, "replanificar", falla)
        with pytest.raises(RuntimeError):
            client.patch(f"/tareas/{t['id_tarea']}", json={"estado": "COMPLETADA"}, headers=usuario_a.headers)
        assert movimientos(db, db.get(Usuario, usuario_a.id)) == []

    def test_completado_simultaneo_solo_suma_una_vez(self, engine, db, u, iniciar, tarea):
        iniciar()
        t = tarea(1, completada=en(0, 9))
        fabrica = sessionmaker(bind=engine, expire_on_commit=False)
        barrera, errores = threading.Barrier(2), []

        def trabajar():
            try:
                with fabrica() as s:
                    usuario = s.get(Usuario, u.id_usuario)
                    barrera.wait()
                    GamificacionService(s).tarea_completada(usuario, t.id_tarea, True, en(0, 9))
                    s.commit()
            except Exception as e:  # pragma: no cover - se reporta abajo
                errores.append(e)

        hilos = [threading.Thread(target=trabajar) for _ in range(2)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        assert errores == []
        assert len(movimientos(db, u, motivo="TAREA_A_TIEMPO")) == 1
        db.expire_all()
        assert db.get(PerfilGamificacion, u.id_usuario).puntos_totales == 10 + 5


# =========================================================================================== RF-23
class TestLogros:
    def test_catalogo_inicial_cargado_por_la_migracion(self, db):
        codigos = set(db.scalars(select(Logro.codigo)))
        assert len(codigos) == 12
        assert {"RACHA_3", "A_TIEMPO_1", "PUNTOS_100", "ANTICIPADA_1"} <= codigos
        assert set(db.scalars(select(Logro.categoria))) == {"RACHA", "VELOCIDAD", "PRODUCTIVIDAD", "CONSTANCIA"}

    def test_logro_se_desbloquea_una_vez_con_fecha_y_puntos(self, g, db, u, iniciar, tarea):
        iniciar()
        t = tarea(1, completada=en(0, 9))
        g.tarea_completada(u, t.id_tarea, True, en(0, 9))
        g.tarea_completada(u, t.id_tarea, True, en(0, 10))
        db.commit()
        obtenidos = list(db.scalars(select(LogroUsuario).where(LogroUsuario.id_usuario == u.id_usuario)))
        assert len(obtenidos) == 1
        assert obtenidos[0].fecha_desbloqueo == en(0, 9)
        assert [m.cantidad for m in movimientos(db, u, motivo="LOGRO_DESBLOQUEADO")] == [5]

    def test_bd_impide_logro_duplicado(self, db, u, iniciar):
        iniciar()
        id_logro = db.scalar(select(Logro.id_logro).where(Logro.codigo == "RACHA_3"))
        for _ in range(2):
            db.add(LogroUsuario(id_usuario=u.id_usuario, id_logro=id_logro, fecha_desbloqueo=en(0, 9)))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_logro_de_racha_se_conserva_al_perder_la_racha(self, g, db, u, iniciar, tarea):
        racha_de(g, db, u, tarea, iniciar, 3)
        tarea(3)
        evaluar(g, db, u, 4)
        p = g.progreso(u, en(4, 9))
        codigos = {x["codigo"] for x in p["logros_desbloqueados"]}
        assert "RACHA_3" in codigos and p["racha_actual"] == 0

    def test_logro_anticipada_requiere_24_horas(self, client, db, usuario_a):
        rapida = _crear_api(client, usuario_a, hours=30)
        justa = _crear_api(client, usuario_a, hours=23)
        _estado(client, usuario_a, justa["id_tarea"], "COMPLETADA")
        p = _progreso(client, usuario_a)
        assert "ANTICIPADA_1" not in {x["codigo"] for x in p["logros_desbloqueados"]}
        _estado(client, usuario_a, rapida["id_tarea"], "COMPLETADA")
        p = _progreso(client, usuario_a)
        assert "ANTICIPADA_1" in {x["codigo"] for x in p["logros_desbloqueados"]}

    def test_progreso_de_logros_pendientes(self, client, usuario_a):
        _estado(client, usuario_a, _crear_api(client, usuario_a, hours=5)["id_tarea"], "COMPLETADA")
        pendientes = {x["codigo"]: x for x in _progreso(client, usuario_a)["logros_pendientes"]}
        assert (pendientes["A_TIEMPO_10"]["valor_actual"], pendientes["A_TIEMPO_10"]["progreso"]) == (1, 10)
        assert pendientes["PUNTOS_100"]["valor_actual"] == 15

    def test_logros_en_el_idioma_del_usuario(self, client, usuario_a):
        assert client.patch("/usuarios/me", json={"idioma": "en"}, headers=usuario_a.headers).status_code == 200
        r = client.get("/gamificacion/logros", headers=usuario_a.headers)
        nombres = {x["codigo"]: x["nombre"] for x in r.json()}
        assert nombres["RACHA_7"] == "Solid week"

    def test_puntos_de_un_logro_pueden_desbloquear_otro(self, g, db, u, iniciar, tarea, monkeypatch):
        monkeypatch.setattr(settings, "gam_puntos_tarea_a_tiempo", 95)
        iniciar()
        t = tarea(1, completada=en(0, 9))
        g.tarea_completada(u, t.id_tarea, True, en(0, 9))  # 95 + 5 (A_TIEMPO_1) = 100 -> PUNTOS_100 (+10)
        db.commit()
        db.expire_all()
        assert db.get(PerfilGamificacion, u.id_usuario).puntos_totales == 110
        assert {m.clave_idempotencia for m in movimientos(db, u, motivo="LOGRO_DESBLOQUEADO")} == {"LOGRO:A_TIEMPO_1", "LOGRO:PUNTOS_100"}

    def test_logro_inactivo_no_se_otorga(self, g, db, u, iniciar, tarea):
        logro = db.scalar(select(Logro).where(Logro.codigo == "A_TIEMPO_1"))
        logro.activo = False
        db.commit()
        try:
            iniciar()
            t = tarea(1, completada=en(0, 9))
            g.tarea_completada(u, t.id_tarea, True, en(0, 9))
            db.commit()
            assert movimientos(db, u, motivo="LOGRO_DESBLOQUEADO") == []
        finally:
            logro.activo = True
            db.commit()


# ===================================================================================== RF-24 / RF-27
def _siete_y_falla(g, db, u, tarea, iniciar):
    """Racha de 7 (gana 1 protección) e incumple el día 7. Devuelve el perfil evaluado el día 8."""
    racha_de(g, db, u, tarea, iniciar, 7)
    tarea(7, completada=en(7, 9))
    tarea(7)
    return evaluar(g, db, u, 8)


class TestProteccionYRecompensas:
    def test_racha_de_7_da_una_proteccion_una_sola_vez(self, g, db, u, iniciar, tarea):
        perfil = racha_de(g, db, u, tarea, iniciar, 7)
        evaluar(g, db, u, 7, h=20)
        assert perfil.protecciones_disponibles == 1
        mov = movimientos(db, u, codigo_recompensa="RACHA_PERIODO")
        assert [(m.recurso, m.cantidad, m.motivo) for m in mov] == [("PROTECCION_RACHA", 1, "RECOMPENSA")]

    def test_usar_proteccion_conserva_la_racha(self, g, db, u, iniciar, tarea):
        perfil = _siete_y_falla(g, db, u, tarea, iniciar)
        assert (perfil.racha_actual, perfil.protecciones_disponibles) == (0, 1)
        perfil = g.usar_proteccion(u, en(8, 9))
        assert (perfil.racha_actual, perfil.racha_maxima, perfil.protecciones_disponibles) == (7, 7, 0)
        d = dias(db, u)[dia(7)]
        assert (d.resultado, d.tareas_comprometidas, d.tareas_cumplidas_a_tiempo, d.racha_resultante) == ("PROTEGIDO", 2, 1, 7)
        assert [m.cantidad for m in movimientos(db, u, motivo="PROTECCION_USADA")] == [-1]
        tarea(8, completada=en(8, 10))
        assert evaluar(g, db, u, 9).racha_actual == 8  # la racha continúa

    def test_sin_protecciones_no_se_puede(self, g, db, u, iniciar, tarea):
        racha_de(g, db, u, tarea, iniciar, 2)
        tarea(2)
        evaluar(g, db, u, 3)
        with pytest.raises(Conflicto) as e:
            g.usar_proteccion(u, en(3, 9))
        assert e.value.codigo == "SIN_PROTECCIONES"

    def test_nada_que_proteger(self, g, db, u, iniciar, tarea):
        racha_de(g, db, u, tarea, iniciar, 7)
        with pytest.raises(Conflicto) as e:
            g.usar_proteccion(u, en(7, 9))
        assert e.value.codigo == "NADA_QUE_PROTEGER"

    def test_no_se_puede_proteger_un_incumplimiento_antiguo(self, g, db, u, iniciar, tarea):
        _siete_y_falla(g, db, u, tarea, iniciar)
        evaluar(g, db, u, 9)  # se evaluó el día siguiente
        with pytest.raises(Conflicto) as e:
            g.usar_proteccion(u, en(9, 9))
        assert e.value.codigo == "NADA_QUE_PROTEGER"

    def test_proteccion_simultanea_solo_se_aplica_una_vez(self, engine, g, db, u, iniciar, tarea):
        _siete_y_falla(g, db, u, tarea, iniciar)
        perfil = g._perfil(u, en(8, 9))
        g._movimiento(u, perfil, "PROTECCION_RACHA", 1, "RECOMPENSA", "PRUEBA:EXTRA", en(8, 9))
        db.commit()
        fabrica = sessionmaker(bind=engine, expire_on_commit=False)
        barrera, resultados = threading.Barrier(2), []

        def trabajar():
            with fabrica() as s:
                usuario = s.get(Usuario, u.id_usuario)
                barrera.wait()
                try:
                    GamificacionService(s).usar_proteccion(usuario, en(8, 9))
                    resultados.append("ok")
                except Conflicto as e:
                    resultados.append(e.codigo)
                    s.rollback()

        hilos = [threading.Thread(target=trabajar) for _ in range(2)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        assert sorted(resultados) == ["NADA_QUE_PROTEGER", "ok"]
        db.expire_all()
        assert db.get(PerfilGamificacion, u.id_usuario).protecciones_disponibles == 1
        assert len(movimientos(db, u, motivo="PROTECCION_USADA")) == 1

    def test_maximo_de_protecciones(self, g, db, u, iniciar):
        iniciar()
        perfil = g._perfil(u, en(0, 9))
        aplicadas = [g._movimiento(u, perfil, "PROTECCION_RACHA", 1, "RECOMPENSA", f"PRUEBA:{i}", en(0, 9)) for i in range(4)]
        db.commit()
        assert aplicadas == [True, True, True, False]
        assert perfil.protecciones_disponibles == settings.gam_max_protecciones == 3

    def test_bd_impide_protecciones_negativas(self, db, u, iniciar):
        iniciar()
        with pytest.raises(IntegrityError):
            db.execute(text("UPDATE perfil_gamificacion SET protecciones_disponibles = -1"))
        db.rollback()

    def test_recompensa_por_puntos_acumulados_una_vez(self, g, db, u, iniciar):
        iniciar()
        perfil = g._perfil(u, en(0, 9))
        g._movimiento(u, perfil, "PUNTOS", 600, "RECOMPENSA", "PRUEBA:PUNTOS", en(0, 9))
        g._revisar_logros_y_recompensas(u, perfil, en(0, 9))
        g._revisar_logros_y_recompensas(u, perfil, en(0, 10))
        db.commit()
        assert len(movimientos(db, u, codigo_recompensa="PUNTOS_ACUMULADOS")) == 1
        assert perfil.protecciones_disponibles == 1


# =========================================================================================== RF-25
class TestRecuperacion:
    def _perder(self, g, db, u, tarea, iniciar, n=3):
        """Racha de n y la pierde el día n por una tarea pendiente. Evalúa el día n+1."""
        racha_de(g, db, u, tarea, iniciar, n)
        atrasada = tarea(n)
        evaluar(g, db, u, n + 1)
        return atrasada

    def test_iniciar_registra_racha_y_tareas_atrasadas(self, g, db, u, iniciar, tarea):
        atrasada = self._perder(g, db, u, tarea, iniciar)
        rec = g.iniciar_recuperacion(u, en(4, 9))
        assert (rec.estado, rec.racha_perdida, rec.tareas_atrasadas) == ("ACTIVA", 3, [str(atrasada.id_tarea)])
        assert (rec.fecha_inicio, rec.fecha_fin_prevista) == (dia(4), dia(6))

    def test_exitosa_restaura_la_racha(self, g, db, u, iniciar, tarea):
        atrasada = self._perder(g, db, u, tarea, iniciar)
        g.iniciar_recuperacion(u, en(4, 9))
        atrasada.estado, atrasada.fecha_completada = "COMPLETADA", en(4, 10)  # tarde, pero se atiende
        for n in (4, 5, 6):
            tarea(n, completada=en(n, 11))
        db.commit()
        perfil = evaluar(g, db, u, 7)
        rec = db.scalar(select(RecuperacionRacha))
        assert (rec.estado, rec.racha_restaurada, rec.motivo_resolucion) == ("EXITOSA", 6, "CONDICIONES_CUMPLIDAS")
        assert (perfil.racha_actual, perfil.racha_maxima) == (6, 6)

    def test_nuevo_incumplimiento_la_hace_fallida(self, g, db, u, iniciar, tarea):
        self._perder(g, db, u, tarea, iniciar)
        g.iniciar_recuperacion(u, en(4, 9))
        tarea(4)
        perfil = evaluar(g, db, u, 5)
        rec = db.scalar(select(RecuperacionRacha))
        assert (rec.estado, rec.motivo_resolucion) == ("FALLIDA", "NUEVO_INCUMPLIMIENTO")
        assert perfil.racha_actual == 0

    def test_sin_atender_las_atrasadas_falla_al_terminar(self, g, db, u, iniciar, tarea):
        self._perder(g, db, u, tarea, iniciar)
        g.iniciar_recuperacion(u, en(4, 9))
        evaluar(g, db, u, 6)
        assert db.scalar(select(RecuperacionRacha.estado)) == "ACTIVA"  # aún no termina el periodo
        evaluar(g, db, u, 7)
        db.expire_all()
        rec = db.scalar(select(RecuperacionRacha))
        assert (rec.estado, rec.motivo_resolucion) == ("FALLIDA", "TAREAS_ATRASADAS_PENDIENTES")

    def test_cancelar_y_no_reintentar_la_misma_racha(self, g, db, u, iniciar, tarea):
        self._perder(g, db, u, tarea, iniciar)
        rec = g.iniciar_recuperacion(u, en(4, 9))
        rec = g.cancelar_recuperacion(u, rec.id_recuperacion, en(4, 10))
        assert rec.estado == "CANCELADA"
        with pytest.raises(Conflicto) as e:
            g.cancelar_recuperacion(u, rec.id_recuperacion, en(4, 11))
        assert e.value.codigo == "RECUPERACION_NO_ACTIVA"
        with pytest.raises(Conflicto) as e:
            g.iniciar_recuperacion(u, en(4, 12))
        assert e.value.codigo == "SIN_RACHA_PERDIDA"

    def test_solo_una_activa(self, g, db, u, iniciar, tarea):
        self._perder(g, db, u, tarea, iniciar)
        g.iniciar_recuperacion(u, en(4, 9))
        with pytest.raises(Conflicto) as e:
            g.iniciar_recuperacion(u, en(4, 10))
        assert e.value.codigo == "RECUPERACION_ACTIVA"

    def test_bd_impide_dos_activas(self, db, u, iniciar):
        iniciar()
        for n in (0, 1):
            d = DiaRacha(id_usuario=u.id_usuario, fecha=dia(n), resultado="INCUMPLIDO", tareas_comprometidas=1,
                         tareas_cumplidas_a_tiempo=0, racha_previa=2, racha_resultante=0)
            db.add(d)
            db.flush()
            db.add(RecuperacionRacha(id_usuario=u.id_usuario, id_dia_perdido=d.id_dia_racha, racha_perdida=2,
                                     tareas_atrasadas=[], fecha_inicio=dia(2), fecha_fin_prevista=dia(4)))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_sin_racha_perdida(self, g, u, iniciar):
        iniciar()
        with pytest.raises(Conflicto) as e:
            g.iniciar_recuperacion(u, en(1, 9))
        assert e.value.codigo == "SIN_RACHA_PERDIDA"

    def test_ventana_para_iniciar_vencida(self, g, db, u, iniciar, tarea):
        self._perder(g, db, u, tarea, iniciar)
        evaluar(g, db, u, 7)  # pasaron 3 días evaluados desde la pérdida
        with pytest.raises(Conflicto) as e:
            g.iniciar_recuperacion(u, en(7, 9))
        assert e.value.codigo == "SIN_RACHA_PERDIDA"

    def test_dia_protegido_no_se_recupera_y_recuperado_no_se_protege(self, g, db, u, iniciar, tarea):
        _siete_y_falla(g, db, u, tarea, iniciar)
        g.usar_proteccion(u, en(8, 9))
        with pytest.raises(Conflicto):
            g.iniciar_recuperacion(u, en(8, 10))

    def test_recuperacion_impide_proteger_ese_dia(self, g, db, u, iniciar, tarea):
        _siete_y_falla(g, db, u, tarea, iniciar)
        g.iniciar_recuperacion(u, en(8, 9))
        with pytest.raises(Conflicto) as e:
            g.usar_proteccion(u, en(8, 10))
        assert e.value.codigo == "NADA_QUE_PROTEGER"

    def test_no_se_cancela_la_de_otro_usuario(self, g, db, u, iniciar, tarea, crear_usuario):
        self._perder(g, db, u, tarea, iniciar)
        rec = g.iniciar_recuperacion(u, en(4, 9))
        otro = db.get(Usuario, crear_usuario().id)
        with pytest.raises(NoEncontrado):
            g.cancelar_recuperacion(otro, rec.id_recuperacion, en(4, 10))
        db.rollback()
        assert db.scalar(select(RecuperacionRacha.estado)) == "ACTIVA"


# ====================================================================================== RF-26 y API
class TestApi:
    def test_requiere_sesion(self, client):
        for metodo, ruta in [("get", "/gamificacion/progreso"), ("get", "/gamificacion/logros"),
                             ("get", "/gamificacion/historial"), ("post", "/gamificacion/protecciones/usar"),
                             ("post", "/gamificacion/recuperaciones"),
                             ("post", f"/gamificacion/recuperaciones/{uuid.uuid4()}/cancelar")]:
            assert getattr(client, metodo)(ruta).status_code == 401, ruta

    def test_progreso_inicial(self, client, usuario_a):
        p = _progreso(client, usuario_a)
        assert (p["racha_actual"], p["racha_maxima"], p["puntos_totales"], p["nivel"], p["protecciones_disponibles"]) == (0, 0, 0, 1, 0)
        assert p["logros_desbloqueados"] == [] and len(p["logros_pendientes"]) == 12
        assert p["recuperacion_activa"] is None and p["puede_proteger"] is None and p["puede_recuperar"] is False
        assert p["hoy"]["tareas_comprometidas"] == 0

    def test_progreso_muestra_compromisos_de_hoy(self, client, usuario_a):
        ahora = datetime.now(timezone.utc)
        zona = ZoneInfo(settings.zona_horaria_defecto)
        fin_hoy = datetime.combine(ahora.astimezone(zona).date() + timedelta(days=1), time.min, tzinfo=zona)
        if fin_hoy - ahora < timedelta(minutes=10):
            pytest.skip("demasiado cerca de la medianoche local")
        limite = (fin_hoy - timedelta(minutes=1)).isoformat()
        r = client.post("/tareas", json={"titulo": "Hoy", "fecha_limite": limite, "prioridad": "ALTA"}, headers=usuario_a.headers)
        assert r.status_code == 201, r.text
        assert _progreso(client, usuario_a)["hoy"]["tareas_comprometidas"] == 1

    def test_cada_usuario_ve_solo_su_progreso(self, client, usuario_a, usuario_b):
        _estado(client, usuario_a, _crear_api(client, usuario_a, hours=5)["id_tarea"], "COMPLETADA")
        assert _progreso(client, usuario_a)["puntos_totales"] == 15
        assert _progreso(client, usuario_b)["puntos_totales"] == 0
        # un id de usuario enviado por el cliente se ignora
        r = client.get(f"/gamificacion/progreso?id_usuario={usuario_a.id}", headers=usuario_b.headers)
        assert r.json()["puntos_totales"] == 0
        hist_b = client.get("/gamificacion/historial", headers=usuario_b.headers).json()
        assert hist_b["transacciones"] == []

    def test_errores_de_negocio_por_api(self, client, usuario_a, usuario_b):
        r = client.post("/gamificacion/protecciones/usar", headers=usuario_a.headers)
        assert (r.status_code, r.json()["error"]["codigo"]) == (409, "SIN_PROTECCIONES")
        r = client.post("/gamificacion/recuperaciones", headers=usuario_a.headers)
        assert (r.status_code, r.json()["error"]["codigo"]) == (409, "SIN_RACHA_PERDIDA")
        r = client.post(f"/gamificacion/recuperaciones/{uuid.uuid4()}/cancelar", headers=usuario_b.headers)
        assert (r.status_code, r.json()["error"]["codigo"]) == (404, "RECUPERACION_NO_ENCONTRADA")

    def test_historial_no_expone_datos_sensibles(self, client, usuario_a):
        _estado(client, usuario_a, _crear_api(client, usuario_a, hours=5)["id_tarea"], "COMPLETADA")
        r = client.get("/gamificacion/historial", headers=usuario_a.headers)
        assert r.status_code == 200
        cuerpo = r.text.lower()
        assert "password" not in cuerpo and "hash" not in cuerpo and "token" not in cuerpo
        assert {t["motivo"] for t in r.json()["transacciones"]} == {"TAREA_A_TIEMPO", "LOGRO_DESBLOQUEADO"}

    def test_proteccion_y_recuperacion_por_api(self, client, db, usuario_a, g, insertar_tarea):
        """Prepara una racha perdida ayer directamente en la BD y la recupera/cancela por la API."""
        usuario = db.get(Usuario, usuario_a.id)
        zona = ZoneInfo(settings.zona_horaria_defecto)
        hoy = datetime.now(timezone.utc).astimezone(zona).date()
        perfil = g.repo.perfil_bloqueado(usuario.id_usuario, hoy - timedelta(days=1))
        perfil.ultima_fecha_evaluada = hoy - timedelta(days=1)
        db.add(DiaRacha(id_usuario=usuario.id_usuario, fecha=hoy - timedelta(days=1), resultado="INCUMPLIDO",
                        tareas_comprometidas=1, tareas_cumplidas_a_tiempo=0, racha_previa=5, racha_resultante=0))
        db.commit()
        p = _progreso(client, usuario_a)
        assert p["puede_recuperar"] is True and p["puede_proteger"] is None  # sin protecciones
        r = client.post("/gamificacion/recuperaciones", headers=usuario_a.headers)
        assert r.status_code == 201, r.text
        rec = r.json()
        assert (rec["estado"], rec["racha_perdida"]) == ("ACTIVA", 5)
        assert _progreso(client, usuario_a)["recuperacion_activa"]["id_recuperacion"] == rec["id_recuperacion"]
        r = client.post(f"/gamificacion/recuperaciones/{rec['id_recuperacion']}/cancelar", headers=usuario_a.headers)
        assert r.json()["estado"] == "CANCELADA"


# ============================================================================== integración con tareas
class TestFechaProgramada:
    def _limite(self, **delta):
        return (datetime.now(timezone.utc) + timedelta(**delta)).isoformat()

    def _hoy(self):
        return datetime.now(timezone.utc).astimezone(ZoneInfo(settings.zona_horaria_defecto)).date()

    def test_crear_con_fecha_programada_valida(self, client, usuario_a):
        manana = (self._hoy() + timedelta(days=1)).isoformat()
        r = client.post("/tareas", json={"titulo": "P", "fecha_limite": self._limite(days=4), "prioridad": "ALTA",
                                         "fecha_programada": manana}, headers=usuario_a.headers)
        assert r.status_code == 201, r.text
        assert r.json()["fecha_programada"] == manana

    @pytest.mark.parametrize("dias", [-1, 10])
    def test_fecha_programada_fuera_de_rango(self, client, usuario_a, dias):
        fecha = (self._hoy() + timedelta(days=dias)).isoformat()
        r = client.post("/tareas", json={"titulo": "P", "fecha_limite": self._limite(days=4), "prioridad": "ALTA",
                                         "fecha_programada": fecha}, headers=usuario_a.headers)
        assert (r.status_code, r.json()["error"]["codigo"]) == (422, "FECHA_PROGRAMADA_INVALIDA")

    def test_no_se_puede_mover_un_dia_programado_que_ya_llego(self, client, usuario_a):
        hoy = self._hoy().isoformat()
        r = client.post("/tareas", json={"titulo": "P", "fecha_limite": self._limite(days=4), "prioridad": "ALTA",
                                         "fecha_programada": hoy}, headers=usuario_a.headers)
        id_tarea = r.json()["id_tarea"]
        for valor in [None, (self._hoy() + timedelta(days=1)).isoformat()]:
            r = client.patch(f"/tareas/{id_tarea}", json={"fecha_programada": valor}, headers=usuario_a.headers)
            assert (r.status_code, r.json()["error"]["codigo"]) == (422, "FECHA_PROGRAMADA_NO_EDITABLE")

    def test_editar_fecha_programada_futura_y_queda_en_historial(self, client, usuario_a):
        r = client.post("/tareas", json={"titulo": "P", "fecha_limite": self._limite(days=4), "prioridad": "ALTA"},
                        headers=usuario_a.headers)
        id_tarea = r.json()["id_tarea"]
        fecha = (self._hoy() + timedelta(days=2)).isoformat()
        r = client.patch(f"/tareas/{id_tarea}", json={"fecha_programada": fecha}, headers=usuario_a.headers)
        assert r.status_code == 200 and r.json()["fecha_programada"] == fecha
        eventos = client.get(f"/tareas/{id_tarea}/historial", headers=usuario_a.headers).json()
        editada = [e for e in eventos if e["tipo_evento"] == "TAREA_EDITADA"][0]
        assert editada["datos"]["despues"]["fecha_programada"] == fecha

    def test_adelantar_la_fecha_limite_antes_del_dia_programado_se_rechaza(self, client, usuario_a):
        fecha = (self._hoy() + timedelta(days=3)).isoformat()
        r = client.post("/tareas", json={"titulo": "P", "fecha_limite": self._limite(days=5), "prioridad": "ALTA",
                                         "fecha_programada": fecha}, headers=usuario_a.headers)
        r = client.patch(f"/tareas/{r.json()['id_tarea']}", json={"fecha_limite": self._limite(days=1)}, headers=usuario_a.headers)
        assert (r.status_code, r.json()["error"]["codigo"]) == (422, "FECHA_PROGRAMADA_INVALIDA")


def test_proceso_diario_pone_al_dia_a_todos(db, u, iniciar, tarea, crear_usuario):
    iniciar()
    tarea(0, completada=en(0, 9))
    total = procesar_todos(db, en(1, 0, 30))
    assert total >= 1
    assert dias(db, u)[dia(0)].resultado == "CUMPLIDO"
    assert procesar_todos(db, en(1, 1)) == total  # idempotente
    assert db.scalar(select(func.count()).select_from(DiaRacha).where(DiaRacha.id_usuario == u.id_usuario)) == 1
