import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../l10n/textos.dart';
import '../models/modelos.dart';
import '../state/servicios.dart';
import '../widgets/avatar.dart';
import '../widgets/comunes.dart';
import '../widgets/opcion_perfil.dart';

const _tamanoMaxFoto = 5 * 1024 * 1024; // mismo límite que el servidor (que es quien manda)
final _soloLetras = RegExp(r"^[\p{L} '.\-]+$", unicode: true);

/// Perfil: foto, nombre, correo (solo lectura), idioma, notificaciones, apariencia y cierre de sesión.
class PerfilScreen extends StatefulWidget {
  const PerfilScreen({super.key});

  @override
  State<PerfilScreen> createState() => _PerfilScreenState();
}

class _PerfilScreenState extends State<PerfilScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nombre = TextEditingController();
  final _picker = ImagePicker();

  bool _cerrando = false;
  bool _guardandoNombre = false;
  bool _trabajandoFoto = false;
  bool _cambiandoIdioma = false;
  PreferenciaRecordatorios? _preferencia;
  bool _errorPreferencia = false;

  @override
  void initState() {
    super.initState();
    _nombre.text = authController.usuario?.nombre ?? '';
    _nombre.addListener(() => setState(() {})); // habilita/deshabilita "Guardar cambios"
    _cargarPreferencia();
  }

  @override
  void dispose() {
    _nombre.dispose();
    super.dispose();
  }

  Future<void> _cargarPreferencia() async {
    try {
      final p = await authController.obtenerPreferencia();
      if (mounted) setState(() => _preferencia = p);
    } catch (_) {
      if (mounted) setState(() => _errorPreferencia = true);
    }
  }

  bool get _nombreCambio => _nombre.text.trim() != (authController.usuario?.nombre ?? '').trim();

  // ───────────── Nombre ─────────────
  String? _validarNombre(String? v) {
    final t = context.t;
    final texto = (v ?? '').trim().replaceAll(RegExp(r'\s+'), ' ');
    if (texto.length < 2) return t.nombreMuyCorto;
    if (texto.length > 100) return t.nombreMuyLargo;
    if (!_soloLetras.hasMatch(texto)) return t.nombreCaracteres;
    return null;
  }

  Future<void> _guardarNombre() async {
    if (_guardandoNombre || !_formKey.currentState!.validate()) return;
    FocusScope.of(context).unfocus();
    setState(() => _guardandoNombre = true);
    try {
      await authController.actualizarNombre(_nombre.text.trim());
      if (!mounted) return;
      _nombre.text = authController.usuario?.nombre ?? _nombre.text; // el servidor lo normaliza
      mostrarMensaje(context, context.t.perfilActualizado);
    } catch (e) {
      if (mounted) mostrarError(context, e);
    } finally {
      if (mounted) setState(() => _guardandoNombre = false);
    }
  }

  // ───────────── Foto ─────────────
  bool get _hayCamara =>
      !kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.android || defaultTargetPlatform == TargetPlatform.iOS);

  Future<void> _opcionesFoto() async {
    final usuario = authController.usuario;
    if (usuario == null || _trabajandoFoto) return;
    final t = context.t;
    final accion = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (ctx) => SafeArea(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          if (usuario.tieneFoto)
            ListTile(
              leading: const Icon(Icons.visibility_outlined),
              title: Text(t.verFoto),
              onTap: () => Navigator.pop(ctx, 'ver'),
            ),
          ListTile(
            leading: const Icon(Icons.photo_library_outlined),
            title: Text(usuario.tieneFoto ? t.cambiarFoto : t.fotoDeLaGaleria),
            onTap: () => Navigator.pop(ctx, 'galeria'),
          ),
          if (_hayCamara)
            ListTile(
              leading: const Icon(Icons.photo_camera_outlined),
              title: Text(t.fotoDeLaCamara),
              onTap: () => Navigator.pop(ctx, 'camara'),
            ),
          if (usuario.tieneFoto)
            ListTile(
              leading: Icon(Icons.delete_outline, color: Theme.of(ctx).colorScheme.error),
              title: Text(t.eliminarFoto, style: TextStyle(color: Theme.of(ctx).colorScheme.error)),
              onTap: () => Navigator.pop(ctx, 'borrar'),
            ),
        ]),
      ),
    );
    if (!mounted) return;
    switch (accion) {
      case 'ver':
        _verFoto(usuario);
      case 'galeria':
        await _elegirFoto(ImageSource.gallery);
      case 'camara':
        await _elegirFoto(ImageSource.camera);
      case 'borrar':
        await _borrarFoto();
    }
  }

  void _verFoto(Usuario usuario) {
    showDialog<void>(
      context: context,
      builder: (ctx) => Dialog(
        backgroundColor: Colors.transparent,
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Align(
            alignment: Alignment.centerRight,
            child: IconButton.filled(
              tooltip: MaterialLocalizations.of(ctx).closeButtonTooltip,
              onPressed: () => Navigator.pop(ctx),
              icon: const Icon(Icons.close),
            ),
          ),
          const SizedBox(height: 8),
          AvatarUsuario(
              usuario: usuario, radio: (MediaQuery.of(ctx).size.width * 0.4).clamp(80.0, 180.0)),
        ]),
      ),
    );
  }

  String _tipoMime(String nombre) {
    final ext = nombre.contains('.') ? nombre.split('.').last.toLowerCase() : '';
    return switch (ext) {
      'jpg' || 'jpeg' => 'image/jpeg',
      'png' => 'image/png',
      'webp' => 'image/webp',
      _ => 'application/octet-stream', // el servidor decide por el contenido real, no por esto
    };
  }

  Future<void> _elegirFoto(ImageSource origen) async {
    final t = context.t;
    XFile? archivo;
    try {
      archivo = await _picker.pickImage(
          source: origen, maxWidth: 1600, maxHeight: 1600, imageQuality: 90);
    } catch (_) {
      if (mounted) mostrarMensaje(context, t.fotoNoDisponible);
      return;
    }
    if (archivo == null || !mounted) return; // canceló
    setState(() => _trabajandoFoto = true);
    try {
      final bytes = await archivo.readAsBytes();
      if (bytes.length > _tamanoMaxFoto) {
        if (mounted) mostrarMensaje(context, t.errorPorCodigo('FOTO_DEMASIADO_GRANDE')!);
        return;
      }
      await authController.subirFoto(bytes, archivo.name, _tipoMime(archivo.name));
      if (mounted) mostrarMensaje(context, t.fotoActualizada);
    } catch (e) {
      if (mounted) mostrarError(context, e); // incluye "formato no permitido" del servidor
    } finally {
      if (mounted) setState(() => _trabajandoFoto = false);
    }
  }

  Future<void> _borrarFoto() async {
    final t = context.t;
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(t.eliminarFotoTitulo),
        content: Text(t.eliminarFotoTexto),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(t.cancelar)),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: Text(t.eliminar)),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    setState(() => _trabajandoFoto = true);
    try {
      await authController.borrarFoto();
      if (mounted) mostrarMensaje(context, t.fotoEliminada);
    } catch (e) {
      if (mounted) mostrarError(context, e);
    } finally {
      if (mounted) setState(() => _trabajandoFoto = false);
    }
  }

  // ───────────── Idioma ─────────────
  Future<void> _cambiarIdioma(String codigo) async {
    if (_cambiandoIdioma || codigo == idiomaController.codigo) return;
    setState(() => _cambiandoIdioma = true);
    try {
      await authController.cambiarIdioma(codigo);
      // Los textos ya cambiaron: el mensaje sale en el idioma nuevo.
      if (mounted) mostrarMensaje(context, context.t.idiomaActualizado);
    } catch (e) {
      if (mounted) mostrarError(context, e); // el controlador ya restauró el idioma anterior
    } finally {
      if (mounted) setState(() => _cambiandoIdioma = false);
    }
  }

  // ───────────── Notificaciones ─────────────
  Future<void> _editarNotificaciones() async {
    final actual = _preferencia;
    if (actual == null) return;
    final nueva = await showModalBottomSheet<PreferenciaRecordatorios>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (ctx) => _HojaNotificaciones(inicial: actual),
    );
    if (nueva == null || !mounted) return;
    try {
      await authController.guardarPreferencia(nueva.perfil, activas: nueva.activas);
      if (!mounted) return;
      setState(() => _preferencia = nueva);
      mostrarMensaje(context, context.t.preferenciaGuardada);
    } catch (e) {
      if (mounted) mostrarError(context, e);
    }
  }

  // ───────────── Sesión ─────────────
  Future<void> _cerrarSesion() async {
    final t = context.t;
    final confirmado = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(t.cerrarSesionTitulo),
        content: Text(t.cerrarSesionTexto),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(t.cancelar)),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: Text(t.cerrarSesion)),
        ],
      ),
    );
    if (confirmado != true || !mounted) return;
    setState(() => _cerrando = true);
    try {
      await authController.cerrarSesion();
      // Al cambiar la sesión, main.dart reemplaza esta pantalla por el login.
    } finally {
      if (mounted) setState(() => _cerrando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final usuario = authController.usuario;
    if (usuario == null) return const SizedBox.shrink();
    final tema = Theme.of(context);
    final e = tema.colorScheme;
    final t = context.t;
    return ContenidoCentrado(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 120), // espacio para la barra flotante
        children: [
          Text(t.perfil, style: tema.textTheme.headlineMedium),
          const SizedBox(height: 24),

          // ── Foto ──
          Center(
            child: Column(children: [
              Semantics(
                button: true,
                label: t.editarFoto,
                child: InkWell(
                  customBorder: const CircleBorder(),
                  onTap: _trabajandoFoto ? null : _opcionesFoto,
                  child: Stack(alignment: Alignment.center, children: [
                    AvatarUsuario(usuario: usuario, radio: 52),
                    if (_trabajandoFoto)
                      const SizedBox(
                          width: 104, height: 104, child: CircularProgressIndicator(strokeWidth: 3)),
                    Positioned(
                      right: 0,
                      bottom: 0,
                      child: Container(
                        padding: const EdgeInsets.all(7),
                        decoration: BoxDecoration(
                          color: e.primary,
                          shape: BoxShape.circle,
                          border: Border.all(color: e.surface, width: 2),
                        ),
                        child: Icon(Icons.photo_camera_outlined, size: 16, color: e.onPrimary),
                      ),
                    ),
                  ]),
                ),
              ),
              TextButton(
                onPressed: _trabajandoFoto ? null : _opcionesFoto,
                child: Text(t.editarFoto),
              ),
            ]),
          ),
          const SizedBox(height: 8),

          // ── Datos de la cuenta ──
          Text(t.datosDeLaCuenta, style: tema.textTheme.titleSmall),
          const SizedBox(height: 12),
          Superficie(
            padding: const EdgeInsets.all(16),
            child: Form(
              key: _formKey,
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                TextFormField(
                  controller: _nombre,
                  enabled: !_guardandoNombre,
                  textCapitalization: TextCapitalization.words,
                  textInputAction: TextInputAction.done,
                  autofillHints: const [AutofillHints.name],
                  maxLength: 100,
                  decoration: decoracionCampo(context, t.nombre).copyWith(counterText: ''),
                  validator: _validarNombre,
                  onFieldSubmitted: (_) => _guardarNombre(),
                ),
                const SizedBox(height: 16),
                // Correo: solo lectura.
                InputDecorator(
                  decoration: decoracionCampo(context, t.correo,
                      ayuda: t.correoNoEditable, sufijo: const Icon(Icons.lock_outline, size: 18)),
                  child: Text(usuario.email,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: tema.textTheme.bodyLarge?.copyWith(color: e.onSurfaceVariant)),
                ),
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: (_guardandoNombre || !_nombreCambio) ? null : _guardarNombre,
                  child: _guardandoNombre
                      ? const SizedBox(
                          height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                      : Text(t.guardarCambios),
                ),
              ]),
            ),
          ),
          const SizedBox(height: 16),
          Superficie(
            child: ListTile(
              leading: const Icon(Icons.public),
              title: Text(t.zonaHoraria),
              subtitle: Text(usuario.zonaHoraria),
            ),
          ),
          const SizedBox(height: 24),

          // ── Idioma ──
          Text(t.idioma, style: tema.textTheme.titleSmall),
          const SizedBox(height: 12),
          ListenableBuilder(
            listenable: idiomaController,
            builder: (context, _) => Wrap(spacing: 8, runSpacing: 8, children: [
              PildoraFiltro(
                etiqueta: t.espanol,
                icono: Icons.translate,
                activo: idiomaController.codigo == 'es',
                onTap: () => _cambiarIdioma('es'),
              ),
              PildoraFiltro(
                etiqueta: t.ingles,
                icono: Icons.translate,
                activo: idiomaController.codigo == 'en',
                onTap: () => _cambiarIdioma('en'),
              ),
            ]),
          ),
          const SizedBox(height: 24),

          // ── Notificaciones ──
          Text(t.notificaciones, style: tema.textTheme.titleSmall),
          const SizedBox(height: 12),
          Superficie(
            child: ListTile(
              leading: const Icon(Icons.notifications_outlined),
              title: Text(t.recordatorios),
              subtitle: _preferencia != null
                  ? Text(_preferencia!.activas
                      ? t.nombrePerfil(_preferencia!.perfil)
                      : '${t.nombrePerfil(_preferencia!.perfil)} · ${t.desactivados}')
                  : (_errorPreferencia ? const Text('—') : Text(t.cargando)),
              trailing: const Icon(Icons.chevron_right),
              onTap: _preferencia == null ? null : _editarNotificaciones,
            ),
          ),
          const SizedBox(height: 24),

          // ── Apariencia ──
          Text(t.apariencia, style: tema.textTheme.titleSmall),
          const SizedBox(height: 12),
          ListenableBuilder(
            listenable: temaController,
            builder: (context, _) => Wrap(spacing: 8, runSpacing: 8, children: [
              PildoraFiltro(
                etiqueta: t.claro,
                icono: Icons.light_mode_outlined,
                activo: temaController.modo == ThemeMode.light,
                onTap: () => temaController.cambiar(ThemeMode.light),
              ),
              PildoraFiltro(
                etiqueta: t.oscuro,
                icono: Icons.dark_mode_outlined,
                activo: temaController.modo == ThemeMode.dark,
                onTap: () => temaController.cambiar(ThemeMode.dark),
              ),
              PildoraFiltro(
                etiqueta: t.sistema,
                icono: Icons.brightness_auto_outlined,
                activo: temaController.modo == ThemeMode.system,
                onTap: () => temaController.cambiar(ThemeMode.system),
              ),
            ]),
          ),
          const SizedBox(height: 32),
          OutlinedButton.icon(
            onPressed: _cerrando ? null : _cerrarSesion,
            icon: const Icon(Icons.logout),
            label: Text(t.cerrarSesion),
          ),
        ],
      ),
    );
  }
}

