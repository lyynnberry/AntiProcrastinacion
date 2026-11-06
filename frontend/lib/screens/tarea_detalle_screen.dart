import 'package:flutter/material.dart';

import '../l10n/textos.dart';
import '../models/modelos.dart';
import '../state/servicios.dart';
import '../widgets/comunes.dart';
import 'tarea_form_screen.dart';

/// Detalle de una tarea (RF-07) con acciones de editar (RF-05) y eliminar (RF-06),
/// y la lista de sus próximos recordatorios (RF-12 / RF-13).
class TareaDetalleScreen extends StatefulWidget {
  const TareaDetalleScreen({super.key, required this.idTarea});

  final String idTarea;

  @override
  State<TareaDetalleScreen> createState() => _TareaDetalleScreenState();
}

class _TareaDetalleScreenState extends State<TareaDetalleScreen> {
  late Future<_Datos> _futuro;
  bool _trabajando = false;

  @override
  void initState() {
    super.initState();
    _futuro = _cargar();
  }

  Future<_Datos> _cargar() async {
    final tarea = await tareasRepo.obtener(widget.idTarea);
    String? nombreMateria;
    if (tarea.idMateria != null) {
      // Si falla la consulta de materias, la tarea se muestra igual (sin el nombre).
      try {
        final materias = await materiasRepo.listar();
        for (final m in materias) {
          if (m.id == tarea.idMateria) nombreMateria = m.nombre;
        }
      } catch (_) {
        // Se omite el nombre de la materia; el resto de la tarea sigue siendo válido.
      }
    }
    // Los recordatorios son informativos: si fallan, la tarea se muestra igual.
    List<Recordatorio>? recordatorios;
    try {
      final todos = await notificacionesRepo.sincronizar();
      recordatorios = todos.where((r) => r.idTarea == tarea.id).toList();
    } catch (_) {
      recordatorios = null;
    }
    return _Datos(tarea, nombreMateria, recordatorios);
  }

  void _recargar() => setState(() => _futuro = _cargar());

  Future<void> _completar(Tarea tarea) async {
    if (_trabajando) return;
    setState(() => _trabajando = true);
    try {
      await tareasRepo.actualizar(tarea.id, {'estado': 'COMPLETADA'});
      if (mounted) _recargar();
    } catch (e) {
      if (mounted) mostrarError(context, e);
    } finally {
      if (mounted) setState(() => _trabajando = false);
    }
  }

