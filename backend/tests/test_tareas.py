"""Pruebas de RF-04 a RF-09 y RF-11: crear, editar, eliminar, consultar/filtrar tareas."""
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select

from app.modules.historial.models import HistorialEvento
from app.modules.tareas.models import Tarea


def en(dias=0, horas=0) -> str:
    """Fecha ISO con zona horaria, relativa a ahora."""
    return (datetime.now(timezone.utc) + timedelta(days=dias, hours=horas)).isoformat()


def nueva_tarea(**extra) -> dict:
    return {"titulo": "Entregar ensayo", "fecha_limite": en(dias=1), "prioridad": "ALTA", **extra}


def crear_materia(client, usuario, nombre="Historia") -> str:
    r = client.post("/materias", json={"nombre": nombre}, headers=usuario.headers)
    assert r.status_code == 201, r.text
    return r.json()["id_materia"]


def crear_tarea(client, usuario, **extra) -> dict:
    r = client.post("/tareas", json=nueva_tarea(**extra), headers=usuario.headers)
    assert r.status_code == 201, r.text
    return r.json()


# ======================================================================= crear (RF-04, 08, 09)
def test_crear_tarea_valida(client, usuario_a, db):
    r = client.post("/tareas", json=nueva_tarea(descripcion="Capítulos 1 a 3"), headers=usuario_a.headers)
    assert r.status_code == 201
    t = r.json()
    assert t["titulo"] == "Entregar ensayo"
    assert t["descripcion"] == "Capítulos 1 a 3"
    assert t["prioridad"] == "ALTA"
    assert t["estado"] == "PENDIENTE"  # RF-04 regla 5
    assert t["id_materia"] is None  # la materia es opcional
    assert t["fecha_limite_original"] == t["fecha_limite"]

    tarea = db.scalar(select(Tarea))
    assert tarea.id_usuario == usuario_a.id  # RF-04 regla 6
    assert tarea.estado == "PENDIENTE"
    assert tarea.prioridad == 3


def test_crear_tarea_sin_descripcion_ni_materia(client, usuario_a):
    r = client.post("/tareas", json=nueva_tarea(), headers=usuario_a.headers)
    assert r.status_code == 201
    assert r.json()["descripcion"] is None


def test_crear_tarea_requiere_autenticacion(client):
    assert client.post("/tareas", json=nueva_tarea()).status_code == 401


def test_crear_tarea_sin_titulo(client, usuario_a):
    datos = nueva_tarea()
    del datos["titulo"]
    r = client.post("/tareas", json=datos, headers=usuario_a.headers)
    assert r.status_code == 422


@pytest.mark.parametrize("titulo", ["", "    "])
def test_crear_tarea_con_titulo_vacio(client, usuario_a, titulo):
    r = client.post("/tareas", json=nueva_tarea(titulo=titulo), headers=usuario_a.headers)
    assert r.status_code == 422


@pytest.mark.parametrize("prioridad", ["URGENTE", "alta", "", 2])
def test_crear_tarea_con_prioridad_invalida(client, usuario_a, prioridad):
    r = client.post("/tareas", json=nueva_tarea(prioridad=prioridad), headers=usuario_a.headers)
    assert r.status_code == 422


@pytest.mark.parametrize("prioridad", ["BAJA", "MEDIA", "ALTA"])
def test_crear_tarea_con_las_tres_prioridades(client, usuario_a, prioridad):
    assert crear_tarea(client, usuario_a, prioridad=prioridad)["prioridad"] == prioridad


def test_crear_tarea_no_acepta_estado(client, usuario_a):
    """Toda tarea nueva es Pendiente; el cliente no puede elegir otro estado."""
    r = client.post("/tareas", json=nueva_tarea(estado="COMPLETADA"), headers=usuario_a.headers)
    assert r.status_code == 422


