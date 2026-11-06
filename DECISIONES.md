# Decisiones técnicas – RF-01 a RF-11

Registro breve de lo adoptado. Etiquetas: **[DOC]** viene de la documentación (V6); **[DECISIÓN]** es una decisión técnica del equipo (aprobada o adoptada por simplicidad, revisable).

## Aprobadas por el equipo
| Tema | Decisión |
|---|---|
| Backend | Python + FastAPI, SQLAlchemy 2 (síncrono) + Alembic |
| Base de datos | PostgreSQL (el modelo [DOC] usa UUID, TIMESTAMPTZ, JSON, CHECK, FK compuestas) |
| Arquitectura | Módulos por funcionalidad; capas router → service → repository → model |
| Conexión | Online-first. Offline/sincronización: trabajo futuro (Anexo B debe ajustarse) |
| Contraseñas | Argon2id [DOC permite Argon2id o bcrypt]; nunca texto plano |
| Historial | Solo lo necesario para RF-05 y RF-06 (ver abajo) |

## Criterios de negocio resueltos
| Criterio | Resolución |
|---|---|
| Estado **Vencida** | Se **calcula** al consultar: tarea Pendiente/En progreso con `fecha_limite` < ahora. La API **rechaza** que el usuario la establezca. La BD la permite en el CHECK [DOC] para un futuro proceso (RF-17), pero hoy nunca se escribe. |
| Editar tarea vencida | No obliga a cambiar la fecha. La fecha solo se valida si **cambia** respecto a la guardada. Si el cliente reenvía el mismo valor, no es un cambio. |
| Validación de fecha límite | Al crear: > ahora (equivale a > `fecha_creacion`, RF-08). Al modificarla: > ahora. La BD mantiene además `CHECK fecha_limite > fecha_creacion` [DOC]. Se exige zona horaria explícita. |
| Pertenencia | Toda consulta de tareas/materias filtra por el usuario autenticado. Recurso ajeno → 404 (no revela existencia). Respaldo en BD: FK compuesta `(id_materia, id_usuario)` [DOC]. |
| Materia opcional | `id_materia` nullable; si se asigna, debe ser del mismo usuario y estar activa. Se puede quitar enviando `null`. |

## Decisiones menores adoptadas (revisables)
- **Sesión**: JWT de acceso (15 min) + refresh token opaco (se guarda solo su hash) en `SESION_AUTENTICACION` [DOC]. Vigencia absoluta de la sesión: 30 días. En cada petición se comprueba en BD que la sesión no esté revocada ni expirada, para que *cerrar sesión* sea inmediato (RF-03 reglas 3–5). El refresh token rota en cada uso.
- **Contraseña**: 8–128 caracteres, al menos una letra y un número.
- **`nombre`** del usuario: opcional. `auth_uid` (Google) **no** se crea todavía.
- **Normalización de materia**: sin espacios en extremos, espacios internos colapsados, comparación sin distinguir mayúsculas/minúsculas (no se ignoran acentos).
- **Reabrir tarea completada**: permitido; se limpia `fecha_completada`. El cambio queda en el historial.
- **Orden de consulta**: `fecha_limite` ascendente. Paginación simple `limite` (máx. 200) / `desplazamiento`. Filtro de fechas: rango de días en la zona horaria del usuario.
- **Historial mínimo**: tabla `historial_evento` [DOC] con eventos `TAREA_EDITADA` (valores antes/después) y `TAREA_ELIMINADA`. Faltan los demás eventos de RF-32 (creación, cambio de estado, etc.) y las FK a notificación/sesión de enfoque, que se agregarán con sus módulos.
- Nombres de tablas y columnas iguales a [DOC] para mantener trazabilidad.
- **Orden de materias**: se ordena en Python ignorando acentos/mayúsculas, porque la collation de PostgreSQL dejaba "Álgebra" después de "Física".
- **Flutter**: estado con `ChangeNotifier` + instancias únicas (`state/servicios.dart`), no Riverpod como se había propuesto: menos dependencias y menos que aprender para este avance. Navegación con `Navigator` y `NavigationBar` integrados. Selectores propios (`CampoSelector`) en vez de Dropdown, para no depender de cambios de API entre versiones de Flutter.
- Un recurso ajeno (tarea) devuelve 404 igual que uno inexistente; una materia ajena al asociarla devuelve 404 `MATERIA_NO_ENCONTRADA`.
- Los eventos de historial no se escriben cuando una edición no cambia ningún valor.

