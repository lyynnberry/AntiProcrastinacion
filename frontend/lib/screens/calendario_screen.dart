import 'package:flutter/material.dart';

import '../models/modelos.dart';
import '../state/servicios.dart';
import '../widgets/comunes.dart';
import 'tarea_detalle_screen.dart';

const _meses = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];
const _diasSemana = ['L', 'M', 'M', 'J', 'V', 'S', 'D'];

DateTime _soloDia(DateTime d) => DateTime(d.year, d.month, d.day);

/// Calendario básico: muestra por mes qué días tienen tareas con fecha límite.
/// Usa el filtro por rango de fechas de RF-07 (no es un requerimiento aparte).
class CalendarioScreen extends StatefulWidget {
  const CalendarioScreen({super.key});

  @override
  State<CalendarioScreen> createState() => _CalendarioScreenState();
}

class _CalendarioScreenState extends State<CalendarioScreen> {
  late DateTime _mes; // siempre el día 1 del mes mostrado
  late DateTime _seleccionado;
  late Future<List<Tarea>> _futuro;

  @override
  void initState() {
    super.initState();
    final hoy = DateTime.now();
    _mes = DateTime(hoy.year, hoy.month);
    _seleccionado = _soloDia(hoy);
    _futuro = _consultar();
  }

  Future<List<Tarea>> _consultar() => tareasRepo.listar(
        desde: DateTime(_mes.year, _mes.month, 1),
        hasta: DateTime(_mes.year, _mes.month + 1, 0), // último día del mes
      );

  void _recargar() => setState(() => _futuro = _consultar());

  void _cambiarMes(int delta) {
    final hoy = DateTime.now();
    setState(() {
      _mes = DateTime(_mes.year, _mes.month + delta);
      // El día elegido debe pertenecer al mes mostrado: hoy si es ese mes, o el día 1.
      _seleccionado = (_mes.year == hoy.year && _mes.month == hoy.month)
          ? _soloDia(hoy)
          : DateTime(_mes.year, _mes.month, 1);
      _futuro = _consultar();
    });
  }

  Future<void> _abrirTarea(String id) async {
    await Navigator.of(context)
        .push(MaterialPageRoute(builder: (_) => TareaDetalleScreen(idTarea: id)));
    if (mounted) _recargar();
  }

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final e = tema.colorScheme;
    return ContenidoCentrado(
      child: FutureBuilder<List<Tarea>>(
        future: _futuro,
        builder: (context, snap) {
          final cargando = snap.connectionState != ConnectionState.done;
          final porDia = <DateTime, List<Tarea>>{};
          for (final t in snap.data ?? const <Tarea>[]) {
            porDia.putIfAbsent(_soloDia(t.fechaLimite), () => []).add(t);
          }
          final delDia = porDia[_seleccionado] ?? const <Tarea>[];

          Widget lista;
          if (cargando) {
            lista = const Padding(
              padding: EdgeInsets.symmetric(vertical: 32),
              child: Center(child: CircularProgressIndicator()),
            );
          } else if (snap.hasError) {
            lista = EstadoError(error: snap.error, onReintentar: _recargar);
          } else if (delDia.isEmpty) {
            lista = const EstadoVacio(
                icono: Icons.event_available_outlined,
                mensaje: 'No hay tareas con fecha límite este día.');
          } else {
            lista = Superficie(
              child: Column(children: [
                for (var i = 0; i < delDia.length; i++) ...[
                  if (i > 0) const Divider(),
                  TareaTile(tarea: delDia[i], onTap: () => _abrirTarea(delDia[i].id)),
                ],
              ]),
            );
          }

          return ListView(
            padding: const EdgeInsets.fromLTRB(20, 24, 20, 24),
            children: [
              Text('Calendario', style: tema.textTheme.headlineMedium),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  IconButton(
                    tooltip: 'Mes anterior',
                    onPressed: () => _cambiarMes(-1),
                    icon: const Icon(Icons.chevron_left),
                  ),
                  Text('${_meses[_mes.month - 1]} ${_mes.year}',
                      style: tema.textTheme.titleMedium),
                  IconButton(
                    tooltip: 'Mes siguiente',
                    onPressed: () => _cambiarMes(1),
                    icon: const Icon(Icons.chevron_right),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(children: [
                for (final d in _diasSemana)
                  Expanded(
                    child: Center(
                      child: Text(d,
                          style: tema.textTheme.labelMedium
                              ?.copyWith(color: e.onSurfaceVariant)),
                    ),
                  ),
              ]),
              const SizedBox(height: 4),
              _Cuadricula(
                mes: _mes,
                seleccionado: _seleccionado,
                porDia: porDia,
                onSeleccionar: (d) => setState(() => _seleccionado = d),
              ),
              const SizedBox(height: 20),
              Text('Tareas del ${formatoFecha(_seleccionado)}', style: tema.textTheme.titleSmall),
              const SizedBox(height: 12),
              lista,
            ],
          );
        },
      ),
    );
  }
}

class _Cuadricula extends StatelessWidget {
  const _Cuadricula({
    required this.mes,
    required this.seleccionado,
    required this.porDia,
    required this.onSeleccionar,
  });

  final DateTime mes;
  final DateTime seleccionado;
  final Map<DateTime, List<Tarea>> porDia;
  final ValueChanged<DateTime> onSeleccionar;

  @override
  Widget build(BuildContext context) {
    final diasEnMes = DateTime(mes.year, mes.month + 1, 0).day;
    final huecosIniciales = mes.weekday - 1; // la semana empieza en lunes
    final hoy = _soloDia(DateTime.now());
    final esquema = Theme.of(context).colorScheme;

    final celdas = <Widget>[
      for (var i = 0; i < huecosIniciales; i++) const SizedBox.shrink(),
      for (var dia = 1; dia <= diasEnMes; dia++)
        Builder(builder: (context) {
          final fecha = DateTime(mes.year, mes.month, dia);
          final tareas = porDia[fecha] ?? const <Tarea>[];
          final esSeleccionado = fecha == seleccionado;
          final esHoy = fecha == hoy;
          final hayVencida = tareas.any((t) => t.vencida);
          return Semantics(
            button: true,
            selected: esSeleccionado,
            onTap: () => onSeleccionar(fecha),
            label: '$dia de ${_meses[mes.month - 1]}'
                '${tareas.isEmpty ? '' : ', ${tareas.length} tarea${tareas.length == 1 ? '' : 's'}'}',
            child: ExcludeSemantics(
              child: InkWell(
                borderRadius: BorderRadius.circular(12),
                onTap: () => onSeleccionar(fecha),
                child: Container(
                  margin: const EdgeInsets.all(2),
                  decoration: BoxDecoration(
                    color: esSeleccionado ? esquema.primaryContainer : null,
                    border: esHoy ? Border.all(color: esquema.secondary, width: 1.5) : null,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text('$dia',
                          style: TextStyle(
                            color: esSeleccionado
                                ? esquema.onPrimaryContainer
                                : esquema.onSurface,
                            fontWeight:
                                esSeleccionado || esHoy ? FontWeight.w700 : FontWeight.w400,
                          )),
                      // El espacio del punto se reserva siempre para que los números no "salten".
                      Container(
                        width: 5,
                        height: 5,
                        margin: const EdgeInsets.only(top: 3),
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: tareas.isEmpty
                              ? Colors.transparent
                              : (hayVencida ? esquema.error : esquema.secondary),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          );
        }),
    ];

    return GridView.count(
      crossAxisCount: 7,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      children: celdas,
    );
  }
}
