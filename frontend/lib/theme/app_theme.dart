import 'package:flutter/material.dart';

/// Paleta de la app. Los cinco colores base vienen del diseño; el resto son neutros derivados
/// de ellos (fondos, bordes y texto) para que la interfaz se vea limpia y legible.
///
/// ── TEMA CLARO (predeterminado) ───────────────────────────────────────────────
/// [verdeClaro] #DFEAA6  Elemento seleccionado: pestaña activa, día elegido en el calendario,
///                       opción activa de los selectores, estado "En progreso", avatar.
/// [verde]      #96B23C  Acción principal: botones (Entrar, Crear cuenta, Guardar, Marcar como
///                       completada), botón flotante "Nueva tarea" y estado "Completada".
/// [verdeOscuro]#628D3D  Detalles de interacción: botón al presionarlo, borde del campo
///                       enfocado, indicador de carga, marca "hoy" y puntos del calendario.
/// [rosa]       #F2CEDD  Atención: estado "Vencida" y su tarjeta en el resumen de Inicio.
/// [marron]     #665048  Texto, íconos, bordes de botones secundarios y barra de mensajes.
/// ── Derivados claros ──────────────────────────────────────────────────────────
/// [fondoClaro] #FBFCF5  Fondo de todas las pantallas.     [blanco]      #FFFFFF  Campos y listas.
/// [bordeClaro] #E4E8D0  Líneas y divisores.               [tintaClaro]  #2B2421  Texto sobre el verde.
/// [errorClaro] #B3423A  Errores de formulario y acción de eliminar.
///
/// ── TEMA OSCURO (misma paleta, otros tonos) ───────────────────────────────────
/// [oscFondo]  #1F1A18  Fondo (marrón muy oscuro, de #665048).   [oscSuperficie] #2B2421  Campos y listas.
/// [oscVerde]  #A9C34A  Botones y botón flotante (#96B23C más luminoso).
/// [oscVerde2] #7FB052  Botón presionado, foco, carga, "hoy" (#628D3D más claro).
/// [oscSeleccion] #424D26 Elemento seleccionado y "En progreso" (#DFEAA6 en tono profundo).
/// [oscRosaFondo] #4A3A42 Estado "Vencida" (#F2CEDD apagado); su texto usa [rosa].
/// [oscTexto]  #E9F0C4  Texto principal (#DFEAA6 suavizado).
/// [oscBorde]  #3E3430  Líneas y divisores.   [oscError] #E8837A  Errores.
class Paleta {
  Paleta._();

  // Base (tema claro)
  static const verdeClaro = Color(0xFFDFEAA6);
  static const verde = Color(0xFF96B23C);
  static const verdeOscuro = Color(0xFF628D3D);
  static const rosa = Color(0xFFF2CEDD);
  static const marron = Color(0xFF665048);

  // Derivados del tema claro
  static const fondoClaro = Color(0xFFFBFCF5);
  static const blanco = Color(0xFFFFFFFF);
  static const bordeClaro = Color(0xFFE4E8D0);
  static const campoClaro = Color(0xFFBFC6A0);
  static const marronSuave = Color(0xFF7A665D);
  static const tintaClaro = Color(0xFF2B2421);
  static const errorClaro = Color(0xFFB3423A);
  static const neutroClaro = Color(0xFFEEF0E0);

  // Tema oscuro
  static const oscFondo = Color(0xFF1F1A18);
  static const oscSuperficie = Color(0xFF2B2421);
  static const oscBorde = Color(0xFF3E3430);
  static const oscCampo = Color(0xFF5A4C46);
  static const oscVerde = Color(0xFFA9C34A);
  static const oscVerde2 = Color(0xFF7FB052);
  static const oscSeleccion = Color(0xFF424D26);
  static const oscRosaFondo = Color(0xFF4A3A42);
  static const oscRosa = Color(0xFFE8B8CD);
  static const oscTexto = Color(0xFFE9F0C4);
  static const oscTextoSuave = Color(0xFFC4BFAA);
  static const oscNeutro = Color(0xFF352C28);
  static const oscError = Color(0xFFE8837A);
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
  inverseSurface: Paleta.marron,
  onInverseSurface: Paleta.fondoClaro,
  inversePrimary: Paleta.verdeClaro,
  surfaceTint: Colors.transparent,
  surfaceContainerLowest: Paleta.blanco,
  surfaceContainerLow: Color(0xFFF6F8EC),
  surfaceContainer: Color(0xFFF1F4E3),
  surfaceContainerHigh: Paleta.blanco,
  surfaceContainerHighest: Color(0xFFEAEED9),
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
  surfaceContainerLow: Color(0xFF241E1B),
  surfaceContainer: Paleta.oscSuperficie,
  surfaceContainerHigh: Color(0xFF352C28),
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

  final forma = RoundedRectangleBorder(borderRadius: BorderRadius.circular(14));
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
        minimumSize: const WidgetStatePropertyAll(Size(64, 50)),
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
        minimumSize: const WidgetStatePropertyAll(Size(64, 50)),
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
    floatingActionButtonTheme: FloatingActionButtonThemeData(
      backgroundColor: esquema.primary,
      foregroundColor: esquema.onPrimary,
      elevation: 0,
      focusElevation: 0,
      hoverElevation: 0,
      highlightElevation: 0,
      shape: const StadiumBorder(),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: esquema.surface,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      height: 68,
      indicatorColor: esquema.primaryContainer,
      labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
      iconTheme: WidgetStateProperty.resolveWith((estados) => IconThemeData(
          size: 24,
          color: estados.contains(WidgetState.selected)
              ? esquema.onPrimaryContainer
              : esquema.onSurfaceVariant)),
      labelTextStyle: WidgetStateProperty.resolveWith((estados) => TextStyle(
          fontSize: 12,
          fontWeight:
              estados.contains(WidgetState.selected) ? FontWeight.w600 : FontWeight.w500,
          color: estados.contains(WidgetState.selected)
              ? esquema.onSurface
              : esquema.onSurfaceVariant)),
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
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
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
