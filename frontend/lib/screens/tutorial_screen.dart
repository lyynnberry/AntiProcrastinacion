import 'package:flutter/material.dart';

import '../l10n/textos.dart';
import '../state/servicios.dart';
import '../widgets/comunes.dart';

class _Paso {
  const _Paso(this.icono, this.titulo, this.texto);

  final IconData icono;
  final String Function(Textos) titulo;
  final String Function(Textos) texto;
}

final _pasos = <_Paso>[
  _Paso(Icons.checklist_rounded, (t) => t.tut1Titulo, (t) => t.tut1Texto), // RF-04..RF-09
  _Paso(Icons.notifications_active_outlined, (t) => t.tut2Titulo, (t) => t.tut2Texto), // RF-12/13
  _Paso(Icons.local_fire_department_outlined, (t) => t.tut3Titulo, (t) => t.tut3Texto), // RF-21
  _Paso(Icons.flag_outlined, (t) => t.tut4Titulo, (t) => t.tut4Texto), // RF-28/29
];

/// Tutorial breve de primer uso (4 pasos). "Omitir" y "Comenzar" lo dan por visto: se guarda en el
/// servidor y no vuelve a aparecer. Si falla el guardado se avisa y se puede reintentar.
class TutorialScreen extends StatefulWidget {
  const TutorialScreen({super.key});

  @override
  State<TutorialScreen> createState() => _TutorialScreenState();
}

class _TutorialScreenState extends State<TutorialScreen> {
  final _controlador = PageController();
  int _indice = 0;
  bool _guardando = false;

  bool get _esUltimo => _indice == _pasos.length - 1;

  @override
  void dispose() {
    _controlador.dispose();
    super.dispose();
  }

  void _siguiente() {
    if (_esUltimo) {
      _terminar();
    } else {
      _controlador.nextPage(duration: const Duration(milliseconds: 280), curve: Curves.easeOut);
    }
  }

  Future<void> _terminar() async {
    if (_guardando) return;
    setState(() => _guardando = true);
    try {
      await authController.completarTutorial(); // main.dart pasa solo al dashboard
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
              // Barra superior: progreso "1/4" y Omitir.
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 12, 12, 0),
                child: Row(children: [
                  Semantics(
                    label: t.pasoDeTotal(_indice + 1, _pasos.length),
                    child: ExcludeSemantics(
                      child: Text('${_indice + 1}/${_pasos.length}',
                          style: tema.textTheme.titleSmall?.copyWith(color: e.onSurfaceVariant)),
                    ),
                  ),
                  const Spacer(),
                  // El espacio se conserva en el último paso para que nada salte de lugar.
                  Visibility(
                    visible: !_esUltimo,
                    maintainSize: true,
                    maintainAnimation: true,
                    maintainState: true,
                    child: TextButton(
                      onPressed: _guardando ? null : _terminar,
                      child: Text(t.omitir),
                    ),
                  ),
                ]),
              ),
              Expanded(
                child: PageView.builder(
                  controller: _controlador,
                  itemCount: _pasos.length,
                  onPageChanged: (i) => setState(() => _indice = i),
                  itemBuilder: (context, i) => _PaginaPaso(paso: _pasos[i]),
                ),
              ),
              // Indicador de puntos.
              Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                for (var i = 0; i < _pasos.length; i++)
                  AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    margin: const EdgeInsets.symmetric(horizontal: 4),
                    width: i == _indice ? 24 : 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: i == _indice ? e.primary : e.outlineVariant,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
              ]),
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
                child: SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed: _guardando ? null : _siguiente,
                    child: _guardando
                        ? const SizedBox(
                            height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                        : Text(_esUltimo ? t.comenzar : t.siguiente),
                  ),
                ),
              ),
            ]),
          ),
        ),
      ),
    );
  }
}

class _PaginaPaso extends StatelessWidget {
  const _PaginaPaso({required this.paso});

  final _Paso paso;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final e = tema.colorScheme;
    final t = context.t;
    return LayoutBuilder(builder: (context, c) {
      // En pantallas bajas (o con fuente grande) la ilustración se achica en lugar de desbordar.
      final lado = (c.maxHeight * 0.38).clamp(110.0, 200.0);
      return SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 32),
        child: ConstrainedBox(
          constraints: BoxConstraints(minHeight: c.maxHeight),
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
            ExcludeSemantics(
              child: SizedBox(
                width: lado + 24,
                height: lado + 24,
                child: Stack(alignment: Alignment.center, children: [
                  Positioned(
                    right: 0,
                    top: 0,
                    child: Container(
                        width: lado * 0.3,
                        height: lado * 0.3,
                        decoration: BoxDecoration(color: e.primary.withValues(alpha: 0.25), shape: BoxShape.circle)),
                  ),
                  Positioned(
                    left: 0,
                    bottom: 8,
                    child: Container(
                        width: lado * 0.18,
                        height: lado * 0.18,
                        decoration: BoxDecoration(color: e.tertiary.withValues(alpha: 0.35), shape: BoxShape.circle)),
                  ),
                  Container(
                    width: lado,
                    height: lado,
                    decoration: BoxDecoration(color: e.tertiaryContainer, shape: BoxShape.circle),
                    child: Icon(paso.icono, size: lado * 0.46, color: e.onTertiaryContainer),
                  ),
                ]),
              ),
            ),
            const SizedBox(height: 32),
            Semantics(
              header: true,
              child: Text(paso.titulo(t),
                  textAlign: TextAlign.center, style: tema.textTheme.headlineSmall),
            ),
            const SizedBox(height: 12),
            Text(paso.texto(t),
                textAlign: TextAlign.center,
                style: tema.textTheme.bodyLarge?.copyWith(color: e.onSurfaceVariant)),
          ]),
        ),
      );
    });
  }
}
