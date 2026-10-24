import 'package:flutter/material.dart';

import '../l10n/textos.dart';
import '../models/modelos.dart';
import '../state/servicios.dart';
import '../theme/app_theme.dart';
import '../widgets/avatar.dart';
import '../widgets/comunes.dart';
import 'tarea_detalle_screen.dart';
import 'tarea_form_screen.dart';

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

  Future<void> _abrir(Widget pantalla) async {
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => pantalla));
    if (mounted) _recargar();
  }

  String _saludo(Textos t) {
    final hora = DateTime.now().hour;
    if (hora < 12) return t.buenosDias;
    if (hora < 19) return t.buenasTardes;
    return t.buenasNoches;
  }

  @override
  Widget build(BuildContext context) {
    final usuario = authController.usuario;
    final tema = Theme.of(context);
    final e = tema.colorScheme;
    return FutureBuilder<List<Tarea>>(
      future: _futuro,
      builder: (context, snap) {
        Widget cuerpo;
        if (snap.connectionState != ConnectionState.done) {
          cuerpo = const Padding(
            padding: EdgeInsets.symmetric(vertical: 64),
            child: Center(child: CircularProgressIndicator()),
          );
        } else if (snap.hasError) {
          cuerpo = EstadoError(error: snap.error, onReintentar: _recargar);
        } else {
          cuerpo = _Contenido(
            tareas: snap.data!,
            onAbrir: (t) => _abrir(TareaDetalleScreen(idTarea: t.id)),
          );
        }

        return RefreshIndicator(
          onRefresh: _actualizar,
          child: ContenidoCentrado(
            child: ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
              children: [
                Row(children: [
                  if (usuario != null) AvatarUsuario(usuario: usuario, radio: 24),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(_saludo(context.t),
                          style: tema.textTheme.bodySmall?.copyWith(color: e.onSurfaceVariant)),
                      Text(usuario?.nombreParaSaludo ?? '',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: tema.textTheme.titleMedium),
                    ]),
                  ),
                  BotonCircular(
                    icono: Icons.add,
                    tooltip: context.t.nuevaTarea,
                    onPressed: () => _abrir(const TareaFormScreen()),
                  ),
                ]),
                const SizedBox(height: 28),
                Text(context.t.lemaLinea1,
                    style: tema.textTheme.headlineMedium
                        ?.copyWith(fontWeight: FontWeight.w300, height: 1.15)),
                Text(context.t.lemaLinea2,
                    style: tema.textTheme.headlineMedium?.copyWith(height: 1.15)),
                const SizedBox(height: 24),
                cuerpo,
              ],
            ),
          ),
        );
      },
    );
  }
}

class _Contenido extends StatelessWidget {
  const _Contenido({required this.tareas, required this.onAbrir});

  final List<Tarea> tareas;
  final ValueChanged<Tarea> onAbrir;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    int cuenta(String estado) => tareas.where((t) => t.estado == estado).length;
    final total = tareas.length;
    final completadas = cuenta('COMPLETADA');
    final vencidas = cuenta('VENCIDA');
    // La API ya las entrega ordenadas por fecha límite: las vencidas salen primero.
    final atencion = tareas.where((t) => !t.completada).take(5).toList();

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _TarjetaProgreso(total: total, completadas: completadas),
      const SizedBox(height: 24),
      Text(context.t.resumen, style: tema.textTheme.titleMedium),
      const SizedBox(height: 12),
      SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(children: [
          _Conteo(context.t.vencidas, vencidas, 'VENCIDA'),
          const SizedBox(width: 8),
          _Conteo(context.t.pendientes, cuenta('PENDIENTE'), 'PENDIENTE'),
          const SizedBox(width: 8),
          _Conteo(context.t.enProgreso, cuenta('EN_PROGRESO'), 'EN_PROGRESO'),
          const SizedBox(width: 8),
          _Conteo(context.t.listas, completadas, 'COMPLETADA'),
        ]),
      ),
      const SizedBox(height: 28),
      Text(context.t.requierenAtencion, style: tema.textTheme.titleMedium),
      const SizedBox(height: 12),
      if (atencion.isEmpty)
        Superficie(
          child: SizedBox(
            width: double.infinity,
            child: EstadoVacio(icono: Icons.task_alt, mensaje: context.t.noHayPendientes),
          ),
        )
      else
        for (final t in atencion) ...[
          TareaTile(tarea: t, onTap: () => onAbrir(t)),
          const SizedBox(height: 12),
        ],
    ]);
  }
}

