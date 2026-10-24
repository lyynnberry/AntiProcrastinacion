import 'package:flutter/material.dart';

import '../l10n/textos.dart';
import '../models/modelos.dart';
import '../state/servicios.dart';
import '../widgets/comunes.dart';
import '../widgets/opcion_perfil.dart';

/// Personalización inicial (primer uso): la persona elige qué tan insistentes quiere los recordatorios.
///
/// Guarda en el servidor; al confirmarse, el servidor marca la personalización como completa y
/// `main.dart` (que decide qué pantalla toca) pasa solo al tutorial. No contradice RF-12/RF-13: la
/// escalada de cada recordatorio sigue existiendo; esto solo es el perfil de preferencia.
class PersonalizacionScreen extends StatefulWidget {
  const PersonalizacionScreen({super.key});

  @override
  State<PersonalizacionScreen> createState() => _PersonalizacionScreenState();
}

class _PersonalizacionScreenState extends State<PersonalizacionScreen> {
  String? _perfil;
  bool _guardando = false;
  bool _sinElegir = false;

  Future<void> _continuar() async {
    if (_guardando) return;
    final perfil = _perfil;
    if (perfil == null) {
      setState(() => _sinElegir = true); // validación: hay que elegir una opción
      return;
    }
    setState(() => _guardando = true);
    try {
      await authController.guardarPreferencia(perfil);
      // Éxito: el estado del usuario cambia y main.dart muestra el tutorial.
    } catch (e) {
      if (mounted) mostrarError(context, e);
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final e = tema.colorScheme;
    final t = context.t;
    return Pantalla(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 480),
            child: Column(children: [
              Expanded(
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(24, 32, 24, 16),
                  children: [
                    Align(
                      alignment: Alignment.centerLeft,
                      child: Container(
                        width: 56,
                        height: 56,
                        decoration: BoxDecoration(color: e.inverseSurface, shape: BoxShape.circle),
                        child: Icon(Icons.tune_rounded, color: e.primary, size: 28),
                      ),
                    ),
                    const SizedBox(height: 24),
                    Semantics(
                      header: true,
                      child: Text(t.personalizaTitulo, style: tema.textTheme.headlineMedium),
                    ),
                    const SizedBox(height: 8),
                    Text(t.personalizaIntro,
                        style: tema.textTheme.bodyMedium?.copyWith(color: e.onSurfaceVariant)),
                    const SizedBox(height: 28),
                    for (final p in perfilesRecordatorios) ...[
                      OpcionPerfil(
                        perfil: p,
                        elegida: _perfil == p,
                        recomendada: p == 'equilibrado',
                        onTap: _guardando
                            ? null
                            : () => setState(() {
                                  _perfil = p;
                                  _sinElegir = false;
                                }),
                      ),
                      const SizedBox(height: 12),
                    ],
                    if (_sinElegir)
                      Padding(
                        padding: const EdgeInsets.only(top: 4, left: 4),
                        child: Text(t.elijeUnaOpcion,
                            style: tema.textTheme.bodySmall?.copyWith(color: e.error)),
                      )
                    else
                      Padding(
                        padding: const EdgeInsets.only(top: 4, left: 4),
                        child: Text(t.puedesCambiarloDespues,
                            style: tema.textTheme.bodySmall?.copyWith(color: e.onSurfaceVariant)),
                      ),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 8, 24, 16),
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  FilledButton(
                    onPressed: _guardando ? null : _continuar,
                    child: _guardando
                        ? const SizedBox(
                            height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                        : Text(t.continuar),
                  ),
                  TextButton(
                    onPressed: _guardando ? null : authController.cerrarSesion,
                    child: Text(t.cerrarSesion),
                  ),
                ]),
              ),
            ]),
          ),
        ),
      ),
    );
  }
}
