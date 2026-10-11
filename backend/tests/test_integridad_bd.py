"""La base de datos como última línea de defensa.

Aunque los servicios ya validan, estas pruebas insertan datos directamente en la BD para demostrar
que las restricciones (CHECK, FK compuestas, índice único parcial) impiden estados inválidos
incluso si algún día un servicio olvida una validación.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.materias.models import Materia
from app.modules.tareas.models import Tarea


def _tarea(id_usuario, **extra) -> Tarea:
    ahora = datetime.now(timezone.utc)
    campos = dict(
        id_usuario=id_usuario,
        titulo="T",
        prioridad=2,
        estado="PENDIENTE",
        fecha_creacion=ahora,
        fecha_limite=ahora + timedelta(days=1),
        fecha_limite_original=ahora + timedelta(days=1),
    )
    campos.update(extra)
    return Tarea(**campos)


def _materia(id_usuario, nombre="Física", activa=True) -> Materia:
    return Materia(id_usuario=id_usuario, nombre=nombre, nombre_normalizado=nombre.casefold(), activa=activa)


def test_una_tarea_no_puede_apuntar_a_la_materia_de_otro_usuario(db, usuario_a, usuario_b):
    materia_de_b = _materia(usuario_b.id)
    db.add(materia_de_b)
    db.commit()

    db.add(_tarea(usuario_a.id, id_materia=materia_de_b.id_materia))
    with pytest.raises(IntegrityError, match="fk_tarea_materia_del_mismo_usuario"):
        db.commit()
    db.rollback()


def test_una_tarea_puede_apuntar_a_una_materia_propia_o_a_ninguna(db, usuario_a):
    materia = _materia(usuario_a.id)
    db.add(materia)
    db.commit()
    db.add_all([_tarea(usuario_a.id, id_materia=materia.id_materia), _tarea(usuario_a.id)])
    db.commit()  # no lanza


def test_una_tarea_no_puede_apuntar_a_una_materia_inexistente(db, usuario_a):
    db.add(_tarea(usuario_a.id, id_materia=uuid.uuid4()))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


@pytest.mark.parametrize(
    "extra, restriccion",
    [
        ({"prioridad": 5}, "ck_tarea_prioridad_valida"),
        ({"estado": "TERMINADA"}, "ck_tarea_estado_valido"),
        ({"titulo": "   "}, "ck_tarea_titulo_no_vacio"),
    ],
)
def test_check_de_tarea(db, usuario_a, extra, restriccion):
    db.add(_tarea(usuario_a.id, **extra))
    with pytest.raises(IntegrityError, match=restriccion):
        db.commit()
    db.rollback()


def test_la_fecha_limite_debe_ser_posterior_a_la_creacion(db, usuario_a):
    ahora = datetime.now(timezone.utc)
    db.add(_tarea(usuario_a.id, fecha_creacion=ahora, fecha_limite=ahora - timedelta(minutes=1)))
    with pytest.raises(IntegrityError, match="ck_tarea_limite_posterior_a_creacion"):
        db.commit()
    db.rollback()


def test_no_puede_haber_dos_materias_activas_con_el_mismo_nombre(db, usuario_a):
    db.add(_materia(usuario_a.id, "Física"))
    db.commit()
    db.add(_materia(usuario_a.id, "Física"))
    with pytest.raises(IntegrityError, match="uq_materia_usuario_nombre_activa"):
        db.commit()
    db.rollback()


def test_una_materia_inactiva_no_bloquea_el_nombre(db, usuario_a):
    db.add_all([_materia(usuario_a.id, "Física", activa=False), _materia(usuario_a.id, "Física")])
    db.commit()  # no lanza: la unicidad solo aplica a materias activas (RF-10 regla 3)
