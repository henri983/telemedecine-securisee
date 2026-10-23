"""
Service de gestion des patients et dossiers médicaux avec chiffrement AES-256-GCM.
"""

import uuid
from typing import Any, Dict, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.patient import Patient
from src.models.user import User, UserRole
from src.security.crypto import EncryptionService


class DecryptedPatientView:
    """Wrapper pour exposer un patient avec ses données déchiffrées."""

    def __init__(self, patient: Patient, decrypted_data: Dict[str, Any]) -> None:
        self._patient = patient
        self._decrypted = decrypted_data
        self.id = patient.id
        self.user_id = patient.user_id
        self.medical_id = patient.medical_id
        self.consent_given = patient.consent_given
        self.first_name = decrypted_data.get("first_name", "")
        self.last_name = decrypted_data.get("last_name", "")
        self.date_of_birth = decrypted_data.get("date_of_birth", "")
        self.social_security_number = decrypted_data.get("social_security_number", "")
        self.phone = decrypted_data.get("phone", "")
        self.address = decrypted_data.get("address", "")
        self.email = decrypted_data.get("email", "")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._patient, name)


class PatientService:
    """Service gérant le cycle de vie des patients, chiffrement et conformité RGPD."""

    def __init__(
        self,
        db_session: AsyncSession,
        encryption_service: EncryptionService,
    ) -> None:
        self.db = db_session
        self.crypto = encryption_service

    async def create_patient(
        self,
        user_id: str,
        first_name: str,
        last_name: str,
        date_of_birth: str,
        social_security_number: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        email: Optional[str] = None,
        medical_id: Optional[str] = None,
        consent_given: bool = True,
        **extra: Any,
    ) -> Patient:
        """Crée un dossier patient avec chiffrement de tous les PII."""
        med_id = medical_id or f"MED-{uuid.uuid4().hex[:8].upper()}"

        fn_enc = self.crypto.encrypt(first_name)
        ln_enc = self.crypto.encrypt(last_name)
        dob_enc = self.crypto.encrypt(date_of_birth)
        ssn_enc = self.crypto.encrypt(social_security_number) if social_security_number else None
        phone_enc = self.crypto.encrypt(phone) if phone else None
        addr_enc = self.crypto.encrypt(address) if address else None

        patient = Patient(
            id=str(uuid.uuid4()),
            user_id=str(user_id),
            first_name_encrypted=fn_enc,
            last_name_encrypted=ln_enc,
            date_of_birth_encrypted=dob_enc,
            social_security_encrypted=ssn_enc,
            phone_encrypted=phone_enc,
            address_encrypted=addr_enc,
            medical_id=med_id,
            consent_given=consent_given,
        )

        self.db.add(patient)
        await self.db.flush()
        await self.db.refresh(patient)
        return patient

    async def get_patient(
        self,
        patient_id: str,
        requesting_user_id: str,
    ) -> Optional[DecryptedPatientView]:
        """Récupère un patient et déchiffre ses données personnelles après contrôle d'accès."""
        stmt = select(Patient).where(Patient.id == patient_id)
        res = await self.db.execute(stmt)
        patient = res.scalar_one_or_none()
        if not patient:
            return None

        # Contrôle d'accès : le patient lui-même ou un praticien / admin
        if str(patient.user_id) != str(requesting_user_id):
            user_stmt = select(User).where(User.id == requesting_user_id)
            user_res = await self.db.execute(user_stmt)
            user = user_res.scalar_one_or_none()
            if not user or user.role not in [UserRole.PRATICIEN, UserRole.ADMIN]:
                raise PermissionError("Accès interdit aux données de ce patient.")

        decrypted_data: Dict[str, Any] = {
            "first_name": self.crypto.decrypt(patient.first_name_encrypted),
            "last_name": self.crypto.decrypt(patient.last_name_encrypted),
            "date_of_birth": self.crypto.decrypt(patient.date_of_birth_encrypted),
        }
        if patient.social_security_encrypted:
            decrypted_data["social_security_number"] = self.crypto.decrypt(patient.social_security_encrypted)
        if patient.phone_encrypted:
            decrypted_data["phone"] = self.crypto.decrypt(patient.phone_encrypted)
        if patient.address_encrypted:
            decrypted_data["address"] = self.crypto.decrypt(patient.address_encrypted)

        return DecryptedPatientView(patient, decrypted_data)

    async def delete_patient(
        self,
        patient_id: str,
        requesting_user_id: str,
    ) -> bool:
        """Suppression complète d'un patient (Droit à l'oubli RGPD)."""
        patient_view = await self.get_patient(patient_id, requesting_user_id)
        if not patient_view:
            return False

        stmt = delete(Patient).where(Patient.id == patient_id)
        await self.db.execute(stmt)
        await self.db.flush()
        return True

    async def export_patient_data(
        self,
        patient_id: str,
        requesting_user_id: str,
    ) -> Dict[str, Any]:
        """Exporte l'ensemble des données du patient sous format structuré (Portabilité RGPD)."""
        patient_view = await self.get_patient(patient_id, requesting_user_id)
        if not patient_view:
            return {}

        return {
            "patient_id": patient_view.id,
            "medical_id": patient_view.medical_id,
            "user_id": patient_view.user_id,
            "first_name": patient_view.first_name,
            "last_name": patient_view.last_name,
            "date_of_birth": patient_view.date_of_birth,
            "phone": getattr(patient_view, "phone", ""),
            "address": getattr(patient_view, "address", ""),
            "consent_given": patient_view.consent_given,
            "exported_at": str(uuid.uuid4()),
        }
