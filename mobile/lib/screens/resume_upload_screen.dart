import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api/api_client.dart';
import '../controllers/auth_controller.dart';
import '../models/applicant_profile.dart';
import 'auth_form_helpers.dart';
import '../widgets/app_navigation.dart';

const int maxApplicantResumes = 5;

class ResumeUploadScreen extends StatefulWidget {
  const ResumeUploadScreen({super.key});

  @override
  State<ResumeUploadScreen> createState() => _ResumeUploadScreenState();
}

class _ResumeUploadScreenState extends State<ResumeUploadScreen> {
  final TextEditingController _labelController = TextEditingController();
  PlatformFile? _selectedFile;

  @override
  void dispose() {
    _labelController.dispose();
    super.dispose();
  }

  Future<void> _pickResume() async {
    final result = await FilePicker.platform.pickFiles(
      allowMultiple: false,
      type: FileType.custom,
      allowedExtensions: const ['pdf', 'docx'],
      withData: false,
    );

    if (result == null || result.files.isEmpty) {
      return;
    }

    final file = result.files.single;
    if (file.path == null) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Unable to access the selected file path.'),
        ),
      );
      return;
    }

    setState(() {
      _selectedFile = file;
      if (_labelController.text.trim().isEmpty) {
        _labelController.text = _labelFromFileName(file.name);
      }
    });
  }

  Future<void> _upload() async {
    final file = _selectedFile;
    final label = _labelController.text.trim();
    final resumeCount =
        context.read<AuthController>().profile?.resumes.length ?? 0;
    if (resumeCount >= maxApplicantResumes) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('You can upload a maximum of 5 resumes.')),
      );
      return;
    }
    if (file == null || file.path == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Select a PDF or DOCX resume first.')),
      );
      return;
    }
    if (label.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Add a label for this resume.')),
      );
      return;
    }

    try {
      await context.read<AuthController>().uploadResume(
            path: file.path!,
            fileName: file.name,
            title: label,
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Resume uploaded successfully.')),
      );
      setState(() {
        _selectedFile = null;
        _labelController.clear();
      });
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    }
  }

  Future<void> _viewResume(ApplicantResume resume) async {
    final resumePath = resume.resumeUrl?.trim().isNotEmpty == true
        ? resume.resumeUrl!.trim()
        : resume.resumeFile.trim();
    if (resumePath == null || resumePath.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('This resume file is not available.')),
      );
      return;
    }

    try {
      final resumeUri =
          await context.read<ApiClient>().resolveBackendFileUri(resumePath);
      final opened = await launchUrl(
        resumeUri,
        mode: LaunchMode.externalApplication,
      );
      if (!opened) {
        throw Exception('Unable to open the resume file.');
      }
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    }
  }

  Future<void> _renameResume(ApplicantResume resume) async {
    final controller = TextEditingController(text: _resumeLabel(resume));
    final newLabel = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Edit resume label'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(
            labelText: 'Resume label',
            hintText: 'Example: Digital content creator',
          ),
          textCapitalization: TextCapitalization.words,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(controller.text.trim()),
            child: const Text('Save'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (newLabel == null || newLabel.isEmpty) return;

    try {
      await context.read<AuthController>().renameResume(
            resumeId: resume.id,
            title: newLabel,
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Resume label updated.')),
      );
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    }
  }

  Future<void> _deleteResume(ApplicantResume resume) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete resume?'),
        content: Text(
          'Remove "${_resumeLabel(resume)}" from your resume library?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    try {
      await context.read<AuthController>().deleteResume(resumeId: resume.id);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Resume deleted.')),
      );
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthController>();
    final resumes = auth.profile?.resumes ?? const <ApplicantResume>[];
    final canUploadMore = resumes.length < maxApplicantResumes;

    return AppBackScope(
      child: Scaffold(
        appBar: appScreenAppBar(context, title: 'Resume library'),
        body: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Your resumes (${resumes.length}/$maxApplicantResumes)',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Upload up to 5 resumes and label each one for the role '
                        'or profile you want to use, such as “Marketing agent” '
                        'or “Digital content creator”.',
                      ),
                      const SizedBox(height: 16),
                      if (resumes.isEmpty)
                        const Text('No resumes uploaded yet.')
                      else
                        for (final resume in resumes)
                          _resumeTile(context, resume, auth.isLoading),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Upload PDF or DOCX',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Maximum file size is validated by the backend at 5MB.',
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _labelController,
                        enabled: !auth.isLoading && canUploadMore,
                        decoration: const InputDecoration(
                          labelText: 'Resume label',
                          hintText: 'Example: Marketing agent',
                        ),
                        textCapitalization: TextCapitalization.words,
                      ),
                      const SizedBox(height: 16),
                      OutlinedButton.icon(
                        onPressed:
                            auth.isLoading || !canUploadMore ? null : _pickResume,
                        icon: const Icon(Icons.attach_file),
                        label: const Text('Choose resume'),
                      ),
                      if (_selectedFile != null) ...[
                        const SizedBox(height: 12),
                        Text('Selected: ${_selectedFile!.name}'),
                      ],
                      if (!canUploadMore) ...[
                        const SizedBox(height: 12),
                        const Text(
                          'You have reached the maximum of 5 resumes. '
                          'Delete one before uploading another.',
                        ),
                      ],
                      const SizedBox(height: 20),
                      FilledButton.icon(
                        onPressed:
                            auth.isLoading || !canUploadMore ? null : _upload,
                        icon: const Icon(Icons.cloud_upload_outlined),
                        label: auth.isLoading
                            ? const Text('Uploading...')
                            : const Text('Upload resume'),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _resumeTile(BuildContext context, ApplicantResume resume, bool isLoading) {
    return Card.outlined(
      child: ListTile(
        leading: const Icon(Icons.description_outlined),
        title: Text(_resumeLabel(resume)),
        subtitle: const Text('Available for job applications'),
        trailing: PopupMenuButton<String>(
          enabled: !isLoading,
          onSelected: (value) {
            if (value == 'view') _viewResume(resume);
            if (value == 'rename') _renameResume(resume);
            if (value == 'delete') _deleteResume(resume);
          },
          itemBuilder: (context) => [
            const PopupMenuItem(value: 'view', child: Text('View')),
            const PopupMenuItem(value: 'rename', child: Text('Edit label')),
            const PopupMenuItem(value: 'delete', child: Text('Delete')),
          ],
        ),
      ),
    );
  }

  String _resumeLabel(ApplicantResume resume) {
    final title = resume.title.trim();
    if (title.isNotEmpty) return title;
    return resume.resumeFile.split('/').last;
  }

  String _labelFromFileName(String fileName) {
    return fileName
        .replaceFirst(RegExp(r'\.(pdf|docx)$', caseSensitive: false), '')
        .replaceAll(RegExp(r'[_-]+'), ' ');
  }
}
