"""Interview evaluation APIs with AI service-backed transcription and summaries."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_services.interview_evaluation import generate_interview_summary, transcribe_interview_recording
from apps.interviews.models import Interview
from apps.notifications.services import create_notification
from apps.interviews.views import visible_interviews_for
from apps.users.models import User
from .models import InterviewAISummary, InterviewEvaluation, InterviewRecording, InterviewTranscript
from .serializers import (
    InterviewAISummarySerializer,
    InterviewAISummaryUpdateSerializer,
    InterviewEvaluationDetailSerializer,
    InterviewEvaluationSerializer,
    InterviewEvaluationSubmitSerializer,
    InterviewRecordingSerializer,
    InterviewRecordingUploadSerializer,
    InterviewTranscriptSerializer,
)


def assigned_interview_or_404(user, interview_id):
    if user.role != User.Role.INTERVIEWER:
        raise PermissionDenied('Only the assigned interviewer can perform this action.')
    return get_object_or_404(visible_interviews_for(user), id=interview_id)


def assigned_recording_or_404(user, recording_id):
    if user.role != User.Role.INTERVIEWER:
        raise PermissionDenied('Only the assigned interviewer can perform this action.')
    return get_object_or_404(
        InterviewRecording.objects.select_related(
            'interview',
            'interview__application',
            'interview__application__job',
            'interview__application__applicant',
            'interview__interviewer',
            'interview__organization',
        ),
        id=recording_id,
        interview__in=visible_interviews_for(user),
    )


def assigned_transcript_or_404(user, transcript_id):
    if user.role != User.Role.INTERVIEWER:
        raise PermissionDenied('Only the assigned interviewer can perform this action.')
    return get_object_or_404(
        InterviewTranscript.objects.select_related(
            'recording',
            'recording__interview',
            'recording__interview__application',
            'recording__interview__application__job',
            'recording__interview__interviewer',
        ),
        id=transcript_id,
        recording__interview__in=visible_interviews_for(user),
    )


def assigned_summary_or_404(user, summary_id):
    if user.role != User.Role.INTERVIEWER:
        raise PermissionDenied('Only the assigned interviewer can edit interview summaries.')
    return get_object_or_404(
        InterviewAISummary.objects.select_related(
            'transcript',
            'transcript__recording',
            'transcript__recording__interview',
            'transcript__recording__interview__application',
            'transcript__recording__interview__interviewer',
        ),
        id=summary_id,
        transcript__recording__interview__in=visible_interviews_for(user),
    )


def recruiter_owned_interview_or_404(user, interview_id):
    if user.role != User.Role.RECRUITER:
        raise PermissionDenied('Only the recruiter who owns the application can view evaluation detail.')
    return get_object_or_404(
        visible_interviews_for(user).prefetch_related('evaluations__answers__criterion'),
        id=interview_id,
        application__job__recruiter=user,
    )


class InterviewRecordingUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, interview_id):
        interview = assigned_interview_or_404(request.user, interview_id)
        serializer = InterviewRecordingUploadSerializer(
            data=request.data,
            context={'request': request, 'interview': interview},
        )
        serializer.is_valid(raise_exception=True)
        recording = serializer.save()
        return Response(InterviewRecordingSerializer(recording, context={'request': request}).data, status=status.HTTP_201_CREATED)


class InterviewRecordingTranscribeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, recording_id):
        recording = assigned_recording_or_404(request.user, recording_id)
        transcription_result = transcribe_interview_recording(recording)
        transcript = InterviewTranscript.objects.create(recording=recording, **transcription_result)
        return Response(InterviewTranscriptSerializer(transcript).data, status=status.HTTP_201_CREATED)


class InterviewTranscriptGenerateSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, transcript_id):
        transcript = assigned_transcript_or_404(request.user, transcript_id)
        summary_payload = generate_interview_summary(transcript)
        summary = InterviewAISummary.objects.create(transcript=transcript, **summary_payload)
        return Response(InterviewAISummarySerializer(summary, context={'request': request}).data, status=status.HTTP_201_CREATED)


class InterviewAISummaryUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, summary_id):
        summary = assigned_summary_or_404(request.user, summary_id)
        interview = summary.transcript.recording.interview
        if InterviewEvaluation.objects.filter(interview=interview).exists():
            raise ValidationError({'summary': 'AI summary cannot be edited after final evaluation submission.'})
        serializer = InterviewAISummaryUpdateSerializer(
            summary,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        summary = serializer.save()
        return Response(InterviewAISummarySerializer(summary, context={'request': request}).data)


class InterviewEvaluationSubmitAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, interview_id):
        interview = assigned_interview_or_404(request.user, interview_id)
        if InterviewEvaluation.objects.filter(interview=interview).exists():
            raise ValidationError({'interview': 'An evaluation has already been submitted for this interview.'})

        serializer = InterviewEvaluationSubmitSerializer(
            data=request.data,
            context={'request': request, 'interview': interview},
        )
        serializer.is_valid(raise_exception=True)
        evaluation = serializer.save()
        interview.change_status(Interview.Status.COMPLETED, changed_by=request.user, note='Interview evaluation submitted.')
        create_notification(
            interview.recruiter,
            'evaluation_submitted',
            'Interview evaluation submitted',
            f'{request.user.full_name} submitted an evaluation for {interview.application.applicant.full_name}.',
            related_entity=evaluation,
        )
        return Response(InterviewEvaluationSerializer(evaluation).data, status=status.HTTP_201_CREATED)


class InterviewEvaluationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, interview_id):
        interview = recruiter_owned_interview_or_404(request.user, interview_id)
        return Response(InterviewEvaluationDetailSerializer(interview).data)