/// Hoja inferior para cambiar el perfil de recordatorios y activarlos/desactivarlos.
class _HojaNotificaciones extends StatefulWidget {
  const _HojaNotificaciones({required this.inicial});

  final PreferenciaRecordatorios inicial;

  @override
  State<_HojaNotificaciones> createState() => _HojaNotificacionesState();
}

class _HojaNotificacionesState extends State<_HojaNotificaciones> {
  late String _perfil = widget.inicial.perfil;
  late bool _activas = widget.inicial.activas;

  @override
  Widget build(BuildContext context) {
    final t = context.t;
    return SafeArea(
      child: SingleChildScrollView(
        padding: EdgeInsets.fromLTRB(
            20, 0, 20, 16 + MediaQuery.of(context).viewInsets.bottom),
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text(t.recordatorios, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 12),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(t.recordatoriosActivados),
            value: _activas,
            onChanged: (v) => setState(() => _activas = v),
          ),
          const SizedBox(height: 8),
          for (final p in perfilesRecordatorios) ...[
            OpcionPerfil(perfil: p, elegida: _perfil == p, onTap: () => setState(() => _perfil = p)),
            const SizedBox(height: 10),
          ],
          const SizedBox(height: 6),
          FilledButton(
            onPressed: () =>
                Navigator.pop(context, PreferenciaRecordatorios(perfil: _perfil, activas: _activas)),
            child: Text(t.guardar),
          ),
        ]),
      ),
    );
  }
}
