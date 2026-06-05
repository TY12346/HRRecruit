import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../controllers/auth_controller.dart';
import 'auth_form_helpers.dart';

class ResumeUploadScreen extends StatefulWidget {
  const ResumeUploadScreen({super.key});

  @override
  State<ResumeUploadScreen> createState() => _ResumeUploadScreenState();
}

class _ResumeUploadScreenState extends State<ResumeUploadScreen> {
  PlatformFile? _selectedFile;

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
        const SnackBar(content: Text('Unable to access the selected file path.')),
      );
      return;
    }

    setState(() => _selectedFile = file);
  }

  Future<void> _upload() async {
    final file = _selectedFile;
    if (file == null || file.path == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Select a PDF or DOCX resume first.')),
      );
      return;
    }

    try {
      await context.read<AuthController>().uploadResume(
            path: file.path!,
            fileName: file.name,
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Resume uploaded successfully.')),
      );
      setState(() => _selectedFile = null);
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthController>();
    final currentResume = auth.profile?.resumeFile;

    return Scaffold(
      appBar: AppBar(title: const Text('Resume upload')),
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
                      'Current resume',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      currentResume == null || currentResume.isEmpty
                          ? 'No resume uploaded yet.'
                          : currentResume,
                    ),
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
                    const Text('Maximum file size is validated by the backend at 5MB.'),
                    const SizedBox(height: 16),
                    OutlinedButton.icon(
                      onPressed: auth.isLoading ? null : _pickResume,
                      icon: const Icon(Icons.attach_file),
                      label: const Text('Choose resume'),
                    ),
                    if (_selectedFile != null) ...[
                      const SizedBox(height: 12),
                      Text('Selected: ${_selectedFile!.name}'),
                    ],
                    const SizedBox(height: 20),
                    FilledButton.icon(
                      onPressed: auth.isLoading ? null : _upload,
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
    );
  }
}