def test_crear_tarea_no_acepta_id_usuario(client, usuario_a, usuario_b):
    r = client.post("/tareas", json=nueva_tarea(id_usuario=str(usuario_b.id)), headers=usuario_a.headers)
    assert r.status_code == 422


def test_crear_tarea_con_fecha_limite_pasada(client, usuario_a):
    r = client.post("/tareas", json=nueva_tarea(fecha_limite=en(horas=-1)), headers=usuario_a.headers)
    assert r.status_code == 422
    assert r.json()["error"]["codigo"] == "FECHA_LIMITE_INVALIDA"


def test_crear_tarea_con_fecha_limite_sin_zona_horaria(client, usuario_a):
    r = client.post("/tareas", json=nueva_tarea(fecha_limite="2099-01-01T10:00:00"), headers=usuario_a.headers)
    assert r.status_code == 422


def test_crear_tarea_con_fecha_limite_mal_formada(client, usuario_a):
    r = client.post("/tareas", json=nueva_tarea(fecha_limite="mañana"), headers=usuario_a.headers)
    assert r.status_code == 422


# ======================================================================= materia (RF-11)
def test_crear_tarea_con_materia_propia(client, usuario_a):
    id_materia = crear_materia(client, usuario_a)
    assert crear_tarea(client, usuario_a, id_materia=id_materia)["id_materia"] == id_materia


def test_crear_tarea_con_materia_de_otro_usuario(client, usuario_a, usuario_b):
    materia_de_b = crear_materia(client, usuario_b)
    r = client.post("/tareas", json=nueva_tarea(id_materia=materia_de_b), headers=usuario_a.headers)
    assert r.status_code == 404
    assert r.json()["error"]["codigo"] == "MATERIA_NO_ENCONTRADA"
    assert client.get("/tareas", headers=usuario_a.headers).json() == []  # no se creó nada


def test_crear_tarea_con_materia_inexistente(client, usuario_a):
    r = client.post("/tareas", json=nueva_tarea(id_materia=str(uuid.uuid4())), headers=usuario_a.headers)
    assert r.status_code == 404


def test_asociar_cambiar_y_quitar_materia_al_editar(client, usuario_a, usuario_b):
    historia = crear_materia(client, usuario_a, "Historia")
    fisica = crear_materia(client, usuario_a, "Física")
    ajena = crear_materia(client, usuario_b, "Química")
    tarea = crear_tarea(client, usuario_a)
    url = f"/tareas/{tarea['id_tarea']}"

    r = client.patch(url, json={"id_materia": historia}, headers=usuario_a.headers)
    assert r.json()["id_materia"] == historia

    r = client.patch(url, json={"id_materia": fisica}, headers=usuario_a.headers)  # RF-11 regla 4
    assert r.json()["id_materia"] == fisica

    r = client.patch(url, json={"id_materia": ajena}, headers=usuario_a.headers)
    assert r.status_code == 404
    assert client.get(url, headers=usuario_a.headers).json()["id_materia"] == fisica  # no cambió

    r = client.patch(url, json={"id_materia": None}, headers=usuario_a.headers)  # la materia es opcional
    assert r.status_code == 200
    assert r.json()["id_materia"] is None


# ======================================================================= consultar detalle (RF-07)
def test_obtener_detalle(client, usuario_a):
    tarea = crear_tarea(client, usuario_a)
    r = client.get(f"/tareas/{tarea['id_tarea']}", headers=usuario_a.headers)
    assert r.status_code == 200
    assert r.json()["id_tarea"] == tarea["id_tarea"]


def test_obtener_tarea_inexistente(client, usuario_a):
    r = client.get(f"/tareas/{uuid.uuid4()}", headers=usuario_a.headers)
    assert r.status_code == 404
    assert r.json()["error"]["codigo"] == "TAREA_NO_ENCONTRADA"


def test_obtener_con_id_mal_formado(client, usuario_a):
    assert client.get("/tareas/no-es-uuid", headers=usuario_a.headers).status_code == 422


