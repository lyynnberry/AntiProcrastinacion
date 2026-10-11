import 'dart:async';
import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import '../config.dart';

/// Error devuelto por el backend (formato {"error": {"codigo", "mensaje", "detalles"}}).
class ApiException implements Exception {
  ApiException(this.statusCode, this.codigo, this.mensaje);

  final int statusCode;
  final String codigo;
  final String mensaje;

  @override
  String toString() => mensaje;
}

/// Cliente HTTP único. Se encarga de:
/// - agregar el token de acceso a cada petición,
/// - guardar el refresh token en almacenamiento seguro (RF-03: mantener sesión),
/// - renovar el acceso automáticamente cuando el backend responde 401,
/// - avisar ([alExpirarSesion]) cuando la sesión ya no se puede recuperar.
class ApiClient {
  ApiClient({http.Client? httpClient, FlutterSecureStorage? storage})
      : _http = httpClient ?? http.Client(),
        _storage = storage ?? const FlutterSecureStorage();

  static const _claveRefresh = 'refresh_token';
  static const _tiempoMaximo = Duration(seconds: 20);

  final http.Client _http;
  final FlutterSecureStorage _storage;
  String? _accessToken;
  String? _refreshToken;
  Future<bool>? _renovacionEnCurso;

  /// Se ejecuta cuando el refresh token fue rechazado y la sesión se perdió.
  void Function()? alExpirarSesion;

  bool get tieneSesionGuardada => _refreshToken != null;

  Future<void> cargarSesionGuardada() async {
    try {
      _refreshToken = await _storage.read(key: _claveRefresh);
    } catch (_) {
      // Si el almacenamiento seguro falla, se trata como "sin sesión guardada".
      _refreshToken = null;
    }
  }

  Future<void> guardarTokens(Map<String, dynamic> tokens) async {
    _accessToken = tokens['access_token'] as String;
    _refreshToken = tokens['refresh_token'] as String;
    await _storage.write(key: _claveRefresh, value: _refreshToken);
  }

  Future<void> limpiarTokens() async {
    _accessToken = null;
    _refreshToken = null;
    try {
      await _storage.delete(key: _claveRefresh);
    } catch (_) {
      // Los tokens en memoria ya se descartaron; no hay más que hacer.
    }
  }

  /// Cambia el refresh token por un nuevo acceso. Devuelve false si no se pudo.
  ///
  /// El refresh token rota en cada uso (ver decisiones del proyecto). Por eso, si varias
  /// peticiones reciben 401 a la vez, todas comparten UNA sola renovación: de lo contrario la
  /// segunda usaría un token ya revocado y cerraría la sesión sin motivo.
  Future<bool> renovar() {
    return _renovacionEnCurso ??= _renovar().whenComplete(() => _renovacionEnCurso = null);
  }

  Future<bool> _renovar() async {
    final refresh = _refreshToken;
    if (refresh == null) return false;
    try {
      final tokens = await post('/auth/refresh', body: {'refresh_token': refresh}, auth: false);
      await guardarTokens(tokens as Map<String, dynamic>);
      return true;
    } on ApiException catch (e) {
      // Solo un 401 significa "sesión inválida". Un corte de red o un 500 no deben cerrarla.
      if (e.statusCode == 401) await limpiarTokens();
      return false;
    }
  }

  Future<dynamic> get(String ruta, {Map<String, String>? query}) =>
      _enviar('GET', ruta, query: query);

  Future<dynamic> post(String ruta, {Object? body, bool auth = true}) =>
      _enviar('POST', ruta, body: body, auth: auth);

  Future<dynamic> patch(String ruta, {Object? body}) => _enviar('PATCH', ruta, body: body);

  Future<void> delete(String ruta) async {
    await _enviar('DELETE', ruta);
  }

  Future<dynamic> _enviar(
    String metodo,
    String ruta, {
    Map<String, String>? query,
    Object? body,
    bool auth = true,
    bool puedeReintentar = true,
  }) async {
    final uri = Uri.parse('$apiBaseUrl$ruta').replace(queryParameters: query);
    final peticion = http.Request(metodo, uri)..headers['Accept'] = 'application/json';
    if (auth && _accessToken != null) {
      peticion.headers['Authorization'] = 'Bearer $_accessToken';
    }
    if (body != null) {
      peticion.headers['Content-Type'] = 'application/json';
      peticion.body = jsonEncode(body);
    }

    http.Response respuesta;
    try {
      final flujo = await _http.send(peticion).timeout(_tiempoMaximo);
      respuesta = await http.Response.fromStream(flujo).timeout(_tiempoMaximo);
    } on TimeoutException {
      throw ApiException(0, 'SIN_CONEXION', 'El servidor tardó demasiado en responder.');
    } on http.ClientException {
      throw ApiException(0, 'SIN_CONEXION', 'No se pudo conectar con el servidor.');
    }

    if (respuesta.statusCode == 401 && auth) {
      // Acceso vencido: se intenta renovar UNA vez y se repite la petición.
      if (puedeReintentar && _refreshToken != null && await renovar()) {
        return _enviar(metodo, ruta,
            query: query, body: body, auth: auth, puedeReintentar: false);
      }
      // Sin refresh token (rechazado o inexistente) la sesión se perdió: se avisa a la app.
      if (_refreshToken == null) alExpirarSesion?.call();
    }

    if (respuesta.statusCode >= 200 && respuesta.statusCode < 300) {
      if (respuesta.bodyBytes.isEmpty) return null;
      return jsonDecode(utf8.decode(respuesta.bodyBytes));
    }
    throw _construirError(respuesta);
  }

  ApiException _construirError(http.Response r) {
    try {
      final cuerpo = jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
      final error = cuerpo['error'] as Map<String, dynamic>;
      var mensaje = error['mensaje'] as String;
      final detalles = error['detalles'];
      if (detalles is List && detalles.isNotEmpty) {
        final lineas = detalles
            .whereType<Map<String, dynamic>>()
            .map((d) => '• ${d['campo']}: ${d['mensaje']}');
        mensaje = [mensaje, ...lineas].join('\n');
      }
      return ApiException(r.statusCode, error['codigo'] as String, mensaje);
    } catch (_) {
      return ApiException(r.statusCode, 'ERROR', 'Error inesperado (${r.statusCode}).');
    }
  }
}
