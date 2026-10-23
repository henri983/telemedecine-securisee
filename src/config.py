"""
Configuration de l'application.

Charge les variables d'environnement depuis un fichier .env
et les expose via un objet Settings Pydantic.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres de configuration de l'application télémédecine."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Base de données ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./telemedecine.db"

    # --- Sécurité générale ---
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_WITH_SECURE_RANDOM_KEY"

    # --- JWT ---
    JWT_SECRET_KEY: str = "CHANGE_ME_JWT_SECRET_KEY_MIN_32_CHARS"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30
    JWT_REFRESH_EXPIRATION_DAYS: int = 7

    # --- Chiffrement AES-256 ---
    ENCRYPTION_KEY: str = "CHANGE_ME_BASE64_ENCODED_32_BYTES_KEY"

    # --- CORS ---
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    # --- Logging ---
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # --- Environnement ---
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"

    # --- IA ---
    AI_MODEL_PATH: str = "models/suspicious_behavior_model.joblib"
    ANOMALY_THRESHOLD: float = 0.7

    # --- Rate Limiting ---
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_AUTH_PER_MINUTE: int = 10

    @property
    def allowed_origins_list(self) -> list[str]:
        """Retourne la liste des origines CORS autorisées."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def encryption_key_bytes(self) -> bytes:
        """Retourne la clé de chiffrement en bytes (base64 décodé)."""
        import base64
        return base64.urlsafe_b64decode(self.ENCRYPTION_KEY)

    @property
    def is_production(self) -> bool:
        """Vérifie si l'application est en mode production."""
        return self.ENVIRONMENT == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Retourne l'instance singleton des paramètres.

    Utilise lru_cache pour ne charger qu'une seule fois.
    """
    return Settings()
