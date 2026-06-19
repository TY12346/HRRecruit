import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../controllers/auth_controller.dart';
import 'auth_form_helpers.dart';

enum _ForgotPasswordStep { requestEmail, enterOtp, enterNewPassword }

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _requestFormKey = GlobalKey<FormState>();
  final _otpFormKey = GlobalKey<FormState>();
  final _passwordFormKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _otpController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  _ForgotPasswordStep _step = _ForgotPasswordStep.requestEmail;
  String? _developmentResetCode;

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
      final resetCode = await context
          .read<AuthController>()
          .requestPasswordReset(email: _emailController.text.trim());
      if (!mounted) return;
      setState(() {
        _step = _ForgotPasswordStep.enterOtp;
        _developmentResetCode = resetCode;
        if (resetCode != null && resetCode.isNotEmpty) {
          _otpController.text = resetCode;
        }
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            resetCode == null || resetCode.isEmpty
                ? 'If the email exists, an OTP has been sent.'
                : 'Development OTP received and prefilled.',
          ),
        ),
      );
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    }
  }

  void _submitOtp() {
    if (!_otpFormKey.currentState!.validate()) return;
    setState(() => _step = _ForgotPasswordStep.enterNewPassword);
  }

  Future<void> _confirmReset() async {
    if (!_passwordFormKey.currentState!.validate()) return;
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

  void _restart() {
    setState(() {
      _step = _ForgotPasswordStep.requestEmail;
      _developmentResetCode = null;
      _otpController.clear();
      _newPasswordController.clear();
      _confirmPasswordController.clear();
    });
  }

  String get _stepTitle {
    switch (_step) {
      case _ForgotPasswordStep.requestEmail:
        return 'Reset your password';
      case _ForgotPasswordStep.enterOtp:
        return 'Enter OTP';
      case _ForgotPasswordStep.enterNewPassword:
        return 'Create new password';
    }
  }

  String get _stepDescription {
    switch (_step) {
      case _ForgotPasswordStep.requestEmail:
        return 'Enter your account email. HRRecruit will send an OTP to your email.';
      case _ForgotPasswordStep.enterOtp:
        return 'Enter the 6-digit OTP sent to ${_emailController.text.trim()}.';
      case _ForgotPasswordStep.enterNewPassword:
        return 'OTP submitted. Enter a new password for your account.';
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
                _stepTitle,
                style: Theme.of(context).textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                _stepDescription,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              if (_step == _ForgotPasswordStep.requestEmail)
                _buildEmailStep(isLoading),
              if (_step == _ForgotPasswordStep.enterOtp) _buildOtpStep(isLoading),
              if (_step == _ForgotPasswordStep.enterNewPassword)
                _buildPasswordStep(isLoading),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEmailStep(bool isLoading) {
    return Form(
      key: _requestFormKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _emailController,
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
          FilledButton(
            onPressed: isLoading ? null : _requestReset,
            child: Text(isLoading ? 'Sending...' : 'Submit'),
          ),
        ],
      ),
    );
  }

  Widget _buildOtpStep(bool isLoading) {
    return Form(
      key: _otpFormKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (_developmentResetCode != null && _developmentResetCode!.isNotEmpty) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Text(
                  'Development mode: OTP $_developmentResetCode has been prefilled because emails may be printed in the backend console instead of delivered to an inbox.',
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],
          TextFormField(
            controller: _otpController,
            keyboardType: TextInputType.number,
            maxLength: 6,
            decoration: const InputDecoration(
              labelText: 'OTP',
              border: OutlineInputBorder(),
            ),
            validator: (value) =>
                (value?.trim().length ?? 0) == 6 ? null : 'Enter the 6-digit OTP.',
          ),
          const SizedBox(height: 12),
          FilledButton(
            onPressed: isLoading ? null : _submitOtp,
            child: const Text('Submit'),
          ),
          TextButton(
            onPressed: isLoading ? null : _restart,
            child: const Text('Use a different email'),
          ),
        ],
      ),
    );
  }

  Widget _buildPasswordStep(bool isLoading) {
    return Form(
      key: _passwordFormKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _newPasswordController,
            obscureText: true,
            decoration: const InputDecoration(
              labelText: 'New password',
              border: OutlineInputBorder(),
            ),
            validator: (value) => (value?.length ?? 0) >= 8
                ? null
                : 'Password must be at least 8 characters.',
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
            onPressed: isLoading
                ? null
                : () => setState(() => _step = _ForgotPasswordStep.enterOtp),
            child: const Text('Back to OTP'),
          ),
        ],
      ),
    );
  }
}
