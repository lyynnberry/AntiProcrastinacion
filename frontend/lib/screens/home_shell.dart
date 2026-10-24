import 'package:flutter/material.dart';

import '../l10n/textos.dart';
import '../theme/app_theme.dart';
import '../widgets/comunes.dart';
import 'calendario_screen.dart';
import 'inicio_screen.dart';
import 'perfil_screen.dart';
import 'tareas_screen.dart';

/// Navegación principal: Inicio | Tareas | Calendario | Perfil.
class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _indice = 0;

  @override
  Widget build(BuildContext context) {
    // Se reconstruye la pestaña al cambiar, así siempre muestra datos recién consultados.
    const paginas = <Widget>[InicioScreen(), TareasScreen(), CalendarioScreen(), PerfilScreen()];
    return Pantalla(
      body: SafeArea(bottom: false, child: paginas[_indice]),
      barraInferior: _BarraFlotante(
        indice: _indice,
        onCambio: (i) => setState(() => _indice = i),
      ),
    );
  }
}

class _Destino {
  const _Destino(this.icono, this.iconoActivo, this.etiqueta);

  final IconData icono;
  final IconData iconoActivo;
  final String Function(Textos) etiqueta; // se resuelve con el idioma actual
}

final _destinos = [
  _Destino(Icons.home_outlined, Icons.home, (t) => t.inicio),
  _Destino(Icons.checklist, Icons.checklist, (t) => t.tareas),
  _Destino(Icons.calendar_month_outlined, Icons.calendar_month, (t) => t.calendario),
  _Destino(Icons.person_outline, Icons.person, (t) => t.perfil),
];

/// Barra de navegación en forma de píldora flotante. La opción activa muestra su nombre.
class _BarraFlotante extends StatelessWidget {
  const _BarraFlotante({required this.indice, required this.onCambio});

  final int indice;
  final ValueChanged<int> onCambio;

  @override
  Widget build(BuildContext context) {
    final e = Theme.of(context).colorScheme;
    final oscuro = Theme.of(context).brightness == Brightness.dark;
    return SafeArea(
      top: false,
      minimum: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 0),
        // heightFactor: 1 hace que el Center mida solo lo que mide la barra. Sin él, el Center
        // se estira a toda la altura disponible y deja la pantalla sin espacio para el contenido.
        child: Center(
          heightFactor: 1,
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 440),
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: oscuro ? Paleta.oscTarjetaOscura : e.inverseSurface,
                borderRadius: BorderRadius.circular(36),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.18),
                    blurRadius: 24,
                    offset: const Offset(0, 8),
                  ),
                ],
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  for (var i = 0; i < _destinos.length; i++)
                    _Item(
                      destino: _destinos[i],
                      activo: i == indice,
                      onTap: () => onCambio(i),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _Item extends StatelessWidget {
  const _Item({required this.destino, required this.activo, required this.onTap});

  final _Destino destino;
  final bool activo;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final e = Theme.of(context).colorScheme;
    // Sobre la barra oscura: la opción activa va en el color de acción y el resto en blanco suave.
    final colorActivo = e.onPrimary;
    const colorInactivo = Color(0xB3FFFFFF);
    return Semantics(
      button: true,
      selected: activo,
      label: destino.etiqueta(context.t),
      child: ExcludeSemantics(
        child: Material(
          color: activo ? e.primary : Colors.transparent,
          shape: const StadiumBorder(),
          child: InkWell(
            customBorder: const StadiumBorder(),
            onTap: onTap,
            child: AnimatedSize(
              duration: const Duration(milliseconds: 180),
              curve: Curves.easeOut,
              child: Container(
                height: 48,
                constraints: const BoxConstraints(minWidth: 48),
                padding: EdgeInsets.symmetric(horizontal: activo ? 16 : 12),
                child: Row(mainAxisSize: MainAxisSize.min, children: [
                  Icon(activo ? destino.iconoActivo : destino.icono,
                      size: 22, color: activo ? colorActivo : colorInactivo),
                  if (activo) ...[
                    const SizedBox(width: 8),
                    Text(destino.etiqueta(context.t),
                        style: TextStyle(
                            color: colorActivo, fontWeight: FontWeight.w600, fontSize: 14)),
                  ],
                ]),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
