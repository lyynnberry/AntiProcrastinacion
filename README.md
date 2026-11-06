# AntiProcrastinación – avance RF-01 a RF-11, RF-12/RF-13, RF-21 a RF-27 y RF-32

| Parte | Estado |
|---|---|
| `backend/` (FastAPI + PostgreSQL) | **Implementado y probado** (198 pruebas: RF-01 a RF-11, RF-12, RF-13 y RF-32) |
| `frontend/` (Flutter) | 

Decisiones y puntos abiertos: [`DECISIONES.md`](DECISIONES.md).

## Backend

### Puesta en marcha
```bash
cd backend
python3 -m venv .venv && source .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# OPCIÓN A (la más fácil): PostgreSQL en Docker. Crea el usuario y la BD que espera la configuración.
docker run --name antiproc-db -d -p 5432:5432 \
  -e POSTGRES_USER=antiproc -e POSTGRES_PASSWORD=antiproc_dev -e POSTGRES_DB=antiprocrastinacion \
  postgres:16
docker exec antiproc-db createdb -U antiproc antiprocrastinacion_test   # solo para las pruebas

# OPCIÓN B: PostgreSQL instalado en tu equipo
#   createuser antiproc --pwprompt                 (contraseña: antiproc_dev)
#   createdb -O antiproc antiprocrastinacion
#   createdb -O antiproc antiprocrastinacion_test

cp .env.example .env                           # ajusta DATABASE_URL si cambiaste usuario/contraseña
alembic upgrade head                           # crea las tablas
uvicorn app.main:app --reload                  # API en http://127.0.0.1:8000  ·  documentación interactiva: /docs
```

### Pruebas
```bash
pytest -q          # usa la BD *_test (nunca la de desarrollo) y la crea desde las migraciones
```

### Estructura
```
backend/app/
├─ core/        configuración, errores, seguridad (hash, tokens), dependencias comunes
├─ db/          conexión y base declarativa
└─ modules/     un paquete por funcionalidad, cada uno con las capas:
   ├─ auth/       router → service → repository → models   (+ schemas, validators)
   ├─ usuarios/   perfil, idioma, personalización inicial, tutorial, preferencia de recordatorios y foto (+ imagen.py)
   ├─ materias/
   ├─ tareas/     (+ enums, reglas.py con las reglas puras)
   └─ historial/  mínimo para RF-05 y RF-06
backend/migrations/   Alembic (esquema versionado)
backend/tests/        pruebas por funcionalidad + integridad de BD
```
Para agregar un RF nuevo (p. ej. notificaciones): crear `modules/notificaciones/` con las mismas capas, importar su modelo en `db/registro_modelos.py`, generar la migración (`alembic revision --autogenerate -m "..."`) y registrar su router en `main.py`.

### Trazabilidad RF → código → pruebas
| RF | Endpoint | Código principal | Pruebas |
|---|---|---|---|
| RF-01 Registrar usuario | `POST /auth/registro` | `auth/service.py::registrar`, `auth/validators.py` | `test_auth.py` (registro) |
| RF-02 Iniciar sesión | `POST /auth/login` | `auth/service.py::iniciar_sesion` | `test_auth.py` (login) |
| RF-03 Mantener sesión | `POST /auth/refresh`, `POST /auth/logout`, todos los protegidos | `auth/service.py::{renovar_sesion,autenticar,cerrar_sesion}` | `test_auth.py` (sesión) |
| RF-04 Crear tarea | `POST /tareas` | `tareas/service.py::crear` | `test_tareas.py` (crear) |
| RF-05 Editar tarea | `PATCH /tareas/{id}` | `tareas/service.py::actualizar` | `test_tareas.py` (editar, vencidas) |
| RF-06 Eliminar tarea | `DELETE /tareas/{id}` | `tareas/service.py::eliminar` | `test_tareas.py` (eliminar) |
| RF-07 Consultar y filtrar | `GET /tareas`, `GET /tareas/{id}` | `tareas/repository.py::listar` | `test_tareas.py` (filtros) |
| RF-08 Fecha límite | (en crear/editar) | `tareas/reglas.py`, CHECK en BD | `test_tareas.py`, `test_integridad_bd.py` |
| RF-09 Prioridad | (en crear/editar) | `tareas/enums.py`, CHECK en BD | `test_tareas.py` |
| RF-10 Crear materia | `POST /materias`, `GET /materias` | `materias/service.py` | `test_materias.py` |
| RF-11 Asociar materia | (en crear/editar tarea) | `tareas/service.py::_exigir_materia_propia`, FK compuesta | `test_tareas.py`, `test_integridad_bd.py` |

### Perfil y primer uso (extensión posterior a RF-11)
| Qué | Endpoint | Código principal | Pruebas |
|---|---|---|---|
| Estado del flujo, idioma, foto | `GET /usuarios/me` | `usuarios/schemas.py::UsuarioSalida` | `test_perfil.py` |
| Cambiar nombre / idioma | `PATCH /usuarios/me` | `usuarios/service.py::actualizar` | `test_perfil.py` |
| Preferencia de recordatorios (completa la personalización) | `GET`/`PUT /usuarios/me/preferencia-notificacion` | `usuarios/service.py::guardar_preferencia` | `test_perfil.py` |
| Tutorial visto (o saltado) | `POST /usuarios/me/tutorial/completar` | `usuarios/service.py::completar_tutorial` | `test_perfil.py` |
| Foto de perfil | `PUT`/`GET`/`DELETE /usuarios/me/foto` | `usuarios/imagen.py`, `usuarios/service.py` | `test_perfil.py` |

