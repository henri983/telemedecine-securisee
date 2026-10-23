"""
Alias racine pour les dépendances partagées (utilisé notamment par les fixtures de test).
"""

from src.api.dependencies import (
    get_anomaly_detector,
    get_crypto_service,
    get_current_user,
    get_db_session,
    get_jwt_handler,
)

__all__ = [
    "get_anomaly_detector",
    "get_crypto_service",
    "get_current_user",
    "get_db_session",
    "get_jwt_handler",
]
