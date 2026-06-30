from datetime import timedelta
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.ai_services.summary_service import build_summary_transparency_metadata
from apps.applications.models import ApplicationStageHistory, JobApplication
from apps.billing.models import Payment, Subscription, SubscriptionPlan
from apps.evaluations.models import (
    EvaluationAnswer,
    InterviewAISummary,
    InterviewEvaluation,
    InterviewRecording,
    InterviewTranscript,
)
from apps.hiring.models import HiringDecision, JobOffer
from apps.interviews.models import Interview, InterviewStatusHistory
from apps.jobs.models import EvaluationCriterion, InterviewEvaluationForm, JobPosting, JobRequirement
from apps.notifications.models import Notification
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import ApplicantProfile, ApplicantResume, User, create_profile_for_user


DEMO_PASSWORD = 'DemoPass123!'
DEMO_EMAILS = {
    User.Role.HR_HEAD: 'demo.hrhead@example.com',
    User.Role.RECRUITER: 'demo.recruiter@example.com',
    User.Role.INTERVIEWER: 'demo.interviewer@example.com',
    User.Role.APPLICANT: 'demo.applicant@example.com',
}


class Command(BaseCommand):
    help = 'Create or update fake HRRecruit demo data for FYP demonstrations.'

    def add_arguments(self, parser):
        parser.add_argument('--password', default=DEMO_PASSWORD, help='Password to set for all demo users.')
        parser.add_argument(
            '--no-update-password',
            action='store_true',
            help='Do not reset passwords for existing demo users.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options['password']
        if not password:
            raise CommandError('Password must not be empty.')

        users = self._seed_users(password=password, update_password=not options['no_update_password'])
        resumes = self._seed_resumes(users[User.Role.APPLICANT])
        organization = self._seed_organization(users)
        jobs = self._seed_jobs(organization, users[User.Role.RECRUITER])
        application = self._seed_application(jobs['software_engineer'], users, resumes['software_engineer'])
        interview = self._seed_interview(application, organization, users)
        self._seed_hiring(application, users)
        self._seed_notifications(application, interview, users)
        self._seed_billing(organization)

        self.stdout.write(self.style.SUCCESS('Demo seed data created/updated successfully.'))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Demo login credentials'))
        for role, email in DEMO_EMAILS.items():
            self.stdout.write(f'- {role}: {email} / {password}')
        self.stdout.write('')
        self.stdout.write('Seeded demo organization: TechNova Solutions Sdn Bhd')
        self.stdout.write('Seeded demo jobs: Software Engineer, Data Analyst')
        self.stdout.write('Seeded applicant resumes: Software Engineer Resume, Data Analyst Resume')
        self.stdout.write('Seed command is idempotent and does not delete existing data.')

    def _seed_users(self, password, update_password):
        user_specs = {
            User.Role.HR_HEAD: {
                'email': DEMO_EMAILS[User.Role.HR_HEAD],
                'full_name': 'Demo HR Head',
                'phone_number': '+60010000001',
            },
            User.Role.RECRUITER: {
                'email': DEMO_EMAILS[User.Role.RECRUITER],
                'full_name': 'Demo Recruiter',
                'phone_number': '+60010000002',
            },
            User.Role.INTERVIEWER: {
                'email': DEMO_EMAILS[User.Role.INTERVIEWER],
                'full_name': 'Demo Interviewer',
                'phone_number': '+60010000003',
            },
            User.Role.APPLICANT: {
                'email': DEMO_EMAILS[User.Role.APPLICANT],
                'full_name': 'Demo Applicant',
                'phone_number': '+60010000004',
            },
        }
        users = {}
        for role, spec in user_specs.items():
            email = User.objects.normalize_email(spec['email'])
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'full_name': spec['full_name'],
                    'phone_number': spec['phone_number'],
                    'role': role,
                    'is_active': True,
                },
            )
            changed_fields = []
            for field in ('full_name', 'phone_number'):
                if getattr(user, field) != spec[field]:
                    setattr(user, field, spec[field])
                    changed_fields.append(field)
            if user.role != role:
                user.role = role
                changed_fields.append('role')
            if not user.is_active:
                user.is_active = True
                changed_fields.append('is_active')
            if created or update_password:
                user.set_password(password)
                changed_fields.append('password')
            if changed_fields:
                user.save(update_fields=sorted(set(changed_fields)))
            create_profile_for_user(user)
            users[role] = user

        ApplicantProfile.objects.update_or_create(
            user=users[User.Role.APPLICANT],
            defaults={
                'linkedin_url': 'https://www.linkedin.com/in/demo-applicant',
                'personal_summary': (
                    'Fake demo applicant profile for HRRecruit. Software engineer with Django, React, '
                    'PostgreSQL, REST API, and analytics dashboard experience.'
                ),
            },
        )
        return users

    def _seed_resumes(self, applicant):
        resume_specs = {
            'software_engineer': {
                'title': 'Software Engineer Resume',
                'filename': 'demo-software-engineer-resume.txt',
                'is_default': True,
                'content': (
                    'Demo Software Engineer Resume\n'
                    'Bachelor in Computer Science. 2.5 years building Python, Django, REST API, React, '
                    'PostgreSQL, analytics dashboards, role-based access control, and SaaS workflows.'
                ),
            },
            'data_analyst': {
                'title': 'Data Analyst Resume',
                'filename': 'demo-data-analyst-resume.txt',
                'is_default': False,
                'content': (
                    'Demo Data Analyst Resume\n'
                    'Experience with SQL, Excel, reporting dashboards, hiring funnel metrics, data visualization, '
                    'stakeholder communication, and recruitment analytics.'
                ),
            },
        }
        resumes = {}
        for key, spec in resume_specs.items():
            resume, _ = ApplicantResume.objects.update_or_create(
                applicant=applicant,
                title=spec['title'],
                defaults={'is_default': spec['is_default']},
            )
            if not resume.resume_file:
                resume.resume_file.save(spec['filename'], ContentFile(spec['content'].encode('utf-8')), save=True)
            elif resume.is_default != spec['is_default']:
                resume.is_default = spec['is_default']
                resume.save(update_fields=['is_default'])
            resumes[key] = resume

        profile = applicant.applicant_profile
        if not profile.resume_file:
            profile.resume_file.save('demo-profile-resume.txt', ContentFile(resume_specs['software_engineer']['content'].encode('utf-8')), save=True)
        profile.save(update_fields=['resume_file', 'updated_at'])
        return resumes

    def _seed_organization(self, users):
        organization, _ = Organization.objects.update_or_create(
            registration_no='DEMO-TN-001',
            defaults={
                'name': 'TechNova Solutions Sdn Bhd',
                'email': 'demo.hr@technova.example.com',
                'contact_number': '+60300000000',
                'address': 'Level 10, Demo Tower, Kuala Lumpur, Malaysia',
                'status': Organization.Status.ACTIVE,
                'created_by': users[User.Role.HR_HEAD],
            },
        )
        for role in (User.Role.HR_HEAD, User.Role.RECRUITER, User.Role.INTERVIEWER):
            OrganizationMembership.objects.update_or_create(
                organization=organization,
                user=users[role],
                defaults={'role': role, 'status': OrganizationMembership.Status.ACTIVE},
            )
        return organization

    def _seed_jobs(self, organization, recruiter):
        software_engineer, _ = JobPosting.objects.update_or_create(
            organization=organization,
            title='Software Engineer',
            defaults={
                'recruiter': recruiter,
                'description': (
                    'Build and maintain HRRecruit SaaS modules, REST APIs, recruitment workflows, '
                    'and responsive recruiter dashboards.'
                ),
                'employment_type': 'Full-time',
                'approximate_salary': Decimal('6500.00'),
                'location': 'Kuala Lumpur / Hybrid',
                'status': JobPosting.Status.OPEN,
            },
        )
        data_analyst, _ = JobPosting.objects.update_or_create(
            organization=organization,
            title='Data Analyst',
            defaults={
                'recruiter': recruiter,
                'description': (
                    'Prepare recruitment funnel reports, analyze hiring metrics, and build operational '
                    'dashboards for HR leadership.'
                ),
                'employment_type': 'Full-time',
                'approximate_salary': Decimal('5200.00'),
                'location': 'Kuala Lumpur',
                'status': JobPosting.Status.OPEN,
            },
        )
        self._seed_requirements(
            software_engineer,
            [
                (JobRequirement.RequirementType.SKILL, 'Python, Django, React, PostgreSQL, REST API', '40.00', '70.00'),
                (JobRequirement.RequirementType.EDUCATION, 'Bachelor in Computer Science or related field', '20.00', '60.00'),
                (JobRequirement.RequirementType.EXPERIENCE, 'At least 2 years of software development experience', '30.00', '65.00'),
                (JobRequirement.RequirementType.OTHER, 'Good communication and teamwork skills', '10.00', '60.00'),
            ],
        )
        self._seed_requirements(
            data_analyst,
            [
                (JobRequirement.RequirementType.SKILL, 'SQL, Excel, dashboard reporting, data visualization', '45.00', '65.00'),
                (JobRequirement.RequirementType.EDUCATION, 'Bachelor in Data Analytics, Statistics, Business, or related field', '20.00', '60.00'),
                (JobRequirement.RequirementType.EXPERIENCE, '1-2 years of analytics or reporting experience', '25.00', '55.00'),
                (JobRequirement.RequirementType.OTHER, 'Able to explain insights clearly to HR stakeholders', '10.00', '60.00'),
            ],
        )
        self._seed_evaluation_form(software_engineer)
        self._seed_evaluation_form(data_analyst)
        return {'software_engineer': software_engineer, 'data_analyst': data_analyst}

    def _seed_requirements(self, job, requirements):
        for requirement_type, description, weight_score, minimum_threshold in requirements:
            JobRequirement.objects.update_or_create(
                job=job,
                requirement_type=requirement_type,
                description=description,
                defaults={
                    'weight_score': Decimal(weight_score),
                    'minimum_threshold': Decimal(minimum_threshold),
                },
            )

    def _seed_evaluation_form(self, job):
        form, _ = InterviewEvaluationForm.objects.update_or_create(
            job=job,
            defaults={'title': f'{job.title} Interview Evaluation'},
        )
        criteria = [
            ('Technical fit', 'Role-specific technical and problem-solving capability.', '10.00', '40.00'),
            ('Communication', 'Clarity, listening, and ability to explain decisions.', '10.00', '25.00'),
            ('Culture and teamwork', 'Collaboration, ownership, and professional attitude.', '10.00', '20.00'),
            ('Learning agility', 'Ability to learn new tools and improve from feedback.', '10.00', '15.00'),
        ]
        for name, description, max_score, weight_score in criteria:
            EvaluationCriterion.objects.update_or_create(
                form=form,
                criterion_name=name,
                defaults={
                    'description': description,
                    'max_score': Decimal(max_score),
                    'weight_score': Decimal(weight_score),
                },
            )
        return form

    def _seed_application(self, job, users, selected_resume):
        semantic_score = Decimal('82.00')
        skill_score = Decimal('88.00')
        experience_score = Decimal('78.00')
        education_score = Decimal('85.00')
        final_score = (
            Decimal('0.4') * semantic_score
            + Decimal('0.3') * skill_score
            + Decimal('0.2') * experience_score
            + Decimal('0.1') * education_score
        ).quantize(Decimal('0.01'))
        application, _ = JobApplication.objects.update_or_create(
            applicant=users[User.Role.APPLICANT],
            job=job,
            defaults={
                'status': JobApplication.Status.HIRED,
                'resume': selected_resume,
                'recruiter_remark': 'Demo candidate completed the full FYP workflow and accepted the offer.',
                'assigned_interviewer': users[User.Role.INTERVIEWER],
                'extracted_resume_text': (
                    'Fake demo resume: Bachelor in Computer Science. 2.5 years building Python, Django, '
                    'React, PostgreSQL, and REST API projects. Built analytics dashboards and collaborated '
                    'with cross-functional teams.'
                ),
                'extracted_skills': ['Python', 'Django', 'React', 'PostgreSQL', 'REST API'],
                'extracted_experience': {
                    'years': 2.5,
                    'summary': '2.5 years of software development experience in SaaS and analytics projects.',
                },
                'extracted_education': {
                    'highest_level': 'Bachelor',
                    'field': 'Computer Science',
                    'matches_requirement': True,
                },
                'semantic_score': semantic_score,
                'skill_score': skill_score,
                'experience_score': experience_score,
                'education_score': education_score,
                'final_score': final_score,
                'score_explanation': {
                    'formula': '0.4 * semantic_score + 0.3 * skill_score + 0.2 * experience_score + 0.1 * education_score',
                    'summary': 'Strong skill match and relevant education; experience meets the 2-year requirement.',
                    'decision_support_note': 'AI screening supports recruiter review and does not make the final hiring decision.',
                },
            },
        )
        self._ensure_application_history(application, JobApplication.Status.SUBMITTED, JobApplication.Status.SCREENED_QUALIFIED, users[User.Role.RECRUITER], 'AI screening qualified for recruiter review.')
        self._ensure_application_history(application, JobApplication.Status.SCREENED_QUALIFIED, JobApplication.Status.SHORTLISTED, users[User.Role.RECRUITER], 'Recruiter shortlisted candidate for interview.')
        self._ensure_application_history(application, JobApplication.Status.SHORTLISTED, JobApplication.Status.INTERVIEW_ACCEPTED, users[User.Role.APPLICANT], 'Applicant accepted scheduled interview.')
        self._ensure_application_history(application, JobApplication.Status.INTERVIEW_ACCEPTED, JobApplication.Status.EVALUATION_SUBMITTED, users[User.Role.INTERVIEWER], 'Interviewer submitted evaluation.')
        self._ensure_application_history(application, JobApplication.Status.EVALUATION_SUBMITTED, JobApplication.Status.HIRED, users[User.Role.HR_HEAD], 'HR head approved hiring and applicant accepted offer.')
        return application

    def _ensure_application_history(self, application, from_stage, to_stage, changed_by, note):
        ApplicationStageHistory.objects.get_or_create(
            application=application,
            from_stage=from_stage,
            to_stage=to_stage,
            defaults={'changed_by': changed_by, 'note': note},
        )

    def _seed_interview(self, application, organization, users):
        scheduled_datetime = timezone.now() + timedelta(days=2)
        interview, _ = Interview.objects.update_or_create(
            application=application,
            organization=organization,
            defaults={
                'recruiter': users[User.Role.RECRUITER],
                'interviewer': users[User.Role.INTERVIEWER],
                'scheduled_datetime': scheduled_datetime,
                'mode': Interview.Mode.ONLINE,
                'meeting_link': 'https://meet.example.com/hrrecruit-demo-software-engineer',
                'location': '',
                'status': Interview.Status.COMPLETED,
            },
        )
        self._ensure_interview_history(interview, Interview.Status.ASSIGNED, Interview.Status.SCHEDULED, users[User.Role.RECRUITER], 'Recruiter scheduled interview.')
        self._ensure_interview_history(interview, Interview.Status.SCHEDULED, Interview.Status.COMPLETED, users[User.Role.INTERVIEWER], 'Interview completed for demo workflow.')
        recording = self._seed_recording(interview, users[User.Role.INTERVIEWER])
        transcript = self._seed_transcript(recording)
        self._seed_ai_summary(transcript, users[User.Role.INTERVIEWER])
        self._seed_evaluation(interview, users[User.Role.INTERVIEWER])
        return interview

    def _ensure_interview_history(self, interview, from_status, to_status, changed_by, note):
        InterviewStatusHistory.objects.get_or_create(
            interview=interview,
            from_status=from_status,
            to_status=to_status,
            defaults={'changed_by': changed_by, 'note': note},
        )

    def _seed_recording(self, interview, uploaded_by):
        recording = InterviewRecording.objects.filter(interview=interview, uploaded_by=uploaded_by).first()
        if recording:
            return recording
        recording = InterviewRecording(interview=interview, uploaded_by=uploaded_by)
        recording.audio_file.save('demo-interview-placeholder.mp3', ContentFile(b'Fake demo audio placeholder.'), save=True)
        return recording

    def _seed_transcript(self, recording):
        transcript_text = (
            'Interviewer: Please describe your Django experience. Candidate: I built REST APIs, '
            'implemented role-based permissions, and optimized PostgreSQL queries. Interviewer: How do you '
            'work with React teams? Candidate: I align API contracts early and test workflows end to end.'
        )
        transcript, _ = InterviewTranscript.objects.update_or_create(
            recording=recording,
            defaults={
                'transcript_text': transcript_text,
                'transcript_json': {
                    'provider': 'mock',
                    'segments': [
                        {'speaker': 'Interviewer', 'text': 'Please describe your Django experience.'},
                        {'speaker': 'Candidate', 'text': 'I built REST APIs and optimized PostgreSQL queries.'},
                    ],
                },
            },
        )
        return transcript

    def _seed_ai_summary(self, transcript, interviewer):
        InterviewAISummary.objects.update_or_create(
            transcript=transcript,
            defaults={
                'strengths': 'Strong Django, REST API, React collaboration, and PostgreSQL understanding.',
                'weaknesses': 'Could provide deeper examples of production incident handling.',
                'communication_score': Decimal('8.50'),
                'overall_impression': 'Positive fit for the Software Engineer demo role.',
                'editable_summary_text': (
                    'Mock AI summary for demo only. Candidate communicates clearly, meets the core technical '
                    'requirements, and should be reviewed by the recruiter and HR head before any final decision.'
                ),
                'summary_json': {
                    'transparency': build_summary_transparency_metadata(
                        transcript.transcript_text,
                        provider='mock',
                        model='seed-demo-summary',
                        fallback_reason='Seeded deterministic demo summary.',
                        generation_mode='seeded_mock',
                    ),
                },
                'edited_by': interviewer,
            },
        )

    def _seed_evaluation(self, interview, interviewer):
        evaluation, _ = InterviewEvaluation.objects.update_or_create(
            interview=interview,
            interviewer=interviewer,
            defaults={
                'total_score': Decimal('84.00'),
                'overall_comment': 'Recommended for hire in the demo workflow based on technical fit and communication.',
            },
        )
        form = interview.application.job.interview_evaluation_form
        score_map = {
            'Technical fit': Decimal('8.50'),
            'Communication': Decimal('8.00'),
            'Culture and teamwork': Decimal('8.50'),
            'Learning agility': Decimal('8.50'),
        }
        for criterion in form.criteria.all():
            EvaluationAnswer.objects.update_or_create(
                evaluation=evaluation,
                criterion=criterion,
                defaults={
                    'score': score_map.get(criterion.criterion_name, Decimal('8.00')),
                    'comment': f'Demo evaluation answer for {criterion.criterion_name}.',
                },
            )

    def _seed_hiring(self, application, users):
        decision, _ = HiringDecision.objects.update_or_create(
            application=application,
            recruiter=users[User.Role.RECRUITER],
            defaults={
                'decision': HiringDecision.Decision.HIRE,
                'recruiter_justification': (
                    'Candidate passed AI-assisted screening, interview evaluation, and role-fit review. '
                    'Recruiter recommends hire; HR head remains final approver.'
                ),
                'status': HiringDecision.Status.APPROVED,
                'hr_head': users[User.Role.HR_HEAD],
                'hr_head_justification': 'Approved for demo offer after reviewing recruiter recommendation and interview evidence.',
                'reviewed_at': timezone.now(),
            },
        )
        JobOffer.objects.update_or_create(
            application=application,
            defaults={
                'offer_message': (
                    'Fake demo offer for Software Engineer at TechNova Solutions Sdn Bhd. This offer is '
                    'for FYP demonstration only and contains no real employment commitment.'
                ),
                'salary_amount': Decimal('6500.00'),
                'salary_currency': 'MYR',
                'start_date': timezone.localdate() + timedelta(days=21),
                'employment_type': 'Full-time',
                'work_arrangement': 'Hybrid',
                'probation_months': 3,
                'benefits_summary': 'Medical coverage, annual leave, learning allowance, and hybrid work arrangement.',
                'internal_notes': 'Seeded demo offer. No real employment commitment.',
                'candidate_response_note': 'Accepted for the FYP demo workflow.',
                'offer_status': JobOffer.OfferStatus.ACCEPTED,
                'respond_deadline': timezone.now() + timedelta(days=7),
                'responded_at': timezone.now(),
            },
        )
        return decision

    def _seed_notifications(self, application, interview, users):
        notifications = [
            (users[User.Role.APPLICANT], 'application_status', 'Application shortlisted', 'Your demo Software Engineer application was shortlisted.', 'JobApplication', application.id),
            (users[User.Role.APPLICANT], 'interview_scheduled', 'Interview scheduled', 'Your demo interview has been scheduled.', 'Interview', interview.id),
            (users[User.Role.APPLICANT], 'job_offer', 'Demo job offer accepted', 'Your fake demo job offer has been accepted.', 'JobOffer', application.job_offers.first().id),
            (users[User.Role.RECRUITER], 'hiring_decision_update', 'HR approved recommendation', 'The HR head approved the demo hiring recommendation.', 'HiringDecision', application.hiring_decisions.first().id),
            (users[User.Role.HR_HEAD], 'hiring_decision_update', 'Offer accepted', 'The applicant accepted the fake demo offer.', 'JobApplication', application.id),
        ]
        for recipient, notification_type, title, message, entity_type, entity_id in notifications:
            Notification.objects.update_or_create(
                recipient=recipient,
                notification_type=notification_type,
                related_entity_type=entity_type,
                related_entity_id=entity_id,
                defaults={'title': title, 'message': message, 'is_read': False},
            )

    def _seed_billing(self, organization):
        plan, _ = SubscriptionPlan.objects.update_or_create(
            name=SubscriptionPlan.Name.PRO,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            defaults={
                'max_job_postings': 10,
                'price': Decimal('299.00'),
                'features_description': 'Demo Pro plan for FYP workflow with multiple active job postings.',
                'is_active': True,
            },
        )
        start_date = timezone.localdate()
        end_date = start_date + timedelta(days=30)
        subscription = Subscription.objects.filter(organization=organization, plan=plan, status=Subscription.Status.ACTIVE).first()
        if subscription:
            subscription.start_date = start_date
            subscription.end_date = end_date
            subscription.is_auto_renew = False
            subscription.cancel_at_period_end = False
            subscription.cancelled_at = None
            subscription.cancellation_reason = ''
            subscription.save(
                update_fields=[
                    'start_date',
                    'end_date',
                    'is_auto_renew',
                    'cancel_at_period_end',
                    'cancelled_at',
                    'cancellation_reason',
                ]
            )
        else:
            subscription = Subscription.objects.create(
                organization=organization,
                plan=plan,
                start_date=start_date,
                end_date=end_date,
                status=Subscription.Status.ACTIVE,
                is_auto_renew=False,
            )
        payment = Payment.objects.filter(subscription=subscription, payment_gateway=Payment.PaymentGateway.DEMO).first()
        if payment:
            payment.transaction_reference = 'DEMO-SEED-PAYMENT'
            payment.amount = plan.price
            payment.currency = 'MYR'
            payment.status = Payment.Status.PAID
            payment.billing_reason = Payment.BillingReason.SUBSCRIPTION_CREATE
            payment.paid_at = timezone.now()
            payment.due_at = timezone.now()
            payment.failure_reason = ''
            payment.save(
                update_fields=[
                    'transaction_reference',
                    'amount',
                    'currency',
                    'status',
                    'billing_reason',
                    'paid_at',
                    'due_at',
                    'failure_reason',
                ]
            )
        else:
            Payment.objects.create(
                subscription=subscription,
                payment_gateway=Payment.PaymentGateway.DEMO,
                transaction_reference='DEMO-SEED-PAYMENT',
                amount=plan.price,
                currency='MYR',
                status=Payment.Status.PAID,
                billing_reason=Payment.BillingReason.SUBSCRIPTION_CREATE,
                paid_at=timezone.now(),
                due_at=timezone.now(),
            )
