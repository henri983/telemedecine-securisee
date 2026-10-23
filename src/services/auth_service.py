"""
Service d'authentification et gestion des mots de passe.
"""

import re
from typing import Any, Dict, Optional
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User, UserRole


class AuthService:
    """Service gérant le hash, la vérification et les règles de robustesse des identifiants."""

    def __init__(self, db_session: Optional[AsyncSession] = None) -> None:
        self.db = db_session

    @staticmethod
    def _to_bytes(password: str) -> bytes:
        """Convertit et tronque le mot de passe selon la limite de 72 octets de bcrypt."""
        pw_bytes = password.encode("utf-8")
        return pw_bytes[:72]

    def hash_password(self, password: str) -> str:
        """Hache un mot de passe avec bcrypt et salt aléatoire sécurisé."""
        pw_b = self._to_bytes(password)
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(pw_b, salt).decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Vérifie la correspondance entre mot de passe en clair et hash."""
        pw_b = self._to_bytes(plain_password)
        try:
            return bcrypt.checkpw(pw_b, hashed_password.encode("utf-8"))
        except Exception:
            return False

    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """Vérifie les critères de robustesse."""
        if len(password) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
        if not re.search(r"[A-ZÀ-ÖØ-ß]", password):
            return False
        if not re.search(r"[a-zà-öø-ÿ]", password):
            return False
        if not re.search(r"\d", password):
            return False
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+\\/~\[\]]", password):
            return False
        return True

    async def register(
        self,
        email: str,
        password: str,
        role: UserRole = UserRole.PATIENT,
    ) -> User:
        """Crée un nouvel utilisateur après validation des règles de sécurité."""
        if not self.validate_password_strength(password):
            raise ValueError("Le mot de passe ne respecte pas les critères de sécurité.")

        hashed = self.hash_password(password)
        user = User(
            email=email.lower().strip(),
            hashed_password=hashed,
            role=role,
            is_active=True,
        )
        if self.db:
            self.db.add(user)
            await self.db.flush()
            await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authentifie un utilisateur par email et mot de passe."""
        if not self.db:
            return None
        stmt = select(User).where(User.email == email.lower().strip())
        res = await self.db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user
