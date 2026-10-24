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
