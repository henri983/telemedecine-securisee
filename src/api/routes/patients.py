"""
Routes de gestion des patients avec chiffrement de bout en bout et conformité RGPD.
"""

import html
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_crypto_service, get_current_user, get_db_session
from src.models.patient import Patient
from src.models.user import User, UserRole
from src.schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from src.security.crypto import EncryptionService
from src.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouveau dossier patient",
)
async def create_patient(
    payload: PatientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    crypto: EncryptionService = Depends(get_crypto_service),
) -> PatientResponse:
    """Crée un dossier médical patient. Seuls les praticiens et administrateurs sont autorisés."""
    if current_user.role not in [UserRole.PRATICIEN, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les praticiens et administrateurs peuvent créer un dossier patient.",
        )

    service = PatientService(db_session=db, encryption_service=crypto)
    user_id = payload.user_id or str(current_user.id)

    sanitized_fn = html.escape(payload.first_name)
    sanitized_ln = html.escape(payload.last_name)
    patient = await service.create_patient(
        user_id=user_id,
        first_name=sanitized_fn,
        last_name=sanitized_ln,
        date_of_birth=payload.date_of_birth,
        social_security_number=payload.social_security_number,
        phone=payload.phone,
        address=payload.address,
        medical_id=payload.medical_id,
        consent_given=payload.consent_given,
    )

    return PatientResponse(
        id=patient.id,
        user_id=patient.user_id,
        medical_id=patient.medical_id,
        first_name=sanitized_fn,
        last_name=sanitized_ln,
        date_of_birth=payload.date_of_birth,
        phone=payload.phone,
        address=payload.address,
        consent_given=patient.consent_given,
        created_at=patient.created_at,
    )


@router.get(
    "/",
    response_model=List[PatientResponse],
    summary="Lister les patients (autorisé aux praticiens/admins)",
)
async def list_patients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    crypto: EncryptionService = Depends(get_crypto_service),
) -> List[PatientResponse]:
    """Liste les dossiers patients."""
    if current_user.role not in [UserRole.PRATICIEN, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Privilèges insuffisants.",
        )

    stmt = select(Patient)
    result = await db.execute(stmt)
    patients = result.scalars().all()

    response: List[PatientResponse] = []
    for p in patients:
        fn = crypto.decrypt(p.first_name_encrypted)
        ln = crypto.decrypt(p.last_name_encrypted)
        dob = crypto.decrypt(p.date_of_birth_encrypted)
        response.append(
            PatientResponse(
                id=p.id,
                user_id=p.user_id,
                medical_id=p.medical_id,
                first_name=fn,
                last_name=ln,
                date_of_birth=dob,
                consent_given=p.consent_given,
                created_at=p.created_at,
            )
        )
    return response


@router.get(
    "/me",
    response_model=PatientResponse,
    summary="Consulter ses propres données patient",
)
async def get_my_patient_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    crypto: EncryptionService = Depends(get_crypto_service),
) -> PatientResponse:
    """Retourne le dossier patient associé au compte utilisateur connecté."""
    stmt = select(Patient).where(Patient.user_id == str(current_user.id))
    result = await db.execute(stmt)
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun dossier patient associé à ce compte.",
        )

    fn = crypto.decrypt(p.first_name_encrypted)
    ln = crypto.decrypt(p.last_name_encrypted)
    dob = crypto.decrypt(p.date_of_birth_encrypted)

    return PatientResponse(
        id=p.id,
        user_id=p.user_id,
        medical_id=p.medical_id,
        first_name=fn,
        last_name=ln,
        date_of_birth=dob,
        consent_given=p.consent_given,
        created_at=p.created_at,
    )


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Consulter un dossier patient spécifique",
)
async def get_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    crypto: EncryptionService = Depends(get_crypto_service),
) -> PatientResponse:
    """Consulte un patient par son ID."""
    service = PatientService(db_session=db, encryption_service=crypto)
    try:
        patient_view = await service.get_patient(patient_id, str(current_user.id))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès interdit à ce dossier médical.",
        )

    if not patient_view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient introuvable.",
        )

    return PatientResponse(
        id=patient_view.id,
        user_id=patient_view.user_id,
        medical_id=patient_view.medical_id,
        first_name=patient_view.first_name,
        last_name=patient_view.last_name,
        date_of_birth=patient_view.date_of_birth,
        phone=getattr(patient_view, "phone", None),
        address=getattr(patient_view, "address", None),
        consent_given=patient_view.consent_given,
        created_at=getattr(patient_view, "created_at", None),
    )


