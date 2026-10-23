"""
Package des schémas Pydantic.

Exporte tous les schémas de validation et sérialisation.
"""

from src.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from src.schemas.patient import PatientCreate, PatientUpdate, PatientResponse, PatientExport
from src.schemas.consultation import ConsultationCreate, ConsultationUpdate, ConsultationResponse
from src.schemas.medical_record import MedicalRecordCreate, MedicalRecordResponse

__all__: list[str] = [
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "PatientCreate",
    "PatientUpdate",
    "PatientResponse",
    "PatientExport",
    "ConsultationCreate",
    "ConsultationUpdate",
    "ConsultationResponse",
    "MedicalRecordCreate",
    "MedicalRecordResponse",
]
