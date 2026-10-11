import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'screens/home_shell.dart';
import 'screens/login_screen.dart';
import 'state/auth_controller.dart';
import 'state/servicios.dart';
import 'theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Se lee el tema guardado antes de dibujar la primera pantalla, para que no "parpadee".
  await temaController.cargar();
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
      listenable: temaController,
      builder: (context, _) => MaterialApp(
        navigatorKey: _navegador,
        title: 'AntiProcrastinación',
        debugShowCheckedModeBanner: false,
        // Toda la app está en español: textos del sistema, selector de fecha y hora, etc.
        locale: const Locale('es', 'MX'),
        supportedLocales: const [Locale('es', 'MX'), Locale('es')],
        localizationsDelegates: const [
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
                return const Scaffold(body: Center(child: CircularProgressIndicator()));
              case EstadoSesion.sinSesion:
                return const LoginScreen();
              case EstadoSesion.conSesion:
                return const HomeShell();
            }
          },
        ),
      ),
    );
  }
}
