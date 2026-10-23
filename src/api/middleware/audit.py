"""
Middleware d'audit et analyse comportementale en temps réel (IA).
"""

import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.ai.anomaly_detector import AnomalyDetector

logger = logging.getLogger("telemedicine.audit")


class AuditAndAnomalyMiddleware(BaseHTTPMiddleware):
    """Journalise les requêtes sans PII et interroge le moteur IA sur les anomalies."""

    def __init__(self, app, detector: AnomalyDetector | None = None) -> None:
        super().__init__(app)
        self.detector = detector or AnomalyDetector()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"

        # Traitement de la requête
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Évaluation comportementale basique sur métadonnées (sans PII)
        event = {
            "hour": time.localtime().tm_hour,
            "ip_address": client_ip,
            "endpoint": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "request_count": 1,
            "data_volume_mb": 0.01,
        }

        try:
            analysis = self.detector.analyze(event)
            if analysis.is_suspicious:
                logger.warning(
                    f"[ALERTE IA] Comportement suspect détecté (score={analysis.risk_score}): "
                    f"{', '.join(analysis.reasons)} - Route: {request.method} {request.url.path}"
                )
        except Exception:
            pass

        return response
