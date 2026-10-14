"""
Global views for Orqen backend configuration.
"""

import logging
from django.db import connection
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger('orqen')


class HealthCheckView(APIView):
    """
    Health check endpoint for Orqen.
    Returns operational status and verifies database connectivity.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        db_status = "ok"
        db_detail = None

        try:
            connection.ensure_connection()
            if not connection.is_usable():
                connection.close()
                connection.connect()
                if not connection.is_usable():
                    raise RuntimeError("Database connection is not usable")
        except Exception as exc:
            db_status = "error"
            db_detail = str(exc)
            logger.warning("Health check database probe failed: %s", exc)

        is_healthy = (db_status == "ok")

        raw_engine = connection.settings_dict.get('ENGINE') or 'unknown'
        engine_name = raw_engine.split('.')[-1]

        response_payload = {
            "status": "healthy" if is_healthy else "degraded",
            "service": "orqen-backend",
            "version": "v1",
            "timestamp": timezone.now().isoformat(),
            "database": {
                "status": db_status,
                "engine": engine_name,
            },
        }

        if db_detail:
            response_payload["database"]["detail"] = db_detail

        http_status = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(response_payload, status=http_status)