# ======================================================================= editar (RF-05)
def test_editar_tarea_y_registrar_el_cambio_en_el_historial(client, usuario_a, db):
    tarea = crear_tarea(client, usuario_a)
    r = client.patch(
        f"/tareas/{tarea['id_tarea']}",
        json={"titulo": "Ensayo final", "descripcion": "Con bibliografía", "prioridad": "BAJA"},
        headers=usuario_a.headers,
    )
    assert r.status_code == 200
    t = r.json()
    assert (t["titulo"], t["descripcion"], t["prioridad"]) == ("Ensayo final", "Con bibliografía", "BAJA")

    eventos = db.scalars(select(HistorialEvento)).all()
    assert len(eventos) == 1
    assert eventos[0].tipo_evento == "TAREA_EDITADA"
    assert eventos[0].id_usuario == usuario_a.id
    assert eventos[0].datos["antes"]["titulo"] == "Entregar ensayo"
    assert eventos[0].datos["despues"]["titulo"] == "Ensayo final"


def test_editar_sin_cambios_reales_no_genera_historial(client, usuario_a, db):
    tarea = crear_tarea(client, usuario_a)
    r = client.patch(
        f"/tareas/{tarea['id_tarea']}",
        json={"titulo": tarea["titulo"], "prioridad": tarea["prioridad"]},
        headers=usuario_a.headers,
    )
    assert r.status_code == 200
    assert db.scalars(select(HistorialEvento)).all() == []


def test_editar_con_cuerpo_vacio(client, usuario_a):
    tarea = crear_tarea(client, usuario_a)
    r = client.patch(f"/tareas/{tarea['id_tarea']}", json={}, headers=usuario_a.headers)
    assert r.status_code == 422


@pytest.mark.parametrize("campo", ["titulo", "prioridad", "estado", "fecha_limite"])
def test_editar_campos_obligatorios_no_admiten_null(client, usuario_a, campo):
    tarea = crear_tarea(client, usuario_a)
    r = client.patch(f"/tareas/{tarea['id_tarea']}", json={campo: None}, headers=usuario_a.headers)
    assert r.status_code == 422


def test_editar_con_titulo_vacio(client, usuario_a):
    tarea = crear_tarea(client, usuario_a)
    r = client.patch(f"/tareas/{tarea['id_tarea']}", json={"titulo": "  "}, headers=usuario_a.headers)
    assert r.status_code == 422


def test_editar_con_prioridad_invalida(client, usuario_a):
    tarea = crear_tarea(client, usuario_a)
    r = client.patch(f"/tareas/{tarea['id_tarea']}", json={"prioridad": "MAXIMA"}, headers=usuario_a.headers)
    assert r.status_code == 422


def test_editar_con_estado_invalido(client, usuario_a):
    tarea = crear_tarea(client, usuario_a)
    r = client.patch(f"/tareas/{tarea['id_tarea']}", json={"estado": "TERMINADA"}, headers=usuario_a.headers)
    assert r.status_code == 422


def test_editar_no_permite_cambiar_el_propietario(client, usuario_a, usuario_b):
    tarea = crear_tarea(client, usuario_a)
    r = client.patch(
        f"/tareas/{tarea['id_tarea']}", json={"id_usuario": str(usuario_b.id)}, headers=usuario_a.headers
    )
    assert r.status_code == 422


def test_el_usuario_no_puede_establecer_el_estado_vencida(client, usuario_a):
    tarea = crear_tarea(client, usuario_a)  # vence mañana: NO está vencida
    r = client.patch(f"/tareas/{tarea['id_tarea']}", json={"estado": "VENCIDA"}, headers=usuario_a.headers)
    assert r.status_code == 422
    assert r.json()["error"]["codigo"] == "ESTADO_NO_EDITABLE"
    assert client.get(f"/tareas/{tarea['id_tarea']}", headers=usuario_a.headers).json()["estado"] == "PENDIENTE"


