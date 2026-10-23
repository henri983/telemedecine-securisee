"""
Modèle consultation médicale.

Stocke les informations de consultation avec notes et diagnostics chiffrés.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class ConsultationStatus(str, enum.Enum):
    """Statuts possibles d'une consultation."""

    PLANIFIEE = "planifiee"
    EN_COURS = "en_cours"
    TERMINEE = "terminee"
    ANNULEE = "annulee"


class Consultation(Base):
    """
    Modèle ORM représentant une consultation médicale.

    Les notes et le diagnostic sont chiffrés en AES-256-GCM.

    Attributes:
        id: Identifiant unique UUID.
        patient_id: Référence vers le patient.
        practitioner_id: Référence vers le praticien.
        scheduled_at: Date et heure programmées de la consultation.
        notes_encrypted: Notes médicales chiffrées.
        diagnosis_encrypted: Diagnostic chiffré.
        status: Statut de la consultation.
        created_at: Date de création.
    """

    __tablename__ = "consultations"

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
    practitioner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    notes_encrypted: Mapped[bytes | None] = mapped_column(
        LargeBinary,
        nullable=True,
    )
    diagnosis_encrypted: Mapped[bytes | None] = mapped_column(
        LargeBinary,
        nullable=True,
    )
    status: Mapped[ConsultationStatus] = mapped_column(
        Enum(ConsultationStatus),
        nullable=False,
        default=ConsultationStatus.PLANIFIEE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relations
    patient: Mapped["Patient"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Patient",
        back_populates="consultations",
        lazy="selectin",
    )
    practitioner: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Consultation(id={self.id}, status={self.status})>"
