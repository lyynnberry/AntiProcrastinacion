import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Tema de la app. Por defecto es el claro; la elección del usuario se recuerda.
class TemaController extends ChangeNotifier {
  TemaController(this._storage);

  static const _clave = 'tema';

  final FlutterSecureStorage _storage;
  ThemeMode modo = ThemeMode.light;

  Future<void> cargar() async {
    try {
      final guardado = await _storage.read(key: _clave).timeout(const Duration(seconds: 2));
      modo = switch (guardado) {
        'dark' => ThemeMode.dark,
        'system' => ThemeMode.system,
        _ => ThemeMode.light,
      };
    } catch (_) {
      modo = ThemeMode.light; // si no se puede leer, se queda el tema claro
    }
  }

  Future<void> cambiar(ThemeMode nuevo) async {
    if (nuevo == modo) return;
    modo = nuevo;
    notifyListeners();
    try {
      await _storage.write(key: _clave, value: nuevo.name);
    } catch (_) {
      // No guardar la preferencia no es grave: solo se perderá al cerrar la app.
    }
  }
}
