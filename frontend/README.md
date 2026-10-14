# AntiProcrastinación (frontend)

App Flutter para estudiantes universitarios. Avance actual: RF-01 a RF-11 (autenticación, sesión,
tareas, materias y relación tarea-materia). Requiere Flutter ≥ 3.38 (Dart ≥ 3.11).

## Ejecutar

```bash
flutter pub get
flutter run                      # Android: usa http://10.0.2.2:8000; Chrome/iOS/escritorio: http://localhost:8000
flutter run --dart-define=API_BASE_URL=http://192.168.1.50:8000   # teléfono físico
```

El backend debe estar encendido (ver su propio README). Para Chrome, el backend necesita
`ENTORNO=desarrollo` (habilita CORS solo para `localhost`).

## Comprobar

```bash
flutter analyze
flutter test
```

## Estructura

```
lib/
  api/        cliente HTTP (tokens, renovación de sesión) y repositorios
  models/     modelos que reflejan las respuestas del backend
  state/      controladores: sesión (AuthController) y tema (TemaController)
  theme/      paleta de colores y tema claro/oscuro (app_theme.dart)
  screens/    pantallas
  widgets/    widgets compartidos (campos, etiquetas de estado, filas de tarea)
```

## Diseño, tema y colores

Estilo minimalista y suave: fondo neutro con un degradado muy sutil, tarjetas blancas muy
redondeadas, barra inferior flotante, píldoras para filtros y un anillo de progreso en Inicio.
Los colores de la paleta (verde, rosa, marrón) se usan solo como acentos; los fondos son neutros.

El tema claro es el predeterminado; en **Perfil → Apariencia** se puede cambiar a oscuro o al del
sistema, y la elección se recuerda. Todos los colores están en `lib/theme/app_theme.dart` y el
comentario de `Paleta` explica para qué se usa cada uno. Los componentes visuales compartidos
(tarjetas, píldoras, anillo, etiquetas) están en `lib/widgets/comunes.dart`.
