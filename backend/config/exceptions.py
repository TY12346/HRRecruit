"""API exception handling helpers for clean JSON error responses."""

from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def clean_exception_handler(exc, context):
    """Return JSON for API errors without exposing stack traces."""
    response = drf_exception_handler(exc, context)
    if response is None:
        return Response(
            {'detail': 'Internal server error.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(response.data, list):
        response.data = {'errors': response.data}
    elif not isinstance(response.data, dict):
        response.data = {'detail': response.data}
    return response


def json_server_error(request):
    """Django 500 handler that avoids HTML traceback responses for API clients."""
    return JsonResponse(
        {'detail': 'Internal server error.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
