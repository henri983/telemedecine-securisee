"""
Routeur central agrégeant tous les endpoints de l'API.
"""

from fastapi import APIRouter

from src.api.routes.auth import router as auth_router
from src.api.routes.consultations import router as consultations_router
from src.api.routes.medical_records import router as medical_records_router
from src.api.routes.patients import router as patients_router
from src.api.routes.rgpd import router as rgpd_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(patients_router)
api_router.include_router(consultations_router)
api_router.include_router(medical_records_router)
api_router.include_router(rgpd_router)

__all__ = ["api_router"]
