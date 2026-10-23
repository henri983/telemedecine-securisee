"""
Package sécurité.

Exporte les composants de chiffrement, JWT et RBAC.
"""

from src.security.crypto import EncryptionService
from src.security.jwt_handler import JWTHandler
from src.security.rbac import Permission, ROLE_PERMISSIONS, require_permission
from src.security.data_masking import mask_email, mask_name, mask_pii, anonymize_for_logs

__all__: list[str] = [
    "EncryptionService",
    "JWTHandler",
    "Permission",
    "ROLE_PERMISSIONS",
    "require_permission",
    "mask_email",
    "mask_name",
    "mask_pii",
    "anonymize_for_logs",
]
