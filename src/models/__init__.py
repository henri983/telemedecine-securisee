"""
Package des modèles SQLAlchemy.

Exporte tous les modèles ORM pour faciliter les imports.
"""

from src.models.user import User, UserRole
from src.models.patient import Patient
from src.models.consultation import Consultation, ConsultationStatus
from src.models.medical_record import MedicalRecord
from src.models.audit_log import AuditLog

__all__: list[str] = [
    "User",
    "UserRole",
    "Patient",
    "Consultation",
    "ConsultationStatus",
    "MedicalRecord",
    "AuditLog",
]