Migración `0002`: columnas `usuario.idioma`, `personalizacion_completada_en`, `tutorial_completado_en`, `foto_actualizada_en` y tablas `preferencia_notificacion` y `foto_perfil`. Si ya tenías la BD en `0001`: `alembic upgrade head`. Hace falta `pip install -r requirements.txt` (nuevo: Pillow, python-multipart).

### RF-12, RF-13 y RF-32 (notificaciones e historial)
Detalle completo en [`docs/RF-12_RF-13_RF-32.md`](docs/RF-12_RF-13_RF-32.md).

| RF | Endpoint | Código principal | Pruebas |
|---|---|---|---|
| RF-12 Generar notificaciones | `POST /notificaciones/sincronizar`, `GET /notificaciones` (+ automático al crear/editar/eliminar tareas y al cambiar preferencias) | `notificaciones/service.py` | `test_notificaciones.py` |
| RF-13 Escalar frecuencia | (dentro del plan) | `notificaciones/planificador.py` (reglas puras) | `test_planificador_notificaciones.py`, `test_notificaciones.py` |
| RF-32 Historial de tareas | `GET /tareas/{id}/historial` | `tareas/service.py`, `historial/` | `test_historial_rf32.py` |

Migración `0003` (`0003_notificaciones_rf_12_13.py`): tabla `notificacion` y columna `historial_evento.id_notificacion`. Solo agrega estructura. Si tu BD está en `0002`: `alembic upgrade head`.

Proceso periódico (opcional, idempotente): `python -m app.modules.notificaciones.procesos` registra las enviadas y extiende el plan de todos los usuarios. Se puede programar con cron.

### RF-21 a RF-27 (gamificación)
Detalle completo en [`docs/RF-21_RF-27.md`](docs/RF-21_RF-27.md).

| RF | Endpoint | Código principal | Pruebas |
|---|---|---|---|
| RF-21 Racha diaria | (automático) `GET /gamificacion/progreso` | `gamificacion/reglas.py`, `gamificacion/service.py` | `test_gamificacion_reglas.py`, `test_gamificacion.py` |
| RF-22 Puntos | (al completar una tarea) | `tareas/service.py` → `GamificacionService.tarea_completada` | `test_gamificacion.py` |
| RF-23 Logros | `GET /gamificacion/logros` | `gamificacion/service.py` | `test_gamificacion.py` |
| RF-24 Protección | `POST /gamificacion/protecciones/usar` | `gamificacion/service.py` | `test_gamificacion.py` |
| RF-25 Recuperación | `POST /gamificacion/recuperaciones`, `POST /gamificacion/recuperaciones/{id}/cancelar` | `gamificacion/service.py` | `test_gamificacion.py` |
| RF-26 Progreso | `GET /gamificacion/progreso`, `GET /gamificacion/historial` | `gamificacion/router.py` | `test_gamificacion.py` |
| RF-27 Recompensas | (automático) | `gamificacion/service.py` | `test_gamificacion.py` |

Migración `0004` (`0004_gamificacion_rf_21_27.py`): 6 tablas de gamificación, columna `tarea.fecha_programada` y catálogo de 12 logros. Solo agrega. Si tu BD está en `0003`: `alembic upgrade head`.

Proceso diario (opcional, idempotente): `python -m app.modules.gamificacion.procesos`.

### Modificaciones al modelo del documento
Ver `DECISIONES.md` y los docstrings de cada `models.py`. Resumen: se agregó `materia.nombre_normalizado` y dos restricciones únicas (soporte de RF-10/RF-11); no se crearon `usuario.auth_uid`, `tarea.progreso`, `tarea.veces_pospuesta` (ni, hasta RF-21, `tarea.fecha_programada`, que se agregó en la migración `0004`) ni los FK de historial a notificación/sesión de enfoque (pertenecen a requerimientos posteriores).

## Frontend (borrador sin verificar)
No hay carpetas `android/` ni `ios/`; se generan con Flutter instalado:
```bash
cd frontend
flutter create . --platforms=android --project-name antiprocrastinacion   # genera las plataformas sin tocar lib/
flutter pub get
flutter analyze                                                          # corregir lo que aparezca
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000        # emulador Android
```
- Con **teléfono físico**: usa la IP de tu computadora (`http://192.168.x.x:8000`) y arranca el backend con `uvicorn app.main:app --host 0.0.0.0`.
- La API usa HTTP sin cifrar en desarrollo: en `android/app/src/main/AndroidManifest.xml` agrega `android:usesCleartextTraffic="true"` en `<application>` (solo para desarrollo).
- `flutter_secure_storage` 9.x requiere `minSdkVersion` 18 o superior (en `android/app/build.gradle`).
- Pantallas: inicio de sesión, registro, **Personalización inicial**, **Tutorial**, Inicio, Tareas (filtros), crear/editar tarea, detalle, Calendario básico y **Perfil** (foto, nombre, idioma, notificaciones, tema, cerrar sesión).
- Gamificación (RF-21 a RF-27): tarjeta de racha en Inicio que abre la pantalla **Progreso** (puntos, nivel, protecciones, recuperación y logros).
- Idiomas (ES/EN): todos los textos están en `lib/l10n/textos.dart` (cada texto lleva sus dos traducciones juntas). Para un idioma nuevo: agregarlo a `idiomasSoportados` y traducir cada texto. Los datos del usuario (títulos, materias) no se traducen.
- Foto de perfil con `image_picker`: tras actualizar el repo ejecuta `flutter pub get`. En iOS ya se agregaron los textos de permiso a `Info.plist`.
- Pendiente tras compilar: probar el flujo completo contra el backend (registro → login → crear materia/tarea → filtrar → editar → eliminar → cerrar sesión → reabrir app).
