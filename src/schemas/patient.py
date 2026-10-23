"""
Schémas Pydantic pour les patients avec conformité RGPD.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PatientCreate(BaseModel):
    """Schéma de création d'un dossier patient."""

    user_id: Optional[str] = Field(None, description="Identifiant utilisateur associé.")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: str = Field(..., description="Date de naissance YYYY-MM-DD")
    medical_id: Optional[str] = Field(None, description="Identifiant médical unique.")
    social_security_number: Optional[str] = Field(None, description="Numéro de sécurité sociale.")
    phone: Optional[str] = Field(None, description="Téléphone.")
    address: Optional[str] = Field(None, description="Adresse.")
    email: Optional[str] = Field(None, description="Email de contact.")
    consent_given: bool = Field(default=True, description="Consentement RGPD explicite.")


class PatientUpdate(BaseModel):
    """Schéma de mise à jour d'un dossier patient."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class PatientResponse(BaseModel):
    """Schéma de retour d'un patient (données déchiffrées)."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    id: str
    user_id: str
    medical_id: str
    first_name: str
    last_name: str
    date_of_birth: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    consent_given: bool
    created_at: Optional[datetime] = None


class PatientExport(BaseModel):
    """Format d'export de données personnelles RGPD (Article 20)."""

    patient_id: str
    medical_id: str
    first_name: str
    last_name: str
    date_of_birth: str
    phone: Optional[str] = None
    address: Optional[str] = None
    consent_given: bool
    exported_at: str
