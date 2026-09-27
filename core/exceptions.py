from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Normalizes API errors into a safe `{"errors": ...}` envelope.
    Preserves field-level validation details without leaking internal info.
    """
    # Call REST framework's default exception handler to get the standard error response
    response = exception_handler(exc, context)

    if response is not None:
        # Standard DRF exceptions (Validation, Auth, Throttling, etc.)
        # We wrap the existing data in the 'errors' key if it isn't already wrapped.
        if isinstance(response.data, dict) and "errors" in response.data and len(response.data) == 1:
            pass  # Already wrapped
        else:
            response.data = {"errors": response.data}
    else:
        # Unhandled exceptions (500 Internal Server Error)
        # Log the exception details internally, but don't expose stack traces to the client
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        response = Response(
            {"errors": {"detail": "Internal server error."}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response
