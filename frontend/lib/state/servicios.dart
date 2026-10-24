import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../api/api_client.dart';
import '../api/repositorios.dart';
import 'auth_controller.dart';
import 'idioma_controller.dart';
import 'tema_controller.dart';

/// Instancias únicas usadas por toda la app (versión sencilla a propósito:
/// más adelante se puede migrar a Provider/Riverpod sin cambiar las pantallas de forma drástica).
final apiClient = ApiClient();
final idiomaController = IdiomaController(const FlutterSecureStorage());
final authController = AuthController(apiClient, idiomaController);
final tareasRepo = TareasRepository(apiClient);
final materiasRepo = MateriasRepository(apiClient);
final temaController = TemaController(const FlutterSecureStorage());
