import 'package:flutter/foundation.dart';

import '../api/api_client.dart';
import '../models/modelos.dart';
import '../widgets/avatar.dart';
import 'idioma_controller.dart';

enum EstadoSesion { iniciando, sinSesion, conSesion }

/// RF-01, RF-02, RF-03: registro, inicio de sesión y sesión persistente.
class AuthController extends ChangeNotifier {
  AuthController(this._api, this._idioma) {
    _api.alExpirarSesion = _sesionExpirada;
  }

  final ApiClient _api;
  final IdiomaController _idioma;

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
    final idiomaLocal = _idioma.codigo; // el que la persona venía usando en este dispositivo
    await iniciarSesion(email, password);
    // La cuenta nueva nace en español; si el dispositivo ya estaba en otro idioma, se respeta.
    if (usuario != null && usuario!.idioma != idiomaLocal) {
      try {
        await cambiarIdioma(idiomaLocal);
      } on ApiException {
        // No es crítico: queda el idioma del servidor y se puede cambiar desde el perfil.
        await _idioma.aplicar(usuario!.idioma);
      }
    }
  }

  Future<void> cerrarSesion() async {
    try {
      await _api.post('/auth/logout');
    } on ApiException {
      // Aunque el servidor no responda, la sesión local se cierra igualmente.
    }
    await _api.limpiarTokens();
    AvatarUsuario.limpiarCache();
    usuario = null;
    sesionExpirada = false;
    _cambiarEstado(EstadoSesion.sinSesion);
  }

  /// El cliente HTTP perdió la sesión (refresh token rechazado): se vuelve al login.
  void _sesionExpirada() {
    if (estado != EstadoSesion.conSesion) return;
    AvatarUsuario.limpiarCache();
    usuario = null;
    sesionExpirada = true;
    _cambiarEstado(EstadoSesion.sinSesion);
  }

  Future<void> _cargarPerfil() async {
    usuario = Usuario.fromJson(await _api.get('/usuarios/me') as Map<String, dynamic>);
    await _idioma.aplicar(usuario!.idioma); // el idioma guardado en el servidor manda
    _cambiarEstado(EstadoSesion.conSesion);
  }

  /// Vuelve a pedir el perfil al servidor (por ejemplo, tras completar un paso del flujo inicial).
  Future<void> recargarPerfil() async {
    usuario = Usuario.fromJson(await _api.get('/usuarios/me') as Map<String, dynamic>);
    notifyListeners();
  }

  void _usarPerfil(dynamic json) {
    usuario = Usuario.fromJson(json as Map<String, dynamic>);
    notifyListeners();
  }

  // ───────────── Perfil, personalización y tutorial ─────────────

  Future<void> actualizarNombre(String nombre) async =>
      _usarPerfil(await _api.patch('/usuarios/me', body: {'nombre': nombre}));

  /// Cambia el idioma al instante y lo guarda en el servidor; si falla, vuelve al anterior.
  Future<void> cambiarIdioma(String nuevo) async {
    final anterior = _idioma.codigo;
    await _idioma.aplicar(nuevo);
    try {
      _usarPerfil(await _api.patch('/usuarios/me', body: {'idioma': nuevo}));
    } catch (_) {
      await _idioma.aplicar(anterior);
      rethrow;
    }
  }

  Future<PreferenciaRecordatorios> obtenerPreferencia() async => PreferenciaRecordatorios.fromJson(
      await _api.get('/usuarios/me/preferencia-notificacion') as Map<String, dynamic>);

  /// Guarda la preferencia. La primera vez, el servidor también marca completa la personalización.
  Future<void> guardarPreferencia(String perfil, {bool activas = true}) async {
    await _api.put('/usuarios/me/preferencia-notificacion',
        body: {'perfil_recordatorios': perfil, 'notificaciones_activas': activas});
    await recargarPerfil();
  }

  Future<void> completarTutorial() async =>
      _usarPerfil(await _api.post('/usuarios/me/tutorial/completar'));

  Future<void> subirFoto(List<int> bytes, String nombreArchivo, String tipoMime) async =>
      _usarPerfil(await _api.subirArchivo('/usuarios/me/foto',
          campo: 'archivo', bytes: bytes, nombreArchivo: nombreArchivo, tipoMime: tipoMime));

  Future<void> borrarFoto() async {
    await _api.delete('/usuarios/me/foto');
    await recargarPerfil();
  }

  Future<List<int>?> descargarFoto() => _api.obtenerBytes('/usuarios/me/foto');

  void _cambiarEstado(EstadoSesion nuevo) {
    estado = nuevo;
    notifyListeners();
  }
}
