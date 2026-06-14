import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AppBackScope extends StatelessWidget {
  const AppBackScope({
    required this.child,
    this.fallbackLocation = '/home',
    super.key,
  });

  final Widget child;
  final String fallbackLocation;

  @override
  Widget build(BuildContext context) {
    return PopScope<Object?>(
      canPop: context.canPop(),
      onPopInvokedWithResult: (didPop, result) {
        if (didPop) return;
        context.go(fallbackLocation);
      },
      child: child,
    );
  }
}

class AppUpButton extends StatelessWidget {
  const AppUpButton({
    this.fallbackLocation = '/home',
    super.key,
  });

  final String fallbackLocation;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: MaterialLocalizations.of(context).backButtonTooltip,
      icon: const Icon(Icons.arrow_back),
      onPressed: () {
        if (context.canPop()) {
          context.pop();
        } else {
          context.go(fallbackLocation);
        }
      },
    );
  }
}

AppBar appScreenAppBar(
  BuildContext context, {
  required String title,
  String fallbackLocation = '/home',
  List<Widget>? actions,
}) {
  return AppBar(
    leading: AppUpButton(fallbackLocation: fallbackLocation),
    title: Text(title),
    actions: actions,
  );
}
