import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../controllers/auth_controller.dart';
import '../services/linkedin_oauth_service.dart';
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
  final _currentPasswordController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _didPopulate = false;
  bool _isImportingLinkedIn = false;

  @override
  void dispose() {
    _fullNameController.dispose();
    _phoneController.dispose();
    _linkedinController.dispose();
    _summaryController.dispose();
    _currentPasswordController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
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

  Future<void> _importLinkedInProfile() async {
    final linkedInOAuthService = context.read<LinkedInOAuthService>();

    try {
      final configuredClientId =
          await linkedInOAuthService.readConfiguredClientId();
      if (!mounted) return;

      final clientId = configuredClientId ??
          await _requestLinkedInClientId(linkedInOAuthService);
      if (clientId == null || clientId.isEmpty) {
        return;
      }

      final shouldContinue = await _confirmLinkedInOAuthSignIn();
      if (!mounted || !shouldContinue) {
        return;
      }

      setState(() => _isImportingLinkedIn = true);
      final importedProfile = await linkedInOAuthService.importProfile(
        clientIdOverride: clientId,
      );
      _linkedinController.text = importedProfile.profileUrl;
      _summaryController.text = importedProfile.summary;

      await context.read<AuthController>().updateProfile(
            fullName: _fullNameController.text.trim(),
            phoneNumber: _phoneController.text.trim(),
            linkedinUrl: importedProfile.profileUrl,
            personalSummary: importedProfile.summary,
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('LinkedIn profile imported successfully.')),
      );
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    } finally {
      if (mounted) {
        setState(() => _isImportingLinkedIn = false);
      }
    }
  }

  Future<bool> _confirmLinkedInOAuthSignIn() async {
    final shouldContinue = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Sign in to LinkedIn and allow access'),
        content: const Text(
          'HRRecruit will open LinkedIn OAuth 2.0 next. Sign in with your '
          'LinkedIn account email and password on LinkedIn, then choose '
          'Allow access to return and import your profile details.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Cancel'),
          ),
          FilledButton.icon(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            icon: const Icon(Icons.open_in_new_outlined),
            label: const Text('Allow access'),
          ),
        ],
      ),
    );

    return shouldContinue ?? false;
  }

  Future<String?> _requestLinkedInClientId(
    LinkedInOAuthService linkedInOAuthService,
  ) async {
    final controller = TextEditingController();
    final clientId = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('LinkedIn OAuth setup'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Enter the LinkedIn Client ID from your LinkedIn Developer app. '
                'HRRecruit saves this public Client ID on this device and uses '
                'OAuth 2.0 with PKCE; do not enter a Client Secret.',
              ),
              const SizedBox(height: 16),
              TextField(
                controller: controller,
                textInputAction: TextInputAction.done,
                decoration: const InputDecoration(
                  labelText: 'LinkedIn Client ID',
                  border: OutlineInputBorder(),
                ),
                onSubmitted: (_) {
                  final value = controller.text.trim();
                  if (value.isNotEmpty) {
                    Navigator.of(dialogContext).pop(value);
                  }
                },
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              final value = controller.text.trim();
              if (value.isEmpty) {
                ScaffoldMessenger.of(dialogContext).showSnackBar(
                  const SnackBar(
                    content: Text('Enter your LinkedIn Client ID.'),
                  ),
                );
                return;
              }
              Navigator.of(dialogContext).pop(value);
            },
            child: const Text('Save and continue'),
          ),
        ],
      ),
    );
    controller.dispose();

    if (clientId == null || clientId.trim().isEmpty) {
      return null;
    }

    final trimmedClientId = clientId.trim();
    await linkedInOAuthService.saveClientId(trimmedClientId);
    return trimmedClientId;
  }

  Future<void> _changePassword() async {
    if (_newPasswordController.text != _confirmPasswordController.text) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('New password and confirmation do not match.')),
      );
      return;
    }

    try {
      await context.read<AuthController>().changePassword(
            currentPassword: _currentPasswordController.text,
            newPassword: _newPasswordController.text,
          );
      _currentPasswordController.clear();
      _newPasswordController.clear();
      _confirmPasswordController.clear();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Password changed successfully.')),
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
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: auth.isLoading || _isImportingLinkedIn
                      ? null
                      : _importLinkedInProfile,
                  icon: const Icon(Icons.business_center_outlined),
                  label: _isImportingLinkedIn
                      ? const Text('Importing LinkedIn...')
                      : const Text('Import from LinkedIn'),
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
                const SizedBox(height: 24),
                Text(
                  'Change password',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _currentPasswordController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Current password',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _newPasswordController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'New password',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _confirmPasswordController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Confirm new password',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                OutlinedButton.icon(
                  onPressed: auth.isLoading ? null : _changePassword,
                  icon: const Icon(Icons.lock_reset_outlined),
                  label: auth.isLoading
                      ? const Text('Changing...')
                      : const Text('Change password'),
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