## Perfil, personalización inicial y tutorial (extensión posterior a RF-11)
- **Nombre `perfil_recordatorios`, no "intensidad"**: V6 ya usa `notificacion.nivel_intensidad` para el nivel de ESCALADA de cada recordatorio (RF-13). La elección Tranquilo/Equilibrado/Insistente es otra cosa (cuánta insistencia quiere la persona) y se guarda en `preferencia_notificacion`. RF-12/RF-13 la leerán como parámetro; la escalada no cambia. Cómo se traduce cada perfil a intervalos (NOT-01) sigue siendo punto abierto: por ahora **solo se guarda**, no hay notificaciones.
- **Campos nuevos** (V6 §4.2 no los tiene): `usuario.idioma` ('es'|'en'), `personalizacion_completada_en`, `tutorial_completado_en`, `foto_actualizada_en`; tablas `preferencia_notificacion` (perfil + `notificaciones_activas`) y `foto_perfil`. Horas permitidas y zona horaria: la zona ya existe en `usuario`; las horas permitidas no se crearon (no hay RF que las use todavía).
- **El estado del flujo vive en el servidor** (fechas `*_completada_en`), no en el teléfono: si se cierra la app a medias se retoma en el paso pendiente, y sobrevive a cambiar de dispositivo. Orden: Registro → Personalización → Tutorial → Dashboard. Omitir el tutorial lo marca como visto.
- **Sin migración de datos**: los usuarios que ya existían verán la personalización y el tutorial una vez en su siguiente inicio de sesión.
- **Foto**: se guarda en la BD (tabla aparte `foto_perfil`, bytea) y solo la sirve el endpoint autenticado del propio usuario (no hay URL pública). El servidor ignora el nombre y el Content-Type del cliente, abre el archivo con Pillow, acepta solo JPEG/PNG/WebP (máx. 5 MB, 40 MP), y lo **re-codifica** a JPEG 512×512 sin EXIF/GPS. Si más adelante hay mucho tráfico, mover los bytes a almacenamiento de objetos y guardar solo la referencia.
- **Idioma**: guardado por usuario en el servidor (+ copia local para que el login salga en el último idioma usado). Los errores del backend se traducen en la app por su `codigo`; el texto del servidor sigue en español.
- La sesión de PostgreSQL se fija en UTC (`db/session.py`): sin eso las fechas dependían de la zona horaria del servidor de BD (una prueba existente fallaba por eso).
- Nombre editable: 2–100 caracteres; solo letras, espacios, apóstrofo, guion y punto. El correo no es editable.

## Puntos abiertos (conviene decidirlos más adelante)
- Una tarea **completada** puede editarse y cambiar su fecha límite a futuro. Queda en el historial, pero podría distorsionar las métricas de "completada a tiempo" (RF-20). Opciones: bloquear el cambio de fecha en tareas completadas, o exigir reabrirlas primero.
- Sin límite de intentos de login (RNF-04): recomendable antes de publicar.
- RF-01 regla 3 obliga a revelar que un correo ya existe; mitigar con límite de intentos.

## Fuera de alcance (no implementado a propósito)
RF-12 a RF-33, Google Sign-In, límite de intentos de login, reutilización de refresh token revocado (detección), borrado/desactivación de materias.


# RF-12, RF-13 y RF-32 (implementación, 2026-11-06)

Base: las decisiones aprobadas de *Decisiones técnicas — RF-12 a RF-21* (§4 Notificaciones, §5.1, §5.2, §10, §11), guardadas en los archivos del proyecto (`knowledge/claude/DECISIONES.md`). Aquí solo se registra lo que se programó y lo que se tuvo que decidir al implementarlo.

## Arquitectura (aplicada tal como estaba aprobada)
- El backend **genera** los avisos y los guarda (`notificacion`, PROGRAMADA). La app los **recibe** con `POST /notificaciones/sincronizar` y los mostrará como notificaciones **locales**. Sin Firebase ni servidor 24/7.
- **ENVIADA** = la hora ya pasó y el aviso estaba sincronizado con el dispositivo (`fecha_envio = fecha_programada`). Es una aproximación: no confirma que Android lo mostró. Al pasar a ENVIADA se registra `NOTIFICACION_ENVIADA` en el historial (RF-13 regla 5).
- Un aviso cuya hora pasó **sin haberse sincronizado nunca** pasa a CANCELADA (no pudo llegar al teléfono). [DECISIÓN AL IMPLEMENTAR]
- **El plugin de notificaciones del sistema operativo no se agregó todavía** (decisión de la autora, 2026-11-06): no se podía compilar Flutter en el entorno y un plugin nativo sin compilar ponía en riesgo la demo. La app ya consulta y muestra el plan en el detalle de cada tarea.