def test_cambiar_estado_a_en_progreso_y_completada(client, usuario_a, db):
    tarea = crear_tarea(client, usuario_a)
    url = f"/tareas/{tarea['id_tarea']}"

    r = client.patch(url, json={"estado": "EN_PROGRESO"}, headers=usuario_a.headers)
    assert r.json()["estado"] == "EN_PROGRESO"
    assert r.json()["fecha_completada"] is None

    r = client.patch(url, json={"estado": "COMPLETADA"}, headers=usuario_a.headers)
    assert r.json()["estado"] == "COMPLETADA"
    assert r.json()["fecha_completada"] is not None  # RF-05 regla 4


def test_reabrir_una_tarea_completada_limpia_fecha_completada(client, usuario_a):
    tarea = crear_tarea(client, usuario_a)
    url = f"/tareas/{tarea['id_tarea']}"
    client.patch(url, json={"estado": "COMPLETADA"}, headers=usuario_a.headers)
    r = client.patch(url, json={"estado": "PENDIENTE"}, headers=usuario_a.headers)
    assert r.json()["estado"] == "PENDIENTE"
    assert r.json()["fecha_completada"] is None


def test_cambiar_fecha_limite_conserva_la_original(client, usuario_a):
    tarea = crear_tarea(client, usuario_a)
    r = client.patch(
        f"/tareas/{tarea['id_tarea']}", json={"fecha_limite": en(dias=5)}, headers=usuario_a.headers
    )
    assert r.status_code == 200
    assert r.json()["fecha_limite"] != tarea["fecha_limite"]
    assert r.json()["fecha_limite_original"] == tarea["fecha_limite_original"]  # nunca se modifica


def test_cambiar_fecha_limite_a_una_pasada_se_rechaza(client, usuario_a):
    tarea = crear_tarea(client, usuario_a)
    r = client.patch(
        f"/tareas/{tarea['id_tarea']}", json={"fecha_limite": en(horas=-2)}, headers=usuario_a.headers
    )
    assert r.status_code == 422
    assert r.json()["error"]["codigo"] == "FECHA_LIMITE_INVALIDA"


# ----------------------------------------------------------------- tareas vencidas
def test_tarea_vencida_se_identifica_sin_que_el_usuario_la_marque(client, usuario_a, insertar_tarea):
    tarea = insertar_tarea(usuario_a.id, fecha_limite=datetime.now(timezone.utc) - timedelta(hours=1))
    r = client.get(f"/tareas/{tarea.id_tarea}", headers=usuario_a.headers)
    assert r.json()["estado"] == "VENCIDA"


def test_editar_otro_campo_de_una_tarea_vencida_no_exige_cambiar_la_fecha(client, usuario_a, insertar_tarea):
    tarea = insertar_tarea(usuario_a.id, fecha_limite=datetime.now(timezone.utc) - timedelta(hours=1))
    r = client.patch(f"/tareas/{tarea.id_tarea}", json={"titulo": "Nuevo título"}, headers=usuario_a.headers)
    assert r.status_code == 200
    assert r.json()["titulo"] == "Nuevo título"
    assert r.json()["estado"] == "VENCIDA"  # sigue vencida


def test_reenviar_la_misma_fecha_limite_en_una_tarea_vencida_no_es_un_cambio(client, usuario_a, insertar_tarea):
    """Un cliente que reenvía el objeto completo (con la fecha pasada sin tocar) no debe recibir error."""
    tarea = insertar_tarea(usuario_a.id, fecha_limite=datetime.now(timezone.utc) - timedelta(hours=1))
    actual = client.get(f"/tareas/{tarea.id_tarea}", headers=usuario_a.headers).json()
    r = client.patch(
        f"/tareas/{tarea.id_tarea}",
        json={
            "titulo": "Otro",
            "fecha_limite": actual["fecha_limite"],
            "estado": actual["estado"],  # "VENCIDA", tal como la recibió
            "prioridad": actual["prioridad"],
        },
        headers=usuario_a.headers,
    )
    assert r.status_code == 200
    assert r.json()["titulo"] == "Otro"


