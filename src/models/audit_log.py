"""
Modèle journal d'audit.

Enregistre toutes les actions utilisateur pour traçabilité et conformité RGPD.
Aucune donnée personnelle identifiable (PII) ne doit être stockée ici.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class AuditLog(Base):
    """
    Modèle ORM pour le journal d'audit.

    Enregistre chaque action significative avec un score de risque
    calculé par le module IA de détection de comportements suspects.

    Attributes:
        id: Identifiant unique UUID.
        user_id: Identifiant de l'utilisateur (pas de FK pour performance).
        action: Action effectuée (ex: READ_PATIENT, LOGIN, etc.).
        resource: Type de ressource accédée (ex: patient, consultation).
        resource_id: Identifiant de la ressource accédée.
        ip_address: Adresse IP de la requête.
        user_agent: User-Agent du client HTTP.
        risk_score: Score de risque calculé par l'IA (0.0 à 1.0).
        details_json: Détails supplémentaires au format JSON.
        timestamp: Horodatage de l'événement.
    """

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    resource: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    risk_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    details_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, risk={self.risk_score})>"
