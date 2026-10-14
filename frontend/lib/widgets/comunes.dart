import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../api/api_client.dart';
import '../l10n/textos.dart';
import '../models/modelos.dart';
import '../theme/app_theme.dart';

final _regexCorreo = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');

bool esCorreoValido(String texto) => _regexCorreo.hasMatch(texto.trim());

/// Texto para mostrar al usuario, en el idioma de la app. Los errores del backend se traducen por su
/// código; si el código no se conoce, en español se muestra el mensaje del servidor (ya viene en español)
/// y en otros idiomas uno genérico.
String mensajeDeError(BuildContext context, Object? error) {
  final t = context.t;
  if (error is ApiException) {
    return t.errorPorCodigo(error.codigo) ?? (t.esEn ? t.errorInesperado : error.mensaje);
  }
  return t.errorInesperado;
}

void mostrarMensaje(BuildContext context, String texto) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(texto)));
}

void mostrarError(BuildContext context, Object error) =>
    mostrarMensaje(context, mensajeDeError(context, error));

// ─────────────────────────── Estructura de pantalla ───────────────────────────

/// Pantalla con el fondo degradado neutro de la app. Cada pantalla lleva su propio fondo
/// (y no uno global) para que las transiciones entre pantallas se vean opacas y limpias.
class Pantalla extends StatelessWidget {
  const Pantalla({super.key, required this.body, this.appBar, this.barraInferior});

  final Widget body;
  final PreferredSizeWidget? appBar;
  final Widget? barraInferior;

  @override
  Widget build(BuildContext context) {
    final oscuro = Theme.of(context).brightness == Brightness.dark;
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: oscuro ? Paleta.degradadoOscuro : Paleta.degradadoClaro,
          stops: const [0, 0.5, 1],
        ),
      ),
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: appBar,
        body: body,
        bottomNavigationBar: barraInferior,
      ),
    );
  }
}

/// Barra superior transparente, sin sombra, igual en todas las pantallas secundarias.
AppBar barraSimple(BuildContext context, String titulo, {List<Widget>? acciones}) {
  final tema = Theme.of(context);
  return AppBar(
    title: Text(titulo),
    actions: acciones,
    centerTitle: false,
    elevation: 0,
    scrolledUnderElevation: 0,
    backgroundColor: Colors.transparent,
    surfaceTintColor: Colors.transparent,
    foregroundColor: tema.colorScheme.onSurface,
    titleTextStyle: tema.textTheme.titleLarge?.copyWith(color: tema.colorScheme.onSurface),
  );
}

/// Limita el ancho del contenido para que en pantallas grandes (web, tablet) no se estire.
class ContenidoCentrado extends StatelessWidget {
  const ContenidoCentrado({super.key, required this.child, this.anchoMaximo = 640});

  final Widget child;
  final double anchoMaximo;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.topCenter,
      child: ConstrainedBox(constraints: BoxConstraints(maxWidth: anchoMaximo), child: child),
    );
  }
}

/// Tarjeta blanca de esquinas muy redondeadas con una sombra apenas visible.
/// Si recibe [onTap], toda la tarjeta responde al toque.
class Superficie extends StatelessWidget {
  const Superficie({
    super.key,
    required this.child,
    this.padding = EdgeInsets.zero,
    this.onTap,
    this.radio = 24,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final VoidCallback? onTap;
  final double radio;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final e = tema.colorScheme;
    final oscuro = tema.brightness == Brightness.dark;
    final contenido = Padding(padding: padding, child: child);
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(radio),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: oscuro ? 0.25 : 0.05),
            blurRadius: 24,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      // Se usa Material (y no Container) para que el efecto de toque de los hijos se vea.
      child: Material(
        color: e.surfaceContainerLowest,
        clipBehavior: Clip.antiAlias,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radio),
          side: oscuro ? BorderSide(color: e.outlineVariant) : BorderSide.none,
        ),
        child: onTap == null ? contenido : InkWell(onTap: onTap, child: contenido),
      ),
    );
  }
}

