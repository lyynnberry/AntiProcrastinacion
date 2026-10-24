import 'package:flutter/material.dart';

import '../l10n/textos.dart';

/// Tarjeta seleccionable de un perfil de recordatorios (Tranquilo / Equilibrado / Insistente).
/// Se usa en la personalización inicial y al cambiar la preferencia desde el perfil.
class OpcionPerfil extends StatelessWidget {
  const OpcionPerfil({
    super.key,
    required this.perfil,
    required this.elegida,
    required this.onTap,
    this.recomendada = false,
  });

  final String perfil; // tranquilo | equilibrado | insistente
  final bool elegida;
  final bool recomendada;
  final VoidCallback? onTap;

  static IconData icono(String perfil) => switch (perfil) {
        'tranquilo' => Icons.spa_outlined,
        'insistente' => Icons.notifications_active_outlined,
        _ => Icons.balance_outlined,
      };

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final e = tema.colorScheme;
    final t = context.t;
    return Semantics(
      button: true,
      inMutuallyExclusiveGroup: true,
      selected: elegida,
      label: '${t.nombrePerfil(perfil)}. ${t.descPerfil(perfil)}',
      child: ExcludeSemantics(
        child: Material(
          color: elegida ? e.tertiaryContainer : e.surfaceContainerLowest,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
            side: BorderSide(
              color: elegida ? e.primary : e.outlineVariant,
              width: elegida ? 2 : 1,
            ),
          ),
          child: InkWell(
            borderRadius: BorderRadius.circular(24),
            onTap: onTap,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: elegida ? e.surface : e.surfaceContainerHigh,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(icono(perfil), color: elegida ? e.primary : e.onSurfaceVariant),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Row(children: [
                      Flexible(
                        child: Text(t.nombrePerfil(perfil), style: tema.textTheme.titleMedium),
                      ),
                      if (recomendada) ...[
                        const SizedBox(width: 8),
                        Text(t.recomendado,
                            style: tema.textTheme.labelSmall?.copyWith(color: e.primary)),
                      ],
                    ]),
                    const SizedBox(height: 2),
                    Text(t.descPerfil(perfil),
                        style: tema.textTheme.bodySmall?.copyWith(color: e.onSurfaceVariant)),
                  ]),
                ),
                const SizedBox(width: 8),
                Icon(
                  elegida ? Icons.radio_button_checked : Icons.radio_button_unchecked,
                  color: elegida ? e.primary : e.outline,
                ),
              ]),
            ),
          ),
        ),
      ),
    );
  }
}
