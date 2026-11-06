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
    this.fechaProgramada,
  });

  final String id;
  final String titulo;
  final String? descripcion;
  final String prioridad; // BAJA | MEDIA | ALTA
  final String estado; // PENDIENTE | EN_PROGRESO | COMPLETADA | VENCIDA (calculada por el backend)
  final String? idMateria;
  final DateTime fechaLimite; // en hora local del dispositivo
  final DateTime? fechaCompletada;

  /// RF-21: día al que la persona comprometió la tarea (opcional). Es una fecha sin hora.
  final DateTime? fechaProgramada;

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
        fechaProgramada:
            j['fecha_programada'] == null ? null : DateTime.parse(j['fecha_programada'] as String),
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

/// Aviso planificado por el backend (RF-12 / RF-13). Que exista aquí NO significa que ya se haya
/// mostrado en el teléfono: el aviso del sistema operativo se integrará en un paso posterior.
class Recordatorio {
  Recordatorio({
    required this.id,
    this.idTarea,
    required this.tipo,
    this.nivel,
    required this.mensaje,
    required this.estado,
    required this.fechaProgramada,
    this.esAvisoFinal = false,
  });

  final String id;
  final String? idTarea;
  final String tipo; // RECORDATORIO | URGENTE | CRITICA | CORRECTIVA
  final int? nivel; // 1..4: sube conforme se acerca la fecha límite
  final String mensaje; // ya viene en el idioma del usuario
  final String estado; // PROGRAMADA | ENVIADA | CANCELADA ...
  final DateTime fechaProgramada; // hora local
  final bool esAvisoFinal;

  factory Recordatorio.fromJson(Map<String, dynamic> j) => Recordatorio(
        id: j['id_notificacion'] as String,
        idTarea: j['id_tarea'] as String?,
        tipo: j['tipo'] as String,
        nivel: j['nivel_intensidad'] as int?,
        mensaje: j['mensaje'] as String,
        estado: j['estado'] as String,
        fechaProgramada: DateTime.parse(j['fecha_programada'] as String).toLocal(),
        esAvisoFinal: (j['es_aviso_final'] as bool?) ?? false,
      );
}

// ─────────────────────────────── Gamificación (RF-21 a RF-27) ───────────────────────────────

DateTime _soloDia(Object? v) => DateTime.parse(v as String);

/// Un logro del catálogo con el avance de la persona (RF-23). Nombre y descripción ya vienen en su idioma.
class Logro {
  Logro({
    required this.codigo,
    required this.nombre,
    required this.descripcion,
    required this.categoria,
    required this.valorCondicion,
    required this.valorActual,
    required this.progreso,
    required this.recompensaPuntos,
    required this.desbloqueado,
    this.fechaDesbloqueo,
  });

  final String codigo;
  final String nombre;
  final String descripcion;
  final String categoria; // RACHA | VELOCIDAD | PRODUCTIVIDAD | CONSTANCIA
  final int valorCondicion;
  final int valorActual;
  final int progreso; // 0..100
  final int recompensaPuntos;
  final bool desbloqueado;
  final DateTime? fechaDesbloqueo;

  factory Logro.fromJson(Map<String, dynamic> j) => Logro(
        codigo: j['codigo'] as String,
        nombre: j['nombre'] as String,
        descripcion: j['descripcion'] as String,
        categoria: j['categoria'] as String,
        valorCondicion: j['valor_condicion'] as int,
        valorActual: j['valor_actual'] as int,
        progreso: j['progreso'] as int,
        recompensaPuntos: j['recompensa_puntos'] as int,
        desbloqueado: j['desbloqueado'] as bool,
        fechaDesbloqueo:
            j['fecha_desbloqueo'] == null ? null : DateTime.parse(j['fecha_desbloqueo'] as String).toLocal(),
      );
}

/// Recuperación de racha en curso (RF-25).
class RecuperacionActiva {
  RecuperacionActiva({
    required this.id,
    required this.rachaPerdida,
    required this.fechaFinPrevista,
    required this.tareasTotal,
    required this.tareasCompletadas,
    required this.diasRestantes,
  });

  final String id;
  final int rachaPerdida;
  final DateTime fechaFinPrevista;
  final int tareasTotal;
  final int tareasCompletadas;
  final int diasRestantes;

  factory RecuperacionActiva.fromJson(Map<String, dynamic> j) => RecuperacionActiva(
        id: j['id_recuperacion'] as String,
        rachaPerdida: j['racha_perdida'] as int,
        fechaFinPrevista: _soloDia(j['fecha_fin_prevista']),
        tareasTotal: j['tareas_atrasadas_total'] as int,
        tareasCompletadas: j['tareas_atrasadas_completadas'] as int,
        diasRestantes: j['dias_restantes'] as int,
      );
}

/// Estado de gamificación de la persona autenticada (RF-26).
class ProgresoGamificacion {
  ProgresoGamificacion({
    required this.rachaActual,
    required this.rachaMaxima,
    required this.puntos,
    required this.nivel,
    required this.protecciones,
    required this.hoyComprometidas,
    required this.hoyCumplidas,
    required this.tareasATiempo,
    required this.logrosDesbloqueados,
    required this.logrosPendientes,
    this.recuperacion,
    this.proteccionFecha,
    this.proteccionRacha,
    this.puedeRecuperar = false,
  });

  final int rachaActual;
  final int rachaMaxima;
  final int puntos;
  final int nivel;
  final int protecciones;
  final int hoyComprometidas;
  final int hoyCumplidas;
  final int tareasATiempo;
  final List<Logro> logrosDesbloqueados;
  final List<Logro> logrosPendientes;
  final RecuperacionActiva? recuperacion;

  /// Si no es null, se puede usar una protección sobre ese día y la racha volvería a [proteccionRacha].
  final DateTime? proteccionFecha;
  final int? proteccionRacha;
  final bool puedeRecuperar;

  bool get puedeProteger => proteccionFecha != null;

  factory ProgresoGamificacion.fromJson(Map<String, dynamic> j) {
    final hoy = j['hoy'] as Map<String, dynamic>;
    final proteger = j['puede_proteger'] as Map<String, dynamic>?;
    final recuperacion = j['recuperacion_activa'] as Map<String, dynamic>?;
    List<Logro> logros(String clave) =>
        (j[clave] as List<dynamic>).map((e) => Logro.fromJson(e as Map<String, dynamic>)).toList();
    return ProgresoGamificacion(
      rachaActual: j['racha_actual'] as int,
      rachaMaxima: j['racha_maxima'] as int,
      puntos: j['puntos_totales'] as int,
      nivel: j['nivel'] as int,
      protecciones: j['protecciones_disponibles'] as int,
      hoyComprometidas: hoy['tareas_comprometidas'] as int,
      hoyCumplidas: hoy['tareas_cumplidas_a_tiempo'] as int,
      tareasATiempo: j['tareas_a_tiempo'] as int,
      logrosDesbloqueados: logros('logros_desbloqueados'),
      logrosPendientes: logros('logros_pendientes'),
      recuperacion: recuperacion == null ? null : RecuperacionActiva.fromJson(recuperacion),
      proteccionFecha: proteger == null ? null : _soloDia(proteger['fecha']),
      proteccionRacha: proteger == null ? null : proteger['racha_a_conservar'] as int,
      puedeRecuperar: (j['puede_recuperar'] as bool?) ?? false,
    );
  }
}
