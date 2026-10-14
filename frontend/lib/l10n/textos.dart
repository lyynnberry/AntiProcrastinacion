import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

/// Idiomas soportados. Para agregar uno: sumarlo aquí y dar su traducción en cada texto de [Textos].
const idiomasSoportados = ['es', 'en'];
const idiomaPorDefecto = 'es';

/// Textos de TODA la app. Cada texto lleva sus dos traducciones juntas (`_t('español', 'english')`),
/// así es imposible dejar uno sin traducir. Se usa con `context.t.algo`.
///
/// Los datos del usuario (títulos de tareas, nombres de materias) NO se traducen.
class Textos {
  const Textos(this.codigo);

  final String codigo;

  bool get esEn => codigo == 'en';
  String _t(String es, String en) => esEn ? en : es;

  static Textos of(BuildContext context) =>
      Localizations.of<Textos>(context, Textos) ?? const Textos(idiomaPorDefecto);

  // ───────────── Comunes ─────────────
  String get cancelar => _t('Cancelar', 'Cancel');
  String get guardar => _t('Guardar', 'Save');
  String get reintentar => _t('Reintentar', 'Retry');
  String get eliminar => _t('Eliminar', 'Delete');
  String get editar => _t('Editar', 'Edit');
  String get crear => _t('Crear', 'Create');
  String get continuar => _t('Continuar', 'Continue');
  String get siguiente => _t('Siguiente', 'Next');
  String get omitir => _t('Omitir', 'Skip');
  String get comenzar => _t('Comenzar', 'Get started');
  String get todas => _t('Todas', 'All');
  String get limpiar => _t('Limpiar', 'Clear');
  String get guardarCambios => _t('Guardar cambios', 'Save changes');
  String get errorInesperado =>
      _t('Ocurrió un error inesperado. Inténtalo de nuevo.', 'Something went wrong. Please try again.');

  // ───────────── Errores del servidor (por código) ─────────────
  /// Texto para un código de error del backend; null si no se conoce.
  String? errorPorCodigo(String codigo) => switch (codigo) {
        'SIN_CONEXION' => _t('No se pudo conectar con el servidor.', 'Could not connect to the server.'),
        'CREDENCIALES_INVALIDAS' => _t('Correo o contraseña incorrectos.', 'Incorrect email or password.'),
        'SESION_INVALIDA' ||
        'NO_AUTENTICADO' ||
        'TOKEN_INVALIDO' =>
          _t('La sesión no es válida o ya expiró. Inicia sesión de nuevo.',
              'Your session is not valid or has expired. Please sign in again.'),
        'EMAIL_DUPLICADO' =>
          _t('Ya existe una cuenta con ese correo.', 'An account with that email already exists.'),
        'PASSWORD_DEBIL' => _t('La contraseña no cumple los requisitos.', 'The password does not meet the requirements.'),
        'VALIDACION' => _t('Los datos enviados no son válidos.', 'The data you entered is not valid.'),
        'TAREA_NO_ENCONTRADA' => _t('Tarea no encontrada.', 'Task not found.'),
        'MATERIA_NO_ENCONTRADA' => _t('Materia no encontrada.', 'Subject not found.'),
        'MATERIA_DUPLICADA' =>
          _t('Ya tienes una materia con ese nombre.', 'You already have a subject with that name.'),
        'FECHA_LIMITE_INVALIDA' =>
          _t('La fecha límite no es válida.', 'The due date is not valid.'),
        'FOTO_INVALIDA' => _t('El archivo no es una imagen válida.', 'The file is not a valid image.'),
        'FOTO_FORMATO_INVALIDO' =>
          _t('Formato no permitido. Usa una imagen JPG, PNG o WebP.', 'Unsupported format. Use a JPG, PNG or WebP image.'),
        'FOTO_DEMASIADO_GRANDE' => _t('La imagen supera el máximo de 5 MB.', 'The image is larger than 5 MB.'),
        _ => null,
      };

