import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../models/modelos.dart';
import '../state/servicios.dart';

/// Avatar circular del usuario: su foto si tiene y, si no (o mientras carga / si falla), sus iniciales.
///
/// La foto solo se puede pedir con la sesión del dueño, por eso se descarga con el cliente HTTP de la
/// app y se guarda en memoria. La clave de la caché incluye `fotoActualizadaEn`: al cambiar o borrar la
/// foto la clave cambia y se vuelve a pedir.
class AvatarUsuario extends StatefulWidget {
  const AvatarUsuario({super.key, required this.usuario, this.radio = 24});

  final Usuario usuario;
  final double radio;

  static final Map<String, Uint8List> _cache = {};

  /// Vacía la caché (al cerrar sesión, para que la foto de una cuenta no aparezca en otra).
  static void limpiarCache() => _cache.clear();

  @override
  State<AvatarUsuario> createState() => _AvatarUsuarioState();
}

class _AvatarUsuarioState extends State<AvatarUsuario> {
  Uint8List? _bytes;
  String? _claveCargando;

  String? get _clave {
    final u = widget.usuario;
    return u.fotoActualizadaEn == null
        ? null
        : '${u.id}@${u.fotoActualizadaEn!.microsecondsSinceEpoch}';
  }

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  @override
  void didUpdateWidget(AvatarUsuario anterior) {
    super.didUpdateWidget(anterior);
    if (_clave != _claveCargando) _cargar();
  }

  Future<void> _cargar() async {
    final clave = _clave;
    _claveCargando = clave;
    if (clave == null) {
      setState(() => _bytes = null);
      return;
    }
    final enCache = AvatarUsuario._cache[clave];
    if (enCache != null) {
      setState(() => _bytes = enCache);
      return;
    }
    try {
      final datos = await authController.descargarFoto();
      if (!mounted || _claveCargando != clave) return; // llegó otra versión mientras tanto
      if (datos == null) {
        setState(() => _bytes = null);
        return;
      }
      final bytes = Uint8List.fromList(datos);
      AvatarUsuario._cache[clave] = bytes;
      setState(() => _bytes = bytes);
    } catch (_) {
      if (mounted && _claveCargando == clave) setState(() => _bytes = null); // quedan las iniciales
    }
  }

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final e = tema.colorScheme;
    final u = widget.usuario;
    final tamano = widget.radio * 2;
    final iniciales = Center(
      child: Text(
        u.iniciales,
        style: (widget.radio >= 36 ? tema.textTheme.headlineSmall : tema.textTheme.titleMedium)
            ?.copyWith(color: e.onTertiaryContainer),
      ),
    );
    return ExcludeSemantics(
      child: Container(
        width: tamano,
        height: tamano,
        clipBehavior: Clip.antiAlias,
        decoration: BoxDecoration(color: e.tertiaryContainer, shape: BoxShape.circle),
        child: _bytes == null
            ? iniciales
            : Image.memory(
                _bytes!,
                fit: BoxFit.cover,
                gaplessPlayback: true,
                errorBuilder: (_, __, ___) => iniciales,
              ),
      ),
    );
  }
}