@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Mettre à jour un dossier patient",
)
async def update_patient(
    patient_id: str,
    payload: PatientUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    crypto: EncryptionService = Depends(get_crypto_service),
) -> PatientResponse:
    """Met à jour un dossier patient."""
    service = PatientService(db_session=db, encryption_service=crypto)
    patient_view = await service.get_patient(patient_id, str(current_user.id))
    if not patient_view:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient introuvable.")

    stmt = select(Patient).where(Patient.id == patient_id)
    res = await db.execute(stmt)
    p = res.scalar_one()

    if payload.phone:
        p.phone_encrypted = crypto.encrypt(payload.phone)
    if payload.address:
        p.address_encrypted = crypto.encrypt(payload.address)

    await db.flush()
    await db.refresh(p)

    fn = crypto.decrypt(p.first_name_encrypted)
    ln = crypto.decrypt(p.last_name_encrypted)
    dob = crypto.decrypt(p.date_of_birth_encrypted)

    return PatientResponse(
        id=p.id,
        user_id=p.user_id,
        medical_id=p.medical_id,
        first_name=fn,
        last_name=ln,
        date_of_birth=dob,
        phone=payload.phone or getattr(patient_view, "phone", None),
        address=payload.address or getattr(patient_view, "address", None),
        consent_given=p.consent_given,
        created_at=p.created_at,
    )


@router.get(
    "/{patient_id}/consultations",
    summary="Lister les consultations d'un patient",
)
async def list_patient_consultations_alias(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    crypto: EncryptionService = Depends(get_crypto_service),
) -> List[Dict[str, Any]]:
    """Retourne la liste des consultations d'un patient."""
    from src.models.consultation import Consultation

    stmt = select(Consultation).where(Consultation.patient_id == patient_id)
    res = await db.execute(stmt)
    consults = res.scalars().all()

    output: List[Dict[str, Any]] = []
    for c in consults:
        notes = crypto.decrypt(c.notes_encrypted) if c.notes_encrypted else ""
        diag = crypto.decrypt(c.diagnosis_encrypted) if c.diagnosis_encrypted else ""
        output.append(
            {
                "id": c.id,
                "patient_id": c.patient_id,
                "practitioner_id": c.practitioner_id,
                "scheduled_at": c.scheduled_at,
                "notes": notes,
                "diagnosis": diag,
                "status": c.status.value if hasattr(c.status, "value") else str(c.status),
            }
        )
    return output


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer un dossier patient (Droit à l'effacement RGPD)",
)
async def delete_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    crypto: EncryptionService = Depends(get_crypto_service),
) -> Dict[str, str]:
    """Supprime un patient et ses données associées."""
    service = PatientService(db_session=db, encryption_service=crypto)
    try:
        success = await service.delete_patient(patient_id, str(current_user.id))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Privilèges insuffisants pour supprimer ce patient.",
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient introuvable.",
        )
    return {"message": "Dossier patient supprimé conformément au RGPD (Art. 17)."}


@router.get(
    "/{patient_id}/export",
    summary="Exporter l'intégralité du dossier patient (Portabilité RGPD)",
)
async def export_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    crypto: EncryptionService = Depends(get_crypto_service),
) -> Dict[str, Any]:
    """Export structuré des données patient."""
    service = PatientService(db_session=db, encryption_service=crypto)
    try:
        export_data = await service.export_patient_data(patient_id, str(current_user.id))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès interdit à ces données.",
        )

    if not export_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient introuvable.",
        )
    return export_data
