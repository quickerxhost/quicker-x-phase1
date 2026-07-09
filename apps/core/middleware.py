import uuid

from apps.core.request_context import set_request_id


class RequestIDMiddleware:
    """
    Attaches a unique request_id to every incoming request.
    Echoes it back via the X-Request-ID response header and makes it
    available to the response envelope + logging formatter.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.request_id = request_id
        set_request_id(request_id)

        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response
