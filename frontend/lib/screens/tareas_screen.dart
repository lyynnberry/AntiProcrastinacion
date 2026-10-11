import 'package:flutter/material.dart';

import '../models/modelos.dart';
import '../state/servicios.dart';
import '../widgets/comunes.dart';
import 'tarea_detalle_screen.dart';
import 'tarea_form_screen.dart';

const _estadosFiltro = {
  'PENDIENTE': 'Pendiente',
  'EN_PROGRESO': 'En progreso',
  'COMPLETADA': 'Completada',
  'VENCIDA': 'Vencida',
};

/// RF-07: lista de tareas con filtros por estado, prioridad y materia (combinables).
class TareasScreen extends StatefulWidget {
  const TareasScreen({super.key});

  @override
  State<TareasScreen> createState() => _TareasScreenState();
}

class _TareasScreenState extends State<TareasScreen> {
  String? _estado;
  String? _prioridad;
  String? _idMateria;
  List<Materia> _materias = [];
  late Future<List<Tarea>> _futuro;

  bool get _hayFiltros => _estado != null || _prioridad != null || _idMateria != null;

  @override
  void initState() {
    super.initState();
    _futuro = _consultar();
    _cargarMaterias();
  }

  Future<List<Tarea>> _consultar() =>
      tareasRepo.listar(estado: _estado, prioridad: _prioridad, idMateria: _idMateria);

  void _recargar() => setState(() => _futuro = _consultar());

  /// Para el gesto de "tirar para actualizar": el indicador espera a que termine la consulta.
  Future<void> _actualizar() async {
    _recargar();
    try {
      await _futuro;
    } catch (_) {
      // El error se muestra en pantalla; aquí solo importa que termine la espera.
    }
  }

  Future<void> _cargarMaterias() async {
    try {
      final materias = await materiasRepo.listar();
      if (mounted) setState(() => _materias = materias);
    } catch (_) {
      // Si falla, el filtro por materia queda vacío; la lista de tareas sigue funcionando.
    }
  }

  Future<void> _abrir(Widget pantalla) async {
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => pantalla));
    if (!mounted) return;
    _recargar();
    _cargarMaterias();
  }

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Scaffold(
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _abrir(const TareaFormScreen()),
        icon: const Icon(Icons.add),
        label: const Text('Nueva tarea'),
      ),
      body: ContenidoCentrado(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 0),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Tareas', style: tema.textTheme.headlineMedium),
                const SizedBox(height: 16),
                Row(children: [
                  Expanded(
                    child: CampoSelector<String?>(
                      etiqueta: 'Estado',
                      valor: _estado,
                      opciones: [
                        const Opcion<String?>(null, 'Todos'),
                        for (final e in _estadosFiltro.entries) Opcion<String?>(e.key, e.value),
                      ],
                      onChanged: (v) {
                        _estado = v;
                        _recargar();
                      },
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: CampoSelector<String?>(
                      etiqueta: 'Prioridad',
                      valor: _prioridad,
                      opciones: [
                        const Opcion<String?>(null, 'Todas'),
                        for (final e in prioridades.entries) Opcion<String?>(e.key, e.value),
                      ],
                      onChanged: (v) {
                        _prioridad = v;
                        _recargar();
                      },
                    ),
                  ),
                ]),
                const SizedBox(height: 8),
                Row(children: [
                  Expanded(
                    child: CampoSelector<String?>(
                      etiqueta: 'Materia',
                      valor: _idMateria,
                      opciones: [
                        const Opcion<String?>(null, 'Todas'),
                        for (final m in _materias) Opcion<String?>(m.id, m.nombre),
                      ],
                      onChanged: (v) {
                        _idMateria = v;
                        _recargar();
                      },
                    ),
                  ),
                  if (_hayFiltros) ...[
                    const SizedBox(width: 8),
                    TextButton(
                      onPressed: () {
                        _estado = null;
                        _prioridad = null;
                        _idMateria = null;
                        _recargar();
                      },
                      child: const Text('Limpiar'),
                    ),
                  ],
                ]),
              ]),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: FutureBuilder<List<Tarea>>(
                future: _futuro,
                builder: (context, snap) {
                  if (snap.connectionState != ConnectionState.done) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  if (snap.hasError) {
                    return EstadoError(error: snap.error, onReintentar: _recargar);
                  }
                  final tareas = snap.data!;
                  return RefreshIndicator(
                    onRefresh: _actualizar,
                    child: tareas.isEmpty
                        ? ListView(
                            physics: const AlwaysScrollableScrollPhysics(),
                            children: [
                              const SizedBox(height: 48),
                              EstadoVacio(
                                icono: Icons.inbox_outlined,
                                mensaje: _hayFiltros
                                    ? 'Ninguna tarea cumple los filtros.'
                                    : 'Aún no tienes tareas. ¡Crea la primera!',
                              ),
                            ],
                          )
                        : ListView(
                            physics: const AlwaysScrollableScrollPhysics(),
                            // Espacio al final para que el botón flotante no tape la última tarea.
                            padding: const EdgeInsets.fromLTRB(20, 0, 20, 96),
                            children: [
                              Superficie(
                                child: Column(children: [
                                  for (var i = 0; i < tareas.length; i++) ...[
                                    if (i > 0) const Divider(),
                                    TareaTile(
                                      tarea: tareas[i],
                                      onTap: () => _abrir(TareaDetalleScreen(idTarea: tareas[i].id)),
                                    ),
                                  ],
                                ]),
                              ),
                            ],
                          ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
