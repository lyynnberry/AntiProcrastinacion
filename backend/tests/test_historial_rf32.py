"""RF-32: historial de tareas (creación, modificación, cambio de estado, finalización, reprogramación y
eliminación), integridad y aislamiento."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.modules.historial.models import HistorialEvento


def _futuro(**delta) -> str:
    return (datetime.now(timezone.utc) + timedelta(**delta)).isoformat()


def crear(client, usuario, dias=3, titulo="Ensayo"):
    r = client.post(
        "/tareas",
        json={"titulo": titulo, "fecha_limite": _futuro(days=dias), "prioridad": "MEDIA"},
        headers=usuario.headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def tipos(db, id_tarea) -> list[str]:
    db.expire_all()
    return sorted(
        e.tipo_evento for e in db.scalars(select(HistorialEvento).where(HistorialEvento.id_tarea == id_tarea))
    )


def patch(client, usuario, tarea, **cuerpo):
    return client.patch(f"/tareas/{tarea['id_tarea']}", json=cuerpo, headers=usuario.headers)


# ---- un evento por cada acción mínima de RF-32 --------------------------------------------------
def test_crear_registra_tarea_creada(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    evento = db.scalar(select(HistorialEvento).where(HistorialEvento.id_tarea == tarea["id_tarea"]))
    assert evento.tipo_evento == "TAREA_CREADA"
    assert evento.id_usuario == usuario_a.id
    assert evento.origen == "USUARIO"
    assert evento.datos["titulo"] == "Ensayo"
    assert evento.fecha_evento is not None


def test_editar_registra_solo_tarea_editada(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    assert patch(client, usuario_a, tarea, titulo="Ensayo final").status_code == 200
    assert tipos(db, tarea["id_tarea"]) == ["TAREA_CREADA", "TAREA_EDITADA"]


def test_cambio_de_estado(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    assert patch(client, usuario_a, tarea, estado="EN_PROGRESO").status_code == 200
    assert tipos(db, tarea["id_tarea"]) == ["TAREA_CREADA", "TAREA_EDITADA", "TAREA_ESTADO_CAMBIADO"]
    evento = db.scalar(select(HistorialEvento).where(HistorialEvento.tipo_evento == "TAREA_ESTADO_CAMBIADO"))
    assert evento.datos == {"antes": "PENDIENTE", "despues": "EN_PROGRESO"}


def test_finalizacion_a_tiempo(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    assert patch(client, usuario_a, tarea, estado="COMPLETADA").status_code == 200
    evento = db.scalar(select(HistorialEvento).where(HistorialEvento.tipo_evento == "TAREA_COMPLETADA"))
    assert evento.datos["a_tiempo"] is True
    assert evento.datos["estado_anterior"] == "PENDIENTE"


def test_finalizacion_con_retraso_se_conserva(client, usuario_a, db, insertar_tarea):
    """RF-13 reglas 6-7 / RF-12 regla 5: completar después de la fecha límite no cuenta como a tiempo."""
    ahora = datetime.now(timezone.utc)
    tarea = insertar_tarea(usuario_a.id, fecha_limite=ahora - timedelta(hours=2))
    r = client.patch(f"/tareas/{tarea.id_tarea}", json={"estado": "COMPLETADA"}, headers=usuario_a.headers)
    assert r.status_code == 200
    evento = db.scalar(select(HistorialEvento).where(HistorialEvento.tipo_evento == "TAREA_COMPLETADA"))
    assert evento.datos["a_tiempo"] is False


def test_no_se_puede_volver_a_tiempo_moviendo_la_fecha_al_completar(client, usuario_a, db, insertar_tarea):
    ahora = datetime.now(timezone.utc)
    tarea = insertar_tarea(usuario_a.id, fecha_limite=ahora - timedelta(hours=2))
    r = client.patch(
        f"/tareas/{tarea.id_tarea}",
        json={"estado": "COMPLETADA", "fecha_limite": _futuro(days=1)},
        headers=usuario_a.headers,
    )
    # La fecha de una tarea que queda COMPLETADA no puede cambiar (TAR-09).
    assert r.status_code == 422
    assert r.json()["error"]["codigo"] == "FECHA_TAREA_COMPLETADA"


def test_tarea_completada_no_cambia_su_fecha_hasta_reabrirla(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    patch(client, usuario_a, tarea, estado="COMPLETADA")
    r = patch(client, usuario_a, tarea, fecha_limite=_futuro(days=9))
    assert r.status_code == 422 and r.json()["error"]["codigo"] == "FECHA_TAREA_COMPLETADA"
    # Reabrir y cambiar la fecha en la misma operación sí se permite.
    r = patch(client, usuario_a, tarea, estado="PENDIENTE", fecha_limite=_futuro(days=9))
    assert r.status_code == 200
    assert "TAREA_REABIERTA" in tipos(db, tarea["id_tarea"])


def test_reabrir(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    patch(client, usuario_a, tarea, estado="COMPLETADA")
    patch(client, usuario_a, tarea, estado="PENDIENTE")
    assert tipos(db, tarea["id_tarea"]).count("TAREA_REABIERTA") == 1


def test_posponer_a_una_fecha_posterior(client, usuario_a, db):
    tarea = crear(client, usuario_a, dias=3)
    assert patch(client, usuario_a, tarea, fecha_limite=_futuro(days=5)).status_code == 200
    evento = db.scalar(select(HistorialEvento).where(HistorialEvento.tipo_evento == "TAREA_POSPUESTA"))
    assert evento.datos["antes"] < evento.datos["despues"]
    assert evento.datos["fecha_limite_original"] == evento.datos["antes"]
    assert "TAREA_REPROGRAMADA" not in tipos(db, tarea["id_tarea"])


def test_adelantar_la_fecha_es_reprogramacion(client, usuario_a, db):
    tarea = crear(client, usuario_a, dias=5)
    assert patch(client, usuario_a, tarea, fecha_limite=_futuro(days=2)).status_code == 200
    assert "TAREA_REPROGRAMADA" in tipos(db, tarea["id_tarea"])
    assert "TAREA_POSPUESTA" not in tipos(db, tarea["id_tarea"])


def test_reprogramar_una_tarea_vencida(client, usuario_a, db, insertar_tarea):
    tarea = insertar_tarea(usuario_a.id, fecha_limite=datetime.now(timezone.utc) - timedelta(hours=3))
    r = client.patch(f"/tareas/{tarea.id_tarea}", json={"fecha_limite": _futuro(days=2)}, headers=usuario_a.headers)
    assert r.status_code == 200
    evento = db.scalar(select(HistorialEvento).where(HistorialEvento.tipo_evento == "TAREA_REPROGRAMADA"))
    assert evento.datos["estaba_vencida"] is True


def test_eliminar_registra_y_conserva_el_historial(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    patch(client, usuario_a, tarea, titulo="Otro")
    assert client.delete(f"/tareas/{tarea['id_tarea']}", headers=usuario_a.headers).status_code == 204
    # RF-06 regla 5 / RF-32 regla 12: los registros anteriores siguen ahí.
    assert tipos(db, tarea["id_tarea"]) == ["TAREA_CREADA", "TAREA_EDITADA", "TAREA_ELIMINADA"]


# ---- una operación, un evento de cada tipo -------------------------------------------------------
def test_una_operacion_no_duplica_eventos(client, usuario_a, db):
    tarea = crear(client, usuario_a, dias=3)
    r = patch(client, usuario_a, tarea, titulo="Nuevo", estado="EN_PROGRESO", fecha_limite=_futuro(days=4))
    assert r.status_code == 200
    assert tipos(db, tarea["id_tarea"]) == [
        "TAREA_CREADA", "TAREA_EDITADA", "TAREA_ESTADO_CAMBIADO", "TAREA_POSPUESTA",
    ]


def test_una_operacion_fallida_no_deja_eventos(client, usuario_a, db):
    tarea = crear(client, usuario_a)
    antes = tipos(db, tarea["id_tarea"])
    pasada = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    r = patch(client, usuario_a, tarea, titulo="No debe quedar", fecha_limite=pasada)
    assert r.status_code == 422
    assert tipos(db, tarea["id_tarea"]) == antes


def test_el_historial_no_cambia_con_ediciones_posteriores(client, usuario_a, db):
    tarea = crear(client, usuario_a, titulo="Original")
    creado = db.scalar(select(HistorialEvento).where(HistorialEvento.tipo_evento == "TAREA_CREADA"))
    datos_originales = dict(creado.datos)
    patch(client, usuario_a, tarea, titulo="Cambiado")
    db.expire_all()
    assert db.get(HistorialEvento, creado.id_evento).datos == datos_originales


# ---- consulta y aislamiento ---------------------------------------------------------------------
def test_consultar_historial_de_una_tarea(client, usuario_a):
    tarea = crear(client, usuario_a)
    patch(client, usuario_a, tarea, estado="COMPLETADA")
    r = client.get(f"/tareas/{tarea['id_tarea']}/historial", headers=usuario_a.headers)
    assert r.status_code == 200
    eventos = r.json()
    assert eventos[0]["tipo_evento"] == "TAREA_CREADA"
    assert {"TAREA_EDITADA", "TAREA_COMPLETADA"} <= {e["tipo_evento"] for e in eventos}
    fechas = [e["fecha_evento"] for e in eventos]
    assert fechas == sorted(fechas)


def test_historial_ajeno_no_es_visible(client, usuario_a, usuario_b):
    tarea = crear(client, usuario_a)
    r = client.get(f"/tareas/{tarea['id_tarea']}/historial", headers=usuario_b.headers)
    assert r.status_code == 404
    assert client.get(f"/tareas/{tarea['id_tarea']}/historial").status_code == 401


def test_cada_usuario_solo_genera_eventos_propios(client, usuario_a, usuario_b, db):
    tarea = crear(client, usuario_a)
    patch(client, usuario_b, tarea, titulo="Hackeada")  # 404
    client.delete(f"/tareas/{tarea['id_tarea']}", headers=usuario_b.headers)  # 404
    db.expire_all()
    assert all(e.id_usuario == usuario_a.id for e in db.scalars(select(HistorialEvento)))
