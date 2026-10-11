import '../models/modelos.dart';
import 'api_client.dart';

String _dosDigitos(int n) => n.toString().padLeft(2, '0');

/// El backend espera los días como AAAA-MM-DD.
String _soloFecha(DateTime d) => '${d.year}-${_dosDigitos(d.month)}-${_dosDigitos(d.day)}';

/// RF-04 a RF-09 y RF-11. Cada método corresponde a un endpoint de /tareas.
class TareasRepository {
  TareasRepository(this._api);

  final ApiClient _api;

  /// RF-07: todos los filtros son opcionales y se combinan.
  Future<List<Tarea>> listar({
    String? estado,
    String? prioridad,
    String? idMateria,
    DateTime? desde,
    DateTime? hasta,
  }) async {
    final query = <String, String>{'limite': '200'};
    if (estado != null) query['estado'] = estado;
    if (prioridad != null) query['prioridad'] = prioridad;
    if (idMateria != null) query['id_materia'] = idMateria;
    if (desde != null) query['fecha_desde'] = _soloFecha(desde);
    if (hasta != null) query['fecha_hasta'] = _soloFecha(hasta);
    final datos = await _api.get('/tareas', query: query) as List<dynamic>;
    return datos.map((e) => Tarea.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Tarea> obtener(String id) async =>
      Tarea.fromJson(await _api.get('/tareas/$id') as Map<String, dynamic>);

  Future<Tarea> crear({
    required String titulo,
    String? descripcion,
    required DateTime fechaLimite,
    required String prioridad,
    String? idMateria,
  }) async {
    final cuerpo = <String, dynamic>{
      'titulo': titulo,
      'fecha_limite': fechaLimite.toUtc().toIso8601String(),
      'prioridad': prioridad,
    };
    if (descripcion != null && descripcion.isNotEmpty) cuerpo['descripcion'] = descripcion;
    if (idMateria != null) cuerpo['id_materia'] = idMateria;
    return Tarea.fromJson(await _api.post('/tareas', body: cuerpo) as Map<String, dynamic>);
  }

  /// RF-05: se envían SOLO los campos que cambiaron (el backend valida la fecha límite
  /// únicamente cuando se modifica).
  Future<Tarea> actualizar(String id, Map<String, dynamic> cambios) async =>
      Tarea.fromJson(await _api.patch('/tareas/$id', body: cambios) as Map<String, dynamic>);

  /// RF-06: la confirmación con el usuario se pide en la pantalla ANTES de llamar a este método.
  Future<void> eliminar(String id) => _api.delete('/tareas/$id');
}

/// RF-10.
class MateriasRepository {
  MateriasRepository(this._api);

  final ApiClient _api;

  Future<List<Materia>> listar() async {
    final datos = await _api.get('/materias') as List<dynamic>;
    return datos.map((e) => Materia.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Materia> crear(String nombre) async =>
      Materia.fromJson(await _api.post('/materias', body: {'nombre': nombre}) as Map<String, dynamic>);
}
