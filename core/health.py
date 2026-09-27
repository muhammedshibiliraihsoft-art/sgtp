from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import connection, DatabaseError
import logging

logger = logging.getLogger(__name__)

@extend_schema(
    responses={
        200: inline_serializer(
            name='HealthLiveResponse',
            fields={'status': serializers.CharField()}
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_live(request):
    """
    Liveness probe. Lightweight check that the process is alive.
    Returns 200 OK unconditionally.
    """
    return Response({"status": "alive"}, status=status.HTTP_200_OK)

@extend_schema(
    responses={
        200: inline_serializer(
            name='HealthReadyResponse',
            fields={'status': serializers.CharField()}
        ),
        503: inline_serializer(
            name='HealthUnavailableResponse',
            fields={'status': serializers.CharField()}
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_ready(request):
    """
    Readiness probe. Verifies database connectivity.
    Returns 200 OK if ready, 503 Service Unavailable on dependency failure.
    Does not expose internal DB details.
    """
    try:
        connection.ensure_connection()
        return Response({"status": "ready"}, status=status.HTTP_200_OK)
    except DatabaseError as e:
        logger.error("Database connection failed during health_ready check.", exc_info=True)
        return Response({"status": "unavailable"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
