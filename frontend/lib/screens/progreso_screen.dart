import 'package:flutter/material.dart';

import '../l10n/textos.dart';
import '../models/modelos.dart';
import '../state/servicios.dart';
import '../widgets/comunes.dart';

/// RF-26: progreso de gamificación (racha, puntos, nivel, protecciones, logros y recuperación).
/// Se abre desde la tarjeta de racha de Inicio. Todas las cifras las calcula el backend.
class ProgresoScreen extends StatefulWidget {
  const ProgresoScreen({super.key});

  @override
  State<ProgresoScreen> createState() => _ProgresoScreenState();
}

class _ProgresoScreenState extends State<ProgresoScreen> {
  late Future<ProgresoGamificacion> _futuro;
  bool _trabajando = false;

  @override
  void initState() {
    super.initState();
    _futuro = gamificacionRepo.progreso();
  }

  void _recargar() => setState(() => _futuro = gamificacionRepo.progreso());

  Future<bool> _confirmar(String titulo, String texto, String accion) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(titulo),
        content: Text(texto),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(ctx.t.cancelar)),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: Text(accion)),
        ],
      ),
    );
    return ok ?? false;
  }

  /// Ejecuta una acción, muestra el resultado y recarga. Evita dobles toques mientras trabaja.
  Future<void> _accion(Future<void> Function() hacer, String exito) async {
    if (_trabajando) return;
    setState(() => _trabajando = true);
    try {
      await hacer();
      if (!mounted) return;
      mostrarMensaje(context, exito);
      _recargar();
    } catch (e) {
      if (mounted) mostrarError(context, e);
    } finally {
      if (mounted) setState(() => _trabajando = false);
    }
  }

  Future<void> _usarProteccion() async {
    final t = context.t;
    if (!await _confirmar(t.proteccionTitulo, t.proteccionConfirmar, t.usarProteccion)) return;
    await _accion(() => gamificacionRepo.usarProteccion(), t.proteccionUsada);
  }

  Future<void> _iniciarRecuperacion() async {
    final t = context.t;
    if (!await _confirmar(t.recuperacionTitulo, t.recuperacionTexto, t.iniciarRecuperacion)) return;
    await _accion(() => gamificacionRepo.iniciarRecuperacion(), t.recuperacionIniciada);
  }

  Future<void> _cancelarRecuperacion(String id) async {
    final t = context.t;
    if (!await _confirmar(t.cancelarRecuperacion, t.cancelarRecuperacionConfirmar, t.cancelarRecuperacion)) return;
    await _accion(() => gamificacionRepo.cancelarRecuperacion(id), t.recuperacionCancelada);
  }

  @override
  Widget build(BuildContext context) {
    return Pantalla(
      appBar: barraSimple(context, context.t.progreso),
      body: FutureBuilder<ProgresoGamificacion>(
        future: _futuro,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) return EstadoError(error: snap.error, onReintentar: _recargar);
          return RefreshIndicator(
            onRefresh: () async {
              _recargar();
              try {
                await _futuro;
              } catch (_) {
                // El error se muestra en pantalla.
              }
            },
            child: ContenidoProgreso(
              progreso: snap.data!,
              ocupado: _trabajando,
              onUsarProteccion: _usarProteccion,
              onIniciarRecuperacion: _iniciarRecuperacion,
              onCancelarRecuperacion: _cancelarRecuperacion,
            ),
          );
        },
      ),
    );
  }
}

/// Contenido de la pantalla, separado para poder probarlo sin servidor.
class ContenidoProgreso extends StatelessWidget {
  const ContenidoProgreso({
    super.key,
    required this.progreso,
    this.ocupado = false,
    this.onUsarProteccion,
    this.onIniciarRecuperacion,
    this.onCancelarRecuperacion,
  });

  final ProgresoGamificacion progreso;
  final bool ocupado;
  final VoidCallback? onUsarProteccion;
  final VoidCallback? onIniciarRecuperacion;
  final ValueChanged<String>? onCancelarRecuperacion;

