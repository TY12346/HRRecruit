import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/api_client.dart';

class ApiSettingsButton extends StatefulWidget {
  const ApiSettingsButton({super.key});

  @override
  State<ApiSettingsButton> createState() => _ApiSettingsButtonState();
}

class _ApiSettingsButtonState extends State<ApiSettingsButton> {
  late Future<String> _currentBaseUrl;

  @override
  void initState() {
    super.initState();
    _currentBaseUrl = context.read<ApiClient>().currentBaseUrl();
  }

  void _refreshCurrentBaseUrl() {
    setState(() {
      _currentBaseUrl = context.read<ApiClient>().currentBaseUrl();
    });
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<String>(
      future: _currentBaseUrl,
      builder: (context, snapshot) {
        final currentUrl = snapshot.data ?? ApiClient.defaultBaseUrl;
        return Column(
          children: [
            const SizedBox(height: 8),
            Text(
              'Current API: $currentUrl',
              style: Theme.of(context).textTheme.bodySmall,
              textAlign: TextAlign.center,
            ),
            if (currentUrl.contains('10.0.2.2'))
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(
                  '10.0.2.2 only works in the Android emulator. For this phone, use your computer LAN IP.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.error,
                      ),
                  textAlign: TextAlign.center,
                ),
              ),
            TextButton.icon(
              onPressed: () => _showApiSettingsDialog(context),
              icon: const Icon(Icons.settings_outlined),
              label: const Text('API settings'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _showApiSettingsDialog(BuildContext context) async {
    final apiClient = context.read<ApiClient>();
    final controller = TextEditingController(text: await apiClient.currentBaseUrl());

    if (!context.mounted) {
      controller.dispose();
      return;
    }

    final apiSettingAction = await showDialog<String>(
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
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop('__default__'),
              child: const Text('Use default'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(dialogContext).pop(controller.text),
              child: const Text('Save'),
            ),
          ],
        );
      },
    );

    if (apiSettingAction == null) {
      controller.dispose();
      return;
    }

    final normalizedBaseUrl = apiSettingAction == '__default__'
        ? await apiClient.resetBaseUrlToDefault()
        : ApiClient.normalizeBaseUrl(apiSettingAction);
    if (apiSettingAction != '__default__') {
      await apiClient.updateBaseUrl(normalizedBaseUrl);
    }
    controller.dispose();
    _refreshCurrentBaseUrl();

    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('API URL saved: $normalizedBaseUrl')),
    );
  }
}