/// Aspecto de todos los campos de texto (se define aquí y no en el tema para no depender
/// de cambios de API entre versiones de Flutter).
InputDecoration decoracionCampo(
  BuildContext context,
  String etiqueta, {
  String? ayuda,
  Widget? sufijo,
}) {
  final e = Theme.of(context).colorScheme;
  OutlineInputBorder borde(Color color, [double ancho = 1]) => OutlineInputBorder(
        borderRadius: BorderRadius.circular(20),
        borderSide: BorderSide(color: color, width: ancho),
      );
  return InputDecoration(
    labelText: etiqueta,
    helperText: ayuda,
    helperMaxLines: 2,
    suffixIcon: sufijo,
    filled: true,
    fillColor: e.surfaceContainerLowest,
    floatingLabelStyle: TextStyle(color: e.onSurface),
    contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
    border: borde(e.outlineVariant),
    enabledBorder: borde(e.outlineVariant),
    focusedBorder: borde(e.secondary, 1.6),
    errorBorder: borde(e.error),
    focusedErrorBorder: borde(e.error, 1.6),
  );
}

// ─────────────────────────────── Botones y píldoras ───────────────────────────────

/// Botón circular oscuro (como el "+" de las referencias).
class BotonCircular extends StatelessWidget {
  const BotonCircular({
    super.key,
    required this.icono,
    required this.tooltip,
    required this.onPressed,
  });

  final IconData icono;
  final String tooltip;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    final e = Theme.of(context).colorScheme;
    return Tooltip(
      message: tooltip,
      child: Material(
        color: e.inverseSurface,
        shape: const CircleBorder(),
        child: InkWell(
          customBorder: const CircleBorder(),
          onTap: onPressed,
          child: SizedBox(
            width: 48,
            height: 48,
            child: Icon(icono, color: e.onInverseSurface),
          ),
        ),
      ),
    );
  }
}

/// Píldora para filtros y opciones. Activa = oscura.
class PildoraFiltro extends StatelessWidget {
  const PildoraFiltro({
    super.key,
    required this.etiqueta,
    required this.onTap,
    this.activo = false,
    this.icono,
    this.conFlecha = false,
  });

  final String etiqueta;
  final VoidCallback? onTap;
  final bool activo;
  final IconData? icono;
  final bool conFlecha;

  @override
  Widget build(BuildContext context) {
    final e = Theme.of(context).colorScheme;
    final color = activo ? e.onInverseSurface : e.onSurface;
    return Semantics(
      button: true,
      selected: activo,
      child: Material(
        color: activo ? e.inverseSurface : e.surfaceContainerLowest,
        shape: StadiumBorder(
          side: activo ? BorderSide.none : BorderSide(color: e.outlineVariant),
        ),
        child: InkWell(
          customBorder: const StadiumBorder(),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
            child: Row(mainAxisSize: MainAxisSize.min, children: [
              if (icono != null) ...[Icon(icono, size: 18, color: color), const SizedBox(width: 6)],
              Text(etiqueta,
                  style: Theme.of(context)
                      .textTheme
                      .labelLarge
                      ?.copyWith(color: color, fontWeight: FontWeight.w600)),
              if (conFlecha) ...[
                const SizedBox(width: 4),
                Icon(Icons.keyboard_arrow_down, size: 18, color: color),
              ],
            ]),
          ),
        ),
      ),
    );
  }
}

/// Una opción de un [CampoSelector] o [SelectorPildora].
class Opcion<T> {
  const Opcion(this.valor, this.etiqueta);

  final T valor;
  final String etiqueta;
}

/// Diálogo para elegir una opción. Se usa en lugar de un Dropdown para no depender de
/// detalles que cambian entre versiones de Flutter.
Future<Opcion<T>?> elegirOpcion<T>(
  BuildContext context,
  String etiqueta,
  List<Opcion<T>> opciones,
  T valor,
) {
  return showDialog<Opcion<T>>(
    context: context,
    builder: (ctx) {
      final esquema = Theme.of(ctx).colorScheme;
      return SimpleDialog(
        title: Text(etiqueta),
        children: [
          for (final o in opciones)
            SimpleDialogOption(
              onPressed: () => Navigator.pop(ctx, o),
              child: Row(children: [
                Expanded(
                  child: Text(o.etiqueta,
                      style: TextStyle(fontWeight: o.valor == valor ? FontWeight.w700 : null)),
                ),
                if (o.valor == valor) Icon(Icons.check, size: 18, color: esquema.secondary),
              ]),
            ),
        ],
      );
    },
  );
}