def test_cambiar_la_fecha_de_una_tarea_vencida_a_otra_pasada_se_rechaza(client, usuario_a, insertar_tarea):
    tarea = insertar_tarea(usuario_a.id, fecha_limite=datetime.now(timezone.utc) - timedelta(hours=1))
    r = client.patch(
        f"/tareas/{tarea.id_tarea}", json={"fecha_limite": en(horas=-5)}, headers=usuario_a.headers
    )
    assert r.status_code == 422


def test_reprogramar_una_tarea_vencida_a_futuro_la_deja_pendiente(client, usuario_a, insertar_tarea):
    tarea = insertar_tarea(usuario_a.id, fecha_limite=datetime.now(timezone.utc) - timedelta(hours=1))
    r = client.patch(f"/tareas/{tarea.id_tarea}", json={"fecha_limite": en(dias=2)}, headers=usuario_a.headers)
    assert r.status_code == 200
    assert r.json()["estado"] == "PENDIENTE"


def test_completar_una_tarea_vencida(client, usuario_a, insertar_tarea):
    tarea = insertar_tarea(usuario_a.id, fecha_limite=datetime.now(timezone.utc) - timedelta(hours=1))
    r = client.patch(f"/tareas/{tarea.id_tarea}", json={"estado": "COMPLETADA"}, headers=usuario_a.headers)
    assert r.status_code == 200
    assert r.json()["estado"] == "COMPLETADA"
    assert r.json()["fecha_completada"] > r.json()["fecha_limite"]  # completada con retraso (se conserva)


