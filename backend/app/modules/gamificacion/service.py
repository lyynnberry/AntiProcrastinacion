"""Lógica de gamificación: RF-21 (racha), RF-22 (puntos), RF-23 (logros), RF-24 (protección),
RF-25 (recuperación), RF-26 (progreso) y RF-27 (recompensas).

Integridad:
- Toda operación que modifica la gamificación de un usuario bloquea primero su fila de `perfil_gamificacion`
  (SELECT ... FOR UPDATE). Así dos solicitudes simultáneas se ejecutan una detrás de otra.
- Cada movimiento de puntos/protecciones lleva una `clave_idempotencia` única por usuario: la misma acción
  nunca suma dos veces (aunque el bloqueo fallara, la BD lo rechaza).
- Nada hace commit salvo los métodos públicos llamados desde la API; cuando la gamificación se dispara desde
  una tarea (`tarea_completada`) usa la transacción de esa operación: si falla, no queda nada a medias.
"""
import uuid
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import Conflicto, NoEncontrado
from app.core.tiempo import zona_horaria
from app.modules.gamificacion import reglas
from app.modules.gamificacion.models import (
    DiaRacha,
    Logro,
    LogroUsuario,
    PerfilGamificacion,
    RecuperacionRacha,
    TransaccionGamificacion,
)
from app.modules.gamificacion.repository import GamificacionRepository
from app.modules.tareas.enums import EstadoTarea
from app.modules.usuarios.models import Usuario

PUNTOS = "PUNTOS"
PROTECCION = "PROTECCION_RACHA"


class GamificacionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = GamificacionRepository(db)

    # =========================================================================== auxiliares
    def _zona(self, usuario: Usuario):
        return zona_horaria(usuario.zona_horaria)

    def _hoy(self, usuario: Usuario, ahora: datetime) -> date:
        return ahora.astimezone(self._zona(usuario)).date()

    def _perfil(self, usuario: Usuario, ahora: datetime) -> PerfilGamificacion:
        # Primer día evaluable = día en que se crea el perfil: no hay racha retroactiva.
        return self.repo.perfil_bloqueado(usuario.id_usuario, self._hoy(usuario, ahora))

    def _movimiento(
        self,
        usuario: Usuario,
        perfil: PerfilGamificacion,
        recurso: str,
        cantidad: int,
        motivo: str,
        clave: str,
        ahora: datetime,
        **referencias,
    ) -> bool:
        """Registra un movimiento en el libro y actualiza el perfil. Devuelve False si no se aplicó
        (ya existía esa acción, el inventario está lleno o no alcanza)."""
        if cantidad == 0 or self.repo.existe_clave(usuario.id_usuario, clave):
            return False
        if recurso == PROTECCION:
            nuevo = perfil.protecciones_disponibles + cantidad
            if nuevo < 0 or (cantidad > 0 and nuevo > settings.gam_max_protecciones):
                return False
        elif perfil.puntos_totales + cantidad < 0:  # RF-22 regla 7
            return False
        ok = self.repo.insertar_unico(
            TransaccionGamificacion(
                id_usuario=usuario.id_usuario,
                recurso=recurso,
                cantidad=cantidad,
                motivo=motivo,
                clave_idempotencia=clave,
                fecha=ahora,
                **referencias,
            )
        )
        if not ok:
            return False
        if recurso == PROTECCION:
            perfil.protecciones_disponibles += cantidad
        else:
            perfil.puntos_totales += cantidad
            perfil.nivel = reglas.nivel_para(perfil.puntos_totales, settings.gam_puntos_por_nivel)
        return True

    def _indicadores(self, usuario: Usuario, perfil: PerfilGamificacion) -> reglas.Indicadores:
        return reglas.Indicadores(
            racha_actual=perfil.racha_actual,
            racha_maxima=perfil.racha_maxima,
            puntos_totales=perfil.puntos_totales,
            tareas_a_tiempo=self.repo.contar_tareas_a_tiempo(usuario.id_usuario),
            tareas_anticipadas=self.repo.contar_tareas_anticipadas(usuario.id_usuario),
        )

    def _subir_racha_maxima(self, perfil: PerfilGamificacion) -> None:
        perfil.racha_maxima = max(perfil.racha_maxima, perfil.racha_actual)  # §7 regla 10: nunca baja

    # ===================================================================== RF-21: racha diaria
    def compromisos_del_dia(self, usuario: Usuario, dia: date) -> list[reglas.Compromiso]:
        zona = self._zona(usuario)
        inicio, fin = reglas.limites_del_dia(dia, zona)
        compromisos: dict[uuid.UUID, reglas.Compromiso] = {}
        for t in self.repo.tareas_del_dia(usuario.id_usuario, dia, inicio, fin):
            completada = t.fecha_completada if t.estado == EstadoTarea.COMPLETADA.value else None
            compromisos[t.id_tarea] = reglas.Compromiso(t.id_tarea, t.fecha_limite, completada)
        # Antitrampa: una tarea cuya fecha límite estaba en este día y se movió DURANTE el día sigue
        # comprometida con él, con el límite que tenía (no se salva la racha posponiendo).
        movidas = {}
        for e in self.repo.cambios_de_fecha_en(usuario.id_usuario, inicio, fin):
            antes = datetime.fromisoformat(e.datos["antes"])
            if e.id_tarea not in compromisos and inicio <= antes < fin:
                movidas.setdefault(e.id_tarea, antes)
        for t in self.repo.tareas_por_id(usuario.id_usuario, list(movidas)):
            eliminada_antes = t.fecha_eliminacion is not None and (t.fecha_eliminacion < inicio or t.fecha_creacion >= inicio)
            if not eliminada_antes and t.fecha_programada is None:
                completada = t.fecha_completada if t.estado == EstadoTarea.COMPLETADA.value else None
                compromisos[t.id_tarea] = reglas.Compromiso(t.id_tarea, movidas[t.id_tarea], completada)
        return list(compromisos.values())

    def poner_al_dia(self, usuario: Usuario, ahora: datetime) -> PerfilGamificacion:
        """Evalúa en orden todos los días cerrados pendientes (§7 reglas 9 y 12). Idempotente: un día ya
        evaluado no se vuelve a evaluar (y la BD tiene UNIQUE (usuario, fecha))."""
        perfil = self._perfil(usuario, ahora)
        zona = self._zona(usuario)
        hoy = self._hoy(usuario, ahora)
        for dia in reglas.dias_pendientes(perfil.ultima_fecha_evaluada, perfil.primer_dia_evaluable, hoy):
            _, fin = reglas.limites_del_dia(dia, zona)
            res = reglas.evaluar_dia(perfil.racha_actual, self.compromisos_del_dia(usuario, dia), fin)
            registro = DiaRacha(
                id_usuario=usuario.id_usuario,
                fecha=dia,
                resultado=res.resultado,
                tareas_comprometidas=res.comprometidas,
                tareas_cumplidas_a_tiempo=res.cumplidas,
                racha_previa=res.racha_previa,
                racha_resultante=res.racha_resultante,
                fecha_evaluacion=ahora,
            )
            self.repo.agregar(registro)
            self.db.flush()
            perfil.racha_actual = res.racha_resultante
            self._subir_racha_maxima(perfil)
            perfil.ultima_fecha_evaluada = dia
            # RF-27: mantener la racha un periodo establecido -> +1 protección.
            if reglas.recompensa_por_racha(res.racha_resultante, res.racha_previa, settings.gam_recompensa_racha_cada_dias):
                self._movimiento(
                    usuario, perfil, PROTECCION, 1, "RECOMPENSA", f"RECOMPENSA:RACHA:{dia.isoformat()}", ahora,
                    codigo_recompensa="RACHA_PERIODO", id_dia_racha=registro.id_dia_racha,
                )
        self._actualizar_recuperacion(usuario, perfil, ahora)
        self._revisar_logros_y_recompensas(usuario, perfil, ahora)
        self.db.flush()
        return perfil

    # =========================================================== RF-22: puntos al completar tareas
    def tarea_completada(self, usuario: Usuario, id_tarea: uuid.UUID, a_tiempo: bool, ahora: datetime) -> None:
        """Se llama desde TareaService cuando una tarea pasa a COMPLETADA (misma transacción)."""
        perfil = self.poner_al_dia(usuario, ahora)
        puntos = reglas.puntos_por_completar(
            a_tiempo, settings.gam_puntos_tarea_a_tiempo, settings.gam_puntos_tarea_con_retraso
        )
        if a_tiempo:
            # Una sola vez por tarea en toda su vida, aunque se reabra y se vuelva a completar (RF-22 regla 6).
            self._movimiento(usuario, perfil, PUNTOS, puntos, "TAREA_A_TIEMPO", f"TAREA_A_TIEMPO:{id_tarea}", ahora, id_tarea=id_tarea)
        elif puntos > 0:
            self._movimiento(
                usuario, perfil, PUNTOS, puntos, "RECOMPENSA", f"TAREA_CON_RETRASO:{id_tarea}", ahora,
                id_tarea=id_tarea, codigo_recompensa="TAREA_CON_RETRASO",
            )
        self._revisar_logros_y_recompensas(usuario, perfil, ahora)
        self.db.flush()

    # ============================================================= RF-23 y RF-27: logros y recompensas
    def _revisar_logros_y_recompensas(self, usuario: Usuario, perfil: PerfilGamificacion, ahora: datetime) -> None:
        """Comprueba todas las condiciones. Se repite mientras algo cambie, porque los puntos de un logro
        pueden desbloquear otro (por ejemplo, uno de PUNTOS_TOTALES)."""
        logros = self.repo.logros_activos()
        while True:
            cambio = False
            obtenidos = self.repo.logros_del_usuario(usuario.id_usuario)
            ind = self._indicadores(usuario, perfil)
            for logro in logros:
                if logro.id_logro in obtenidos:
                    continue  # RF-23 regla 2
                if reglas.condicion_cumplida(logro.tipo_condicion, logro.valor_condicion, ind):
                    if self.repo.insertar_unico(
                        LogroUsuario(id_usuario=usuario.id_usuario, id_logro=logro.id_logro, fecha_desbloqueo=ahora)
                    ):
                        cambio = True
                        self._movimiento(
                            usuario, perfil, PUNTOS, logro.recompensa_puntos, "LOGRO_DESBLOQUEADO",
                            f"LOGRO:{logro.codigo}", ahora, id_logro=logro.id_logro,
                        )
            # RF-27: recompensa única por puntos acumulados.
            if perfil.puntos_totales >= settings.gam_recompensa_puntos_umbral:
                if self._movimiento(
                    usuario, perfil, PROTECCION, 1, "RECOMPENSA",
                    f"RECOMPENSA:PUNTOS:{settings.gam_recompensa_puntos_umbral}", ahora,
                    codigo_recompensa="PUNTOS_ACUMULADOS",
                ):
                    cambio = True
            if not cambio:
                return

    # =============================================================================== RF-24
    def _proteccion_posible(self, usuario: Usuario, perfil: PerfilGamificacion) -> DiaRacha | None:
        """El día INCUMPLIDO más reciente, si todavía se puede proteger: es el último día evaluado (la
        protección vale hasta que se evalúa el día siguiente), rompió una racha > 0 y no tiene recuperación."""
        if perfil.ultima_fecha_evaluada is None:
            return None
        dia = self.repo.dia(usuario.id_usuario, perfil.ultima_fecha_evaluada)
        if dia is None or dia.resultado != reglas.INCUMPLIDO or dia.racha_previa <= 0:
            return None
        if self.repo.recuperacion_de_dia(usuario.id_usuario, dia.id_dia_racha) is not None:
            return None
        return dia

    def usar_proteccion(self, usuario: Usuario, ahora: datetime) -> PerfilGamificacion:
        perfil = self.poner_al_dia(usuario, ahora)
        if perfil.protecciones_disponibles < 1:
            raise Conflicto("No tienes protecciones de racha disponibles.", "SIN_PROTECCIONES")
        dia = self._proteccion_posible(usuario, perfil)
        if dia is None:
            raise Conflicto("No hay un incumplimiento reciente que haya roto tu racha.", "NADA_QUE_PROTEGER")
        usada = self._movimiento(
            usuario, perfil, PROTECCION, -1, "PROTECCION_USADA", f"PROTECCION_USADA:{dia.id_dia_racha}", ahora,
            id_dia_racha=dia.id_dia_racha,
        )
        if not usada:
            raise Conflicto("Ese día ya fue protegido.", "PROTECCION_YA_USADA")
        # El día conserva sus conteos (p. ej. 2 de 3 tareas): el incumplimiento original queda registrado.
        dia.resultado = reglas.PROTEGIDO
        dia.racha_resultante = dia.racha_previa
        perfil.racha_actual = dia.racha_previa  # RF-24 regla 5: la racha conserva su valor
        self._subir_racha_maxima(perfil)
        self._revisar_logros_y_recompensas(usuario, perfil, ahora)
        self.db.commit()
        return perfil

    # =============================================================================== RF-25
    def _racha_recuperable(self, usuario: Usuario, perfil: PerfilGamificacion) -> DiaRacha | None:
        dia = self.repo.ultimo_incumplido_con_racha(usuario.id_usuario)
        if dia is None or perfil.ultima_fecha_evaluada is None:
            return None
        if (perfil.ultima_fecha_evaluada - dia.fecha).days >= settings.gam_recuperacion_ventana_dias:
            return None  # pasó la ventana para iniciarla
        if self.repo.recuperacion_de_dia(usuario.id_usuario, dia.id_dia_racha) is not None:
            return None  # cada racha perdida solo se puede intentar recuperar una vez
        return dia

    def iniciar_recuperacion(self, usuario: Usuario, ahora: datetime) -> RecuperacionRacha:
        perfil = self.poner_al_dia(usuario, ahora)
        if self.repo.recuperacion_activa(usuario.id_usuario) is not None:
            raise Conflicto("Ya tienes una recuperación en curso.", "RECUPERACION_ACTIVA")
        dia = self._racha_recuperable(usuario, perfil)
        if dia is None:
            raise Conflicto("No tienes una racha perdida que se pueda recuperar.", "SIN_RACHA_PERDIDA")
        _, fin = reglas.limites_del_dia(dia.fecha, self._zona(usuario))
        atrasadas = [str(c.id_tarea) for c in self.compromisos_del_dia(usuario, dia.fecha) if not reglas.cumplida_en_plazo(c, fin)]
        hoy = self._hoy(usuario, ahora)
        recuperacion = RecuperacionRacha(
            id_usuario=usuario.id_usuario,
            id_dia_perdido=dia.id_dia_racha,
            racha_perdida=dia.racha_previa,
            tareas_atrasadas=atrasadas,
            fecha_inicio=hoy,
            fecha_fin_prevista=hoy + timedelta(days=settings.gam_recuperacion_dias - 1),
            estado="ACTIVA",
            fecha_creacion=ahora,
        )
        if not self.repo.insertar_unico(recuperacion):
            raise Conflicto("Ya tienes una recuperación en curso.", "RECUPERACION_ACTIVA")
        self.db.commit()
        return recuperacion

    def cancelar_recuperacion(self, usuario: Usuario, id_recuperacion: uuid.UUID, ahora: datetime) -> RecuperacionRacha:
        self._perfil(usuario, ahora)  # bloqueo
        rec = self.repo.recuperacion(usuario.id_usuario, id_recuperacion)
        if rec is None:
            raise NoEncontrado("Recuperación no encontrada.", "RECUPERACION_NO_ENCONTRADA")
        if rec.estado != "ACTIVA":
            raise Conflicto("La recuperación ya terminó.", "RECUPERACION_NO_ACTIVA")
        rec.estado = "CANCELADA"
        rec.motivo_resolucion = "CANCELADA_POR_USUARIO"
        rec.fecha_resolucion = ahora
        self.db.commit()
        return rec

    def _avance_recuperacion(self, usuario: Usuario, rec: RecuperacionRacha) -> tuple[int, int]:
        ids = [uuid.UUID(i) for i in rec.tareas_atrasadas]
        tareas = self.repo.tareas_por_id(usuario.id_usuario, ids)
        hechas = sum(1 for t in tareas if t.estado == EstadoTarea.COMPLETADA.value and t.fecha_eliminacion is None)
        return hechas, len(ids)

    def _actualizar_recuperacion(self, usuario: Usuario, perfil: PerfilGamificacion, ahora: datetime) -> None:
        rec = self.repo.recuperacion_activa(usuario.id_usuario)
        if rec is None:
            return
        ultima = perfil.ultima_fecha_evaluada
        dias = self.repo.dias_entre(usuario.id_usuario, rec.fecha_inicio, rec.fecha_fin_prevista) if ultima else []
        hechas, total = self._avance_recuperacion(usuario, rec)
        nuevo = reglas.resolver_recuperacion(
            [d.resultado for d in dias], ultima is not None and ultima >= rec.fecha_fin_prevista, hechas == total
        )
        if nuevo is None:
            return
        rec.estado = nuevo
        rec.fecha_resolucion = ahora
        if nuevo == "EXITOSA":
            # La racha vuelve al valor perdido + los días cumplidos desde que se perdió (RF-25 regla 7).
            rec.racha_restaurada = rec.racha_perdida + perfil.racha_actual
            rec.motivo_resolucion = "CONDICIONES_CUMPLIDAS"
            perfil.racha_actual = rec.racha_restaurada
            self._subir_racha_maxima(perfil)
        else:
            rec.motivo_resolucion = (
                "NUEVO_INCUMPLIMIENTO" if any(d.resultado == reglas.INCUMPLIDO for d in dias) else "TAREAS_ATRASADAS_PENDIENTES"
            )

    # =============================================================================== RF-26
    def progreso(self, usuario: Usuario, ahora: datetime) -> dict:
        """Estado actual de la cuenta del usuario AUTENTICADO (nunca se recibe un id de usuario)."""
        perfil = self.poner_al_dia(usuario, ahora)
        self.db.commit()
        ind = self._indicadores(usuario, perfil)
        obtenidos = self.repo.logros_del_usuario(usuario.id_usuario)
        desbloqueados, pendientes = [], []
        for logro in self.repo.logros_activos():
            dato = self._logro_salida(logro, usuario.idioma, ind, obtenidos.get(logro.id_logro))
            (desbloqueados if dato["desbloqueado"] else pendientes).append(dato)

        hoy = self._hoy(usuario, ahora)
        _, fin_hoy = reglas.limites_del_dia(hoy, self._zona(usuario))
        compromisos_hoy = self.compromisos_del_dia(usuario, hoy)

        rec = self.repo.recuperacion_activa(usuario.id_usuario)
        recuperacion = None
        if rec is not None:
            hechas, total = self._avance_recuperacion(usuario, rec)
            recuperacion = {
                "id_recuperacion": rec.id_recuperacion,
                "estado": rec.estado,
                "racha_perdida": rec.racha_perdida,
                "fecha_inicio": rec.fecha_inicio,
                "fecha_fin_prevista": rec.fecha_fin_prevista,
                "tareas_atrasadas_total": total,
                "tareas_atrasadas_completadas": hechas,
                "dias_restantes": max((rec.fecha_fin_prevista - hoy).days + 1, 0),
            }
        dia_protegible = self._proteccion_posible(usuario, perfil)
        return {
            "racha_actual": perfil.racha_actual,
            "racha_maxima": perfil.racha_maxima,
            "puntos_totales": perfil.puntos_totales,
            "nivel": perfil.nivel,
            "protecciones_disponibles": perfil.protecciones_disponibles,
            "ultima_fecha_evaluada": perfil.ultima_fecha_evaluada,
            "hoy": {
                "fecha": hoy,
                "tareas_comprometidas": len(compromisos_hoy),
                "tareas_cumplidas_a_tiempo": sum(1 for c in compromisos_hoy if reglas.cumplida_en_plazo(c, fin_hoy)),
            },
            "tareas_a_tiempo": ind.tareas_a_tiempo,
            "logros_desbloqueados": desbloqueados,
            "logros_pendientes": sorted(pendientes, key=lambda x: -x["progreso"]),
            "recuperacion_activa": recuperacion,
            "puede_proteger": (
                {"fecha": dia_protegible.fecha, "racha_a_conservar": dia_protegible.racha_previa}
                if dia_protegible is not None and perfil.protecciones_disponibles > 0
                else None
            ),
            "puede_recuperar": rec is None and self._racha_recuperable(usuario, perfil) is not None,
        }

    @staticmethod
    def _logro_salida(logro: Logro, idioma: str, ind: reglas.Indicadores, obtenido: LogroUsuario | None) -> dict:
        porcentaje, actual = reglas.progreso(logro.tipo_condicion, logro.valor_condicion, ind)
        return {
            "codigo": logro.codigo,
            "nombre": logro.nombre_en if idioma == "en" else logro.nombre,
            "descripcion": logro.descripcion_en if idioma == "en" else logro.descripcion,
            "categoria": logro.categoria,
            "tipo_condicion": logro.tipo_condicion,
            "valor_condicion": logro.valor_condicion,
            "valor_actual": logro.valor_condicion if obtenido else actual,
            "progreso": 100 if obtenido else porcentaje,
            "recompensa_puntos": logro.recompensa_puntos,
            "desbloqueado": obtenido is not None,
            "fecha_desbloqueo": obtenido.fecha_desbloqueo if obtenido else None,
        }

    def logros(self, usuario: Usuario, ahora: datetime) -> list[dict]:
        progreso = self.progreso(usuario, ahora)
        return progreso["logros_desbloqueados"] + progreso["logros_pendientes"]

    def historial(self, usuario: Usuario, ahora: datetime, limite: int) -> dict:
        self.poner_al_dia(usuario, ahora)
        self.db.commit()
        return {
            "transacciones": self.repo.transacciones(usuario.id_usuario, limite),
            "dias": self.repo.ultimos_dias(usuario.id_usuario, limite),
            "recuperaciones": self.repo.recuperaciones(usuario.id_usuario, limite),
        }


def procesar_todos(db: Session, ahora: datetime) -> int:
    """Proceso diario (cron): pone al día la racha de todos los usuarios activos. Idempotente."""
    from sqlalchemy import select

    usuarios = list(db.scalars(select(Usuario).where(Usuario.activo.is_(True))))
    servicio = GamificacionService(db)
    for usuario in usuarios:
        servicio.poner_al_dia(usuario, ahora)
        db.commit()
    return len(usuarios)
