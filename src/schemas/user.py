"""
Schémas Pydantic pour les utilisateurs.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.user import UserRole


class UserCreate(BaseModel):
    """Schéma de création d'un utilisateur."""

    email: EmailStr = Field(..., description="Adresse email unique de l'utilisateur.")
    password: str = Field(..., min_length=8, description="Mot de passe robuste.")
    full_name: Optional[str] = Field(None, description="Nom complet de l'utilisateur.")
    role: UserRole = Field(default=UserRole.PATIENT, description="Rôle RBAC.")


class UserLogin(BaseModel):
    """Schéma de connexion utilisateur."""

    email: EmailStr = Field(..., description="Adresse email.")
    password: str = Field(..., description="Mot de passe.")


class UserResponse(BaseModel):
    """Schéma de réponse pour un utilisateur (sans données sensibles)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """Schéma de réponse JWT."""

    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
