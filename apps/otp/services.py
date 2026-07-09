import hashlib
import logging
import random
from datetime import timedelta

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.core.exceptions import ApplicationError
from apps.otp.models import OTPVerification

logger = logging.getLogger(__name__)

OTP_LENGTH = 4
OTP_TTL_MINUTES = 10


def _hash_code(code: str) -> str:
    return hashlib.sha256(f"{code}{settings.SECRET_KEY}".encode()).hexdigest()


def generate_and_send_otp(target: str, purpose: str, channel: str = OTPVerification.Channel.SMS, user=None):
    code = "".join(random.choices("0123456789", k=OTP_LENGTH))

    OTPVerification.objects.filter(target=target, purpose=purpose, is_used=False).update(is_used=True)

    otp = OTPVerification.objects.create(
        user=user,
        target=target,
        code_hash=_hash_code(code),
        purpose=purpose,
        channel=channel,
        expires_at=timezone.now() + timedelta(minutes=OTP_TTL_MINUTES),
        created_by=user,
    )

    _deliver_otp(target, code, channel)
    return otp


def _deliver_otp(target: str, code: str, channel: str):
    if channel == OTPVerification.Channel.EMAIL:
        send_mail(
            subject="Your Quicker-X verification code",
            message=f"Your verification code is {code}. It expires in {OTP_TTL_MINUTES} minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[target],
            fail_silently=True,
        )
    else:
        _send_sms_otp(target, code)


def _send_sms_otp(target: str, code: str):
    """
    Sends the OTP via Fast2SMS if FAST2SMS_API_KEY is configured.
    Falls back to the original DEBUG-log-only behavior if it isn't
    configured yet, so nothing breaks for anyone who hasn't set up an
    SMS provider — this is purely additive.
    """
    api_key = getattr(settings, "FAST2SMS_API_KEY", None)

    if not api_key:
        if settings.DEBUG:
            logger.warning(
                "[DEV-ONLY] SMS OTP for %s: %s (expires in %s min)", target, code, OTP_TTL_MINUTES
            )
        return

    # Fast2SMS's OTP route expects a bare 10-digit Indian mobile number,
    # not the E.164-formatted (+91XXXXXXXXXX) number stored on the model.
    digits = "".join(ch for ch in target if ch.isdigit())
    number = digits[-10:] if len(digits) >= 10 else digits

    try:
        response = requests.post(
            "https://www.fast2sms.com/dev/bulkV2",
            headers={"authorization": api_key},
            data={
                "route": "otp",
                "variables_values": code,
                "numbers": number,
            },
            timeout=10,
        )
        if not response.ok:
            logger.error("Fast2SMS OTP send failed for %s: %s", target, response.text)
    except requests.RequestException:
        logger.exception("Fast2SMS OTP send raised an exception for %s", target)


def verify_otp(target: str, purpose: str, code: str) -> OTPVerification:
    otp = (
        OTPVerification.objects.filter(target=target, purpose=purpose, is_used=False)
        .order_by("-created_at")
        .first()
    )

    if otp is None:
        raise ApplicationError("No active OTP found for this request.", status_code=404)

    if otp.is_expired:
        raise ApplicationError("OTP has expired. Please request a new one.", status_code=400)

    if otp.is_exhausted:
        raise ApplicationError("Maximum verification attempts exceeded.", status_code=429)

    otp.attempts += 1

    if otp.code_hash != _hash_code(code):
        otp.save(update_fields=["attempts"])
        raise ApplicationError("Invalid OTP code.", status_code=400)

    otp.is_used = True
    otp.save(update_fields=["attempts", "is_used"])
    return otp
