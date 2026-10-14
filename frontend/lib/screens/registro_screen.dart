import 'package:flutter/material.dart';

import '../l10n/textos.dart';
import '../state/servicios.dart';
import '../widgets/comunes.dart';

final _tieneLetra = RegExp(r'\p{L}', unicode: true);
final _tieneNumero = RegExp(r'\d');

/// RF-01: registro. Las reglas definitivas de la contraseña las valida el backend
/// (8 a 128 caracteres, al menos una letra y un número); aquí se avisa antes de enviar.
class RegistroScreen extends StatefulWidget {
  const RegistroScreen({super.key});

  @override
  State<RegistroScreen> createState() => _RegistroScreenState();
}

class _RegistroScreenState extends State<RegistroScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nombre = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _enviando = false;
  bool _verPassword = false;

  @override
  void dispose() {
    _nombre.dispose();
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _registrar() async {
    if (_enviando || !_formKey.currentState!.validate()) return;
    setState(() => _enviando = true);
    try {
      await authController.registrar(
        email: _email.text.trim(),
        password: _password.text,
        nombre: _nombre.text.trim(),
      );
      // Registro + inicio de sesión correctos: se vuelve a la raíz, que ya muestra la pantalla principal.
      if (mounted) Navigator.of(context).popUntil((ruta) => ruta.isFirst);
    } catch (e) {
      if (mounted) mostrarError(context, e);
    } finally {
      if (mounted) setState(() => _enviando = false);
    }
  }

  String? _validarPassword(String? v) {
    final t = context.t;
    final texto = v ?? '';
    if (texto.length < 8) return t.passMin;
    if (texto.length > 128) return t.passMax;
    if (!_tieneLetra.hasMatch(texto)) return t.passLetra;
    if (!_tieneNumero.hasMatch(texto)) return t.passNumero;
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Pantalla(
      appBar: barraSimple(context, ''),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: Form(
                key: _formKey,
                child: AutofillGroup(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(context.t.creaTuCuenta, style: tema.textTheme.headlineMedium),
                      const SizedBox(height: 8),
                      Text(
                        context.t.organizaTusTareasLema,
                        style: tema.textTheme.bodyMedium
                            ?.copyWith(color: tema.colorScheme.onSurfaceVariant),
                      ),
                      const SizedBox(height: 32),
                      TextFormField(
                        controller: _nombre,
                        textCapitalization: TextCapitalization.words,
                        textInputAction: TextInputAction.next,
                        autofillHints: const [AutofillHints.name],
                        decoration: decoracionCampo(context, context.t.nombreOpcional),
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _email,
                        keyboardType: TextInputType.emailAddress,
                        textInputAction: TextInputAction.next,
                        autofillHints: const [AutofillHints.email],
                        decoration: decoracionCampo(context, context.t.correo),
                        validator: (v) {
                          final texto = v?.trim() ?? '';
                          if (texto.isEmpty) return context.t.escribeTuCorreo;
                          if (!esCorreoValido(texto)) return context.t.correoInvalido;
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _password,
                        obscureText: !_verPassword,
                        textInputAction: TextInputAction.done,
                        autofillHints: const [AutofillHints.newPassword],
                        decoration: decoracionCampo(
                          context,
                          context.t.contrasena,
                          ayuda: context.t.ayudaContrasena,
                          sufijo: IconButton(
                            tooltip: _verPassword ? context.t.ocultarContrasena : context.t.mostrarContrasena,
                            onPressed: () => setState(() => _verPassword = !_verPassword),
                            icon: Icon(_verPassword
                                ? Icons.visibility_off_outlined
                                : Icons.visibility_outlined),
                          ),
                        ),
                        validator: _validarPassword,
                        onFieldSubmitted: (_) => _registrar(),
                      ),
                      const SizedBox(height: 24),
                      FilledButton(
                        onPressed: _enviando ? null : _registrar,
                        child: _enviando
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(strokeWidth: 2))
                            : Text(context.t.crearCuenta),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
