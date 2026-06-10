# HRRecruit Known Limitations and Future Enhancements

This document records known limitations honestly for FYP submission and examiner review. HRRecruit is a working academic prototype, not a complete production SaaS platform.

## Implemented but Prototype-Level Areas

- Role-based workflows are implemented for the FYP use cases, but production deployments would need more extensive penetration testing and audit logging.
- Organization isolation is implemented in the backend views, but should be re-reviewed before any real multi-tenant production use.
- Analytics and reports are suitable for demo/review data, not large-scale reporting workloads.
- Local media storage is suitable for development/demo but not for production resume and recording storage.

## AI and Resume Screening Limitations

- Scanned-image resumes and OCR are not supported unless OCR is explicitly added and configured.
- Resume parsing quality depends on file text extraction. Image-only PDFs may produce little or no useful text.
- Sentence-BERT or other semantic-model behavior may fall back to local lexical matching if the model/dependency is unavailable.
- AI screening scores are decision-support signals only. The recruiter must make shortlist/reject decisions and the HR head must approve hiring decisions.
- The scoring formula is deterministic and documented for FYP transparency, but it is not validated as an industry-grade hiring model.
- The system does not guarantee bias-free candidate ranking. Human review remains required.

## Interview Transcription and AI Summary Limitations

- Transcription may use mock/demo fallback in demo mode.
- AI interview summary may use mock/demo fallback in demo mode.
- Real ASR/LLM integrations require credentials, privacy review, error handling, and external API mocking in tests.
- Transcript quality is limited by audio quality and the configured transcription implementation.

## Email, Calendar, and Notification Limitations

- Local/demo email uses the Django console email backend.
- Real SendGrid or production email delivery requires additional configuration and testing.
- Calendar integration is not enabled by default and should be treated as optional/future unless explicitly implemented/configured.
- Notifications are application-level records; push notifications such as Firebase Cloud Messaging are not part of the default demo setup.

## Authentication and Account Limitations

- Password reset APIs exist, but password reset UI coverage may be partial depending on the client workflow being demonstrated.
- JWT login is implemented, but refresh-token UX may be partial if client-side refresh handling is not fully wired for every screen.
- Additional production protections such as throttling, suspicious-login detection, account lockout, and MFA are future enhancements.

## Payment and Subscription Limitations

- Demo payment should be used unless a real gateway is configured and tested.
- Stripe-related endpoints/settings are optional and require valid credentials, webhook setup, and sandbox testing.
- PayPal/FPX real payment integrations are not enabled by default.
- Billing data in seeded demo records is fake and intended only for FYP presentation.

## PDF, Reporting, and Analytics Limitations

- PDF export requires `reportlab` and a working backend environment.
- PDF generation has not been optimized for very large organizations or long report histories.
- Analytics are based on application database records and demo workflows; they are not a data warehouse/BI implementation.

## Demo Data Limitations

- Demo data uses fake people, organization details, jobs, applications, interviews, notifications, offers, invoices, and payment records.
- The seed command is intended for demonstration and should not be run against production data.
- Seeded scores/transcripts/summaries are designed to demonstrate workflow behavior, not real candidate evaluation.

## Deployment Limitations

- The documented setup targets local/demo deployment.
- There is no complete production CI/CD pipeline in this repository.
- Static/media serving, HTTPS, observability, backups, and secret management need production-specific setup.
- Local media storage should be replaced or hardened before production usage.

## Future Enhancements

Recommended future work includes:

- OCR support for scanned/image-based resumes.
- Production-grade AI model hosting or properly governed third-party AI integration.
- Bias monitoring, explainability improvements, and configurable screening thresholds.
- Stronger security throttling for login, OTP, password reset, and file upload endpoints.
- Full deployment pipeline with CI/CD, environment separation, migrations, backups, and monitoring.
- Stronger frontend and mobile automated tests.
- End-to-end tests covering the complete web/mobile recruitment lifecycle.
- Real payment/email/calendar production setup with sandbox tests and secure credential handling.
- Push notifications for mobile applicants if needed.
- More advanced analytics, report filters, and audit trails.
