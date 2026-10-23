"""
Routes de gestion de la conformité RGPD (Consentement, Droit à l'oubli, Registre).
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.dependencies import get_current_user
from src.models.user import User, UserRole
from src.services.rgpd_service import RGPDService

router = APIRouter(prefix="/rgpd", tags=["Conformité RGPD"])
_service = RGPDService()


class ConsentRequest(BaseModel):
    consent_type: str = Field(..., description="Finalité du consentement")
    given: bool = Field(..., description="Accepté ou révoqué")


@router.post("/consent/{user_id}", summary="Enregistrer un consentement explicite")
async def record_user_consent(
    user_id: str,
    payload: ConsentRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Enregistre le recueil de consentement de l'utilisateur."""
    if str(current_user.id) != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé.")

    return await _service.record_consent(
        user_id=user_id,
        consent_type=payload.consent_type,
        given=payload.given,
    )


@router.get("/consent/{user_id}", summary="Vérifier le statut d'un consentement")
async def check_user_consent(
    user_id: str,
    consent_type: str = "data_processing",
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Consulte l'état du consentement pour une finalité donnée."""
    if str(current_user.id) != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé.")

    is_given = await _service.check_consent(user_id=user_id, consent_type=consent_type)
    return {"user_id": user_id, "consent_type": consent_type, "given": is_given}


@router.get("/processing-register", summary="Consulter le registre des activités de traitement (Art. 30)")
async def get_processing_register(
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Registre des traitements opposable et auditable selon le RGPD."""
    return await _service.get_processing_register()
