import secrets
import threading
import time

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


ULID_ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
_ULID_LOCK = threading.Lock()
_LAST_TIMESTAMP = -1
_LAST_RANDOMNESS = 0


def _encode_crockford(value, length):
    characters = []
    for _ in range(length):
        value, remainder = divmod(value, 32)
        characters.append(ULID_ALPHABET[remainder])
    return ''.join(reversed(characters))


def generate_readable_id(prefix):
    """Return a typed ULID: a sortable timestamp plus 80 random bits."""
    global _LAST_RANDOMNESS, _LAST_TIMESTAMP
    with _ULID_LOCK:
        timestamp_value = int(time.time_ns() // 1_000_000)
        if timestamp_value == _LAST_TIMESTAMP:
            _LAST_RANDOMNESS = (_LAST_RANDOMNESS + 1) % (1 << 80)
        else:
            _LAST_TIMESTAMP = timestamp_value
            _LAST_RANDOMNESS = secrets.randbits(80)
        timestamp = _encode_crockford(timestamp_value, 10)
        randomness = _encode_crockford(_LAST_RANDOMNESS, 16)
    return f'{prefix}-{timestamp}{randomness}'


class ReadableIdManager(models.Manager):
    def bulk_create(self, objs, **kwargs):
        # Django accepts any iterable here. Materialize it before assigning IDs so
        # generator expressions are not exhausted before Django inserts them.
        objs = list(objs)
        for obj in objs:
            if not obj.public_id:
                obj.public_id = generate_readable_id(obj.readable_id_prefix())
        return super().bulk_create(objs, **kwargs)


class ReadableIdModel(models.Model):
    """Keep numeric database PKs while giving every domain record a public ID."""

    public_id = models.CharField(max_length=30, unique=True, editable=False)
    objects = ReadableIdManager()

    class Meta:
        abstract = True

    @classmethod
    def readable_id_prefix(cls):
        return READABLE_ID_PREFIXES.get(cls._meta.label, cls.__name__[:3].upper())

    def save(self, *args, **kwargs):
        if not self.public_id:
            self.public_id = generate_readable_id(self.readable_id_prefix())
        return super().save(*args, **kwargs)
