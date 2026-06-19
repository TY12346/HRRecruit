import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../controllers/auth_controller.dart';
import 'auth_form_helpers.dart';
import '../widgets/app_navigation.dart';

class _LinkedInProfileImport {
  const _LinkedInProfileImport({
    required this.url,
    required this.summary,
  });

  final String url;
  final String summary;
}

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
    final importedUrlController = TextEditingController(
      text: _linkedinController.text.trim(),
    );
    final importedSummaryController = TextEditingController(
      text: _summaryController.text.trim(),
    );

    final importedProfile = await showDialog<_LinkedInProfileImport>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Import LinkedIn profile'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Paste your public LinkedIn profile URL. HRRecruit will save the URL and prepare a profile summary '
                'for recruiter review. No LinkedIn OAuth or external API call is used in this demo import.',
              ),
              const SizedBox(height: 16),
              TextField(
                controller: importedUrlController,
                keyboardType: TextInputType.url,
                decoration: const InputDecoration(
                  labelText: 'LinkedIn profile URL',
                  hintText: 'https://www.linkedin.com/in/your-name',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: importedSummaryController,
                minLines: 3,
                maxLines: 6,
                decoration: const InputDecoration(
                  labelText: 'Imported summary',
                  helperText: 'Optional. Edit or add a summary from your LinkedIn profile.',
                  alignLabelWithHint: true,
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Cancel'),
          ),
          FilledButton.icon(
            onPressed: () {
              final url = importedUrlController.text.trim();
              final summary = importedSummaryController.text.trim();
              final uri = Uri.tryParse(url);
              final isLinkedInUrl = uri != null &&
                  (uri.scheme == 'http' || uri.scheme == 'https') &&
                  uri.host.toLowerCase().contains('linkedin.com');

              if (!isLinkedInUrl) {
                ScaffoldMessenger.of(dialogContext).showSnackBar(
                  const SnackBar(
                    content: Text('Enter a valid LinkedIn profile URL.'),
                  ),
                );
                return;
              }

              Navigator.of(dialogContext).pop(
                _LinkedInProfileImport(
                  url: url,
                  summary: summary.isNotEmpty
                      ? summary
                      : _buildLinkedInSummary(url),
                ),
              );
            },
            icon: const Icon(Icons.download_outlined),
            label: const Text('Import'),
          ),
        ],
      ),
    );

    importedUrlController.dispose();
    importedSummaryController.dispose();

    if (importedProfile == null) {
      return;
    }

    setState(() {
      _isImportingLinkedIn = true;
      _linkedinController.text = importedProfile.url;
      _summaryController.text = importedProfile.summary;
    });

    try {
      await context.read<AuthController>().updateProfile(
            fullName: _fullNameController.text.trim(),
            phoneNumber: _phoneController.text.trim(),
            linkedinUrl: importedProfile.url,
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

  static String _buildLinkedInSummary(String url) {
    final uri = Uri.parse(url);
    final slug = uri.pathSegments.isNotEmpty ? uri.pathSegments.last : '';
    final displayName = slug
        .split(RegExp(r'[-_]'))
        .where((part) => part.isNotEmpty)
        .map((part) => '${part[0].toUpperCase()}${part.substring(1)}')
        .join(' ');

    if (displayName.isEmpty) {
      return 'Imported from LinkedIn profile: $url';
    }
    return '$displayName imported their public LinkedIn profile for recruiter review.';
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
                      : const Text('Import LinkedIn profile'),
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
