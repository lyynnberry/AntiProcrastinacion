import 'package:flutter/foundation.dart';

import '../api/api_client.dart';
import '../models/modelos.dart';

enum EstadoSesion { iniciando, sinSesion, conSesion }

/// RF-01, RF-02, RF-03: registro, inicio de sesión y sesión persistente.
class AuthController extends ChangeNotifier {
  AuthController(this._api) {
    _api.alExpirarSesion = _sesionExpirada;
  }

  final ApiClient _api;

  EstadoSesion estado = EstadoSesion.iniciando;
  Usuario? usuario;

  /// true si la sesión se cerró porque el servidor ya no la acepta (para avisar en el login).
  bool sesionExpirada = false;

  /// Al abrir la app: si hay una sesión guardada y sigue vigente, entra sin pedir contraseña (RF-03).
  Future<void> iniciar() async {
    await _api.cargarSesionGuardada();
    if (_api.tieneSesionGuardada && await _api.renovar()) {
      try {
        await _cargarPerfil();
        return;
      } on ApiException catch (e) {
        // Solo se descarta la sesión si el servidor la rechaza; un corte de red no debe cerrarla.
        if (e.statusCode == 401 || e.statusCode == 403) await _api.limpiarTokens();
      }
    }
    _cambiarEstado(EstadoSesion.sinSesion);
  }

  Future<void> iniciarSesion(String email, String password) async {
    final tokens = await _api.post('/auth/login',
        body: {'email': email, 'password': password}, auth: false);
    await _api.guardarTokens(tokens as Map<String, dynamic>);
    sesionExpirada = false;
    await _cargarPerfil();
  }

  Future<void> registrar({required String email, required String password, String? nombre}) async {
    await _api.post('/auth/registro',
        body: {
          'email': email,
          'password': password,
          if (nombre != null && nombre.isNotEmpty) 'nombre': nombre,
        },
        auth: false);
    await iniciarSesion(email, password);
  }

  Future<void> cerrarSesion() async {
    try {
      await _api.post('/auth/logout');
    } on ApiException {
      // Aunque el servidor no responda, la sesión local se cierra igualmente.
    }
    await _api.limpiarTokens();
    usuario = null;
    sesionExpirada = false;
    _cambiarEstado(EstadoSesion.sinSesion);
  }

  /// El cliente HTTP perdió la sesión (refresh token rechazado): se vuelve al login.
  void _sesionExpirada() {
    if (estado != EstadoSesion.conSesion) return;
    usuario = null;
    sesionExpirada = true;
    _cambiarEstado(EstadoSesion.sinSesion);
  }

  Future<void> _cargarPerfil() async {
    usuario = Usuario.fromJson(await _api.get('/usuarios/me') as Map<String, dynamic>);
    _cambiarEstado(EstadoSesion.conSesion);
  }

  void _cambiarEstado(EstadoSesion nuevo) {
    estado = nuevo;
    notifyListeners();
  }
}