  @override
  Widget build(BuildContext context) {
    final t = context.t;
    final tema = Theme.of(context);
    final p = progreso;
    return ContenidoCentrado(
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
        children: [
          TarjetaRacha(progreso: p),
          const SizedBox(height: 16),
          Row(children: [
            Expanded(child: _Dato(Icons.star_outline, '${p.puntos}', t.puntos)),
            const SizedBox(width: 8),
            Expanded(child: _Dato(Icons.military_tech_outlined, '${p.nivel}', t.nivelEtiqueta)),
            const SizedBox(width: 8),
            Expanded(child: _Dato(Icons.shield_outlined, '${p.protecciones}', t.protecciones)),
          ]),
          const SizedBox(height: 8),
          _Dato(Icons.emoji_events_outlined, t.dias(p.rachaMaxima), t.rachaMaxima),
          if (p.puedeProteger) ...[
            const SizedBox(height: 16),
            _Aviso(
              icono: Icons.shield_outlined,
              titulo: t.proteccionTitulo,
              texto: t.proteccionTexto(p.proteccionFecha!, p.proteccionRacha!),
              accion: t.usarProteccion,
              onPressed: ocupado ? null : onUsarProteccion,
            ),
          ],
          if (p.recuperacion != null) ...[
            const SizedBox(height: 16),
            _Aviso(
              icono: Icons.restore,
              titulo: t.recuperacionEnCurso(p.recuperacion!.rachaPerdida),
              texto: t.recuperacionAvance(
                  p.recuperacion!.tareasCompletadas, p.recuperacion!.tareasTotal, p.recuperacion!.diasRestantes),
              accion: t.cancelarRecuperacion,
              secundaria: true,
              onPressed: ocupado || onCancelarRecuperacion == null
                  ? null
                  : () => onCancelarRecuperacion!(p.recuperacion!.id),
            ),
          ] else if (p.puedeRecuperar) ...[
            const SizedBox(height: 16),
            _Aviso(
              icono: Icons.restore,
              titulo: t.recuperacionTitulo,
              texto: t.recuperacionTexto,
              accion: t.iniciarRecuperacion,
              onPressed: ocupado ? null : onIniciarRecuperacion,
            ),
          ],
          const SizedBox(height: 28),
          Text(t.logros, style: tema.textTheme.titleMedium),
          const SizedBox(height: 12),
          Text(t.logrosObtenidos, style: tema.textTheme.labelLarge),
          const SizedBox(height: 8),
          if (p.logrosDesbloqueados.isEmpty)
            Superficie(child: EstadoVacio(icono: Icons.emoji_events_outlined, mensaje: t.sinLogros))
          else
            for (final l in p.logrosDesbloqueados) ...[LogroTile(logro: l), const SizedBox(height: 8)],
          const SizedBox(height: 16),
          Text(t.logrosPorObtener, style: tema.textTheme.labelLarge),
          const SizedBox(height: 8),
          for (final l in p.logrosPendientes) ...[LogroTile(logro: l), const SizedBox(height: 8)],
        ],
      ),
    );
  }
}

/// Tarjeta con la racha actual y el compromiso de hoy. Se usa en Inicio y en Progreso.
class TarjetaRacha extends StatelessWidget {
  const TarjetaRacha({super.key, required this.progreso, this.onTap});

