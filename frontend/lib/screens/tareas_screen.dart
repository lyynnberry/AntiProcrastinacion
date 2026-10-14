import 'package:flutter/material.dart';

import '../l10n/textos.dart';
import '../models/modelos.dart';
import '../state/servicios.dart';
import '../widgets/comunes.dart';
import 'tarea_detalle_screen.dart';
import 'tarea_form_screen.dart';

const _estadosFiltro = ['PENDIENTE', 'EN_PROGRESO', 'COMPLETADA', 'VENCIDA'];

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
    return ContenidoCentrado(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
            child: Row(children: [
              Expanded(child: Text(context.t.tareas, style: tema.textTheme.headlineMedium)),
              BotonCircular(
                icono: Icons.add,
                tooltip: context.t.nuevaTarea,
                onPressed: () => _abrir(const TareaFormScreen()),
              ),
            ]),
          ),
          const SizedBox(height: 20),
          // Estado: píldoras en una fila que se desplaza.
          SizedBox(
            height: 44,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 20),
              children: [
                for (final e in <String?>[null, ..._estadosFiltro])
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: PildoraFiltro(
                      etiqueta: e == null ? context.t.todas : context.t.estado(e),
                      activo: _estado == e,
                      onTap: () {
                        _estado = e;
                        _recargar();
                      },
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 4),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Wrap(spacing: 8, runSpacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
              SelectorPildora<String?>(
                etiqueta: context.t.prioridadEtiqueta,
                valor: _prioridad,
                opciones: [
                  Opcion<String?>(null, context.t.todas),
                  for (final p in codigosPrioridad) Opcion<String?>(p, context.t.prioridad(p)),
                ],
                onChanged: (v) {
                  _prioridad = v;
                  _recargar();
                },
              ),
              SelectorPildora<String?>(
                etiqueta: context.t.materia,
                valor: _idMateria,
                opciones: [
                  Opcion<String?>(null, context.t.todas),
                  for (final m in _materias) Opcion<String?>(m.id, m.nombre),
                ],
                onChanged: (v) {
                  _idMateria = v;
                  _recargar();
                },
              ),
              if (_hayFiltros)
                TextButton(
                  onPressed: () {
                    _estado = null;
                    _prioridad = null;
                    _idMateria = null;
                    _recargar();
                  },
                  child: Text(context.t.limpiar),
                ),
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
                                  ? context.t.ningunaCumpleFiltros
                                  : context.t.aunNoTienesTareas,
                            ),
                          ],
                        )
                      : ListView.separated(
                          physics: const AlwaysScrollableScrollPhysics(),
                          padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
                          itemCount: tareas.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 12),
                          itemBuilder: (_, i) => TareaTile(
                            tarea: tareas[i],
                            onTap: () => _abrir(TareaDetalleScreen(idTarea: tareas[i].id)),
                          ),
                        ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