  /// RF-06 regla 2: se pide confirmación ANTES de eliminar.
  Future<void> _eliminar(Tarea tarea) async {
    final confirmado = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(ctx.t.eliminarTareaTitulo),
        content: Text(ctx.t.eliminarTareaTexto(tarea.titulo)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(ctx.t.cancelar)),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(ctx).colorScheme.error,
              foregroundColor: Theme.of(ctx).colorScheme.onError,
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(ctx.t.eliminar),
          ),
        ],
      ),
    );
    if (confirmado != true || !mounted) return;
    try {
      await tareasRepo.eliminar(tarea.id);
      if (mounted) Navigator.of(context).pop();
    } catch (e) {
      if (mounted) mostrarError(context, e);
    }
  }

  Future<void> _editar(Tarea tarea) async {
    await Navigator.of(context)
        .push(MaterialPageRoute(builder: (_) => TareaFormScreen(tarea: tarea)));
    if (mounted) _recargar();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_Datos>(
      future: _futuro,
      builder: (context, snap) {
        final datos = snap.data;
        return Pantalla(
          appBar: barraSimple(
            context,
            context.t.detalleDeLaTarea,
            acciones: datos == null
                ? null
                : [
                    IconButton(
                        tooltip: context.t.editar,
                        onPressed: () => _editar(datos.tarea),
                        icon: const Icon(Icons.edit_outlined)),
                    IconButton(
                        tooltip: context.t.eliminar,
                        onPressed: () => _eliminar(datos.tarea),
                        icon: const Icon(Icons.delete_outline)),
                  ],
          ),
          body: Builder(builder: (context) {
            if (snap.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            if (datos == null) {
              return EstadoError(error: snap.error, onReintentar: _recargar);
            }
            final t = datos.tarea;
            final tema = Theme.of(context);
            return ContenidoCentrado(
              child: ListView(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
                children: [
                  Text(t.titulo, style: tema.textTheme.headlineMedium),
                  const SizedBox(height: 14),
                  Wrap(spacing: 8, runSpacing: 8, children: [
                    EtiquetaEstado(t.estado),
                    EtiquetaPrioridad(t.prioridad),
                  ]),
                  const SizedBox(height: 24),
                  Superficie(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Column(children: [
                      _Fila(context.t.descripcion,
                          (t.descripcion?.isNotEmpty ?? false) ? t.descripcion! : '—'),
                      const Divider(),
                      _Fila(context.t.fechaLimite, context.t.fechaHora(t.fechaLimite)),
                      if (t.fechaProgramada != null) ...[
                        const Divider(),
                        _Fila(context.t.fechaProgramada, context.t.fecha(t.fechaProgramada!)),
                      ],
                      const Divider(),
                      _Fila(context.t.materia, datos.nombreMateria ?? context.t.sinMateria),
                      if (t.fechaCompletada != null) ...[
                        const Divider(),
                        _Fila(context.t.completadaEl, context.t.fechaHora(t.fechaCompletada!)),
                      ],
                    ]),
                  ),
                  const SizedBox(height: 24),
                  if (!t.completada)
                    FilledButton.icon(
                      onPressed: _trabajando ? null : () => _completar(t),
                      icon: const Icon(Icons.check),
                      label: Text(context.t.marcarCompletada),
                    ),
                  const SizedBox(height: 24),
                  _SeccionRecordatorios(recordatorios: datos.recordatorios),
                ],
              ),
            );
          }),
        );
      },
    );
  }
}

class _Datos {
  _Datos(this.tarea, this.nombreMateria, this.recordatorios);

  final Tarea tarea;
  final String? nombreMateria;

  /// null = no se pudieron cargar.
  final List<Recordatorio>? recordatorios;
}

/// Próximos avisos de la tarea, tal como los planificó el backend (RF-12 / RF-13).
class _SeccionRecordatorios extends StatelessWidget {
  const _SeccionRecordatorios({required this.recordatorios});

  final List<Recordatorio>? recordatorios;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final lista = recordatorios;
    final Widget contenido;
    if (lista == null) {
      contenido = Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Text(context.t.recordatoriosNoDisponibles, style: tema.textTheme.bodyMedium),
      );
    } else if (lista.isEmpty) {
      contenido = Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Text(context.t.sinRecordatorios, style: tema.textTheme.bodyMedium),
      );
    } else {
      contenido = Column(children: [
        for (var i = 0; i < lista.length; i++) ...[
          if (i > 0) const Divider(),
          _Fila(
            context.t.tipoRecordatorio(lista[i].tipo, esFinal: lista[i].esAvisoFinal),
            context.t.fechaHora(lista[i].fechaProgramada),
          ),
        ],
      ]);
    }
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(context.t.proximosRecordatorios, style: tema.textTheme.titleSmall),
      const SizedBox(height: 4),
      Text(context.t.recordatoriosAviso,
          style: tema.textTheme.bodySmall?.copyWith(color: tema.colorScheme.onSurfaceVariant)),
      const SizedBox(height: 8),
      Superficie(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: contenido,
      ),
    ]);
  }
}

class _Fila extends StatelessWidget {
  const _Fila(this.titulo, this.valor);

  final String titulo;
  final String valor;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: SizedBox(
        width: double.infinity,
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(titulo,
              style: tema.textTheme.labelMedium
                  ?.copyWith(color: tema.colorScheme.onSurfaceVariant)),
          const SizedBox(height: 4),
          Text(valor, style: tema.textTheme.bodyLarge),
        ]),
      ),
    );
  }
}
