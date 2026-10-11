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

## Puntos abiertos (conviene decidirlos más adelante)
- Una tarea **completada** puede editarse y cambiar su fecha límite a futuro. Queda en el historial, pero podría distorsionar las métricas de "completada a tiempo" (RF-20). Opciones: bloquear el cambio de fecha en tareas completadas, o exigir reabrirlas primero.
- Sin límite de intentos de login (RNF-04): recomendable antes de publicar.
- RF-01 regla 3 obliga a revelar que un correo ya existe; mitigar con límite de intentos.

## Fuera de alcance (no implementado a propósito)
RF-12 a RF-33, Google Sign-In, límite de intentos de login, reutilización de refresh token revocado (detección), borrado/desactivación de materias.
