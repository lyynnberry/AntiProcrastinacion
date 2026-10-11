import 'package:flutter/material.dart';

import '../state/servicios.dart';
import '../widgets/comunes.dart';
import 'registro_screen.dart';

/// RF-02: inicio de sesión. Al tener éxito, `main.dart` cambia solo a la pantalla principal.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _enviando = false;
  bool _verPassword = false;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _entrar() async {
    if (_enviando || !_formKey.currentState!.validate()) return;
    setState(() => _enviando = true);
    try {
      await authController.iniciarSesion(_email.text.trim(), _password.text);
    } catch (e) {
      if (mounted) mostrarError(context, e);
    } finally {
      if (mounted) setState(() => _enviando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final e = tema.colorScheme;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: Form(
                key: _formKey,
                child: AutofillGroup(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Container(
                          width: 48,
                          height: 48,
                          decoration: BoxDecoration(
                              color: e.primary, borderRadius: BorderRadius.circular(14)),
                          child: Icon(Icons.check_rounded, color: e.onPrimary, size: 28),
                        ),
                      ),
                      const SizedBox(height: 28),
                      Text('Bienvenido de vuelta', style: tema.textTheme.headlineMedium),
                      const SizedBox(height: 8),
                      Text(
                        authController.sesionExpirada
                            ? 'Tu sesión expiró. Inicia sesión de nuevo.'
                            : 'Inicia sesión para continuar con tus tareas.',
                        style: tema.textTheme.bodyMedium?.copyWith(color: e.onSurfaceVariant),
                      ),
                      const SizedBox(height: 32),
                      TextFormField(
                        controller: _email,
                        keyboardType: TextInputType.emailAddress,
                        textInputAction: TextInputAction.next,
                        autofillHints: const [AutofillHints.email],
                        decoration: decoracionCampo(context, 'Correo electrónico'),
                        validator: (v) {
                          final texto = v?.trim() ?? '';
                          if (texto.isEmpty) return 'Escribe tu correo';
                          if (!esCorreoValido(texto)) return 'El correo no es válido';
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _password,
                        obscureText: !_verPassword,
                        textInputAction: TextInputAction.done,
                        autofillHints: const [AutofillHints.password],
                        decoration: decoracionCampo(
                          context,
                          'Contraseña',
                          sufijo: IconButton(
                            tooltip: _verPassword ? 'Ocultar contraseña' : 'Mostrar contraseña',
                            onPressed: () => setState(() => _verPassword = !_verPassword),
                            icon: Icon(_verPassword
                                ? Icons.visibility_off_outlined
                                : Icons.visibility_outlined),
                          ),
                        ),
                        validator: (v) =>
                            (v == null || v.isEmpty) ? 'Escribe tu contraseña' : null,
                        onFieldSubmitted: (_) => _entrar(),
                      ),
                      const SizedBox(height: 24),
                      FilledButton(
                        onPressed: _enviando ? null : _entrar,
                        child: _enviando
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(strokeWidth: 2))
                            : const Text('Entrar'),
                      ),
                      const SizedBox(height: 8),
                      TextButton(
                        onPressed: _enviando
                            ? null
                            : () => Navigator.of(context).push(
                                MaterialPageRoute(builder: (_) => const RegistroScreen())),
                        child: const Text('¿Aún no tienes cuenta? Crear cuenta'),
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
