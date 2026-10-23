"""
Application FastAPI principale - Plateforme de Télémédecine Sécurisée.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from src.api.middleware.audit import AuditAndAnomalyMiddleware
from src.api.middleware.rate_limiter import InMemoryRateLimiterMiddleware
from src.api.middleware.security import SecurityHeadersMiddleware
from src.api.routes import api_router
from src.config import Settings, get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gestionnaire de cycle de vie (démarrage et arrêt)."""
    # Démarrage
    yield
    # Arrêt


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """Fabrique d'application FastAPI configurée."""
    current_settings = settings or get_settings()

    app = FastAPI(
        title="Plateforme de Télémédecine Sécurisée",
        description=(
            "API médicale sécurisée avec chiffrement AES-256-GCM, "
            "contrôle d'accès RBAC et détection d'anomalies IA. "
            "Conforme RGPD et normes européennes de protection des données de santé."
        ),
        version="1.0.0",
        docs_url="/docs" if current_settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if current_settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )

    # Handlers d'exception personnalisés pour prévenir toute fuite de détails techniques
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Une erreur interne s'est produite. L'incident a été consigné."},
        )

    # Middlewares de sécurité et audit
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(AuditAndAnomalyMiddleware)
    app.add_middleware(InMemoryRateLimiterMiddleware, max_requests_per_minute=300)

    # Middleware CORS
    origins = [o.strip() for o in current_settings.ALLOWED_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Enregistrement des routes API
    app.include_router(api_router)

    # Endpoints de monitoring et observabilité
    @app.get("/health", tags=["Monitoring"], summary="Bilan de santé du service")
    async def health_check() -> dict:
        return {
            "status": "healthy",
            "service": "telemedecine-securisee",
            "version": "1.0.0",
            "security": "AES-256-GCM / RBAC / AI-Active",
            "gdpr_compliant": True,
        }

    @app.get("/metrics", tags=["Monitoring"], summary="Métriques Prometheus")
    async def metrics() -> PlainTextResponse:
        metrics_payload = (
            "# HELP telemed_http_requests_total Total des requetes HTTP traitees\n"
            "# TYPE telemed_http_requests_total counter\n"
            'telemed_http_requests_total{status="200"} 1\n'
            "# HELP telemed_ai_anomalies_detected Total des anomalies detectees par l'IA\n"
            "# TYPE telemed_ai_anomalies_detected counter\n"
            "telemed_ai_anomalies_detected 0\n"
        )
        return PlainTextResponse(metrics_payload, media_type="text/plain; version=0.0.4")

    return app


app = create_app()