  // ───────────── Fechas ─────────────
  List<String> get meses => esEn
      ? const ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
      : const ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];

  String fecha(DateTime d) {
    String dos(int n) => n.toString().padLeft(2, '0');
    return esEn ? '${dos(d.month)}/${dos(d.day)}/${d.year}' : '${dos(d.day)}/${dos(d.month)}/${d.year}';
  }

  String fechaHora(DateTime d) {
    String dos(int n) => n.toString().padLeft(2, '0');
    return '${fecha(d)} ${dos(d.hour)}:${dos(d.minute)}';
  }

  List<String> get diasSemana =>
      esEn ? const ['M', 'T', 'W', 'T', 'F', 'S', 'S'] : const ['L', 'M', 'M', 'J', 'V', 'S', 'D'];

  String diaDeMes(int dia, int mes) => esEn ? '${meses[mes - 1]} $dia' : '$dia de ${meses[mes - 1]}';

  // ───────────── Prioridades y estados ─────────────
  String prioridad(String codigo) => switch (codigo) {
        'BAJA' => _t('Baja', 'Low'),
        'MEDIA' => _t('Media', 'Medium'),
        'ALTA' => _t('Alta', 'High'),
        _ => codigo,
      };
  String prioridadLarga(String codigo) =>
      esEn ? '${prioridad(codigo)} priority' : 'Prioridad ${prioridad(codigo).toLowerCase()}';

  String estado(String codigo) => switch (codigo) {
        'PENDIENTE' => _t('Pendiente', 'Pending'),
        'EN_PROGRESO' => _t('En progreso', 'In progress'),
        'COMPLETADA' => _t('Completada', 'Completed'),
        'VENCIDA' => _t('Vencida', 'Overdue'),
        _ => codigo,
      };
  String get vencidaAutomatico => _t('Vencida (automático)', 'Overdue (automatic)');

  // ───────────── Login / registro ─────────────
  String get bienvenidoDeVuelta => _t('Bienvenido de vuelta', 'Welcome back');
  String get sesionExpiro => _t('Tu sesión expiró. Inicia sesión de nuevo.', 'Your session expired. Please sign in again.');
  String get iniciaSesionParaContinuar =>
      _t('Inicia sesión para continuar con tus tareas.', 'Sign in to continue with your tasks.');
  String get correo => _t('Correo electrónico', 'Email');
  String get escribeTuCorreo => _t('Escribe tu correo', 'Enter your email');
  String get correoInvalido => _t('El correo no es válido', 'The email is not valid');
  String get contrasena => _t('Contraseña', 'Password');
  String get ocultarContrasena => _t('Ocultar contraseña', 'Hide password');
  String get mostrarContrasena => _t('Mostrar contraseña', 'Show password');
  String get escribeTuContrasena => _t('Escribe tu contraseña', 'Enter your password');
  String get entrar => _t('Entrar', 'Sign in');
  String get aunNoTienesCuenta => _t('¿Aún no tienes cuenta? Crear cuenta', "Don't have an account? Sign up");
  String get creaTuCuenta => _t('Crea tu cuenta', 'Create your account');
  String get organizaTusTareasLema =>
      _t('Organiza tus tareas y fechas de entrega en un solo lugar.', 'Organize your tasks and due dates in one place.');
  String get nombreOpcional => _t('Nombre (opcional)', 'Name (optional)');
  String get ayudaContrasena => _t('Mínimo 8 caracteres, con al menos una letra y un número',
      'At least 8 characters, with at least one letter and one number');
  String get crearCuenta => _t('Crear cuenta', 'Sign up');
  String get yaTienesCuenta => _t('¿Ya tienes cuenta? Inicia sesión', 'Already have an account? Sign in');
  String get passMin => _t('Mínimo 8 caracteres', 'At least 8 characters');
  String get passMax => _t('Máximo 128 caracteres', 'At most 128 characters');
  String get passLetra => _t('Incluye al menos una letra', 'Include at least one letter');
  String get passNumero => _t('Incluye al menos un número', 'Include at least one number');

  // ───────────── Navegación ─────────────
  String get inicio => _t('Inicio', 'Home');
  String get tareas => _t('Tareas', 'Tasks');
  String get calendario => _t('Calendario', 'Calendar');
  String get perfil => _t('Perfil', 'Profile');

  // ───────────── Inicio ─────────────
  String get buenosDias => _t('Buenos días', 'Good morning');
  String get buenasTardes => _t('Buenas tardes', 'Good afternoon');
  String get buenasNoches => _t('Buenas noches', 'Good evening');
  String get nuevaTarea => _t('Nueva tarea', 'New task');
  String get lemaLinea1 => _t('Hagamos de hoy', "Let's make today");
  String get lemaLinea2 => _t('un día productivo', 'a productive day');
  String get resumen => _t('Resumen', 'Summary');
  String get vencidas => _t('Vencidas', 'Overdue');
  String get pendientes => _t('Pendientes', 'Pending');
  String get enProgreso => _t('En progreso', 'In progress');
  String get listas => _t('Listas', 'Done');
  String get requierenAtencion => _t('Requieren tu atención', 'Need your attention');
  String get noHayPendientes => _t('No hay tareas pendientes.', 'No pending tasks.');
  String get progresoDeTareas => _t('Progreso de tus tareas', 'Your task progress');
  String porcentajeCompletado(int p) => _t('$p por ciento de tareas completadas', '$p percent of tasks completed');
  String get total => _t('Total', 'Total');
  String get completadas => _t('Completadas', 'Completed');
  String get porHacer => _t('Por hacer', 'To do');

  // ───────────── Tareas ─────────────
  String get prioridadEtiqueta => _t('Prioridad', 'Priority');
  String get materia => _t('Materia', 'Subject');
  String get materiaOpcional => _t('Materia (opcional)', 'Subject (optional)');
  String get sinMateria => _t('Sin materia', 'No subject');
  String get ningunaCumpleFiltros => _t('Ninguna tarea cumple los filtros.', 'No task matches the filters.');
  String get aunNoTienesTareas => _t('Aún no tienes tareas. ¡Crea la primera!', "You don't have any tasks yet. Create the first one!");
  String vence(DateTime d) => _t('Vence ${fechaHora(d)}', 'Due ${fechaHora(d)}');

  // ───────────── Calendario ─────────────
  String get noHayTareasDia => _t('No hay tareas con fecha límite este día.', 'No tasks due on this day.');
  String get mesAnterior => _t('Mes anterior', 'Previous month');
  String get mesSiguiente => _t('Mes siguiente', 'Next month');
  String tareasDelDia(DateTime d) => _t('Tareas del ${fecha(d)}', 'Tasks for ${fecha(d)}');
  String etiquetaDia(int dia, int mes, int cantidad) {
    final base = diaDeMes(dia, mes);
    if (cantidad == 0) return base;
    return esEn
        ? '$base, $cantidad task${cantidad == 1 ? '' : 's'}'
        : '$base, $cantidad tarea${cantidad == 1 ? '' : 's'}';
  }

  // ───────────── Detalle y formulario de tarea ─────────────
  String get detalleDeLaTarea => _t('Detalle de la tarea', 'Task details');
  String get eliminarTareaTitulo => _t('¿Eliminar tarea?', 'Delete task?');
  String eliminarTareaTexto(String titulo) =>
      _t('Se eliminará "$titulo". Esta acción no se puede deshacer.', '"$titulo" will be deleted. This cannot be undone.');
  String get descripcion => _t('Descripción', 'Description');
  String get fechaLimite => _t('Fecha límite', 'Due date');
  String get completadaEl => _t('Completada el', 'Completed on');
  String get marcarCompletada => _t('Marcar como completada', 'Mark as completed');
  String get editarTarea => _t('Editar tarea', 'Edit task');
  String get horaLimite => _t('Hora límite', 'Due time');
  String get nuevaMateria => _t('Nueva materia', 'New subject');
  String get nombreDeLaMateria => _t('Nombre de la materia', 'Subject name');
  String get fechaDebeSerFutura =>
      _t('La fecha límite debe ser posterior a la fecha y hora actual.', 'The due date must be later than the current date and time.');
  String get titulo => _t('Título', 'Title');
  String get tituloObligatorio => _t('El título es obligatorio', 'The title is required');
  String get descripcionOpcional => _t('Descripción (opcional)', 'Description (optional)');
  String get fechaYHoraLimite => _t('Fecha y hora límite', 'Due date and time');
  String get masNuevaMateria => _t('+ Nueva materia…', '+ New subject…');
  String get estadoEtiqueta => _t('Estado', 'Status');
  String get crearTarea => _t('Crear tarea', 'Create task');

  // ───────────── Personalización inicial ─────────────
  String get personalizaTitulo => _t('Personaliza tu experiencia', 'Personalize your experience');
  String get personalizaIntro => _t(
      'Queremos ayudarte a mantenerte al día. Configura cómo quieres recibir tus recordatorios.',
      'We want to help you stay on track. Choose how you want to receive your reminders.');
  String get perfilTranquilo => _t('Tranquilo', 'Relaxed');
  String get perfilEquilibrado => _t('Equilibrado', 'Balanced');
  String get perfilInsistente => _t('Insistente', 'Persistent');
  String get perfilTranquiloDesc => _t('Pocos recordatorios, solo lo importante.', 'Few reminders, only what matters.');
  String get perfilEquilibradoDesc => _t('Recordatorios regulares antes de cada fecha límite.', 'Regular reminders before each deadline.');
  String get perfilInsistenteDesc =>
      _t('Más avisos y más frecuentes para que nada se te escape.', 'More, and more frequent, nudges so nothing slips by.');
  String get recomendado => _t('Recomendado', 'Recommended');
  String get puedesCambiarloDespues =>
      _t('Podrás cambiarlo cuando quieras desde tu perfil.', 'You can change this anytime from your profile.');
  String get elijeUnaOpcion => _t('Elige una opción para continuar.', 'Choose an option to continue.');
  String nombrePerfil(String c) => switch (c) {
        'tranquilo' => perfilTranquilo,
        'insistente' => perfilInsistente,
        _ => perfilEquilibrado,
      };
  String descPerfil(String c) => switch (c) {
        'tranquilo' => perfilTranquiloDesc,
        'insistente' => perfilInsistenteDesc,
        _ => perfilEquilibradoDesc,
      };

  // ───────────── Tutorial ─────────────
  String pasoDeTotal(int paso, int total) => _t('Paso $paso de $total', 'Step $paso of $total');
  String get tut1Titulo => _t('Organiza tus tareas', 'Organize your tasks');
  String get tut1Texto => _t(
      'Crea tareas con título, materia, prioridad y fecha y hora límite, y tenlas siempre a la vista.',
      'Create tasks with a title, subject, priority and due date and time, and keep them in sight.');
  String get tut2Titulo => _t('No dejes pasar tus pendientes', "Don't let tasks slip by");
  String get tut2Texto => _t(
      'Te recordaremos cada tarea antes de su fecha límite, con avisos que aumentan si sigue pendiente.',
      "We'll remind you before each deadline, with nudges that grow stronger while the task stays pending.");
  String get tut3Titulo => _t('Mantén tu racha', 'Keep your streak');
  String get tut3Texto => _t(
      'Cumplir tus tareas a tiempo, día tras día, construye una racha. ¡Que no se rompa!',
      'Finishing tasks on time, day after day, builds a streak. Don\'t let it break!');
  String get tut4Titulo => _t('Recupera el control', 'Take back control');
  String get tut4Texto => _t(
      'Si te atrasas, te ayudamos a reorganizarte con un plan para ponerte al día sin agobiarte.',
      "If you fall behind, we'll help you reorganize with a plan to catch up without the stress.");

  // ───────────── Perfil ─────────────
  String get nombre => _t('Nombre', 'Name');
  String get sinNombreRegistrado => _t('Sin nombre registrado', 'No name set');
  String get editarFoto => _t('Editar foto', 'Edit photo');
  String get agregarFoto => _t('Agregar foto', 'Add photo');
  String get cambiarFoto => _t('Cambiar foto', 'Change photo');
  String get eliminarFoto => _t('Eliminar foto', 'Remove photo');
  String get verFoto => _t('Ver foto', 'View photo');
  String get eliminarFotoTitulo => _t('¿Eliminar tu foto?', 'Remove your photo?');
  String get eliminarFotoTexto => _t('Se mostrarán tus iniciales en su lugar.', 'Your initials will be shown instead.');
  String get fotoActualizada => _t('Foto actualizada.', 'Photo updated.');
  String get fotoEliminada => _t('Foto eliminada.', 'Photo removed.');
  String get fotoDeLaGaleria => _t('Elegir de la galería', 'Choose from gallery');
  String get fotoDeLaCamara => _t('Tomar una foto', 'Take a photo');
  String get fotoNoDisponible => _t('No se pudo abrir la galería o la cámara.', 'Could not open the gallery or camera.');
  String get datosDeLaCuenta => _t('Datos de la cuenta', 'Account');
  String get correoNoEditable => _t('El correo no se puede cambiar.', 'Your email cannot be changed.');
  String get zonaHoraria => _t('Zona horaria', 'Time zone');
  String get nombreMuyCorto => _t('El nombre debe tener al menos 2 caracteres', 'The name must be at least 2 characters');
  String get nombreMuyLargo => _t('Máximo 100 caracteres', 'At most 100 characters');
  String get nombreCaracteres => _t('Usa solo letras, espacios, apóstrofos, guiones y puntos',
      'Use only letters, spaces, apostrophes, hyphens and periods');
  String get perfilActualizado => _t('Cambios guardados.', 'Changes saved.');
  String get idioma => _t('Idioma', 'Language');
  String get espanol => _t('Español', 'Spanish');
  String get ingles => _t('Inglés', 'English');
  String get idiomaActualizado => _t('Idioma actualizado.', 'Language updated.');
  String get apariencia => _t('Apariencia', 'Appearance');
  String get claro => _t('Claro', 'Light');
  String get oscuro => _t('Oscuro', 'Dark');
  String get sistema => _t('Sistema', 'System');
  String get notificaciones => _t('Notificaciones', 'Notifications');
  String get recordatorios => _t('Recordatorios', 'Reminders');
  String get preferenciaGuardada => _t('Preferencia guardada.', 'Preference saved.');
  String get cerrarSesion => _t('Cerrar sesión', 'Log out');
  String get cerrarSesionTitulo => _t('¿Cerrar sesión?', 'Log out?');
  String get cerrarSesionTexto => _t('Tendrás que iniciar sesión de nuevo para ver tus tareas.',
      "You'll need to sign in again to see your tasks.");
  String get desactivados => _t('desactivados', 'off');
  String get recordatoriosActivados => _t('Recordatorios activados', 'Reminders on');
  String get cargando => _t('Cargando…', 'Loading…');
}

class TextosDelegate extends LocalizationsDelegate<Textos> {
  const TextosDelegate();

  @override
  bool isSupported(Locale locale) => idiomasSoportados.contains(locale.languageCode);

  @override
  Future<Textos> load(Locale locale) =>
      SynchronousFuture(Textos(isSupported(locale) ? locale.languageCode : idiomaPorDefecto));

  @override
  bool shouldReload(TextosDelegate old) => false;
}

extension TextosEnContexto on BuildContext {
  Textos get t => Textos.of(this);
}
