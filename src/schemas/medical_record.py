"""
Schémas Pydantic pour les dossiers médicaux.

Gère la validation des données de dossiers médicaux en entrée et en sortie.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MedicalRecordCreate(BaseModel):
    """Schéma de création d'un dossier médical."""

    patient_id: str = Field(
        ...,
        description="Identifiant du patient.",
    )
    record_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Type de document (ordonnance, analyse, imagerie, etc.).",
        examples=["ordonnance", "analyse_sang", "radiographie"],
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Contenu du dossier médical (sera chiffré).",
    )


class MedicalRecordResponse(BaseModel):
    """
    Schéma de réponse pour un dossier médical.

    Le contenu est déchiffré avant sérialisation.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Identifiant unique UUID.")
    patient_id: str = Field(..., description="Identifiant du patient.")
    record_type: str = Field(..., description="Type de document.")
    content: str = Field(..., description="Contenu (déchiffré).")
    practitioner_id: str | None = Field(None, description="Identifiant du praticien.")
    created_at: datetime = Field(..., description="Date de création.")
    updated_at: datetime = Field(..., description="Dernière modification.")
