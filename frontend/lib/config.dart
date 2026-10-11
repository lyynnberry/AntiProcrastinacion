import 'package:flutter/foundation.dart';

const _urlDefinida = String.fromEnvironment('API_BASE_URL');

/// URL base del backend (sin "/" al final).
///
/// Si no se indica otra, se elige según dónde corre la app:
/// - Emulador Android: http://10.0.2.2:8000 (10.0.2.2 es el "localhost" de tu computadora).
/// - Chrome, iOS (simulador) y escritorio: http://localhost:8000.
/// - Teléfono físico: usa la IP de tu computadora en la red Wi-Fi, ej. http://192.168.1.50:8000
///
/// Se puede cambiar al ejecutar:  flutter run --dart-define=API_BASE_URL=http://192.168.1.50:8000
String get apiBaseUrl {
  var url = _urlDefinida;
  if (url.isEmpty) {
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      url = 'http://10.0.2.2:8000';
    } else {
      url = 'http://localhost:8000';
    }
  }
  return url.endsWith('/') ? url.substring(0, url.length - 1) : url;
}
