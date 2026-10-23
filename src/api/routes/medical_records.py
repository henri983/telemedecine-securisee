"""
Routes pour les actes et documents du dossier médical.
"""

import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_crypto_service, get_current_user, get_db_session
from src.models.medical_record import MedicalRecord
from src.models.user import User, UserRole
from src.schemas.medical_record import MedicalRecordCreate, MedicalRecordResponse
from src.security.crypto import EncryptionService

router = APIRouter(prefix="/medical-records", tags=["Dossiers Médicaux"])


@router.post(
    "/",
    response_model=MedicalRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter un document au dossier médical",
)
async def create_medical_record(
    payload: MedicalRecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    crypto: EncryptionService = Depends(get_crypto_service),
) -> MedicalRecordResponse:
    """Enregistre un nouveau document avec chiffrement AES-256-GCM."""
    if current_user.role not in [UserRole.PRATICIEN, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les praticiens peuvent ajouter des actes médicaux.",
        )

    content_enc = crypto.encrypt(payload.content)
    record = MedicalRecord(
        id=str(uuid.uuid4()),
        patient_id=payload.patient_id,
        practitioner_id=str(current_user.id),
        record_type=payload.record_type,
        content_encrypted=content_enc,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)

    return MedicalRecordResponse(
        id=record.id,
        patient_id=record.patient_id,
        practitioner_id=record.practitioner_id,
        record_type=record.record_type,
        content=payload.content,
        created_at=record.created_at,
    )


@router.get(
    "/{record_id}",
    response_model=MedicalRecordResponse,
    summary="Consulter un document médical déchiffré",
)
async def get_medical_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    crypto: EncryptionService = Depends(get_crypto_service),
) -> MedicalRecordResponse:
    """Récupère un document médical déchiffré."""
    stmt = select(MedicalRecord).where(MedicalRecord.id == record_id)
    res = await db.execute(stmt)
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acte introuvable.")

    content = crypto.decrypt(rec.content_encrypted)
    return MedicalRecordResponse(
        id=rec.id,
        patient_id=rec.patient_id,
        practitioner_id=rec.practitioner_id,
        record_type=rec.record_type,
        content=content,
        created_at=rec.created_at,
    )
