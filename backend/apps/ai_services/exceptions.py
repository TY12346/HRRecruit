"""Shared exceptions for strict AI service failures."""

from rest_framework.exceptions import APIException


class AIServiceUnavailable(APIException):
    """Raised when a required AI provider/model is unavailable or fails."""

    status_code = 503
    default_detail = 'Required AI service is unavailable.'
    default_code = 'ai_service_unavailable'
