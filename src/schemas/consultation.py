"""
Schémas Pydantic pour les consultations médicales.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from src.models.consultation import ConsultationStatus


class ConsultationCreate(BaseModel):
    """Schéma de création d'une consultation."""

    patient_id: str = Field(..., description="Identifiant du patient.")
    scheduled_at: Optional[datetime] = Field(default=None, description="Date et heure de la consultation.")
    date: Optional[str] = Field(default=None, description="Alias date string.")
    notes: Optional[str] = Field(default="", description="Notes médicales.")
    diagnosis: Optional[str] = Field(default=None, description="Diagnostic.")
    diagnostic: Optional[str] = Field(default=None, description="Alias diagnostic.")
    motif: Optional[str] = Field(default=None, description="Motif de consultation.")
    prescription: Optional[str] = Field(default=None, description="Prescription ordonnance.")


class ConsultationUpdate(BaseModel):
    """Schéma de mise à jour d'une consultation."""

    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None
    diagnosis: Optional[str] = None
    status: Optional[ConsultationStatus] = None


class ConsultationResponse(BaseModel):
    """Schéma de réponse pour une consultation déchiffrée."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    id: str
    patient_id: str
    practitioner_id: str
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None
    diagnosis: Optional[str] = None
    status: Optional[str] = None
