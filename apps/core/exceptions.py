import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions as drf_exceptions
from rest_framework.views import exception_handler as drf_exception_handler

from apps.core.responses import error_response

logger = logging.getLogger(__name__)


class ApplicationError(Exception):
    """
    Base class for domain/service-layer errors.
    Raise this from services and it will be converted to a clean
    error envelope with the given status code.
    """

    def __init__(self, message, errors=None, status_code=400):
        self.message = message
        self.errors = errors
        self.status_code = status_code
        super().__init__(message)


def custom_exception_handler(exc, context):
    """
    Ensures every error response — DRF validation errors, auth errors,
    404s, permission errors, and our own ApplicationError — is returned
    in the standard { success, message, data, errors, timestamp,
    request_id } envelope.
    """
    if isinstance(exc, ApplicationError):
        return error_response(message=exc.message, errors=exc.errors, status_code=exc.status_code)

    if isinstance(exc, Http404):
        exc = drf_exceptions.NotFound()

    if isinstance(exc, PermissionDenied):
        exc = drf_exceptions.PermissionDenied()

    response = drf_exception_handler(exc, context)

    if response is None:
        logger.exception("Unhandled exception", exc_info=exc)
        return error_response(
            message="Internal server error.",
            errors={"detail": "An unexpected error occurred."},
            status_code=500,
        )

    message = "Validation failed." if response.status_code == 400 else "Request failed."
    if isinstance(exc, drf_exceptions.AuthenticationFailed):
        message = "Authentication failed."
    elif isinstance(exc, drf_exceptions.NotAuthenticated):
        message = "Authentication credentials were not provided."
    elif isinstance(exc, drf_exceptions.PermissionDenied):
        message = "You do not have permission to perform this action."
    elif isinstance(exc, drf_exceptions.NotFound):
        message = "Resource not found."
    elif isinstance(exc, drf_exceptions.Throttled):
        message = "Too many requests. Please try again later."

    return error_response(message=message, errors=response.data, status_code=response.status_code)