def test_una_tarea_completada_a_tiempo_no_aparece_como_vencida(client, usuario_a, insertar_tarea):
    tarea = insertar_tarea(
        usuario_a.id, estado="COMPLETADA", fecha_limite=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    assert client.get(f"/tareas/{tarea.id_tarea}", headers=usuario_a.headers).json()["estado"] == "COMPLETADA"


# ======================================================================= eliminar (RF-06)
def test_eliminar_tarea(client, usuario_a, db):
    tarea = crear_tarea(client, usuario_a)
    url = f"/tareas/{tarea['id_tarea']}"

    assert client.delete(url, headers=usuario_a.headers).status_code == 204

    assert client.get(url, headers=usuario_a.headers).status_code == 404
    assert client.get("/tareas", headers=usuario_a.headers).json() == []  # ya no aparece (regla 3)

    db.expire_all()
    fila = db.scalar(select(Tarea))
    assert fila is not None and fila.fecha_eliminacion is not None  # eliminación lógica
    evento = db.scalar(select(HistorialEvento).where(HistorialEvento.tipo_evento == "TAREA_ELIMINADA"))
    assert evento is not None and evento.id_tarea == fila.id_tarea  # regla 4


def test_eliminar_dos_veces(client, usuario_a):
    tarea = crear_tarea(client, usuario_a)
    url = f"/tareas/{tarea['id_tarea']}"
    assert client.delete(url, headers=usuario_a.headers).status_code == 204
    assert client.delete(url, headers=usuario_a.headers).status_code == 404


def test_no_se_puede_editar_una_tarea_eliminada(client, usuario_a):
    tarea = crear_tarea(client, usuario_a)
    url = f"/tareas/{tarea['id_tarea']}"
    client.delete(url, headers=usuario_a.headers)
    assert client.patch(url, json={"titulo": "x"}, headers=usuario_a.headers).status_code == 404


def test_eliminar_inexistente(client, usuario_a):
    assert client.delete(f"/tareas/{uuid.uuid4()}", headers=usuario_a.headers).status_code == 404


# ======================================================================= aislamiento entre usuarios
def test_un_usuario_no_puede_ver_editar_ni_eliminar_tareas_de_otro(client, usuario_a, usuario_b, db):
    tarea = crear_tarea(client, usuario_a, titulo="Privada de Ana")
    url = f"/tareas/{tarea['id_tarea']}"

    assert client.get(url, headers=usuario_b.headers).status_code == 404
    assert client.patch(url, json={"titulo": "Hackeada"}, headers=usuario_b.headers).status_code == 404
    assert client.delete(url, headers=usuario_b.headers).status_code == 404

    # La tarea de Ana quedó intacta.
    db.expire_all()
    fila = db.scalar(select(Tarea))
    assert fila.titulo == "Privada de Ana"
    assert fila.fecha_eliminacion is None
    assert db.scalars(select(HistorialEvento)).all() == []


def test_la_lista_solo_contiene_tareas_propias(client, usuario_a, usuario_b):
    crear_tarea(client, usuario_a, titulo="De Ana")
    crear_tarea(client, usuario_b, titulo="De Beto")
    assert [t["titulo"] for t in client.get("/tareas", headers=usuario_a.headers).json()] == ["De Ana"]
    assert [t["titulo"] for t in client.get("/tareas", headers=usuario_b.headers).json()] == ["De Beto"]


def test_filtrar_por_la_materia_de_otro_usuario_no_devuelve_nada(client, usuario_a, usuario_b):
    materia_de_b = crear_materia(client, usuario_b)
    crear_tarea(client, usuario_b, id_materia=materia_de_b)
    r = client.get("/tareas", params={"id_materia": materia_de_b}, headers=usuario_a.headers)
    assert r.status_code == 200 and r.json() == []


# ======================================================================= filtros (RF-07)
@pytest.fixture
def escenario(client, usuario_a, insertar_tarea):
    """Cinco tareas de Ana con estados, prioridades y fechas distintas."""
    ahora = datetime.now(timezone.utc)
    materia = crear_materia(client, usuario_a, "Cálculo")
    m = uuid.UUID(materia)
    t = {
        "pendiente": insertar_tarea(usuario_a.id, "Pendiente", ahora + timedelta(days=1), prioridad=1, id_materia=m),
        "progreso": insertar_tarea(usuario_a.id, "En progreso", ahora + timedelta(days=3), prioridad=3, estado="EN_PROGRESO"),
        "completada": insertar_tarea(usuario_a.id, "Completada", ahora + timedelta(days=2), prioridad=2, estado="COMPLETADA"),
        "vencida": insertar_tarea(usuario_a.id, "Vencida", ahora - timedelta(hours=1), prioridad=2),
        "vencida_en_progreso": insertar_tarea(
            usuario_a.id, "Vencida en progreso", ahora - timedelta(hours=5), prioridad=1, estado="EN_PROGRESO"
        ),
    }
    return {"materia": materia, "tareas": t}


def titulos(respuesta) -> list[str]:
    assert respuesta.status_code == 200, respuesta.text
    return [t["titulo"] for t in respuesta.json()]


def test_sin_filtros_devuelve_todas_ordenadas_por_fecha_limite(client, usuario_a, escenario):
    assert titulos(client.get("/tareas", headers=usuario_a.headers)) == [
        "Vencida en progreso", "Vencida", "Pendiente", "Completada", "En progreso",
    ]


@pytest.mark.parametrize(
    "estado, esperado",
    [
        ("PENDIENTE", ["Pendiente"]),
        ("EN_PROGRESO", ["En progreso"]),  # la en progreso ya vencida cuenta como VENCIDA
        ("COMPLETADA", ["Completada"]),
        ("VENCIDA", ["Vencida en progreso", "Vencida"]),
    ],
)
def test_filtrar_por_estado(client, usuario_a, escenario, estado, esperado):
    assert titulos(client.get("/tareas", params={"estado": estado}, headers=usuario_a.headers)) == esperado


def test_filtrar_por_prioridad(client, usuario_a, escenario):
    r = client.get("/tareas", params={"prioridad": "ALTA"}, headers=usuario_a.headers)
    assert titulos(r) == ["En progreso"]
    r = client.get("/tareas", params={"prioridad": "BAJA"}, headers=usuario_a.headers)
    assert titulos(r) == ["Vencida en progreso", "Pendiente"]


def test_filtrar_por_materia(client, usuario_a, escenario):
    r = client.get("/tareas", params={"id_materia": escenario["materia"]}, headers=usuario_a.headers)
    assert titulos(r) == ["Pendiente"]


def test_filtros_combinados(client, usuario_a, escenario):
    r = client.get("/tareas", params={"estado": "VENCIDA", "prioridad": "BAJA"}, headers=usuario_a.headers)
    assert titulos(r) == ["Vencida en progreso"]
    r = client.get("/tareas", params={"estado": "PENDIENTE", "prioridad": "ALTA"}, headers=usuario_a.headers)
    assert titulos(r) == []  # RF-07 regla 4: deben cumplirse todos los filtros


def test_quitar_los_filtros_recupera_la_lista_completa(client, usuario_a, escenario):
    filtrada = client.get("/tareas", params={"estado": "COMPLETADA"}, headers=usuario_a.headers)
    assert len(filtrada.json()) == 1
    assert len(client.get("/tareas", headers=usuario_a.headers).json()) == 5


def test_filtrar_por_rango_de_fecha_limite_usa_la_zona_horaria_del_usuario(client, usuario_a, insertar_tarea):
    # 10 de mayo de 2030, 23:30 hora de Ciudad de México (zona por defecto) = 11 de mayo 05:30 UTC.
    limite = datetime(2030, 5, 10, 23, 30, tzinfo=ZoneInfo("America/Mexico_City"))
    insertar_tarea(usuario_a.id, "Noche del 10", limite)

    def consulta(desde=None, hasta=None):
        params = {k: v for k, v in {"fecha_desde": desde, "fecha_hasta": hasta}.items() if v}
        return titulos(client.get("/tareas", params=params, headers=usuario_a.headers))

    assert consulta("2030-05-10", "2030-05-10") == ["Noche del 10"]  # el día local, no el día UTC
    assert consulta("2030-05-11", "2030-05-11") == []
    assert consulta(hasta="2030-05-09") == []
    assert consulta(desde="2030-05-10") == ["Noche del 10"]
    assert consulta("2030-05-01", "2030-05-31") == ["Noche del 10"]


def test_rango_de_fechas_invertido(client, usuario_a):
    r = client.get(
        "/tareas", params={"fecha_desde": "2030-05-10", "fecha_hasta": "2030-05-01"}, headers=usuario_a.headers
    )
    assert r.status_code == 422


@pytest.mark.parametrize("params", [{"estado": "TERMINADA"}, {"prioridad": "URGENTE"}, {"id_materia": "x"}, {"fecha_desde": "ayer"}])
def test_filtros_invalidos(client, usuario_a, params):
    assert client.get("/tareas", params=params, headers=usuario_a.headers).status_code == 422


def test_paginacion(client, usuario_a, escenario):
    primera = titulos(client.get("/tareas", params={"limite": 2}, headers=usuario_a.headers))
    segunda = titulos(client.get("/tareas", params={"limite": 2, "desplazamiento": 2}, headers=usuario_a.headers))
    assert primera == ["Vencida en progreso", "Vencida"]
    assert segunda == ["Pendiente", "Completada"]
    assert client.get("/tareas", params={"limite": 0}, headers=usuario_a.headers).status_code == 422


def test_las_tareas_eliminadas_no_aparecen_en_ningun_filtro(client, usuario_a, escenario):
    id_tarea = escenario["tareas"]["pendiente"].id_tarea
    client.delete(f"/tareas/{id_tarea}", headers=usuario_a.headers)
    assert "Pendiente" not in titulos(client.get("/tareas", headers=usuario_a.headers))
    r = client.get("/tareas", params={"id_materia": escenario["materia"]}, headers=usuario_a.headers)
    assert titulos(r) == []