/// Tarjeta oscura con el porcentaje de tareas completadas (anillo) y tres cifras.
class _TarjetaProgreso extends StatelessWidget {
  const _TarjetaProgreso({required this.total, required this.completadas});

  final int total;
  final int completadas;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final oscuro = tema.brightness == Brightness.dark;
    final fondo = oscuro ? Paleta.oscTarjetaOscura : Paleta.tintaClaro;
    const texto = Color(0xFFFFFFFF);
    const textoSuave = Color(0xB3FFFFFF);
    final acento = tema.colorScheme.primary;
    final porcentaje = total == 0 ? 0 : (completadas * 100 / total).round();
    final pendientes = total - completadas;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(color: fondo, borderRadius: BorderRadius.circular(28)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(context.t.progresoDeTareas,
            style: tema.textTheme.titleSmall?.copyWith(color: texto)),
        const SizedBox(height: 16),
        Row(children: [
          Semantics(
            label: context.t.porcentajeCompletado(porcentaje),
            child: AnilloProgreso(
              valor: total == 0 ? 0 : completadas / total,
              colorPista: const Color(0x26FFFFFF),
              colorBarra: acento,
              child: ExcludeSemantics(
                child: Text('$porcentaje%',
                    style: tema.textTheme.titleLarge?.copyWith(color: texto)),
              ),
            ),
          ),
          const SizedBox(width: 20),
          Container(width: 1, height: 80, color: const Color(0x26FFFFFF)),
          const SizedBox(width: 20),
          Expanded(
            child: Column(children: [
              _Cifra(Icons.list_alt_outlined, total, context.t.total, texto, textoSuave),
              const SizedBox(height: 10),
              _Cifra(Icons.check_circle_outline, completadas, context.t.completadas, texto, textoSuave),
              const SizedBox(height: 10),
              _Cifra(Icons.pending_outlined, pendientes, context.t.porHacer, texto, textoSuave),
            ]),
          ),
        ]),
      ]),
    );
  }
}

class _Cifra extends StatelessWidget {
  const _Cifra(this.icono, this.valor, this.etiqueta, this.colorTexto, this.colorSuave);

  final IconData icono;
  final int valor;
  final String etiqueta;
  final Color colorTexto;
  final Color colorSuave;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Row(children: [
      Container(
        width: 30,
        height: 30,
        decoration: BoxDecoration(
          color: const Color(0x1AFFFFFF),
          borderRadius: BorderRadius.circular(9),
        ),
        child: Icon(icono, size: 16, color: colorSuave),
      ),
      const SizedBox(width: 10),
      Expanded(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('$valor',
              style: tema.textTheme.titleSmall?.copyWith(color: colorTexto, height: 1.1)),
          Text(etiqueta,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: tema.textTheme.bodySmall
                  ?.copyWith(color: colorSuave, fontSize: 11, height: 1.1)),
        ]),
      ),
    ]);
  }
}

/// Píldora informativa: cifra dentro de un círculo del color del estado + nombre.
class _Conteo extends StatelessWidget {
  const _Conteo(this.titulo, this.cantidad, this.estado);

  final String titulo;
  final int cantidad;
  final String estado;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final e = tema.colorScheme;
    final estilo = estiloEstado(context, estado);
    return Container(
      padding: const EdgeInsets.fromLTRB(6, 6, 16, 6),
      decoration: BoxDecoration(
        color: e.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: e.outlineVariant),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Container(
          width: 32,
          height: 32,
          alignment: Alignment.center,
          decoration: BoxDecoration(color: estilo.fondo, shape: BoxShape.circle),
          child: Text('$cantidad',
              style: tema.textTheme.labelLarge?.copyWith(color: estilo.texto)),
        ),
        const SizedBox(width: 8),
        Text(titulo, style: tema.textTheme.labelLarge),
      ]),
    );
  }
}
