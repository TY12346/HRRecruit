"""API exception handling helpers for clean JSON error responses."""

import logging

from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


logger = logging.getLogger(__name__)


def clean_exception_handler(exc, context):
    """Return JSON for API errors without exposing stack traces."""
    response = drf_exception_handler(exc, context)
    if response is None:
        view = context.get('view')
        view_name = view.__class__.__name__ if view else 'unknown view'
        logger.exception('Unhandled API exception in %s.', view_name)
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
