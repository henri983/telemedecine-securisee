"""
Système de contrôle d'accès basé sur les rôles (RBAC).

Définit les permissions, leur association aux rôles, et fournit
une dépendance FastAPI pour vérifier les permissions.
"""

import enum
from typing import Any

from fastapi import Depends, HTTPException, status

from src.models.user import UserRole


class Permission(str, enum.Enum):
    """Permissions granulaires pour le contrôle d'accès RBAC."""

    READ_PATIENT = "read:patient"
    WRITE_PATIENT = "write:patient"
    DELETE_PATIENT = "delete:patient"
    READ_CONSULTATION = "read:consultation"
    WRITE_CONSULTATION = "write:consultation"
    READ_MEDICAL_RECORD = "read:medical_record"
    WRITE_MEDICAL_RECORD = "write:medical_record"
    READ_AUDIT = "read:audit"
    MANAGE_USERS = "manage:users"
    EXPORT_DATA = "export:data"
    DELETE_DATA = "delete:data"


# Mappage rôles → permissions
ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.ADMIN: set(Permission),  # Toutes les permissions
    UserRole.PRATICIEN: {
        Permission.READ_PATIENT,
        Permission.WRITE_PATIENT,
        Permission.READ_CONSULTATION,
        Permission.WRITE_CONSULTATION,
        Permission.READ_MEDICAL_RECORD,
        Permission.WRITE_MEDICAL_RECORD,
    },
    UserRole.PATIENT: {
        Permission.READ_PATIENT,
        Permission.READ_CONSULTATION,
        Permission.READ_MEDICAL_RECORD,
        Permission.EXPORT_DATA,
        Permission.DELETE_DATA,
    },
}


def has_permission(role: UserRole, permission: Permission) -> bool:
    """
    Vérifie si un rôle possède une permission donnée.

    Args:
        role: Rôle de l'utilisateur.
        permission: Permission à vérifier.

    Returns:
        bool: True si le rôle possède la permission.
    """
    role_perms: set[Permission] = ROLE_PERMISSIONS.get(role, set())
    return permission in role_perms


def require_permission(permission: Permission) -> Any:
    """
    Crée une dépendance FastAPI qui vérifie une permission.

    Utilise le middleware d'authentification pour récupérer l'utilisateur
    courant et vérifie qu'il possède la permission requise.

    Args:
        permission: Permission requise pour accéder à la route.

    Returns:
        Callable: Dépendance FastAPI.

    Usage:
        @router.get("/patients", dependencies=[Depends(require_permission(Permission.READ_PATIENT))])
        async def get_patients(): ...
    """

    async def _check_permission(
        current_user: dict = Depends(_get_current_user_from_token),
    ) -> dict:
        """Vérifie que l'utilisateur courant possède la permission requise."""
        user_role_str: str = current_user.get("role", "")

        try:
            user_role = UserRole(user_role_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Rôle utilisateur invalide.",
            )

        if not has_permission(user_role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission insuffisante: {permission.value} requise.",
            )

        return current_user

    return _check_permission


async def _get_current_user_from_token() -> dict:
    """
    Placeholder pour la dépendance d'authentification.

    Cette fonction est remplacée par la vraie dépendance dans
    src.api.dependencies.get_current_user lors de l'exécution.
    Elle sert uniquement de type hint pour la chaîne de dépendances.

    Returns:
        dict: Payload du token JWT de l'utilisateur courant.
    """
    # Cette implémentation est écrasée par la dépendance réelle
    # dans api/dependencies.py via l'injection FastAPI
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification requise.",
    )
