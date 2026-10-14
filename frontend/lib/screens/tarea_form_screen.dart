import 'package:flutter/material.dart';

import '../l10n/textos.dart';
import '../models/modelos.dart';
import '../state/servicios.dart';
import '../theme/app_theme.dart';
import '../widgets/comunes.dart';

const _valorNuevaMateria = '__nueva__';

/// RF-04 (crear) y RF-05 (editar). Si recibe [tarea], edita; si no, crea.
class TareaFormScreen extends StatefulWidget {
  const TareaFormScreen({super.key, this.tarea});

  final Tarea? tarea;

  @override
  State<TareaFormScreen> createState() => _TareaFormScreenState();
}

class _TareaFormScreenState extends State<TareaFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _titulo;
  late final TextEditingController _descripcion;
  late String _prioridad;
  late DateTime _fechaLimite;
  late String _estado;
  String? _idMateria;
  List<Materia> _materias = [];
  bool _guardando = false;

  Tarea? get _original => widget.tarea;
  bool get _editando => _original != null;

  @override
  void initState() {
    super.initState();
    final t = _original;
    _titulo = TextEditingController(text: t?.titulo ?? '');
    _descripcion = TextEditingController(text: t?.descripcion ?? '');
    _prioridad = t?.prioridad ?? 'MEDIA';
    _fechaLimite = t?.fechaLimite ?? DateTime.now().add(const Duration(days: 1));
    _estado = t?.estado ?? 'PENDIENTE';
    _idMateria = t?.idMateria;
    _cargarMaterias();
  }

  @override
  void dispose() {
    _titulo.dispose();
    _descripcion.dispose();
    super.dispose();
  }

  Future<void> _cargarMaterias() async {
    try {
      final materias = await materiasRepo.listar();
      if (mounted) setState(() => _materias = materias);
    } catch (e) {
      if (mounted) mostrarError(context, e);
    }
  }

  Future<void> _elegirFechaHora() async {
    final hoy = DateTime.now();
    // Los límites siempre incluyen la fecha actual de la tarea, para que el selector no falle
    // con tareas muy antiguas o muy lejanas.
    final primera = _fechaLimite.isBefore(DateTime(2020)) ? _fechaLimite : DateTime(2020);
    final ultima = _fechaLimite.isAfter(hoy.add(const Duration(days: 365 * 5)))
        ? _fechaLimite
        : hoy.add(const Duration(days: 365 * 5));
    final dia = await showDatePicker(
      context: context,
      initialDate: _fechaLimite,
      firstDate: primera,
      lastDate: ultima,
      helpText: context.t.fechaLimite,
    );
    if (dia == null || !mounted) return;
    final hora = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_fechaLimite),
      helpText: context.t.horaLimite,
    );
    if (hora == null || !mounted) return;
    setState(() => _fechaLimite = DateTime(dia.year, dia.month, dia.day, hora.hour, hora.minute));
  }

  Future<void> _crearMateriaRapida() async {
    final controlador = TextEditingController();
    final nombre = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(ctx.t.nuevaMateria),
        content: TextField(
          controller: controlador,
          autofocus: true,
          textCapitalization: TextCapitalization.sentences,
          decoration: decoracionCampo(ctx, ctx.t.nombreDeLaMateria),
          onSubmitted: (v) => Navigator.pop(ctx, v.trim()),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: Text(ctx.t.cancelar)),
          FilledButton(
              onPressed: () => Navigator.pop(ctx, controlador.text.trim()),
              child: Text(ctx.t.crear)),
        ],
      ),
    );
    controlador.dispose();
    if (nombre == null || nombre.isEmpty || !mounted) return;
    try {
      final materia = await materiasRepo.crear(nombre);
      await _cargarMaterias();
      if (mounted) setState(() => _idMateria = materia.id);
    } catch (e) {
      if (mounted) mostrarError(context, e);
    }
  }

  Future<void> _guardar() async {
    if (_guardando || !_formKey.currentState!.validate()) return;

    final original = _original;
    final fechaCambio = original == null || !_fechaLimite.isAtSameMomentAs(original.fechaLimite);
    // Solo se valida la fecha al crear o cuando el usuario la cambia (el backend aplica la misma regla).
    if (fechaCambio && !_fechaLimite.isAfter(DateTime.now())) {
      mostrarMensaje(context, context.t.fechaDebeSerFutura);
      return;
    }

    setState(() => _guardando = true);
    try {
      final titulo = _titulo.text.trim();
      final descripcion = _descripcion.text.trim();
      if (original == null) {
        await tareasRepo.crear(
          titulo: titulo,
          descripcion: descripcion,
          fechaLimite: _fechaLimite,
          prioridad: _prioridad,
          idMateria: _idMateria,
        );
      } else {
        // Se envía SOLO lo que cambió.
        final cambios = <String, dynamic>{};
        if (titulo != original.titulo) cambios['titulo'] = titulo;
        if (descripcion != (original.descripcion ?? '')) {
          cambios['descripcion'] = descripcion.isEmpty ? null : descripcion;
        }
        if (_prioridad != original.prioridad) cambios['prioridad'] = _prioridad;
        if (fechaCambio) cambios['fecha_limite'] = _fechaLimite.toUtc().toIso8601String();
        if (_idMateria != original.idMateria) cambios['id_materia'] = _idMateria;
        if (_estado != original.estado) cambios['estado'] = _estado;
        if (cambios.isNotEmpty) await tareasRepo.actualizar(original.id, cambios);
      }
      if (mounted) Navigator.of(context).pop();
    } catch (e) {
      if (mounted) mostrarError(context, e);
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final vencidaOriginal = _original?.vencida ?? false;
    return Pantalla(
      appBar: barraSimple(context, _editando ? context.t.editarTarea : context.t.nuevaTarea),
      body: SafeArea(
        child: ContenidoCentrado(
          child: Form(
            key: _formKey,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
              children: [
                TextFormField(
                  controller: _titulo,
                  maxLength: 150,
                  textCapitalization: TextCapitalization.sentences,
                  textInputAction: TextInputAction.next,
                  // El contador de caracteres se oculta para mantener el diseño limpio;
                  // el límite de 150 se sigue aplicando.
                  buildCounter: (context,
                          {required currentLength, required isFocused, required maxLength}) =>
                      null,
                  decoration: decoracionCampo(context, context.t.titulo),
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? context.t.tituloObligatorio : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _descripcion,
                  maxLines: 3,
                  textCapitalization: TextCapitalization.sentences,
                  decoration: decoracionCampo(context, context.t.descripcionOpcional),
                ),
                const SizedBox(height: 24),
                Text(context.t.prioridadEtiqueta, style: tema.textTheme.labelLarge),
                const SizedBox(height: 8),
                Row(children: [
                  for (final p in codigosPrioridad) ...[
                    if (p != codigosPrioridad.first) const SizedBox(width: 8),
                    Expanded(
                      child: _OpcionPrioridad(
                        valor: p,
                        etiqueta: context.t.prioridad(p),
                        elegida: _prioridad == p,
                        onTap: () => setState(() => _prioridad = p),
                      ),
                    ),
                  ],
                ]),
                const SizedBox(height: 24),
                InkWell(
                  borderRadius: BorderRadius.circular(20),
                  onTap: _elegirFechaHora,
                  child: InputDecorator(
                    decoration: decoracionCampo(
                      context,
                      context.t.fechaYHoraLimite,
                      sufijo: const Icon(Icons.event_outlined),
                    ),
                    child: Text(context.t.fechaHora(_fechaLimite)),
                  ),
                ),
                const SizedBox(height: 16),
                CampoSelector<String?>(
                  etiqueta: context.t.materiaOpcional,
                  valor: _idMateria,
                  opciones: [
                    Opcion<String?>(null, context.t.sinMateria),
                    for (final m in _materias) Opcion<String?>(m.id, m.nombre),
                    Opcion<String?>(_valorNuevaMateria, context.t.masNuevaMateria),
                  ],
                  onChanged: (v) {
                    if (v == _valorNuevaMateria) {
                      _crearMateriaRapida();
                    } else {
                      setState(() => _idMateria = v);
                    }
                  },
                ),
                if (_editando) ...[
                  const SizedBox(height: 16),
                  CampoSelector<String>(
                    etiqueta: context.t.estadoEtiqueta,
                    valor: _estado,
                    opciones: [
                      // "Vencida" no se puede elegir: solo se muestra si la tarea ya lo está.
                      if (vencidaOriginal) Opcion<String>('VENCIDA', context.t.vencidaAutomatico),
                      for (final c in codigosEstadoEditable) Opcion<String>(c, context.t.estado(c)),
                    ],
                    onChanged: (v) => setState(() => _estado = v),
                  ),
                ],
                const SizedBox(height: 32),
                FilledButton(
                  onPressed: _guardando ? null : _guardar,
                  child: _guardando
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2))
                      : Text(_editando ? context.t.guardarCambios : context.t.crearTarea),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Opción de prioridad en forma de píldora con borde de color (Baja / Media / Alta).
class _OpcionPrioridad extends StatelessWidget {
  const _OpcionPrioridad({
    required this.valor,
    required this.etiqueta,
    required this.elegida,
    required this.onTap,
  });

  final String valor;
  final String etiqueta;
  final bool elegida;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final e = Theme.of(context).colorScheme;
    final estilo = estiloPrioridad(context, valor);
    return Semantics(
      button: true,
      selected: elegida,
      child: Material(
        color: elegida ? estilo.fondo : e.surfaceContainerLowest,
        shape: StadiumBorder(
          side: BorderSide(
            color: elegida ? estilo.borde : e.outlineVariant,
            width: elegida ? 1.6 : 1,
          ),
        ),
        child: InkWell(
          customBorder: const StadiumBorder(),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 13),
            child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              Container(
                width: 7,
                height: 7,
                decoration: BoxDecoration(color: estilo.punto, shape: BoxShape.circle),
              ),
              const SizedBox(width: 8),
              Text(etiqueta,
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      color: elegida ? estilo.texto : e.onSurface,
                      fontWeight: elegida ? FontWeight.w700 : FontWeight.w600)),
            ]),
          ),
        ),
      ),
    );
  }
}
