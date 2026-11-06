"""RF-12 (generar notificaciones) y RF-13 (escalar frecuencia) contra PostgreSQL real."""
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.modules.historial.models import HistorialEvento
from app.modules.notificaciones.models import Notificacion
from app.modules.notificaciones.service import NotificacionService
from app.modules.usuarios.models import Usuario


def _futuro(**delta) -> str:
    return (datetime.now(timezone.utc) + timedelta(**delta)).isoformat()


def crear(client, usuario, titulo="Ensayo de historia", **delta):
    delta = delta or {"days": 2}
    r = client.post(
        "/tareas",
        json={"titulo": titulo, "fecha_limite": _futuro(**delta), "prioridad": "ALTA"},
        headers=usuario.headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def notifs(db, id_tarea=None, estado=None):
    db.expire_all()
    q = select(Notificacion)
    if id_tarea is not None:
        q = q.where(Notificacion.id_tarea == id_tarea)
    if estado is not None:
        q = q.where(Notificacion.estado == estado)
    return list(db.scalars(q.order_by(Notificacion.fecha_programada)))


def preferencia(client, usuario, perfil="equilibrado", activas=True):
    r = client.put(
        "/usuarios/me/preferencia-notificacion",
        json={"perfil_recordatorios": perfil, "notificaciones_activas": activas},
        headers=usuario.headers,
    )
    assert r.status_code == 200, r.text


# ---- RF-12: generación y asociación -----------------------------------------------------------
def test_crear_tarea_genera_notificaciones_programadas(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    avisos = notifs(db, tarea["id_tarea"])
    assert avisos, "debe existir al menos un aviso"
    ahora = datetime.now(timezone.utc)
    for n in avisos:
        assert n.estado == "PROGRAMADA"  # generada, todavía NO entregada
        assert n.id_usuario == usuario_a.id
        assert str(n.id_tarea) == tarea["id_tarea"]
        assert "Ensayo de historia" in n.mensaje  # RF-12 regla 3
        assert n.fecha_generacion is not None
        assert n.fecha_programada > ahora
        assert n.fecha_sincronizacion is None and n.fecha_envio is None
    assert {n.tipo for n in avisos} <= {"URGENTE", "CRITICA", "CORRECTIVA"}  # vence en 2 días
    assert any(n.es_aviso_final for n in avisos)


def test_niveles_escalan_conforme_se_acerca_la_fecha(client, usuario_a, db):
    tarea = crear(client, usuario_a, days=6)
    previos = [n for n in notifs(db, tarea["id_tarea"]) if n.tipo != "CORRECTIVA"]
    niveles = [n.nivel_intensidad for n in previos]
    assert niveles == sorted(niveles)  # nunca baja
    assert {"RECORDATORIO", "URGENTE", "CRITICA"} <= {n.tipo for n in previos}


def test_api_sincronizar_entrega_el_plan_y_marca_la_sincronizacion(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    r = client.post("/notificaciones/sincronizar", headers=usuario_a.headers)
    assert r.status_code == 200
    lista = r.json()
    assert lista and all(n["estado"] == "PROGRAMADA" and n["id_tarea"] == tarea["id_tarea"] for n in lista)
    assert [n["fecha_programada"] for n in lista] == sorted(n["fecha_programada"] for n in lista)
    assert all(n.fecha_sincronizacion is not None for n in notifs(db, estado="PROGRAMADA"))


def test_endpoints_requieren_sesion(client):
    assert client.post("/notificaciones/sincronizar").status_code == 401
    assert client.get("/notificaciones").status_code == 401


# ---- prevención de duplicados ------------------------------------------------------------------
def test_sincronizar_varias_veces_no_duplica(client, usuario_a, db):
    crear(client, usuario_a)
    primera = client.post("/notificaciones/sincronizar", headers=usuario_a.headers).json()
    segunda = client.post("/notificaciones/sincronizar", headers=usuario_a.headers).json()
    assert [n["id_notificacion"] for n in primera] == [n["id_notificacion"] for n in segunda]
    assert len(notifs(db)) == len(primera)  # no se crearon filas nuevas ni canceladas


def test_la_bd_rechaza_dos_avisos_vigentes_en_el_mismo_momento(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    n = notifs(db, tarea["id_tarea"])[0]
    db.add(Notificacion(id_usuario=n.id_usuario, id_tarea=n.id_tarea, tipo="CRITICA", nivel_intensidad=3,
                        mensaje="duplicado", fecha_programada=n.fecha_programada))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_la_bd_impide_asociar_la_notificacion_a_la_tarea_de_otro(client, usuario_a, usuario_b, db):
    tarea = crear(client, usuario_a)
    db.add(Notificacion(id_usuario=usuario_b.id, id_tarea=tarea["id_tarea"], tipo="CRITICA", nivel_intensidad=3,
                        mensaje="x", fecha_programada=datetime.now(timezone.utc) + timedelta(hours=3)))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


# ---- RF-12 regla 6 / preferencias ---------------------------------------------------------------
def test_perfil_insistente_genera_mas_avisos_que_tranquilo(client, crear_usuario, db):
    conteo = {}
    for perfil in ("tranquilo", "insistente"):
        u = crear_usuario()
        preferencia(client, u, perfil)
        tarea = crear(client, u, days=6)
        conteo[perfil] = len(notifs(db, tarea["id_tarea"], "PROGRAMADA"))
    assert conteo["tranquilo"] < conteo["insistente"]


def test_cambiar_el_perfil_replanifica(client, usuario_a, db):
    tarea = crear(client, usuario_a, days=6)
    antes = len(notifs(db, tarea["id_tarea"], "PROGRAMADA"))
    preferencia(client, usuario_a, "insistente")
    assert len(notifs(db, tarea["id_tarea"], "PROGRAMADA")) > antes


def test_desactivar_notificaciones_cancela_y_reactivar_regenera(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    preferencia(client, usuario_a, activas=False)
    assert notifs(db, tarea["id_tarea"], "PROGRAMADA") == []
    assert all(n.estado == "CANCELADA" and n.fecha_cancelacion for n in notifs(db, tarea["id_tarea"]))
    crear(client, usuario_a, titulo="Otra")  # con avisos desactivados no se generan
    assert notifs(db, estado="PROGRAMADA") == []
    preferencia(client, usuario_a, activas=True)
    assert notifs(db, tarea["id_tarea"], "PROGRAMADA")


# ---- RF-13 regla 4 y RF-06 regla 6: cancelación ---------------------------------------------------
def test_completar_cancela_los_avisos_futuros(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    client.patch(f"/tareas/{tarea['id_tarea']}", json={"estado": "COMPLETADA"}, headers=usuario_a.headers)
    assert notifs(db, tarea["id_tarea"], "PROGRAMADA") == []
    assert notifs(db, tarea["id_tarea"], "CANCELADA")
    # Una tarea completada no genera nuevas notificaciones aunque se vuelva a sincronizar.
    client.post("/notificaciones/sincronizar", headers=usuario_a.headers)
    assert notifs(db, tarea["id_tarea"], "PROGRAMADA") == []


def test_reabrir_vuelve_a_planificar(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    url = f"/tareas/{tarea['id_tarea']}"
    client.patch(url, json={"estado": "COMPLETADA"}, headers=usuario_a.headers)
    client.patch(url, json={"estado": "PENDIENTE"}, headers=usuario_a.headers)
    assert notifs(db, tarea["id_tarea"], "PROGRAMADA")


def test_eliminar_cancela_los_avisos(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    client.delete(f"/tareas/{tarea['id_tarea']}", headers=usuario_a.headers)
    assert notifs(db, tarea["id_tarea"], "PROGRAMADA") == []


def test_cambiar_la_fecha_limite_actualiza_el_plan(client, usuario_a, db):
    tarea = crear(client, usuario_a, days=2)
    viejos = {n.id_notificacion for n in notifs(db, tarea["id_tarea"], "PROGRAMADA")}
    nueva = datetime.now(timezone.utc) + timedelta(days=4)
    r = client.patch(f"/tareas/{tarea['id_tarea']}", json={"fecha_limite": nueva.isoformat()}, headers=usuario_a.headers)
    assert r.status_code == 200
    vigentes = notifs(db, tarea["id_tarea"], "PROGRAMADA")
    final = [n for n in vigentes if n.es_aviso_final]
    assert len(final) == 1
    # El aviso final queda 1 h antes de la NUEVA fecha (o reubicado por silencio, nunca después de ella).
    assert final[0].fecha_programada < nueva
    assert any(n.estado == "CANCELADA" for n in notifs(db, tarea["id_tarea"]) if n.id_notificacion in viejos)


def test_cambiar_el_titulo_actualiza_el_mensaje(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    client.patch(f"/tareas/{tarea['id_tarea']}", json={"titulo": "Exposición"}, headers=usuario_a.headers)
    assert all("Exposición" in n.mensaje for n in notifs(db, tarea["id_tarea"], "PROGRAMADA"))


def test_idioma_del_usuario_en_el_mensaje(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    client.patch("/usuarios/me", json={"idioma": "en"}, headers=usuario_a.headers)
    mensajes = [n.mensaje for n in notifs(db, tarea["id_tarea"], "PROGRAMADA")]
    assert mensajes and all("due" in m for m in mensajes)


# ---- zonas horarias ----------------------------------------------------------------------------
@pytest.mark.parametrize("zona", ["America/Mexico_City", "Asia/Tokyo", "UTC"])
def test_horario_de_silencio_en_la_zona_del_usuario(client, usuario_a, db, zona):
    db.get(Usuario, usuario_a.id).zona_horaria = zona
    db.commit()
    tarea = crear(client, usuario_a, days=6)
    tz = ZoneInfo(zona)
    avisos = notifs(db, tarea["id_tarea"], "PROGRAMADA")
    assert avisos
    for n in avisos:
        assert time(7, 0) <= n.fecha_programada.astimezone(tz).time() < time(22, 0)


# ---- RF-13 regla 5: registrar las enviadas ------------------------------------------------------
def test_aviso_sincronizado_cuya_hora_paso_queda_enviado_y_en_el_historial(client, usuario_a, db):
    tarea = crear(client, usuario_a, days=2)
    usuario = db.get(Usuario, usuario_a.id)
    servicio = NotificacionService(db)
    ahora = datetime.now(timezone.utc)
    servicio.sincronizar(usuario, ahora)
    primero = notifs(db, tarea["id_tarea"], "PROGRAMADA")[0]
    despues = primero.fecha_programada + timedelta(minutes=1)
    servicio.registrar_enviadas(usuario, despues)
    db.commit()
    db.expire_all()
    n = db.get(Notificacion, primero.id_notificacion)
    assert n.estado == "ENVIADA" and n.fecha_envio == n.fecha_programada
    evento = db.scalar(select(HistorialEvento).where(HistorialEvento.tipo_evento == "NOTIFICACION_ENVIADA"))
    assert evento.id_notificacion == n.id_notificacion
    assert evento.origen == "SISTEMA" and str(evento.id_tarea) == tarea["id_tarea"]
    # Ejecutarlo otra vez no duplica el evento.
    servicio.registrar_enviadas(usuario, despues)
    db.commit()
    assert len(db.scalars(select(HistorialEvento).where(HistorialEvento.tipo_evento == "NOTIFICACION_ENVIADA")).all()) == 1


def test_aviso_nunca_sincronizado_no_cuenta_como_enviado(client, usuario_a, db):
    tarea = crear(client, usuario_a, days=2)
    usuario = db.get(Usuario, usuario_a.id)
    primero = notifs(db, tarea["id_tarea"], "PROGRAMADA")[0]
    NotificacionService(db).registrar_enviadas(usuario, primero.fecha_programada + timedelta(minutes=1))
    db.commit()
    db.expire_all()
    assert db.get(Notificacion, primero.id_notificacion).estado == "CANCELADA"


def test_el_plan_se_extiende_al_entrar_en_la_ventana(client, usuario_a, db):
    tarea = crear(client, usuario_a, days=20)
    assert notifs(db, tarea["id_tarea"]) == []  # a más de 7 días todavía no hay avisos
    usuario = db.get(Usuario, usuario_a.id)
    NotificacionService(db).sincronizar(usuario, datetime.now(timezone.utc) + timedelta(days=13))
    assert notifs(db, tarea["id_tarea"], "PROGRAMADA")


def test_maximo_diario_por_usuario(client, usuario_a, db):
    preferencia(client, usuario_a, "tranquilo")  # máximo 4 al día
    for i in range(6):
        crear(client, usuario_a, titulo=f"Tarea {i}", hours=30 + i)
    db.expire_all()
    tz = ZoneInfo(db.get(Usuario, usuario_a.id).zona_horaria)
    por_dia: dict = {}
    for n in notifs(db, estado="PROGRAMADA"):
        dia = n.fecha_programada.astimezone(tz).date()
        por_dia[dia] = por_dia.get(dia, 0) + 1
    assert por_dia and max(por_dia.values()) <= 4


# ---- aislamiento -------------------------------------------------------------------------------
def test_cada_usuario_solo_ve_sus_notificaciones(client, usuario_a, usuario_b, db):
    tarea = crear(client, usuario_a)
    assert client.post("/notificaciones/sincronizar", headers=usuario_b.headers).json() == []
    assert client.get("/notificaciones", headers=usuario_b.headers).json() == []
    r = client.get(f"/notificaciones?id_tarea={tarea['id_tarea']}", headers=usuario_b.headers)
    assert r.json() == []
    propias = client.get(f"/notificaciones?id_tarea={tarea['id_tarea']}", headers=usuario_a.headers).json()
    assert propias and all(n["id_tarea"] == tarea["id_tarea"] for n in propias)
    # La sincronización de Beto no tocó los avisos de Ana.
    assert all(n.fecha_sincronizacion is None for n in notifs(db, tarea["id_tarea"]))


def test_filtrar_por_estado(client, usuario_a):
    tarea = crear(client, usuario_a)
    client.patch(f"/tareas/{tarea['id_tarea']}", json={"estado": "COMPLETADA"}, headers=usuario_a.headers)
    canceladas = client.get("/notificaciones?estado=CANCELADA", headers=usuario_a.headers).json()
    assert canceladas and all(n["estado"] == "CANCELADA" for n in canceladas)
    assert client.get("/notificaciones?estado=OTRO", headers=usuario_a.headers).status_code == 422
