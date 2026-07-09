from apps.audit.models import LoginHistory


def record_login_attempt(request, identifier, status, user=None, failure_reason="", device_id=""):
    ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get(
        "REMOTE_ADDR"
    )
    LoginHistory.objects.create(
        user=user,
        identifier_attempted=identifier,
        status=status,
        failure_reason=failure_reason,
        ip_address=ip,
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        device_id=device_id,
        created_by=user,
    )
