"""
Standard API response envelope used by every endpoint in Quicker-X.

Contract:
{
    "success": bool,
    "message": str,
    "data": any | null,
    "errors": any | null,
    "timestamp": ISO8601 string,
    "request_id": str
}
"""
from django.utils import timezone
from rest_framework.response import Response


def _request_id():
    from apps.core.request_context import get_request_id
    return get_request_id()


def success_response(data=None, message="Success", status_code=200, extra_meta=None):
    payload = {
        "success": True,
        "message": message,
        "data": data,
        "errors": None,
        "timestamp": timezone.now().isoformat(),
        "request_id": _request_id(),
    }
    if extra_meta:
        payload.update(extra_meta)
    return Response(payload, status=status_code)


def error_response(message="Something went wrong", errors=None, status_code=400):
    payload = {
        "success": False,
        "message": message,
        "data": None,
        "errors": errors,
        "timestamp": timezone.now().isoformat(),
        "request_id": _request_id(),
    }
    return Response(payload, status=status_code)
