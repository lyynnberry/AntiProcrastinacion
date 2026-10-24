import 'package:flutter/material.dart';

/// Paleta de la app. Los cinco colores base vienen del diseño y se usan solo como ACENTOS;
/// los fondos son neutros (blancos y grises cálidos con un degradado muy suave).
///
/// ── TEMA CLARO (predeterminado) ───────────────────────────────────────────────
/// [verde]      #96B23C  Acción principal: botones (Entrar, Crear cuenta, Guardar, Marcar como
///                       completada), opción activa de la barra inferior, anillo de progreso,
///                       estado "Completada" y prioridad "Baja".
/// [verdeClaro] #DFEAA6  Etiquetas pequeñas: estado "En progreso" y prioridad "Baja".
/// [verdeOscuro]#628D3D  Botón presionado, borde del campo enfocado, indicador de carga,
///                       marca de "hoy" y puntos de tareas en el calendario.
/// [rosa]       #F2CEDD  Estado "Vencida", prioridad "Alta", avatar y toque de color del fondo.
/// [marron]     #665048  Texto, íconos y bordes de botones secundarios.
/// ── Neutros derivados (fondos) ────────────────────────────────────────────────
/// [fondoClaro] #F4F1EF  Fondo base.  Degradado: [degradadoClaro] rosa muy suave → gris cálido
///                       → gris lavanda, igual en todas las pantallas.
/// [blanco]     #FFFFFF  Tarjetas y campos.        [bordeClaro]  #E9E4E1  Líneas finas.
/// [tintaClaro] #2B2421  Tarjeta de progreso, barra inferior y botones circulares; también el
///                       texto sobre el verde de los botones.
/// [errorClaro] #B3423A  Errores de formulario y acción de eliminar.
///
/// ── TEMA OSCURO (misma paleta, otros tonos) ───────────────────────────────────
/// [oscFondo]  #1F1A18  Fondo base (degradado [degradadoOscuro]).  [oscSuperficie] #2B2425 Tarjetas.
/// [oscTarjetaOscura] #100D0D  Tarjeta de progreso.   [oscVerde] #A9C34A  Botones y activos.
/// [oscVerde2] #7FB052  Botón presionado, foco, "hoy".  [oscRosaFondo] #4A3A42  "Vencida" y "Alta".
/// [oscTexto]  #F1EAE6  Texto principal.   [oscBorde] #3A3230  Líneas.   [oscError] #E8837A  Errores.
class Paleta {
  Paleta._();

  // Base (acentos)
  static const verdeClaro = Color(0xFFDFEAA6);
  static const verde = Color(0xFF96B23C);
  static const verdeOscuro = Color(0xFF628D3D);
  static const rosa = Color(0xFFF2CEDD);
  static const marron = Color(0xFF665048);

  // Neutros del tema claro
  static const fondoClaro = Color(0xFFF4F1EF);
  static const blanco = Color(0xFFFFFFFF);
  static const bordeClaro = Color(0xFFE9E4E1);
  static const campoClaro = Color(0xFFCFC8C3);
  static const marronSuave = Color(0xFF7A665D);
  static const tintaClaro = Color(0xFF2B2421);
  static const errorClaro = Color(0xFFB3423A);
  static const neutroClaro = Color(0xFFEFEBE8);
  static const degradadoClaro = [Color(0xFFF8E6EC), Color(0xFFF4F1EF), Color(0xFFE9E6F0)];

  // Tema oscuro
  static const oscFondo = Color(0xFF1F1A18);
  static const oscSuperficie = Color(0xFF2B2425);
  static const oscTarjetaOscura = Color(0xFF100D0D);
  static const oscBorde = Color(0xFF3A3230);
  static const oscCampo = Color(0xFF54484A);
  static const oscVerde = Color(0xFFA9C34A);
  static const oscVerde2 = Color(0xFF7FB052);
  static const oscSeleccion = Color(0xFF424D26);
  static const oscRosaFondo = Color(0xFF4A3A42);
  static const oscRosa = Color(0xFFE8B8CD);
  static const oscTexto = Color(0xFFF1EAE6);
  static const oscTextoSuave = Color(0xFFBDB3AD);
  static const oscNeutro = Color(0xFF352D2D);
  static const oscError = Color(0xFFE8837A);
  static const degradadoOscuro = [Color(0xFF2B2025), Color(0xFF1C1819), Color(0xFF1F1D26)];
}