## Cómo se recalcula el plan
- `NotificacionService.replanificar(usuario, ahora)` deja en la BD exactamente los avisos futuros que corresponden: crea los nuevos, actualiza el texto de los que siguen (si cambió el título o el idioma) y **cancela** los que ya no aplican. Es **idempotente**.
- Se llama dentro de la misma transacción que la operación que lo provoca: crear, editar (estado, fecha, título), eliminar, cambiar la preferencia o el idioma, y al sincronizar. Si la operación falla, el plan no cambia.
- Antes de replanificar se bloquea la fila del usuario (`SELECT ... FOR UPDATE`) y la BD tiene un **índice único parcial** `(id_tarea, fecha_programada)` para estados no cancelados: no puede haber avisos duplicados ni con dos peticiones simultáneas.
- **Horizonte de 7 días** (`notif_horizonte_horas`): solo se guardan avisos dentro de los próximos 7 días; el plan se extiende al sincronizar o con el proceso `python -m app.modules.notificaciones.procesos`. Así se cumple "con T > 7 días no se planifica ningún aviso todavía" sin APScheduler y sin superar el límite de avisos pendientes de iOS. [DECISIÓN AL IMPLEMENTAR]

## Propuestas de §12 que se tomaron como valor por defecto (configurables, revisables)
V6 no define estos valores. Estaban como [PROPUESTA]; se implementaron como parámetros en `core/config.py` para poder cambiarlos sin tocar la lógica:
- **Alineación** hacia atrás desde la fecha límite (T − h, T − 2h, …).
- **Silencio**: un aviso entre 22:00 y 07:00 locales pasa a las 07:00; si eso queda en o después de la fecha límite, a las 21:30 previas; si ya pasó, se descarta. El aviso T − 1 h **también respeta el silencio** (era el punto abierto).
- **CORRECTIVA** (tarea vencida y abierta): 1 h después de vencer y luego a las 19:00 locales durante 3 días (Tranquilo: solo el primero).
- No se implementó **IGNORADA** ni las respuestas (RESPONDIDA): son de RF-14. `requiere_accion` queda en `false` hasta RF-14.

## Historial (RF-32)
- Catálogo en `historial/tipos.py`: `TAREA_CREADA`, `TAREA_EDITADA`, `TAREA_ESTADO_CAMBIADO`, `TAREA_COMPLETADA`, `TAREA_REABIERTA`, `TAREA_POSPUESTA`, `TAREA_REPROGRAMADA`, `TAREA_ELIMINADA` y `NOTIFICACION_ENVIADA`.
- Una edición genera `TAREA_EDITADA` (todos los cambios, como antes) **más** el evento específico del estado o de la fecha, como fija §5.1 punto 5. Nunca dos eventos del mismo tipo por operación.
- **Reprogramación** (V6 no la distingue de posponer): `TAREA_POSPUESTA` si la tarea estaba abierta y no vencida y la fecha se movió a una posterior (§5.1); `TAREA_REPROGRAMADA` en cualquier otro cambio de fecha (adelantarla o mover una vencida). [DECISIÓN AL IMPLEMENTAR]
- `TAREA_COMPLETADA` guarda `a_tiempo` (RF-12 regla 5: a tiempo si se completa antes o exactamente en la fecha límite). Se compara con la fecha límite vigente **antes** de la operación. [DECISIÓN AL IMPLEMENTAR]
- `tarea.veces_pospuesta` (V6) **no se creó**: se puede derivar contando `TAREA_POSPUESTA`. Se agregará si RF-16 lo necesita como columna.
- Consulta: `GET /tareas/{id}/historial` (solo el dueño; tarea eliminada → 404, pero sus eventos se conservan en la BD).

## TAR-09 implementada (cambio visible en RF-05)
Una tarea **COMPLETADA no puede cambiar su `fecha_limite`** (error 422 `FECHA_TAREA_COMPLETADA`); se permite si en la misma petición se reabre. Era una decisión aprobada (§5.2) y es necesaria para RF-13 reglas 6-7: una entrega con retraso no puede convertirse después en una "a tiempo".

## Cambios en pruebas existentes
Tres pruebas de `test_tareas.py` comprobaban que el historial quedaba vacío o con un solo evento. Desde RF-32 la creación también registra `TAREA_CREADA`, así que se ajustaron para no contar ese evento. No se eliminó ninguna prueba.

## Relación con el parche `entregas/paso1_migracion_0003.patch`
Se revisó y se reutilizó **solo la parte de notificaciones** (columnas, CHECK y FK compuestas). La migración `0003` del repositorio la reemplaza: si algún día se aplican las tablas de enfoque, gamificación o riesgo, deben ir en una migración `0004` nueva, no con ese parche (chocaría con la `0003` actual).

# Gamificación RF-21 a RF-27 (implementación, 2026-11-06)

Base: V6 RF-21 a RF-27 y las propuestas presentadas en el diagnóstico, **aprobadas por la autora** ("Aprobar todo y programar"). Todas las cifras son parámetros de `core/config.py` (prefijo `GAM_`). RF-28 a RF-31 quedan fuera a propósito.

