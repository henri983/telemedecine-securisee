"""
Module de services métier pour la plateforme de télémédecine.
"""

from src.services.auth_service import AuthService
from src.services.consultation_service import ConsultationService
from src.services.encryption_service import get_encryption_service
from src.services.patient_service import PatientService
from src.services.rgpd_service import RGPDService

__all__ = [
    "AuthService",
    "ConsultationService",
    "PatientService",
    "RGPDService",
    "get_encryption_service",
]
