import 'package:antiprocrastinacion/api/api_client.dart';
import 'package:antiprocrastinacion/l10n/textos.dart';
import 'package:antiprocrastinacion/models/modelos.dart';
import 'package:antiprocrastinacion/screens/personalizacion_screen.dart';
import 'package:antiprocrastinacion/screens/tutorial_screen.dart';
import 'package:antiprocrastinacion/theme/app_theme.dart';
import 'package:antiprocrastinacion/widgets/comunes.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Tarea _tarea({String estado = 'PENDIENTE', String titulo = 'Entregar proyecto'}) => Tarea(
      id: '1',
      titulo: titulo,
      prioridad: 'ALTA',
      estado: estado,
      fechaLimite: DateTime(2030, 5, 3, 9, 30),
    );

Widget _envolver(Widget hijo, {Brightness brillo = Brightness.light, String idioma = 'es'}) =>
    MaterialApp(
      theme: construirTema(brillo),
      locale: Locale(idioma),
      supportedLocales: const [Locale('es'), Locale('en')],
      localizationsDelegates: const [
        TextosDelegate(),
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      home: Scaffold(body: hijo),
    );

void main() {
  group('formatos y validaciones', () {
    test('fechaHora usa dos dígitos y el orden de cada idioma', () {
      expect(const Textos('es').fechaHora(DateTime(2030, 5, 3, 9, 5)), '03/05/2030 09:05');
      expect(const Textos('en').fechaHora(DateTime(2030, 5, 3, 9, 5)), '05/03/2030 09:05');
    });

    test('esCorreoValido', () {
      expect(esCorreoValido('ana@correo.com'), isTrue);
      expect(esCorreoValido(' ana@correo.com '), isTrue);
      expect(esCorreoValido('ana@correo'), isFalse);
      expect(esCorreoValido('ana correo@x.com'), isFalse);
    });

    test('los estados y prioridades de la API se traducen', () {
      expect(const Textos('es').estado('EN_PROGRESO'), 'En progreso');
      expect(const Textos('en').estado('EN_PROGRESO'), 'In progress');
      expect(const Textos('en').estado('VENCIDA'), 'Overdue');
      expect(const Textos('en').prioridad('ALTA'), 'High');
    });
  });

  group('idiomas', () {
    test('todos los textos existen en ambos idiomas y no quedan vacíos', () {
      const es = Textos('es');
      const en = Textos('en');
      final pares = <String, List<String>>{
        'tut1': [es.tut1Titulo, en.tut1Titulo],
        'tut4': [es.tut4Texto, en.tut4Texto],
        'personaliza': [es.personalizaIntro, en.personalizaIntro],
        'perfil': [es.perfil, en.perfil],
        'cerrarSesion': [es.cerrarSesion, en.cerrarSesion],
      };
      pares.forEach((clave, v) {
        expect(v[0], isNotEmpty, reason: clave);
        expect(v[1], isNotEmpty, reason: clave);
        expect(v[0], isNot(v[1]), reason: '$clave debería estar traducido');
      });
    });

    test('el texto de introducción de la personalización es el definido', () {
      expect(const Textos('es').personalizaIntro,
          'Queremos ayudarte a mantenerte al día. Configura cómo quieres recibir tus recordatorios.');
    });

    test('los errores del servidor se traducen por código', () {
      expect(const Textos('en').errorPorCodigo('EMAIL_DUPLICADO'), contains('already exists'));
      expect(const Textos('es').errorPorCodigo('FOTO_FORMATO_INVALIDO'), contains('JPG'));
      expect(const Textos('es').errorPorCodigo('CODIGO_RARO'), isNull);
    });

    test('el idioma no soportado cae al español', () async {
      final t = await const TextosDelegate().load(const Locale('fr'));
      expect(t.codigo, 'es');
    });
  });

  group('modelos', () {
    test('Tarea.fromJson convierte la fecha a hora local', () {
      final t = Tarea.fromJson({
        'id_tarea': 'abc',
        'titulo': 'Estudiar',
        'descripcion': null,
        'prioridad': 'MEDIA',
        'estado': 'VENCIDA',
        'id_materia': null,
        'fecha_limite': '2030-01-01T12:00:00Z',
        'fecha_completada': null,
      });
      expect(t.vencida, isTrue);
      expect(t.fechaLimite.isUtc, isFalse);
      expect(t.fechaLimite.toUtc(), DateTime.utc(2030, 1, 1, 12));
    });

    test('Usuario: saludo e iniciales', () {
      final conNombre = Usuario(id: '1', email: 'ana@x.com', nombre: 'Ana López', zonaHoraria: 'UTC');
      final sinNombre = Usuario(id: '2', email: 'juan.perez@x.com', zonaHoraria: 'UTC');
      expect(conNombre.nombreParaSaludo, 'Ana López');
      expect(conNombre.iniciales, 'AL');
      expect(sinNombre.nombreParaSaludo, 'juan.perez');
      expect(sinNombre.iniciales, 'JP');
    });

    test('Usuario.fromJson lee idioma, flujo de primer uso y foto', () {
      final u = Usuario.fromJson({
        'id_usuario': '1',
        'email': 'a@b.com',
        'nombre': null,
        'zona_horaria': 'UTC',
        'idioma': 'en',
        'personalizacion_completada': true,
        'tutorial_completado': false,
        'foto_actualizada_en': '2030-01-01T12:00:00Z',
      });
      expect(u.idioma, 'en');
      expect(u.personalizacionCompletada, isTrue);
      expect(u.tutorialCompletado, isFalse);
      expect(u.tieneFoto, isTrue);
    });

    test('Usuario.fromJson tolera respuestas sin los campos nuevos', () {
      final u = Usuario.fromJson(
          {'id_usuario': '1', 'email': 'a@b.com', 'nombre': null, 'zona_horaria': 'UTC'});
      expect(u.idioma, 'es');
      expect(u.personalizacionCompletada, isFalse);
      expect(u.tieneFoto, isFalse);
    });
  });

  group('widgets', () {
    testWidgets('TareaTile muestra título, estado y responde al toque', (tester) async {
      var toques = 0;
      await tester.pumpWidget(_envolver(TareaTile(tarea: _tarea(), onTap: () => toques++)));

      expect(find.text('Entregar proyecto'), findsOneWidget);
      expect(find.text('Pendiente'), findsOneWidget);
      expect(find.textContaining('Prioridad alta'), findsOneWidget);

      await tester.tap(find.byType(TareaTile));
      expect(toques, 1);
    });

    testWidgets('Etiquetas y anillo de progreso funcionan en tema claro y oscuro', (tester) async {
      for (final brillo in Brightness.values) {
        await tester.pumpWidget(_envolver(
          Column(children: [
            for (final e in const ['PENDIENTE', 'EN_PROGRESO', 'COMPLETADA', 'VENCIDA'])
              EtiquetaEstado(e),
          ]),
          brillo: brillo,
        ));
        expect(find.text('Vencida'), findsOneWidget);
        expect(tester.takeException(), isNull);

        await tester.pumpWidget(_envolver(
          Column(children: [
            for (final p in codigosPrioridad) EtiquetaPrioridad(p),
            const AnilloProgreso(
              valor: 0.72,
              colorPista: Colors.grey,
              colorBarra: Colors.green,
              child: Text('72%'),
            ),
          ]),
          brillo: brillo,
        ));
        expect(find.text('Prioridad media'), findsOneWidget);
        expect(find.text('72%'), findsOneWidget);
        expect(tester.takeException(), isNull);
      }
    });

    testWidgets('las etiquetas cambian de idioma', (tester) async {
      await tester.pumpWidget(_envolver(const EtiquetaPrioridad('ALTA'), idioma: 'en'));
      expect(find.text('High priority'), findsOneWidget);
    });

    testWidgets('mensajeDeError traduce según el idioma', (tester) async {
      late BuildContext ctx;
      await tester.pumpWidget(_envolver(Builder(builder: (c) {
        ctx = c;
        return const SizedBox();
      }), idioma: 'en'));
      expect(mensajeDeError(ctx, ApiException(409, 'EMAIL_DUPLICADO', 'Ya existe una cuenta con ese correo.')),
          'An account with that email already exists.');
      expect(mensajeDeError(ctx, Exception('x')), contains('Something went wrong'));
    });

    testWidgets('Personalización: no deja continuar sin elegir una opción', (tester) async {
      // Pantalla de teléfono (360×800); la de prueba por defecto (800×600) deja opciones fuera de la lista.
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 3;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(_envolver(const PersonalizacionScreen()));
      expect(find.text('Personaliza tu experiencia'), findsOneWidget);
      expect(find.text('Tranquilo'), findsOneWidget);
      expect(find.text('Equilibrado'), findsOneWidget);
      await tester.scrollUntilVisible(find.text('Insistente'), 100);
      expect(find.text('Insistente'), findsOneWidget);

      await tester.tap(find.text('Continuar'));
      await tester.pump();
      await tester.scrollUntilVisible(find.text('Elige una opción para continuar.'), 100);
      expect(find.text('Elige una opción para continuar.'), findsOneWidget);

      await tester.tap(find.text('Insistente'));
      await tester.pump();
      expect(find.text('Elige una opción para continuar.'), findsNothing);
    });

    testWidgets('Tutorial: 4 pasos con progreso, Omitir y Comenzar al final', (tester) async {
      await tester.pumpWidget(_envolver(const TutorialScreen()));
      expect(find.text('1/4'), findsOneWidget);
      expect(find.text('Organiza tus tareas'), findsOneWidget);
      expect(find.text('Omitir'), findsOneWidget);

      for (final titulo in [
        'No dejes pasar tus pendientes',
        'Mantén tu racha',
        'Recupera el control',
      ]) {
        await tester.tap(find.text('Siguiente'));
        await tester.pumpAndSettle();
        expect(find.text(titulo), findsOneWidget);
      }
      expect(find.text('4/4'), findsOneWidget);
      expect(find.text('Comenzar'), findsOneWidget);
      expect(find.text('Siguiente'), findsNothing);
    });

    testWidgets('CampoSelector abre las opciones y devuelve la elegida', (tester) async {
      String? elegido;
      await tester.pumpWidget(_envolver(
        CampoSelector<String?>(
          etiqueta: 'Estado',
          valor: null,
          opciones: const [
            Opcion<String?>(null, 'Todos'),
            Opcion<String?>('PENDIENTE', 'Pendiente'),
          ],
          onChanged: (v) => elegido = v,
        ),
      ));

      expect(find.text('Todos'), findsOneWidget);
      await tester.tap(find.byType(CampoSelector<String?>));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Pendiente'));
      await tester.pumpAndSettle();

      expect(elegido, 'PENDIENTE');
    });
  });

  test('el tema claro es el predeterminado de la paleta', () {
    expect(construirTema(Brightness.light).colorScheme.primary, Paleta.verde);
    expect(construirTema(Brightness.light).colorScheme.surface, Paleta.fondoClaro);
    expect(construirTema(Brightness.dark).colorScheme.surface, Paleta.oscFondo);
  });
}
