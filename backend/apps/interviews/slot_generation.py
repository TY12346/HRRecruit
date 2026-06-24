from dataclasses import dataclass
from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import Interview, InterviewerAvailabilityPattern, InterviewerUnavailableDate


@dataclass(frozen=True)
class GeneratedInterviewSlot:
    id: str
    pattern_id: int
    date: object
    start_time: time
    end_time: time
    start_datetime: object
    end_datetime: object
    mode: str
    meeting_link: str
    location: str
    status: str = 'available'


def _combine_local(day, clock):
    return timezone.make_aware(datetime.combine(day, clock), timezone.get_current_timezone())


def generate_available_slots(interviewer, organization, days_ahead=28, from_datetime=None):
    now = from_datetime or timezone.now()
    start_date = timezone.localdate(now)
    end_date = start_date + timedelta(days=days_ahead)
    patterns = InterviewerAvailabilityPattern.objects.filter(
        organization=organization,
        interviewer=interviewer,
        is_active=True,
        effective_from__lte=end_date,
    ).filter(models_effective_until_filter(start_date)).order_by('day_of_week', 'start_time')
    unavailable = set(InterviewerUnavailableDate.objects.filter(
        organization=organization,
        interviewer=interviewer,
        date__range=(start_date, end_date),
    ).values_list('date', flat=True))
    booked = set(Interview.objects.filter(
        organization=organization,
        interviewer=interviewer,
        interview_date__range=(start_date, end_date),
        status__in=[Interview.Status.ASSIGNED, Interview.Status.SCHEDULED],
    ).values_list('interview_date', 'start_time', 'end_time'))
    slots = []
    for pattern in patterns:
        day = start_date
        while day <= end_date:
            if day.weekday() == pattern.day_of_week and day not in unavailable:
                if day >= pattern.effective_from and (not pattern.effective_until or day <= pattern.effective_until):
                    start_dt = _combine_local(day, pattern.start_time)
                    final_dt = _combine_local(day, pattern.end_time)
                    while start_dt + timedelta(minutes=pattern.slot_duration_minutes) <= final_dt:
                        end_dt = start_dt + timedelta(minutes=pattern.slot_duration_minutes)
                        if start_dt > now and (day, start_dt.time().replace(microsecond=0), end_dt.time().replace(microsecond=0)) not in booked:
                            slots.append(GeneratedInterviewSlot(
                                id=f'pattern:{pattern.id}:{day.isoformat()}:{start_dt.time().strftime("%H:%M")}',
                                pattern_id=pattern.id,
                                date=day,
                                start_time=start_dt.time().replace(microsecond=0),
                                end_time=end_dt.time().replace(microsecond=0),
                                start_datetime=start_dt,
                                end_datetime=end_dt,
                                mode=pattern.mode,
                                meeting_link=pattern.meeting_link,
                                location=pattern.location,
                            ))
                        start_dt = end_dt
            day += timedelta(days=1)
    return sorted(slots, key=lambda slot: slot.start_datetime)


def models_effective_until_filter(start_date):
    from django.db import models
    return models.Q(effective_until__isnull=True) | models.Q(effective_until__gte=start_date)
