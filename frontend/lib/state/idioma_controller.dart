import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../l10n/textos.dart';

/// Idioma de la app. La fuente de verdad es el servidor (guardado por usuario); aquí se guarda además
/// una copia local para que el login y el arranque salgan ya en el último idioma usado.
class IdiomaController extends ChangeNotifier {
  IdiomaController(this._storage);

  static const _clave = 'idioma';

  final FlutterSecureStorage _storage;
  String codigo = idiomaPorDefecto;

  Locale get locale => Locale(codigo);

  Future<void> cargar() async {
    try {
      final guardado = await _storage.read(key: _clave).timeout(const Duration(seconds: 2));
      if (guardado != null && idiomasSoportados.contains(guardado)) codigo = guardado;
    } catch (_) {
      codigo = idiomaPorDefecto;
    }
  }

  /// Aplica el idioma (inmediato) y lo recuerda en el dispositivo.
  Future<void> aplicar(String nuevo) async {
    if (!idiomasSoportados.contains(nuevo)) return;
    if (nuevo != codigo) {
      codigo = nuevo;
      notifyListeners();
    }
    try {
      await _storage.write(key: _clave, value: nuevo);
    } catch (_) {
      // Sin copia local: el idioma se recupera del servidor al iniciar sesión.
    }
  }
}
