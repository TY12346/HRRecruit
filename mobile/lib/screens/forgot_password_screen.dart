import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../controllers/auth_controller.dart';
import 'auth_form_helpers.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _requestFormKey = GlobalKey<FormState>();
  final _confirmFormKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _otpController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _codeRequested = false;

  @override
  void dispose() {
    _emailController.dispose();
    _otpController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _requestReset() async {
    if (!_requestFormKey.currentState!.validate()) return;
    try {
      await context.read<AuthController>().requestPasswordReset(email: _emailController.text.trim());
      if (!mounted) return;
      setState(() => _codeRequested = true);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('If the email exists, a reset code has been sent.')),
      );
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    }
  }

  Future<void> _confirmReset() async {
    if (!_confirmFormKey.currentState!.validate()) return;
    try {
      await context.read<AuthController>().confirmPasswordReset(
            email: _emailController.text.trim(),
            otpCode: _otpController.text.trim(),
            newPassword: _newPasswordController.text,
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Password reset successful. Please log in.')),
      );
      context.go('/login');
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = context.watch<AuthController>().isLoading;
    return Scaffold(
      appBar: AppBar(title: const Text('Forgot password')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Reset your password',
                style: Theme.of(context).textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              const Text(
                'Enter your account email. HRRecruit will email a one-time reset code.',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              Form(
                key: _requestFormKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    TextFormField(
                      controller: _emailController,
                      enabled: !_codeRequested,
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(
                        labelText: 'Email',
                        border: OutlineInputBorder(),
                      ),
                      validator: (value) {
                        final text = value?.trim() ?? '';
                        if (text.isEmpty) return 'Email is required.';
                        if (!text.contains('@')) return 'Enter a valid email address.';
                        return null;
                      },
                    ),
                    const SizedBox(height: 12),
                    if (!_codeRequested)
                      FilledButton(
                        onPressed: isLoading ? null : _requestReset,
                        child: Text(isLoading ? 'Sending...' : 'Send reset code'),
                      ),
                  ],
                ),
              ),
              if (_codeRequested) ...[
                const SizedBox(height: 24),
                Form(
                  key: _confirmFormKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      TextFormField(
                        controller: _otpController,
                        keyboardType: TextInputType.number,
                        maxLength: 6,
                        decoration: const InputDecoration(
                          labelText: 'Reset code',
                          border: OutlineInputBorder(),
                        ),
                        validator: (value) => (value?.trim().length ?? 0) == 6 ? null : 'Enter the 6-digit code.',
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _newPasswordController,
                        obscureText: true,
                        decoration: const InputDecoration(
                          labelText: 'New password',
                          border: OutlineInputBorder(),
                        ),
                        validator: (value) => (value?.length ?? 0) >= 8 ? null : 'Password must be at least 8 characters.',
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _confirmPasswordController,
                        obscureText: true,
                        decoration: const InputDecoration(
                          labelText: 'Confirm new password',
                          border: OutlineInputBorder(),
                        ),
                        validator: (value) => value == _newPasswordController.text ? null : 'Passwords do not match.',
                      ),
                      const SizedBox(height: 16),
                      FilledButton(
                        onPressed: isLoading ? null : _confirmReset,
                        child: Text(isLoading ? 'Resetting...' : 'Reset password'),
                      ),
                      TextButton(
                        onPressed: isLoading ? null : () => setState(() => _codeRequested = false),
                        child: const Text('Use a different email'),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