const _esquemaClaro = ColorScheme(
  brightness: Brightness.light,
  primary: Paleta.verde,
  onPrimary: Paleta.tintaClaro,
  primaryContainer: Paleta.verdeClaro,
  onPrimaryContainer: Paleta.marron,
  secondary: Paleta.verdeOscuro,
  onSecondary: Paleta.tintaClaro,
  secondaryContainer: Paleta.verdeClaro,
  onSecondaryContainer: Paleta.marron,
  tertiary: Paleta.rosa,
  onTertiary: Paleta.marron,
  tertiaryContainer: Paleta.rosa,
  onTertiaryContainer: Paleta.marron,
  error: Paleta.errorClaro,
  onError: Paleta.blanco,
  errorContainer: Paleta.rosa,
  onErrorContainer: Paleta.marron,
  surface: Paleta.fondoClaro,
  onSurface: Paleta.marron,
  onSurfaceVariant: Paleta.marronSuave,
  outline: Paleta.campoClaro,
  outlineVariant: Paleta.bordeClaro,
  shadow: Colors.black,
  scrim: Colors.black,
  inverseSurface: Paleta.tintaClaro,
  onInverseSurface: Paleta.blanco,
  inversePrimary: Paleta.verdeClaro,
  surfaceTint: Colors.transparent,
  surfaceContainerLowest: Paleta.blanco,
  surfaceContainerLow: Color(0xFFF7F4F2),
  surfaceContainer: Color(0xFFF1EEEC),
  surfaceContainerHigh: Paleta.blanco,
  surfaceContainerHighest: Paleta.bordeClaro,
);

const _esquemaOscuro = ColorScheme(
  brightness: Brightness.dark,
  primary: Paleta.oscVerde,
  onPrimary: Paleta.oscFondo,
  primaryContainer: Paleta.oscSeleccion,
  onPrimaryContainer: Paleta.oscTexto,
  secondary: Paleta.oscVerde2,
  onSecondary: Paleta.oscFondo,
  secondaryContainer: Paleta.oscSeleccion,
  onSecondaryContainer: Paleta.oscTexto,
  tertiary: Paleta.oscRosa,
  onTertiary: Paleta.oscFondo,
  tertiaryContainer: Paleta.oscRosaFondo,
  onTertiaryContainer: Paleta.rosa,
  error: Paleta.oscError,
  onError: Paleta.oscFondo,
  errorContainer: Paleta.oscRosaFondo,
  onErrorContainer: Paleta.rosa,
  surface: Paleta.oscFondo,
  onSurface: Paleta.oscTexto,
  onSurfaceVariant: Paleta.oscTextoSuave,
  outline: Paleta.oscCampo,
  outlineVariant: Paleta.oscBorde,
  shadow: Colors.black,
  scrim: Colors.black,
  inverseSurface: Paleta.oscTexto,
  onInverseSurface: Paleta.oscFondo,
  inversePrimary: Paleta.verde,
  surfaceTint: Colors.transparent,
  surfaceContainerLowest: Paleta.oscSuperficie,
  surfaceContainerLow: Color(0xFF241E1F),
  surfaceContainer: Paleta.oscSuperficie,
  surfaceContainerHigh: Color(0xFF352D2D),
  surfaceContainerHighest: Paleta.oscBorde,
);

