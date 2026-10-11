import 'package:flutter/material.dart';

import '../models/modelos.dart';
import '../state/servicios.dart';
import '../theme/app_theme.dart';
import '../widgets/comunes.dart';
import 'tarea_detalle_screen.dart';

/// Inicio: resumen simple de las tareas del usuario (solo datos de RF-04 a RF-09, sin gamificación).
class InicioScreen extends StatefulWidget {
  const InicioScreen({super.key});

  @override
  State<InicioScreen> createState() => _InicioScreenState();
}

class _InicioScreenState extends State<InicioScreen> {
  late Future<List<Tarea>> _futuro;

  @override
  void initState() {
    super.initState();
    _futuro = tareasRepo.listar();
  }

  void _recargar() => setState(() => _futuro = tareasRepo.listar());

  /// Para el gesto de "tirar para actualizar": el indicador espera a que termine la consulta.
  Future<void> _actualizar() async {
    _recargar();
    try {
      await _futuro;
    } catch (_) {
      // El error se muestra en pantalla; aquí solo importa que termine la espera.
    }
  }

  @override
  Widget build(BuildContext context) {
    final nombre = authController.usuario?.nombreParaSaludo ?? '';
    final tema = Theme.of(context);
    final e = tema.colorScheme;
    return FutureBuilder<List<Tarea>>(
      future: _futuro,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snap.hasError) {
          return EstadoError(error: snap.error, onReintentar: _recargar);
        }
        final tareas = snap.data!;
        int cuenta(String estado) => tareas.where((t) => t.estado == estado).length;
        final vencidas = cuenta('VENCIDA');
        // La API ya las entrega ordenadas por fecha límite: las vencidas salen primero.
        final atencion = tareas.where((t) => !t.completada).take(5).toList();

        return RefreshIndicator(
          onRefresh: _actualizar,
          child: ContenidoCentrado(
            child: ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 24),
              children: [
                Text('Hola, $nombre', style: tema.textTheme.headlineMedium),
                const SizedBox(height: 6),
                Text(
                  vencidas > 0
                      ? 'Tienes $vencidas tarea${vencidas == 1 ? '' : 's'} '
                          'vencida${vencidas == 1 ? '' : 's'}.'
                      : 'No tienes tareas vencidas. ¡Sigue así!',
                  style: tema.textTheme.bodyMedium?.copyWith(color: e.onSurfaceVariant),
                ),
                const SizedBox(height: 24),
                Row(children: [
                  _Resumen('Vencidas', vencidas, 'VENCIDA'),
                  const SizedBox(width: 8),
                  _Resumen('Pendientes', cuenta('PENDIENTE'), 'PENDIENTE'),
                  const SizedBox(width: 8),
                  _Resumen('En progreso', cuenta('EN_PROGRESO'), 'EN_PROGRESO'),
                  const SizedBox(width: 8),
                  _Resumen('Listas', cuenta('COMPLETADA'), 'COMPLETADA'),
                ]),
                const SizedBox(height: 32),
                Text('Requieren tu atención', style: tema.textTheme.titleMedium),
                const SizedBox(height: 12),
                if (atencion.isEmpty)
                  const Superficie(
                    child: SizedBox(
                      width: double.infinity,
                      child: EstadoVacio(
                          icono: Icons.task_alt, mensaje: 'No hay tareas pendientes.'),
                    ),
                  )
                else
                  Superficie(
                    child: Column(children: [
                      for (var i = 0; i < atencion.length; i++) ...[
                        if (i > 0) const Divider(),
                        TareaTile(
                          tarea: atencion[i],
                          onTap: () async {
                            await Navigator.of(context).push(MaterialPageRoute(
                                builder: (_) => TareaDetalleScreen(idTarea: atencion[i].id)));
                            if (mounted) _recargar();
                          },
                        ),
                      ],
                    ]),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _Resumen extends StatelessWidget {
  const _Resumen(this.titulo, this.cantidad, this.estado);

  final String titulo;
  final int cantidad;
  final String estado;

  @override
  Widget build(BuildContext context) {
    final estilo = estiloEstado(context, estado);
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 4),
        decoration: BoxDecoration(color: estilo.fondo, borderRadius: BorderRadius.circular(14)),
        child: Column(children: [
          Text('$cantidad',
              style: Theme.of(context)
                  .textTheme
                  .headlineSmall
                  ?.copyWith(color: estilo.texto)),
          const SizedBox(height: 2),
          FittedBox(
            fit: BoxFit.scaleDown,
            child: Text(titulo,
                maxLines: 1,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: estilo.texto)),
          ),
        ]),
      ),
    );
  }
}
