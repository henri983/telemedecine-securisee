"""
Modèle dossier médical.

Stocke les documents médicaux avec contenu chiffré en AES-256-GCM.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class MedicalRecord(Base):
    """
    Modèle ORM représentant un dossier médical.

    Le contenu est chiffré en AES-256-GCM pour protéger
    les informations médicales sensibles.

    Attributes:
        id: Identifiant unique UUID.
        patient_id: Référence vers le patient.
        record_type: Type de document médical (ordonnance, analyse, etc.).
        content_encrypted: Contenu chiffré en AES-256-GCM.
        practitioner_id: Référence vers le praticien ayant créé le dossier.
        created_at: Date de création.
        updated_at: Date de dernière modification.
    """

    __tablename__ = "medical_records"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    record_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    content_encrypted: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )
    practitioner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
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
    patient: Mapped["Patient"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Patient",
        back_populates="medical_records",
        lazy="selectin",
    )
    practitioner: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<MedicalRecord(id={self.id}, type={self.record_type})>"
