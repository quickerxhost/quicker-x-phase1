"""
Lazy Firebase Admin SDK initializer.

Used to verify Firebase Phone Auth ID tokens sent up by the Flutter app,
so the backend can trust that a phone number was actually OTP-verified by
Firebase without ever handling the SMS itself.

Configuration (set ONE of these as a Render env var):
  FIREBASE_CREDENTIALS_JSON   -> the full service account JSON, as a single-line string
  FIREBASE_CREDENTIALS_PATH   -> path to a service account JSON file on disk

Get the service account JSON from:
  Firebase Console -> Project Settings -> Service Accounts -> Generate new private key
"""

import json
import os
import threading

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

from apps.core.exceptions import ApplicationError

_init_lock = threading.Lock()


def _ensure_initialized():
    if firebase_admin._apps:  # already initialized
        return

    with _init_lock:
        if firebase_admin._apps:
            return

        cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

        if cred_json:
            cred = credentials.Certificate(json.loads(cred_json))
        elif cred_path:
            cred = credentials.Certificate(cred_path)
        else:
            raise ApplicationError(
                "Firebase is not configured on the server "
                "(missing FIREBASE_CREDENTIALS_JSON / FIREBASE_CREDENTIALS_PATH).",
                status_code=500,
            )

        firebase_admin.initialize_app(cred)


def verify_firebase_id_token(id_token: str) -> dict:
    """
    Verifies a Firebase ID token and returns its decoded claims.
    Raises ApplicationError(400) if the token is invalid/expired.
    """
    _ensure_initialized()
    try:
        return firebase_auth.verify_id_token(id_token)
    except Exception as exc:  # firebase_admin raises several distinct exception types
        raise ApplicationError(f"Invalid or expired Firebase token: {exc}", status_code=400)
