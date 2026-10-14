import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'screens/home_shell.dart';
import 'l10n/textos.dart';
import 'screens/login_screen.dart';
import 'screens/personalizacion_screen.dart';
import 'screens/tutorial_screen.dart';
import 'state/auth_controller.dart';
import 'state/servicios.dart';
import 'theme/app_theme.dart';
import 'widgets/comunes.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Se lee el tema guardado antes de dibujar la primera pantalla, para que no "parpadee".
  await temaController.cargar();
  await idiomaController.cargar(); // último idioma usado en este dispositivo
  runApp(const AntiProcrastinacionApp());
}

final _temaClaro = construirTema(Brightness.light);
final _temaOscuro = construirTema(Brightness.dark);

class AntiProcrastinacionApp extends StatefulWidget {
  const AntiProcrastinacionApp({super.key});

  @override
  State<AntiProcrastinacionApp> createState() => _AntiProcrastinacionAppState();
}

class _AntiProcrastinacionAppState extends State<AntiProcrastinacionApp> {
  final _navegador = GlobalKey<NavigatorState>();

  @override
  void initState() {
    super.initState();
    authController.addListener(_alCambiarSesion);
    authController.iniciar(); // restaura la sesión guardada, si existe (RF-03)
  }

  @override
  void dispose() {
    authController.removeListener(_alCambiarSesion);
    super.dispose();
  }

  /// Si la sesión se cierra (o expira) con pantallas abiertas encima, se cierran todas para que
  /// no queden tareas de la sesión anterior sobre el login.
  void _alCambiarSesion() {
    if (authController.estado == EstadoSesion.sinSesion) {
      _navegador.currentState?.popUntil((ruta) => ruta.isFirst);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: Listenable.merge([temaController, idiomaController]),
      builder: (context, _) => MaterialApp(
        navigatorKey: _navegador,
        title: 'AntiProcrastinación',
        debugShowCheckedModeBanner: false,
        // Idioma de toda la app (español o inglés): textos propios, selector de fecha y hora, etc.
        locale: idiomaController.locale,
        supportedLocales: [for (final c in idiomasSoportados) Locale(c)],
        localizationsDelegates: const [
          TextosDelegate(),
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        theme: _temaClaro,
        darkTheme: _temaOscuro,
        themeMode: temaController.modo, // claro por defecto
        // Según el estado de la sesión se muestra una pantalla u otra.
        home: ListenableBuilder(
          listenable: authController,
          builder: (context, _) {
            switch (authController.estado) {
              case EstadoSesion.iniciando:
                return const Pantalla(body: Center(child: CircularProgressIndicator()));
              case EstadoSesion.sinSesion:
                return const LoginScreen();
              case EstadoSesion.conSesion:
                // Primer uso: Personalización -> Tutorial -> Dashboard. Los avisos de "ya hecho" viven
                // en el servidor, así que si la app se cierra a medias se retoma en el paso pendiente.
                final u = authController.usuario;
                if (u != null && !u.personalizacionCompletada) return const PersonalizacionScreen();
                if (u != null && !u.tutorialCompletado) return const TutorialScreen();
                return const HomeShell();
            }
          },
        ),
      ),
    );
  }
}
