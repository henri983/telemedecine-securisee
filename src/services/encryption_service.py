"""
Singleton et helpers pour le service de chiffrement.
"""

from src.config import get_settings
from src.security.crypto import EncryptionService

_encryption_instance: EncryptionService | None = None


def get_encryption_service() -> EncryptionService:
    """Retourne l'instance configurée d'EncryptionService."""
    global _encryption_instance
    if _encryption_instance is None:
        settings = get_settings()
        key_raw = settings.ENCRYPTION_KEY
        if len(key_raw) == 64:
            _encryption_instance = EncryptionService(key_hex=key_raw)
        else:
            _encryption_instance = EncryptionService(key=key_raw[:32].encode("utf-8").ljust(32, b"0"))
    return _encryption_instance