/// Filtro compacto en forma de píldora. La PRIMERA opción es la de "sin filtro";
/// cuando se elige otra, la píldora se vuelve oscura y muestra el valor elegido.
class SelectorPildora<T> extends StatelessWidget {
  const SelectorPildora({
    super.key,
    required this.etiqueta,
    required this.opciones,
    required this.valor,
    required this.onChanged,
  });

  final String etiqueta;
  final List<Opcion<T>> opciones;
  final T valor;
  final ValueChanged<T> onChanged;

  @override
  Widget build(BuildContext context) {
    final actual = opciones.firstWhere((o) => o.valor == valor, orElse: () => opciones.first);
    final filtrado = actual.valor != opciones.first.valor;
    return PildoraFiltro(
      etiqueta: filtrado ? '$etiqueta: ${actual.etiqueta}' : etiqueta,
      activo: filtrado,
      conFlecha: true,
      onTap: () async {
        final elegida = await elegirOpcion<T>(context, etiqueta, opciones, actual.valor);
        if (elegida != null) onChanged(elegida.valor);
      },
    );
  }
}

/// Campo de formulario que, al tocarlo, abre un diálogo para elegir una opción.
class CampoSelector<T> extends StatelessWidget {
  const CampoSelector({
    super.key,
    required this.etiqueta,
    required this.opciones,
    required this.valor,
    required this.onChanged,
  });

  final String etiqueta;
  final List<Opcion<T>> opciones;
  final T valor;
  final ValueChanged<T> onChanged;

  @override
  Widget build(BuildContext context) {
    final actual = opciones.firstWhere((o) => o.valor == valor, orElse: () => opciones.first);
    return InkWell(
      borderRadius: BorderRadius.circular(20),
      onTap: () async {
        final elegida = await elegirOpcion<T>(context, etiqueta, opciones, actual.valor);
        if (elegida != null) onChanged(elegida.valor);
      },
      child: InputDecorator(
        decoration: decoracionCampo(
          context,
          etiqueta,
          sufijo: const Icon(Icons.keyboard_arrow_down),
        ),
        child: Text(actual.etiqueta, maxLines: 1, overflow: TextOverflow.ellipsis),
      ),
    );
  }
}

// ─────────────────────────────── Etiquetas de tarea ───────────────────────────────

/// Estado de una tarea como etiqueta: punto de color + texto.
class EtiquetaEstado extends StatelessWidget {
  const EtiquetaEstado(this.estado, {super.key});

  final String estado;

  @override
  Widget build(BuildContext context) {
    final estilo = estiloEstado(context, estado);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: estilo.fondo, borderRadius: BorderRadius.circular(20)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Container(
          width: 6,
          height: 6,
          decoration: BoxDecoration(color: estilo.punto, shape: BoxShape.circle),
        ),
        const SizedBox(width: 6),
        Text(
          context.t.estado(estado),
          style: Theme.of(context)
              .textTheme
              .labelMedium
              ?.copyWith(color: estilo.texto, fontWeight: FontWeight.w600),
        ),
      ]),
    );
  }
}

/// Prioridad de una tarea: píldora con borde, punto y texto ("Prioridad alta").
class EtiquetaPrioridad extends StatelessWidget {
  const EtiquetaPrioridad(this.prioridad, {super.key, this.corta = false});

  final String prioridad;

  /// Si es true muestra solo "Alta"; si no, "Prioridad alta".
  final bool corta;

  @override
  Widget build(BuildContext context) {
    final estilo = estiloPrioridad(context, prioridad);
    final t = context.t;
    final nombre = t.prioridad(prioridad);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: estilo.fondo,
        border: Border.all(color: estilo.borde),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Container(
          width: 6,
          height: 6,
          decoration: BoxDecoration(color: estilo.punto, shape: BoxShape.circle),
        ),
        const SizedBox(width: 6),
        Text(
          corta ? nombre : t.prioridadLarga(prioridad),
          style: Theme.of(context)
              .textTheme
              .labelMedium
              ?.copyWith(color: estilo.texto, fontWeight: FontWeight.w600),
        ),
      ]),
    );
  }
}

