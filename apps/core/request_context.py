"""
Thread-local storage for the current request's correlation ID.
Used so request_id can be attached to responses and log lines without
threading it through every function signature.
"""
import contextvars

_request_id_var = contextvars.ContextVar("request_id", default=None)


def set_request_id(value: str):
    _request_id_var.set(value)


def get_request_id() -> str:
    return _request_id_var.get() or "unknown"
