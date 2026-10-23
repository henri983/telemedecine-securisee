"""
Modèle utilisateur.

Définit le modèle ORM User avec les rôles ADMIN, PRATICIEN et PATIENT.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class UserRole(str, enum.Enum):
    """Rôles utilisateur pour le contrôle d'accès RBAC."""

    ADMIN = "admin"
    PRATICIEN = "praticien"
    PATIENT = "patient"


class User(Base):
    """
    Modèle ORM représentant un utilisateur de la plateforme.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.PATIENT,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relations
    patient_profile: Mapped[Optional["Patient"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Patient",
        back_populates="user",
        uselist=False,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