  final ProgresoGamificacion progreso;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final t = context.t;
    final tema = Theme.of(context);
    final e = tema.colorScheme;
    final p = progreso;
    return Superficie(
      onTap: onTap,
      padding: const EdgeInsets.all(18),
      child: Row(children: [
        Container(
          width: 52,
          height: 52,
          alignment: Alignment.center,
          decoration: BoxDecoration(color: e.primaryContainer, shape: BoxShape.circle),
          child: Icon(Icons.local_fire_department, color: e.onPrimaryContainer),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('${t.racha}: ${t.dias(p.rachaActual)}', style: tema.textTheme.titleMedium),
            const SizedBox(height: 2),
            Text('${p.puntos} ${t.puntos.toLowerCase()} · ${t.nivel(p.nivel)}',
                style: tema.textTheme.bodySmall?.copyWith(color: e.onSurfaceVariant)),
            const SizedBox(height: 2),
            Text(t.hoyCompromisos(p.hoyCumplidas, p.hoyComprometidas),
                style: tema.textTheme.bodySmall?.copyWith(color: e.onSurfaceVariant)),
          ]),
        ),
        if (onTap != null) Icon(Icons.chevron_right, color: e.onSurfaceVariant, semanticLabel: t.verProgreso),
      ]),
    );
  }
}

class LogroTile extends StatelessWidget {
  const LogroTile({super.key, required this.logro});

  final Logro logro;

  @override
  Widget build(BuildContext context) {
    final t = context.t;
    final tema = Theme.of(context);
    final e = tema.colorScheme;
    final l = logro;
    return Superficie(
      padding: const EdgeInsets.all(14),
      radio: 18,
      child: Row(children: [
        Icon(l.desbloqueado ? Icons.emoji_events : Icons.emoji_events_outlined,
            color: l.desbloqueado ? e.primary : e.outline),
        const SizedBox(width: 12),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(l.nombre, style: tema.textTheme.titleSmall),
            Text('${t.categoriaLogro(l.categoria)} · ${l.descripcion}',
                style: tema.textTheme.bodySmall?.copyWith(color: e.onSurfaceVariant)),
            if (!l.desbloqueado) ...[
              const SizedBox(height: 6),
              Semantics(
                label: '${l.valorActual} / ${l.valorCondicion}',
                child: LinearProgressIndicator(value: l.progreso / 100, minHeight: 6),
              ),
              const SizedBox(height: 2),
              Text('${l.valorActual} / ${l.valorCondicion}', style: tema.textTheme.labelSmall),
            ] else if (l.fechaDesbloqueo != null)
              Text(t.fecha(l.fechaDesbloqueo!), style: tema.textTheme.labelSmall),
          ]),
        ),
        const SizedBox(width: 8),
        Text(t.puntosRecompensa(l.recompensaPuntos), style: tema.textTheme.labelMedium),
      ]),
    );
  }
}

class _Dato extends StatelessWidget {
  const _Dato(this.icono, this.valor, this.etiqueta);

  final IconData icono;
  final String valor;
  final String etiqueta;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Superficie(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      radio: 18,
      child: Row(children: [
        Icon(icono, size: 20, color: tema.colorScheme.primary),
        const SizedBox(width: 8),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(valor, style: tema.textTheme.titleSmall),
            Text(etiqueta,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: tema.textTheme.bodySmall?.copyWith(color: tema.colorScheme.onSurfaceVariant)),
          ]),
        ),
      ]),
    );
  }
}

class _Aviso extends StatelessWidget {
  const _Aviso({
    required this.icono,
    required this.titulo,
    required this.texto,
    required this.accion,
    required this.onPressed,
    this.secundaria = false,
  });

  final IconData icono;
  final String titulo;
  final String texto;
  final String accion;
  final VoidCallback? onPressed;
  final bool secundaria;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Superficie(
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Icon(icono, color: tema.colorScheme.primary),
          const SizedBox(width: 8),
          Expanded(child: Text(titulo, style: tema.textTheme.titleSmall)),
        ]),
        const SizedBox(height: 8),
        Text(texto, style: tema.textTheme.bodyMedium),
        const SizedBox(height: 12),
        Align(
          alignment: Alignment.centerRight,
          child: secundaria
              ? OutlinedButton(onPressed: onPressed, child: Text(accion))
              : FilledButton(onPressed: onPressed, child: Text(accion)),
        ),
      ]),
    );
  }
}
