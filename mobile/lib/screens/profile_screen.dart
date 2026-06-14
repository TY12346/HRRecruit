import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../controllers/auth_controller.dart';
import 'auth_form_helpers.dart';
import '../widgets/app_navigation.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  final _fullNameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _linkedinController = TextEditingController();
  final _summaryController = TextEditingController();
  bool _didPopulate = false;

  @override
  void dispose() {
    _fullNameController.dispose();
    _phoneController.dispose();
    _linkedinController.dispose();
    _summaryController.dispose();
    super.dispose();
  }

  void _populateFields(AuthController auth) {
    if (_didPopulate || auth.profile == null) {
      return;
    }
    final profile = auth.profile!;
    _fullNameController.text = profile.fullName;
    _phoneController.text = profile.phoneNumber;
    _linkedinController.text = profile.linkedinUrl;
    _summaryController.text = profile.personalSummary;
    _didPopulate = true;
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    try {
      await context.read<AuthController>().updateProfile(
            fullName: _fullNameController.text.trim(),
            phoneNumber: _phoneController.text.trim(),
            linkedinUrl: _linkedinController.text.trim(),
            personalSummary: _summaryController.text.trim(),
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Profile updated successfully.')),
      );
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthController>();
    _populateFields(auth);

    return AppBackScope(
      child: Scaffold(
        appBar: appScreenAppBar(context, title: 'Profile'),
        body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextFormField(
                  initialValue: auth.profile?.email ?? '',
                  enabled: false,
                  decoration: const InputDecoration(
                    labelText: 'Email',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _fullNameController,
                  decoration: const InputDecoration(
                    labelText: 'Full name',
                    border: OutlineInputBorder(),
                  ),
                  validator: (value) => value == null || value.trim().isEmpty
                      ? 'Full name is required.'
                      : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _phoneController,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: 'Phone number',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _linkedinController,
                  keyboardType: TextInputType.url,
                  decoration: const InputDecoration(
                    labelText: 'LinkedIn URL',
                    border: OutlineInputBorder(),
                  ),
                  validator: (value) {
                    final text = value?.trim() ?? '';
                    if (text.isEmpty) return null;
                    final uri = Uri.tryParse(text);
                    if (uri == null || !uri.hasScheme || uri.host.isEmpty) {
                      return 'Enter a valid URL, for example https://linkedin.com/in/name.';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _summaryController,
                  minLines: 4,
                  maxLines: 8,
                  decoration: const InputDecoration(
                    labelText: 'Personal summary',
                    alignLabelWithHint: true,
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 24),
                FilledButton.icon(
                  onPressed: auth.isLoading ? null : _save,
                  icon: const Icon(Icons.save_outlined),
                  label: auth.isLoading
                      ? const Text('Saving...')
                      : const Text('Save profile'),
                ),
              ],
            ),
          ),
        ),
      ),
      ),
    );
  }
}
