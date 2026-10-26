from dataclasses import dataclass

from rest_framework.response import Response
from rest_framework import status


@dataclass(frozen=True)
class MutationReplay:
    response_data: object
    response_status: int


def mutation_response(result, serializer_class, success_status=status.HTTP_200_OK):
    """Return the exact stored response for a replay, or serialize a new result."""
    if isinstance(result, MutationReplay):
        return Response(result.response_data, status=result.response_status)
    if success_status == status.HTTP_204_NO_CONTENT or result is None:
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(serializer_class(result).data, status=success_status)
