// Modelos que reflejan las respuestas del backend.

/// Códigos de prioridad (RF-09) y estado (RF-05) tal como los usa la API. Sus nombres para mostrar
/// salen de `context.t.prioridad(...)` / `context.t.estado(...)` (según el idioma).
const codigosPrioridad = ['BAJA', 'MEDIA', 'ALTA'];

/// Estados que el usuario puede elegir. "VENCIDA" lo calcula el backend; no se puede establecer.
const codigosEstadoEditable = ['PENDIENTE', 'EN_PROGRESO', 'COMPLETADA'];

/// Perfiles de recordatorios de la personalización inicial.
const perfilesRecordatorios = ['tranquilo', 'equilibrado', 'insistente'];

class Usuario {
  Usuario({
    required this.id,
    required this.email,
    this.nombre,
    required this.zonaHoraria,
    this.idioma = 'es',
    this.personalizacionCompletada = false,
    this.tutorialCompletado = false,
    this.fotoActualizadaEn,
  });

  final String id;
  final String email;
  final String? nombre;
  final String zonaHoraria;
  final String idioma; // 'es' | 'en'

  /// Estado del flujo de primer uso (lo decide el servidor, por eso sobrevive a cerrar la app).
  final bool personalizacionCompletada;
  final bool tutorialCompletado;

  /// null = sin foto. Cambia cada vez que se sube o borra: sirve para refrescar la imagen en pantalla.
  final DateTime? fotoActualizadaEn;

  bool get tieneFoto => fotoActualizadaEn != null;

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
        idioma: (j['idioma'] as String?) ?? 'es',
        personalizacionCompletada: (j['personalizacion_completada'] as bool?) ?? false,
        tutorialCompletado: (j['tutorial_completado'] as bool?) ?? false,
        fotoActualizadaEn: j['foto_actualizada_en'] == null
            ? null
            : DateTime.parse(j['foto_actualizada_en'] as String),
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

/// Preferencia de recordatorios elegida por la persona (no es el nivel de escalada de RF-13).
class PreferenciaRecordatorios {
  PreferenciaRecordatorios({required this.perfil, required this.activas});

  final String perfil; // tranquilo | equilibrado | insistente
  final bool activas;

  factory PreferenciaRecordatorios.fromJson(Map<String, dynamic> j) => PreferenciaRecordatorios(
        perfil: j['perfil_recordatorios'] as String,
        activas: j['notificaciones_activas'] as bool,
      );
}
