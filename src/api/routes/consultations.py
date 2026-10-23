"""
Routes de gestion des consultations médicales.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_crypto_service, get_current_user, get_db_session
from src.models.consultation import Consultation
from src.models.user import User, UserRole
from src.schemas.consultation import ConsultationCreate, ConsultationResponse
from src.security.crypto import EncryptionService
from src.services.consultation_service import ConsultationService

router = APIRouter(prefix="/consultations", tags=["Consultations"])


@router.post(
    "/",
    response_model=ConsultationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle consultation médicale",
)
async def create_consultation(
    payload: ConsultationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    crypto: EncryptionService = Depends(get_crypto_service),
) -> ConsultationResponse:
    """Création d'une consultation réservée aux praticiens et administrateurs."""
    if current_user.role not in [UserRole.PRATICIEN, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les praticiens peuvent enregistrer une consultation médicale.",
        )

    # Vérification de l'existence du patient
    from src.models.patient import Patient
    pat_stmt = select(Patient).where(Patient.id == payload.patient_id)
    pat_res = await db.execute(pat_stmt)
    if not pat_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient introuvable.",
        )

    service = ConsultationService(db_session=db, encryption_service=crypto)
    notes = payload.notes or payload.motif or ""
    diag = payload.diagnosis or payload.diagnostic

    c = await service.create_consultation(
        patient_id=payload.patient_id,
        practitioner_id=str(current_user.id),
        notes=notes,
        diagnosis=diag,
        scheduled_at=payload.scheduled_at,
    )

    return ConsultationResponse(
        id=c.id,
        patient_id=c.patient_id,
        practitioner_id=c.practitioner_id,
        scheduled_at=c.scheduled_at,
        notes=notes,
        diagnosis=diag,
        status=c.status.value if hasattr(c.status, "value") else str(c.status),
    )


@router.get(
    "/{consultation_id}",
    response_model=ConsultationResponse,
    summary="Consulter les détails d'une consultation",
)
async def get_consultation(
    consultation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    crypto: EncryptionService = Depends(get_crypto_service),
) -> ConsultationResponse:
    """Récupère et déchiffre les éléments de la consultation."""
    service = ConsultationService(db_session=db, encryption_service=crypto)
    data = await service.get_consultation(consultation_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation introuvable.",
        )

    return ConsultationResponse(
        id=data["id"],
        patient_id=data["patient_id"],
        practitioner_id=data["practitioner_id"],
        scheduled_at=data["scheduled_at"],
        notes=data["notes"],
        diagnosis=data["diagnosis"],
        status=data["status"].value if hasattr(data["status"], "value") else str(data["status"]),
    )


@router.get(
    "/patient/{patient_id}",
    response_model=List[ConsultationResponse],
    summary="Lister l'historique des consultations d'un patient",
)
async def list_patient_consultations(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    crypto: EncryptionService = Depends(get_crypto_service),
) -> List[ConsultationResponse]:
    """Liste les consultations pour un dossier patient."""
    stmt = select(Consultation).where(Consultation.patient_id == patient_id)
    res = await db.execute(stmt)
    consults = res.scalars().all()

    output: List[ConsultationResponse] = []
    for c in consults:
        notes = crypto.decrypt(c.notes_encrypted) if c.notes_encrypted else ""
        diag = crypto.decrypt(c.diagnosis_encrypted) if c.diagnosis_encrypted else ""
        output.append(
            ConsultationResponse(
                id=c.id,
                patient_id=c.patient_id,
                practitioner_id=c.practitioner_id,
                scheduled_at=c.scheduled_at,
                notes=notes,
                diagnosis=diag,
                status=c.status.value if hasattr(c.status, "value") else str(c.status),
            )
        )
    return output
