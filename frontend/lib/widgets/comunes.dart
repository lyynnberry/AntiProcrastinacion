import 'package:flutter/material.dart';

import '../api/api_client.dart';
import '../models/modelos.dart';
import '../theme/app_theme.dart';

String _dosDigitos(int n) => n.toString().padLeft(2, '0');

String formatoFecha(DateTime d) => '${_dosDigitos(d.day)}/${_dosDigitos(d.month)}/${d.year}';

String formatoFechaHora(DateTime d) =>
    '${formatoFecha(d)} ${_dosDigitos(d.hour)}:${_dosDigitos(d.minute)}';

final _regexCorreo = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');

bool esCorreoValido(String texto) => _regexCorreo.hasMatch(texto.trim());

/// Texto para mostrar al usuario: el del backend (ya viene en español) o uno genérico.
String mensajeDeError(Object? error) =>
    error is ApiException ? error.mensaje : 'Ocurrió un error inesperado. Inténtalo de nuevo.';

void mostrarMensaje(BuildContext context, String texto) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(texto)));
}

void mostrarError(BuildContext context, Object error) =>
    mostrarMensaje(context, mensajeDeError(error));

/// Barra superior plana, sin sombra, igual en todas las pantallas secundarias.
AppBar barraSimple(BuildContext context, String titulo, {List<Widget>? acciones}) {
  final tema = Theme.of(context);
  return AppBar(
    title: Text(titulo),
    actions: acciones,
    centerTitle: false,
    elevation: 0,
    scrolledUnderElevation: 0,
    backgroundColor: tema.colorScheme.surface,
    surfaceTintColor: Colors.transparent,
    foregroundColor: tema.colorScheme.onSurface,
    titleTextStyle: tema.textTheme.titleLarge?.copyWith(color: tema.colorScheme.onSurface),
  );
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
        borderRadius: BorderRadius.circular(14),
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
    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
    border: borde(e.outline),
    enabledBorder: borde(e.outline),
    focusedBorder: borde(e.secondary, 1.6),
    errorBorder: borde(e.error),
    focusedErrorBorder: borde(e.error, 1.6),
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

/// Contenedor con borde fino y esquinas redondeadas (reemplaza a Card, sin sombra).
class Superficie extends StatelessWidget {
  const Superficie({super.key, required this.child, this.padding = EdgeInsets.zero});

  final Widget child;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    final e = Theme.of(context).colorScheme;
    // Se usa Material (y no Container) para que el efecto de toque de los hijos se vea.
    return Material(
      color: e.surfaceContainerLowest,
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: e.outlineVariant),
      ),
      child: Padding(padding: padding, child: child),
    );
  }
}

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
          etiquetaEstado(estado),
          style: Theme.of(context)
              .textTheme
              .labelMedium
              ?.copyWith(color: estilo.texto, fontWeight: FontWeight.w600),
        ),
      ]),
    );
  }
}

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
          Text(mensajeDeError(error),
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: e.onSurfaceVariant)),
          const SizedBox(height: 16),
          OutlinedButton(onPressed: onReintentar, child: const Text('Reintentar')),
        ]),
      ),
    );
  }
}

/// Una opción de un [CampoSelector].
class Opcion<T> {
  const Opcion(this.valor, this.etiqueta);

  final T valor;
  final String etiqueta;
}

/// Campo que, al tocarlo, abre un diálogo para elegir una opción.
/// Se usa en lugar de un Dropdown para no depender de detalles que cambian entre versiones de Flutter.
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
    final esquema = Theme.of(context).colorScheme;
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: () async {
        final elegida = await showDialog<Opcion<T>>(
          context: context,
          builder: (ctx) => SimpleDialog(
            title: Text(etiqueta),
            children: [
              for (final o in opciones)
                SimpleDialogOption(
                  onPressed: () => Navigator.pop(ctx, o),
                  child: Row(children: [
                    Expanded(
                      child: Text(o.etiqueta,
                          style: TextStyle(
                              fontWeight: o.valor == actual.valor ? FontWeight.w700 : null)),
                    ),
                    if (o.valor == actual.valor)
                      Icon(Icons.check, size: 18, color: esquema.secondary),
                  ]),
                ),
            ],
          ),
        );
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

/// Fila de una tarea en las listas.
class TareaTile extends StatelessWidget {
  const TareaTile({super.key, required this.tarea, required this.onTap});

  final Tarea tarea;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final e = tema.colorScheme;
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(children: [
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(
                tarea.titulo,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: tema.textTheme.titleMedium?.copyWith(
                  decoration: tarea.completada ? TextDecoration.lineThrough : null,
                  color: tarea.completada ? e.onSurfaceVariant : e.onSurface,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Vence ${formatoFechaHora(tarea.fechaLimite)} · Prioridad ${(prioridades[tarea.prioridad] ?? tarea.prioridad).toLowerCase()}',
                style: tema.textTheme.bodySmall?.copyWith(color: e.onSurfaceVariant),
              ),
            ]),
          ),
          const SizedBox(width: 12),
          EtiquetaEstado(tarea.estado),
        ]),
      ),
    );
  }
}
