import 'package:flutter/material.dart';

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
    return Scaffold(
      body: SafeArea(child: paginas[_indice]),
      bottomNavigationBar: DecoratedBox(
        decoration: BoxDecoration(
          border: Border(top: BorderSide(color: Theme.of(context).colorScheme.outlineVariant)),
        ),
        child: NavigationBar(
          selectedIndex: _indice,
          onDestinationSelected: (i) => setState(() => _indice = i),
          destinations: const [
            NavigationDestination(
                icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Inicio'),
            NavigationDestination(icon: Icon(Icons.checklist), label: 'Tareas'),
            NavigationDestination(
                icon: Icon(Icons.calendar_month_outlined),
                selectedIcon: Icon(Icons.calendar_month),
                label: 'Calendario'),
            NavigationDestination(
                icon: Icon(Icons.person_outline),
                selectedIcon: Icon(Icons.person),
                label: 'Perfil'),
          ],
        ),
      ),
    );
  }
}
