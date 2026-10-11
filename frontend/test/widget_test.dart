import 'package:antiprocrastinacion/models/modelos.dart';
import 'package:antiprocrastinacion/theme/app_theme.dart';
import 'package:antiprocrastinacion/widgets/comunes.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Tarea _tarea({String estado = 'PENDIENTE', String titulo = 'Entregar proyecto'}) => Tarea(
      id: '1',
      titulo: titulo,
      prioridad: 'ALTA',
      estado: estado,
      fechaLimite: DateTime(2030, 5, 3, 9, 30),
    );

Widget _envolver(Widget hijo, {Brightness brillo = Brightness.light}) => MaterialApp(
      theme: construirTema(brillo),
      home: Scaffold(body: hijo),
    );

void main() {
  group('formatos y validaciones', () {
    test('formatoFechaHora usa dos dígitos', () {
      expect(formatoFechaHora(DateTime(2030, 5, 3, 9, 5)), '03/05/2030 09:05');
    });

    test('esCorreoValido', () {
      expect(esCorreoValido('ana@correo.com'), isTrue);
      expect(esCorreoValido(' ana@correo.com '), isTrue);
      expect(esCorreoValido('ana@correo'), isFalse);
      expect(esCorreoValido('ana correo@x.com'), isFalse);
    });

    test('etiquetaEstado traduce los estados de la API', () {
      expect(etiquetaEstado('EN_PROGRESO'), 'En progreso');
      expect(etiquetaEstado('VENCIDA'), 'Vencida');
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

    testWidgets('EtiquetaEstado funciona en tema claro y oscuro', (tester) async {
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
      }
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