/// Construye el tema minimalista: sin sombras, bordes finos, esquinas redondeadas y mucho aire.
ThemeData construirTema(Brightness brillo) {
  final esquema = brillo == Brightness.light ? _esquemaClaro : _esquemaOscuro;
  final base = ThemeData(colorScheme: esquema, useMaterial3: true).textTheme;

  TextStyle? peso(TextStyle? estilo, FontWeight w, {double? espaciado}) =>
      estilo?.copyWith(fontWeight: w, letterSpacing: espaciado);

  final textos = base.copyWith(
    headlineMedium: peso(base.headlineMedium, FontWeight.w600, espaciado: -0.5),
    headlineSmall: peso(base.headlineSmall, FontWeight.w600, espaciado: -0.3),
    titleLarge: peso(base.titleLarge, FontWeight.w600),
    titleMedium: peso(base.titleMedium, FontWeight.w600),
    titleSmall: peso(base.titleSmall, FontWeight.w600),
    labelLarge: peso(base.labelLarge, FontWeight.w600),
  );

  final forma = RoundedRectangleBorder(borderRadius: BorderRadius.circular(28));
  final estadoPresionado = <WidgetState>{
    WidgetState.pressed,
    WidgetState.hovered,
    WidgetState.focused,
  };

  return ThemeData(
    useMaterial3: true,
    colorScheme: esquema,
    scaffoldBackgroundColor: esquema.surface,
    textTheme: textos,
    splashFactory: InkRipple.splashFactory,
    dividerTheme: DividerThemeData(color: esquema.outlineVariant, thickness: 1, space: 1),
    progressIndicatorTheme: ProgressIndicatorThemeData(color: esquema.secondary),
    textSelectionTheme: TextSelectionThemeData(
      cursorColor: esquema.secondary,
      selectionColor: esquema.primary.withValues(alpha: 0.35),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: ButtonStyle(
        elevation: const WidgetStatePropertyAll(0),
        minimumSize: const WidgetStatePropertyAll(Size(64, 54)),
        shape: WidgetStatePropertyAll(forma),
        textStyle: const WidgetStatePropertyAll(
            TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
        backgroundColor: WidgetStateProperty.resolveWith((estados) {
          if (estados.contains(WidgetState.disabled)) {
            return esquema.primary.withValues(alpha: 0.35);
          }
          return estados.any(estadoPresionado.contains) ? esquema.secondary : esquema.primary;
        }),
        foregroundColor: WidgetStateProperty.resolveWith((estados) {
          if (estados.contains(WidgetState.disabled)) {
            return esquema.onPrimary.withValues(alpha: 0.5);
          }
          return estados.any(estadoPresionado.contains) ? esquema.onSecondary : esquema.onPrimary;
        }),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: ButtonStyle(
        minimumSize: const WidgetStatePropertyAll(Size(64, 54)),
        shape: WidgetStatePropertyAll(forma),
        foregroundColor: WidgetStatePropertyAll(esquema.onSurface),
        textStyle: const WidgetStatePropertyAll(
            TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
        side: WidgetStateProperty.resolveWith((estados) => BorderSide(
            color: estados.contains(WidgetState.disabled)
                ? esquema.outlineVariant
                : esquema.outline)),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: ButtonStyle(
        shape: WidgetStatePropertyAll(forma),
        foregroundColor: WidgetStateProperty.resolveWith((estados) =>
            estados.contains(WidgetState.disabled)
                ? esquema.onSurface.withValues(alpha: 0.4)
                : esquema.onSurface),
        textStyle: const WidgetStatePropertyAll(
            TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
      ),
    ),
    segmentedButtonTheme: SegmentedButtonThemeData(
      style: ButtonStyle(
        shape: WidgetStatePropertyAll(forma),
        side: WidgetStatePropertyAll(BorderSide(color: esquema.outline)),
        textStyle: const WidgetStatePropertyAll(
            TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
        backgroundColor: WidgetStateProperty.resolveWith((estados) =>
            estados.contains(WidgetState.selected)
                ? esquema.primaryContainer
                : esquema.surfaceContainerLowest),
        foregroundColor: WidgetStateProperty.resolveWith((estados) =>
            estados.contains(WidgetState.selected)
                ? esquema.onPrimaryContainer
                : esquema.onSurfaceVariant),
      ),
    ),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      backgroundColor: esquema.inverseSurface,
      contentTextStyle: TextStyle(color: esquema.onInverseSurface, fontSize: 14),
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
  );
}

/// Colores de la etiqueta de un estado de tarea.
class EstiloEstado {
  const EstiloEstado({required this.fondo, required this.texto, required this.punto});

  final Color fondo;
  final Color texto;
  final Color punto;
}

/// Los estados se distinguen por color Y por texto (nunca solo por color).
EstiloEstado estiloEstado(BuildContext context, String estado) {
  final oscuro = Theme.of(context).brightness == Brightness.dark;
  switch (estado) {
    case 'VENCIDA':
      return oscuro
          ? const EstiloEstado(
              fondo: Paleta.oscRosaFondo, texto: Paleta.rosa, punto: Paleta.oscError)
          : const EstiloEstado(
              fondo: Paleta.rosa, texto: Paleta.marron, punto: Paleta.errorClaro);
    case 'COMPLETADA':
      return oscuro
          ? const EstiloEstado(
              fondo: Paleta.oscVerde, texto: Paleta.oscFondo, punto: Paleta.oscFondo)
          : const EstiloEstado(
              fondo: Paleta.verde, texto: Paleta.tintaClaro, punto: Paleta.tintaClaro);
    case 'EN_PROGRESO':
      return oscuro
          ? const EstiloEstado(
              fondo: Paleta.oscSeleccion, texto: Paleta.oscTexto, punto: Paleta.oscVerde)
          : const EstiloEstado(
              fondo: Paleta.verdeClaro, texto: Paleta.marron, punto: Paleta.verdeOscuro);
    default: // PENDIENTE
      return oscuro
          ? const EstiloEstado(
              fondo: Paleta.oscNeutro, texto: Paleta.oscTexto, punto: Paleta.oscTextoSuave)
          : const EstiloEstado(
              fondo: Paleta.neutroClaro, texto: Paleta.marron, punto: Paleta.marronSuave);
  }
}

/// Colores de la etiqueta de prioridad (borde + fondo suave + punto).
class EstiloPrioridad {
  const EstiloPrioridad({
    required this.fondo,
    required this.borde,
    required this.texto,
    required this.punto,
  });

  final Color fondo;
  final Color borde;
  final Color texto;
  final Color punto;
}

/// Baja = verde, Media = ámbar, Alta = rosa. Siempre acompañadas de texto.
EstiloPrioridad estiloPrioridad(BuildContext context, String prioridad) {
  final oscuro = Theme.of(context).brightness == Brightness.dark;
  switch (prioridad) {
    case 'ALTA':
      return oscuro
          ? const EstiloPrioridad(
              fondo: Paleta.oscRosaFondo,
              borde: Color(0xFFC9738D),
              texto: Paleta.rosa,
              punto: Paleta.oscError)
          : const EstiloPrioridad(
              fondo: Paleta.rosa,
              borde: Color(0xFFDB8FA8),
              texto: Paleta.marron,
              punto: Paleta.errorClaro);
    case 'MEDIA':
      return oscuro
          ? const EstiloPrioridad(
              fondo: Color(0xFF4D3F2A),
              borde: Color(0xFFD9A45B),
              texto: Paleta.oscTexto,
              punto: Color(0xFFE0AE62))
          : const EstiloPrioridad(
              fondo: Color(0xFFFBE6C8),
              borde: Color(0xFFE3A857),
              texto: Paleta.marron,
              punto: Color(0xFFC9822A));
    default: // BAJA
      return oscuro
          ? const EstiloPrioridad(
              fondo: Paleta.oscSeleccion,
              borde: Paleta.oscVerde,
              texto: Paleta.oscTexto,
              punto: Paleta.oscVerde)
          : const EstiloPrioridad(
              fondo: Paleta.verdeClaro,
              borde: Paleta.verde,
              texto: Paleta.marron,
              punto: Paleta.verdeOscuro);
  }
}
