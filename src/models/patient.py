"""
Modèle patient.

Stocke les données personnelles chiffrées (AES-256-GCM) pour conformité RGPD.
Les champs sensibles sont stockés en bytes chiffrés.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class Patient(Base):
    """
    Modèle ORM représentant un dossier patient.
    """

    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    first_name_encrypted: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )
    last_name_encrypted: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )
    date_of_birth_encrypted: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )
    social_security_encrypted: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary,
        nullable=True,
    )
    phone_encrypted: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary,
        nullable=True,
    )
    address_encrypted: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary,
        nullable=True,
    )
    medical_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    consent_given: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    consent_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        back_populates="patient_profile",
        lazy="selectin",
    )
    consultations: Mapped[list["Consultation"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Consultation",
        back_populates="patient",
        lazy="selectin",
        foreign_keys="[Consultation.patient_id]",
    )
    medical_records: Mapped[list["MedicalRecord"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "MedicalRecord",
        back_populates="patient",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, medical_id={self.medical_id})>"
