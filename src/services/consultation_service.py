"""
Service de gestion des consultations médicales sécurisées.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.consultation import Consultation
from src.security.crypto import EncryptionService


class ConsultationService:
    """Gestion des consultations médicales avec chiffrement des comptes-rendus."""

    def __init__(
        self,
        db_session: AsyncSession,
        encryption_service: EncryptionService,
    ) -> None:
        self.db = db_session
        self.crypto = encryption_service

    async def create_consultation(
        self,
        patient_id: str,
        practitioner_id: str,
        notes: str,
        diagnosis: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
    ) -> Consultation:
        """Crée une nouvelle consultation avec notes et diagnostic chiffrés."""
        notes_enc = self.crypto.encrypt(notes)
        diag_enc = self.crypto.encrypt(diagnosis) if diagnosis else None

        consultation = Consultation(
            id=str(uuid.uuid4()),
            patient_id=str(patient_id),
            practitioner_id=str(practitioner_id),
            notes_encrypted=notes_enc,
            diagnosis_encrypted=diag_enc,
            scheduled_at=scheduled_at or datetime.now(timezone.utc),
        )

        self.db.add(consultation)
        await self.db.flush()
        await self.db.refresh(consultation)
        return consultation

    async def get_consultation(self, consultation_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une consultation et déchiffre les éléments médicaux."""
        stmt = select(Consultation).where(Consultation.id == consultation_id)
        res = await self.db.execute(stmt)
        c = res.scalar_one_or_none()
        if not c:
            return None

        notes = self.crypto.decrypt(c.notes_encrypted) if c.notes_encrypted else ""
        diag = self.crypto.decrypt(c.diagnosis_encrypted) if c.diagnosis_encrypted else ""

        return {
            "id": c.id,
            "patient_id": c.patient_id,
            "practitioner_id": c.practitioner_id,
            "notes": notes,
            "diagnosis": diag,
            "scheduled_at": c.scheduled_at,
            "status": c.status,
        }
