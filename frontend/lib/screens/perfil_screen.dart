import 'package:flutter/material.dart';

import '../state/servicios.dart';
import '../widgets/comunes.dart';

/// Perfil básico: datos de la cuenta, tema de la app y cierre de sesión (RF-03).
class PerfilScreen extends StatefulWidget {
  const PerfilScreen({super.key});

  @override
  State<PerfilScreen> createState() => _PerfilScreenState();
}

class _PerfilScreenState extends State<PerfilScreen> {
  bool _cerrando = false;

  Future<void> _cerrarSesion() async {
    final confirmado = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('¿Cerrar sesión?'),
        content: const Text('Tendrás que iniciar sesión de nuevo para ver tus tareas.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Cerrar sesión')),
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
    final sinNombre = usuario.nombre?.trim().isEmpty ?? true;
    return ContenidoCentrado(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 24, 20, 24),
        children: [
          Text('Perfil', style: tema.textTheme.headlineMedium),
          const SizedBox(height: 24),
          Row(children: [
            CircleAvatar(
              radius: 30,
              backgroundColor: e.primaryContainer,
              foregroundColor: e.onPrimaryContainer,
              child: Text(usuario.iniciales,
                  style: tema.textTheme.titleLarge?.copyWith(color: e.onPrimaryContainer)),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(sinNombre ? 'Sin nombre registrado' : usuario.nombre!,
                    maxLines: 1, overflow: TextOverflow.ellipsis, style: tema.textTheme.titleMedium),
                const SizedBox(height: 2),
                Text(usuario.email,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: tema.textTheme.bodyMedium?.copyWith(color: e.onSurfaceVariant)),
              ]),
            ),
          ]),
          const SizedBox(height: 24),
          Superficie(
            child: Column(children: [
              ListTile(
                leading: const Icon(Icons.public),
                title: const Text('Zona horaria'),
                subtitle: Text(usuario.zonaHoraria),
              ),
            ]),
          ),
          const SizedBox(height: 24),
          Text('Apariencia', style: tema.textTheme.titleSmall),
          const SizedBox(height: 12),
          ListenableBuilder(
            listenable: temaController,
            builder: (context, _) => SegmentedButton<ThemeMode>(
              showSelectedIcon: false,
              segments: const [
                ButtonSegment(
                    value: ThemeMode.light,
                    icon: Icon(Icons.light_mode_outlined),
                    label: Text('Claro')),
                ButtonSegment(
                    value: ThemeMode.dark,
                    icon: Icon(Icons.dark_mode_outlined),
                    label: Text('Oscuro')),
                ButtonSegment(
                    value: ThemeMode.system,
                    icon: Icon(Icons.brightness_auto_outlined),
                    label: Text('Sistema')),
              ],
              selected: {temaController.modo},
              onSelectionChanged: (s) => temaController.cambiar(s.first),
            ),
          ),
          const SizedBox(height: 32),
          OutlinedButton.icon(
            onPressed: _cerrando ? null : _cerrarSesion,
            icon: const Icon(Icons.logout),
            label: const Text('Cerrar sesión'),
          ),
        ],
      ),
    );
  }
}
