/// Modelos que reflejan las respuestas del backend.

/// Prioridades (RF-09) y estados (RF-05) tal como los usa la API.
const prioridades = {'BAJA': 'Baja', 'MEDIA': 'Media', 'ALTA': 'Alta'};

/// Estados que el usuario puede elegir. "VENCIDA" lo calcula el backend; no se puede establecer.
const estadosEditables = {
  'PENDIENTE': 'Pendiente',
  'EN_PROGRESO': 'En progreso',
  'COMPLETADA': 'Completada',
};

String etiquetaEstado(String estado) =>
    estadosEditables[estado] ?? (estado == 'VENCIDA' ? 'Vencida' : estado);

class Usuario {
  Usuario({required this.id, required this.email, this.nombre, required this.zonaHoraria});

  final String id;
  final String email;
  final String? nombre;
  final String zonaHoraria;

  /// Nombre para saludar: el nombre registrado o, si no hay, la parte del correo antes de la "@".
  String get nombreParaSaludo {
    final n = nombre?.trim() ?? '';
    return n.isNotEmpty ? n : email.split('@').first;
  }

  /// Iniciales para el avatar (1 o 2 letras).
  String get iniciales {
    String primera(String texto) => String.fromCharCode(texto.runes.first).toUpperCase();
    final partes =
        nombreParaSaludo.split(RegExp(r'[\s._-]+')).where((p) => p.isNotEmpty).toList();
    if (partes.isEmpty) return '?';
    return partes.length == 1 ? primera(partes[0]) : primera(partes[0]) + primera(partes[1]);
  }

  factory Usuario.fromJson(Map<String, dynamic> j) => Usuario(
        id: j['id_usuario'] as String,
        email: j['email'] as String,
        nombre: j['nombre'] as String?,
        zonaHoraria: j['zona_horaria'] as String,
      );
}

class Materia {
  Materia({required this.id, required this.nombre});

  final String id;
  final String nombre;

  factory Materia.fromJson(Map<String, dynamic> j) =>
      Materia(id: j['id_materia'] as String, nombre: j['nombre'] as String);
}

class Tarea {
  Tarea({
    required this.id,
    required this.titulo,
    this.descripcion,
    required this.prioridad,
    required this.estado,
    this.idMateria,
    required this.fechaLimite,
    this.fechaCompletada,
  });

  final String id;
  final String titulo;
  final String? descripcion;
  final String prioridad; // BAJA | MEDIA | ALTA
  final String estado; // PENDIENTE | EN_PROGRESO | COMPLETADA | VENCIDA (calculada por el backend)
  final String? idMateria;
  final DateTime fechaLimite; // en hora local del dispositivo
  final DateTime? fechaCompletada;

  bool get vencida => estado == 'VENCIDA';
  bool get completada => estado == 'COMPLETADA';

  factory Tarea.fromJson(Map<String, dynamic> j) => Tarea(
        id: j['id_tarea'] as String,
        titulo: j['titulo'] as String,
        descripcion: j['descripcion'] as String?,
        prioridad: j['prioridad'] as String,
        estado: j['estado'] as String,
        idMateria: j['id_materia'] as String?,
        fechaLimite: DateTime.parse(j['fecha_limite'] as String).toLocal(),
        fechaCompletada: j['fecha_completada'] == null
            ? null
            : DateTime.parse(j['fecha_completada'] as String).toLocal(),
      );
}
