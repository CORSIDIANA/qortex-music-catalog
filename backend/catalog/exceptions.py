from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class Conflict(APIException):
    status_code = 409
    default_code = "conflict"


def exception_handler(exc, context):
    if isinstance(exc, ProtectedError):
        return Response(
            {"detail": "This item is still in use. Remove its relationships first."},
            status=409,
        )
    if isinstance(exc, IntegrityError):
        cause = exc.__cause__
        if getattr(cause, "sqlstate", None) in {"23503", "23505"}:
            return Response(
                {"detail": "The catalog changed during this request. Refresh and try again."},
                status=409,
            )
    return drf_exception_handler(exc, context)
