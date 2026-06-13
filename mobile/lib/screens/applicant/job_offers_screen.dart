import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/job_offer.dart';
import '../../services/applicant_workflow_service.dart';
import '../auth_form_helpers.dart';
import 'applicant_workflow_widgets.dart';
import '../../widgets/app_navigation.dart';

class JobOffersScreen extends StatefulWidget {
  const JobOffersScreen({super.key});

  @override
  State<JobOffersScreen> createState() => _JobOffersScreenState();
}

class _JobOffersScreenState extends State<JobOffersScreen> {
  late Future<List<JobOffer>> _offersFuture;
  int? _busyOfferId;

  @override
  void initState() {
    super.initState();
    _offersFuture = _loadOffers();
  }

  Future<List<JobOffer>> _loadOffers() {
    return context.read<ApplicantWorkflowService>().getJobOffers();
  }

  void _refresh() {
    setState(() {
      _offersFuture = _loadOffers();
    });
  }

  Future<void> _accept(JobOffer offer) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Accept job offer?'),
        content: const Text('This will notify the recruiter and HR team that you accepted the offer.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Accept')),
        ],
      ),
    );
    if (confirmed != true) return;

    await _submitOfferAction(
      offer,
      () => context.read<ApplicantWorkflowService>().acceptJobOffer(offer.id),
      'Job offer accepted.',
    );
  }

  Future<void> _decline(JobOffer offer) async {
    final reason = await _showDeclineReasonDialog();
    if (reason == null) return;

    await _submitOfferAction(
      offer,
      () => context.read<ApplicantWorkflowService>().declineJobOffer(offer.id, reason: reason),
      'Job offer declined.',
    );
  }

  Future<void> _submitOfferAction(
    JobOffer offer,
    Future<JobOffer> Function() action,
    String successMessage,
  ) async {
    setState(() => _busyOfferId = offer.id);
    try {
      await action();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(successMessage)));
      _refresh();
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    } finally {
      if (mounted) setState(() => _busyOfferId = null);
    }
  }

  Future<String?> _showDeclineReasonDialog() async {
    final controller = TextEditingController();
    final result = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Decline job offer'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            labelText: 'Reason (optional)',
            hintText: 'Share a reason if you want',
          ),
          minLines: 2,
          maxLines: 4,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () => Navigator.pop(context, controller.text.trim()),
            child: const Text('Decline'),
          ),
        ],
      ),
    );
    controller.dispose();
    return result;
  }

  @override
  Widget build(BuildContext context) {
    return AppBackScope(
      child: Scaffold(
        appBar: appScreenAppBar(context, title: 'Job offers'),
        body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async {
            _refresh();
            await _offersFuture;
          },
          child: FutureBuilder<List<JobOffer>>(
            future: _offersFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return ApiErrorMessage(error: snapshot.error!, onRetry: _refresh);
              }
              final offers = snapshot.data ?? [];
              if (offers.isEmpty) {
                return const ApplicantWorkflowMessage(
                  icon: Icons.card_giftcard_outlined,
                  title: 'No job offers yet',
                  message: 'Approved offers from recruiters will appear here.',
                );
              }
              return ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: offers.length,
                itemBuilder: (context, index) {
                  final offer = offers[index];
                  return JobOfferCard(
                    offer: offer,
                    isBusy: _busyOfferId == offer.id,
                    onAccept: () => _accept(offer),
                    onDecline: () => _decline(offer),
                  );
                },
              );
            },
          ),
        ),
      ),
      ),
    );
  }
}