## Racha (RF-21)
- **Día comprometido**: el de `tarea.fecha_programada` si existe; si no, el día local de `fecha_limite`. [PROPUESTA APROBADA]
- `tarea.fecha_programada` (DATE, opcional) **se agregó** (antes figuraba como no creada): debe estar entre hoy y el día local de la fecha límite, y no se puede mover ni quitar cuando su día ya llegó (`FECHA_PROGRAMADA_INVALIDA`, `FECHA_PROGRAMADA_NO_EDITABLE`). Si se adelanta la fecha límite antes del día programado, se rechaza.
- **Cumplida a tiempo**: completada en o antes de su límite y, si está programada, antes de que termine su día.
- **Sin racha retroactiva**: el primer día evaluable es el día en que se crea el perfil de gamificación (primera consulta o primera tarea completada).
- **Evaluación**: perezosa (cada consulta y cada tarea completada) + proceso diario opcional. Hoy nunca se evalúa; los días cerrados son inmutables (UNIQUE usuario + fecha).
- **Antitrampa** [DECISIÓN AL IMPLEMENTAR]: una tarea pospuesta o reprogramada **durante** su día sigue contando para ese día con el límite que tenía; una tarea eliminada durante su día también, salvo que se haya creado ese mismo día (duplicado por error).
- **Limitación conocida**: si una tarea se reabre después de medianoche y antes de que se evalúe el día, la evaluación ve la tarea reabierta. El proceso diario cerca de medianoche lo reduce.

## Puntos y nivel (RF-22)
- 10 puntos a tiempo, 0 con retraso; una sola vez por tarea (aunque se reabra); reabrir no resta. Nivel = 1 + puntos // 200.
- Idempotencia: cada movimiento lleva `clave_idempotencia` con UNIQUE `(id_usuario, clave)`; además se bloquea la fila de `perfil_gamificacion` (SELECT … FOR UPDATE) en toda operación. Probado con dos hilos simultáneos.
- Se ejecuta dentro de la transacción de la tarea: si algo falla, no queda ni el cambio de la tarea ni los puntos.

## Logros (RF-23)
- 12 logros iniciales: RACHA 3/7/30 (sobre la racha **máxima**, para que un logro alcanzado no se "pierda"), PRODUCTIVIDAD 1/10/50 tareas a tiempo, CONSTANCIA 100/500/1000 puntos, VELOCIDAD 1/5/20 tareas anticipadas.
- **Extensión a V6**: tipo de condición `TAREAS_ANTICIPADAS` (V6 no trae una condición para VELOCIDAD) = completada al menos 24 h antes del límite; se guarda como `anticipada` en el evento `TAREA_COMPLETADA`.
- **Extensión a V6**: `logro.nombre_en` y `descripcion_en` (la app es bilingüe).

## Protección (RF-24) y recompensas (RF-27)
- Se obtienen protecciones como recompensa: +1 cada vez que la racha llega a un múltiplo de 7 y +1 única al llegar a 500 puntos. Máximo 3 guardadas (si está lleno, no se registra la recompensa).
- Uso **manual**, solo sobre el INCUMPLIDO más reciente mientras siga siendo el último día evaluado y si había racha. El día pasa a PROTEGIDO **conservando sus conteos** y la racha vuelve a `racha_previa`.
- **Extensión a V6**: `dia_racha.racha_previa` (necesaria para restaurar) y `transaccion_gamificacion.codigo_recompensa`.

## Recuperación (RF-25)
- Se puede iniciar si la racha perdida era > 0, el día no fue protegido, no hay otra activa y no pasaron 3 días evaluados desde la pérdida. Una sola vez por racha perdida.
- Periodo de 3 días locales. Condiciones: completar las tareas que causaron el incumplimiento (tarde vale) y no tener ningún INCUMPLIDO en el periodo.
- INCUMPLIDO en el periodo → FALLIDA de inmediato; al terminar → EXITOSA si se completaron, si no FALLIDA; cancelar → CANCELADA. EXITOSA restaura `racha_perdida + racha conseguida en el periodo`.
- Un día protegido no se puede recuperar y un día en recuperación no se puede proteger.
- **Extensión a V6**: `recuperacion_racha.id_dia_perdido`, `tareas_atrasadas`, `racha_restaurada`, `motivo_resolucion`.

## Seguridad
- Ningún endpoint de gamificación recibe un id de usuario: todo sale de la sesión. FK compuestas `(id, id_usuario)` hacia `tarea` y `dia_racha`.
- Las tablas de gamificación solo guardan ids, cifras y fechas: ni contraseñas, ni tokens, ni datos personales.

## Cambios en pruebas existentes
Ninguna prueba anterior se modificó ni eliminó. `conftest.py`: el TRUNCATE incluye las tablas de gamificación (no `logro`, que es catálogo) y `insertar_tarea` acepta `fecha_programada` y `fecha_completada`.
