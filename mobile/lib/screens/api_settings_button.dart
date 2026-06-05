import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/api_client.dart';

class ApiSettingsButton extends StatelessWidget {
  const ApiSettingsButton({super.key});

  @override
  Widget build(BuildContext context) {
    return TextButton.icon(
      onPressed: () => _showApiSettingsDialog(context),
      icon: const Icon(Icons.settings_outlined),
      label: const Text('API settings'),
    );
  }

  Future<void> _showApiSettingsDialog(BuildContext context) async {
    final apiClient = context.read<ApiClient>();
    final controller = TextEditingController(text: await apiClient.currentBaseUrl());

    if (!context.mounted) {
      controller.dispose();
      return;
    }

    final newBaseUrl = await showDialog<String>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('API settings'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'For a physical phone, use your computer LAN IP instead of 10.0.2.2.',
              ),
              const SizedBox(height: 12),
              TextField(
                controller: controller,
                keyboardType: TextInputType.url,
                decoration: const InputDecoration(
                  labelText: 'Backend API base URL',
                  hintText: 'http://192.168.1.10:8000/api/',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(dialogContext).pop(controller.text),
              child: const Text('Save'),
            ),
          ],
        );
      },
    );

    if (newBaseUrl == null) {
      controller.dispose();
      return;
    }

    final normalizedBaseUrl = ApiClient.normalizeBaseUrl(newBaseUrl);
    await apiClient.updateBaseUrl(normalizedBaseUrl);
    controller.dispose();

    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('API URL saved: $normalizedBaseUrl')),
    );
  }
}
