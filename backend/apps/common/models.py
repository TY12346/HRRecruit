import uuid

from django.db import models


READABLE_ID_PREFIXES = {
    'applications.ApplicationStageHistory': 'ASH',
    'applications.EmployerInvite': 'INV',
    'applications.JobApplication': 'APP',
    'billing.Payment': 'PAY',
    'billing.Subscription': 'SUB',
    'billing.SubscriptionPlan': 'PLN',
    'evaluations.EvaluationAnswer': 'EVA',
    'evaluations.InterviewAISummary': 'AIS',
    'evaluations.InterviewEvaluation': 'EVL',
    'evaluations.InterviewRecording': 'REC',
    'evaluations.InterviewTranscript': 'TRN',
    'hiring.HiringDecision': 'HDC',
    'hiring.JobHiringDecision': 'JHD',
    'hiring.JobHiringDecisionItem': 'HDI',
    'hiring.JobOffer': 'OFR',
    'interviews.CalendarEvent': 'CAL',
    'interviews.GoogleCalendarCredential': 'GCC',
    'interviews.Interview': 'INT',
    'interviews.InterviewerAvailabilityPattern': 'AVP',
    'interviews.InterviewerAvailabilitySlot': 'AVS',
    'interviews.InterviewerUnavailableDate': 'UVD',
    'interviews.InterviewSchedulingRequest': 'ISR',
    'interviews.InterviewStatusHistory': 'ISH',
    'jobs.EvaluationCriterion': 'ECR',
    'jobs.InterviewEvaluationForm': 'IEF',
    'jobs.JobPosting': 'JOB',
    'jobs.JobRequirement': 'REQ',
    'jobs.JobRequisition': 'JRE',
    'jobs.SavedJobPosting': 'SAV',
    'notifications.Notification': 'NTF',
    'notifications.PushDevice': 'DEV',
    'organizations.Organization': 'ORG',
    'organizations.OrganizationMembership': 'MEM',
    'users.ApplicantEducation': 'EDU',
    'users.ApplicantExperience': 'EXP',
    'users.ApplicantProfile': 'APF',
    'users.ApplicantResume': 'RSM',
    'users.ApplicantSkill': 'SKL',
    'users.HRHeadProfile': 'HRP',
    'users.InterviewerProfile': 'IPF',
    'users.PasswordResetOTP': 'OTP',
    'users.RecruiterProfile': 'RPF',
    'users.User': 'USR',
}


def generate_readable_id(prefix):
    """Return a non-sequential identifier that is safe to show to users."""
    return f'{prefix}-{uuid.uuid4().hex[:12].upper()}'


class ReadableIdModel(models.Model):
    """Keep numeric database PKs while giving every domain record a public ID."""

    public_id = models.CharField(max_length=16, unique=True, editable=False)

    class Meta:
        abstract = True

    @classmethod
    def readable_id_prefix(cls):
        return READABLE_ID_PREFIXES.get(cls._meta.label, cls.__name__[:3].upper())

    def save(self, *args, **kwargs):
        if not self.public_id:
            self.public_id = generate_readable_id(self.readable_id_prefix())
        return super().save(*args, **kwargs)