/// Tarjeta de una tarea en las listas.
class TareaTile extends StatelessWidget {
  const TareaTile({super.key, required this.tarea, required this.onTap});

  final Tarea tarea;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final e = tema.colorScheme;
    return Superficie(
      onTap: onTap,
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          EtiquetaPrioridad(tarea.prioridad),
          const Spacer(),
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: e.outlineVariant),
            ),
            child: Icon(Icons.north_east, size: 16, color: e.onSurface),
          ),
        ]),
        const SizedBox(height: 12),
        Text(
          tarea.titulo,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: tema.textTheme.titleMedium?.copyWith(
            decoration: tarea.completada ? TextDecoration.lineThrough : null,
            color: tarea.completada ? e.onSurfaceVariant : e.onSurface,
          ),
        ),
        const SizedBox(height: 12),
        Row(children: [
          Icon(Icons.schedule, size: 16, color: e.onSurfaceVariant),
          const SizedBox(width: 6),
          Expanded(
            child: Text(context.t.vence(tarea.fechaLimite),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: tema.textTheme.bodySmall?.copyWith(color: e.onSurfaceVariant)),
          ),
          const SizedBox(width: 8),
          EtiquetaEstado(tarea.estado),
        ]),
      ]),
    );
  }
}

// ─────────────────────────────── Estados de pantalla ───────────────────────────────

/// Mensaje centrado cuando no hay nada que mostrar.
class EstadoVacio extends StatelessWidget {
  const EstadoVacio({super.key, required this.icono, required this.mensaje});

  final IconData icono;
  final String mensaje;

  @override
  Widget build(BuildContext context) {
    final e = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(icono, size: 36, color: e.outline),
          const SizedBox(height: 12),
          Text(mensaje,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: e.onSurfaceVariant)),
        ]),
      ),
    );
  }
}

/// Error de carga con botón para reintentar.
class EstadoError extends StatelessWidget {
  const EstadoError({super.key, required this.error, required this.onReintentar});

  final Object? error;
  final VoidCallback onReintentar;

  @override
  Widget build(BuildContext context) {
    final e = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(Icons.cloud_off_outlined, size: 36, color: e.outline),
          const SizedBox(height: 12),
          Text(mensajeDeError(context, error),
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: e.onSurfaceVariant)),
          const SizedBox(height: 16),
          OutlinedButton(onPressed: onReintentar, child: Text(context.t.reintentar)),
        ]),
      ),
    );
  }
}

// ─────────────────────────────────── Progreso ───────────────────────────────────

/// Anillo de progreso con contenido al centro (como el "72%" de las referencias).
class AnilloProgreso extends StatelessWidget {
  const AnilloProgreso({
    super.key,
    required this.valor,
    required this.colorPista,
    required this.colorBarra,
    required this.child,
    this.tamano = 104,
    this.grosor = 11,
  });

  /// De 0 a 1.
  final double valor;
  final Color colorPista;
  final Color colorBarra;
  final Widget child;
  final double tamano;
  final double grosor;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: tamano,
      height: tamano,
      child: Stack(alignment: Alignment.center, children: [
        CustomPaint(
          size: Size.square(tamano),
          painter: _PintorAnillo(valor.clamp(0.0, 1.0), colorPista, colorBarra, grosor),
        ),
        child,
      ]),
    );
  }
}

class _PintorAnillo extends CustomPainter {
  _PintorAnillo(this.valor, this.colorPista, this.colorBarra, this.grosor);

  final double valor;
  final Color colorPista;
  final Color colorBarra;
  final double grosor;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = (Offset.zero & size).deflate(grosor / 2);
    final pincel = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = grosor
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(rect, 0, 2 * math.pi, false, pincel..color = colorPista);
    if (valor > 0) {
      canvas.drawArc(rect, -math.pi / 2, 2 * math.pi * valor, false, pincel..color = colorBarra);
    }
  }

  @override
  bool shouldRepaint(_PintorAnillo anterior) =>
      anterior.valor != valor ||
      anterior.colorPista != colorPista ||
      anterior.colorBarra != colorBarra ||
      anterior.grosor != grosor;
}
