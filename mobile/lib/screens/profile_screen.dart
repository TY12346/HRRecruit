import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../controllers/auth_controller.dart';
import '../models/applicant_profile.dart';
import 'auth_form_helpers.dart';
import '../widgets/app_navigation.dart';

const _employmentTypeOptions = [
  '',
  'Full-time',
  'Part-time',
  'Contract',
  'Internship',
  'Temporary',
];

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
  List<ApplicantExperience> _experiences = [];
  List<ApplicantEducation> _educations = [];
  List<ApplicantSkill> _skills = [];

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
    _experiences = List.of(profile.experiences);
    _educations = List.of(profile.educations);
    _skills = List.of(profile.skills);
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
            experiences: _experiences,
            educations: _educations,
            skills: _skills,
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
    try {
      final shouldContinue = await _confirmLinkedInPdfImport();
      if (!mounted || !shouldContinue) {
        return;
      }

      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf'],
        withData: false,
      );
      final selectedFile = result?.files.single;
      final selectedPath = selectedFile?.path;
      if (selectedFile == null || selectedPath == null) {
        return;
      }

      setState(() => _isImportingLinkedIn = true);
      await context.read<AuthController>().importLinkedInProfilePdf(
            path: selectedPath,
            fileName: selectedFile.name,
          );
      if (!mounted) return;

      final profile = context.read<AuthController>().profile;
      if (profile != null) {
        _fullNameController.text = profile.fullName;
        _linkedinController.text = profile.linkedinUrl;
        _summaryController.text = profile.personalSummary;
        setState(() {
          _experiences = List.of(profile.experiences);
          _educations = List.of(profile.educations);
          _skills = List.of(profile.skills);
        });
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('LinkedIn PDF imported successfully.')),
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

  Future<bool> _confirmLinkedInPdfImport() async {
    final shouldContinue = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Import LinkedIn profile PDF'),
        content: const Text(
          'Open your LinkedIn profile, save or download it as a PDF, then '
          'upload that PDF here. HRRecruit will extract the text and fill '
          'your candidate profile automatically.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Cancel'),
          ),
          FilledButton.icon(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            icon: const Icon(Icons.upload_file_outlined),
            label: const Text('Choose PDF'),
          ),
        ],
      ),
    );

    return shouldContinue ?? false;
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

  Future<void> _addExperience() async {
    final jobTitle = TextEditingController();
    final companyName = TextEditingController();
    String employmentType = '';
    final startDate = TextEditingController();
    final location = TextEditingController();
    final experience = await showDialog<ApplicantExperience>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Add experience'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _dialogField(jobTitle, 'Job title'),
                _dialogField(companyName, 'Company name'),
                _employmentTypeDropdown(
                  value: employmentType,
                  onChanged: (value) => setDialogState(() => employmentType = value ?? ''),
                ),
                _dialogField(startDate, 'Start date (YYYY-MM-DD)'),
                _dialogField(location, 'Location'),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.of(dialogContext).pop(), child: const Text('Cancel')),
            FilledButton(
              onPressed: () {
                if (jobTitle.text.trim().isEmpty) return;
                Navigator.of(dialogContext).pop(ApplicantExperience(
                  jobTitle: jobTitle.text.trim(),
                  companyName: companyName.text.trim(),
                  employmentType: employmentType,
                  startDate: startDate.text.trim(),
                  location: location.text.trim(),
                ));
              },
              child: const Text('Add'),
            ),
          ],
        ),
      ),
    );
    if (experience != null) setState(() => _experiences.add(experience));
  }

  Future<void> _addEducation() async {
    final schoolName = TextEditingController();
    final degreeName = TextEditingController();
    final fieldOfStudy = TextEditingController();
    final startDate = TextEditingController();
    final endDate = TextEditingController();
    final grade = TextEditingController();
    final education = await showDialog<ApplicantEducation>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Add education'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _dialogField(schoolName, 'School name'),
              _dialogField(degreeName, 'Degree name'),
              _dialogField(fieldOfStudy, 'Field of study'),
              _dialogField(startDate, 'Start date (YYYY-MM-DD)'),
              _dialogField(endDate, 'End date (YYYY-MM-DD)'),
              _dialogField(grade, 'Grade'),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(dialogContext).pop(), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              if (schoolName.text.trim().isEmpty) return;
              Navigator.of(dialogContext).pop(ApplicantEducation(
                schoolName: schoolName.text.trim(),
                degreeName: degreeName.text.trim(),
                fieldOfStudy: fieldOfStudy.text.trim(),
                startDate: startDate.text.trim(),
                endDate: endDate.text.trim(),
                grade: grade.text.trim(),
              ));
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
    if (education != null) setState(() => _educations.add(education));
  }

  Future<void> _addSkill() async {
    final skillName = TextEditingController();
    final skill = await showDialog<ApplicantSkill>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Add skill'),
        content: _dialogField(skillName, 'Skill name'),
        actions: [
          TextButton(onPressed: () => Navigator.of(dialogContext).pop(), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              if (skillName.text.trim().isEmpty) return;
              Navigator.of(dialogContext).pop(ApplicantSkill(skillName: skillName.text.trim()));
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
    if (skill != null) setState(() => _skills.add(skill));
  }

  Widget _employmentTypeDropdown({
    required String value,
    required ValueChanged<String?> onChanged,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: DropdownButtonFormField<String>(
        initialValue: value,
        decoration: const InputDecoration(labelText: 'Employment type', border: OutlineInputBorder()),
        items: _employmentTypeOptions
            .map((option) => DropdownMenuItem(value: option, child: Text(option.isEmpty ? 'Not specified' : option)))
            .toList(),
        onChanged: onChanged,
      ),
    );
  }

  Widget _dialogField(TextEditingController controller, String label) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextField(
        controller: controller,
        decoration: InputDecoration(labelText: label, border: const OutlineInputBorder()),
      ),
    );
  }

  Widget _profileSection({
    required String title,
    required String emptyText,
    required VoidCallback onAdd,
    required List<Widget> children,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(child: Text(title, style: Theme.of(context).textTheme.titleMedium)),
                IconButton(onPressed: onAdd, icon: const Icon(Icons.add_circle_outline)),
              ],
            ),
            if (children.isEmpty) Text(emptyText) else ...children,
          ],
        ),
      ),
    );
  }

  Widget _experienceSections() {
    return _profileSection(
      title: 'Experience',
      emptyText: 'Add your work experience.',
      onAdd: _addExperience,
      children: [
        for (final entry in _experiences.indexed)
          ListTile(
            title: Text(entry.$2.jobTitle),
            subtitle: Text([entry.$2.companyName, entry.$2.employmentType, entry.$2.location].where((value) => value.isNotEmpty).join(' • ')),
            trailing: IconButton(
              icon: const Icon(Icons.delete_outline),
              onPressed: () => setState(() => _experiences.removeAt(entry.$1)),
            ),
          ),
      ],
    );
  }

  Widget _educationSection() {
    return _profileSection(
      title: 'Education',
      emptyText: 'Add your education.',
      onAdd: _addEducation,
      children: [
        for (final entry in _educations.indexed)
          ListTile(
            title: Text(entry.$2.schoolName),
            subtitle: Text([entry.$2.degreeName, entry.$2.fieldOfStudy, entry.$2.grade].where((value) => value.isNotEmpty).join(' • ')),
            trailing: IconButton(
              icon: const Icon(Icons.delete_outline),
              onPressed: () => setState(() => _educations.removeAt(entry.$1)),
            ),
          ),
      ],
    );
  }

  Widget _skillsSection() {
    return _profileSection(
      title: 'Skills',
      emptyText: 'Add your skills.',
      onAdd: _addSkill,
      children: _skills.isEmpty
          ? []
          : [
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final entry in _skills.indexed)
                    InputChip(
                      label: Text(entry.$2.skillName),
                      onDeleted: () => setState(() => _skills.removeAt(entry.$1)),
                    ),
                ],
              ),
            ],
    );
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
                  icon: const Icon(Icons.picture_as_pdf_outlined),
                  label: _isImportingLinkedIn
                      ? const Text('Importing LinkedIn PDF...')
                      : const Text('Import LinkedIn PDF'),
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
                _experienceSections(),
                const SizedBox(height: 12),
                _educationSection(),
                const SizedBox(height: 12),
                _skillsSection(),
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
