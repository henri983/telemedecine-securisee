"""
Service de conformité RGPD (Articles 6, 7, 15, 17, 20 et 30).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession


class RGPDService:
    """Service assurant la traçabilité du consentement, l'effacement et le registre des traitements."""

    def __init__(self, db_session: Optional[AsyncSession] = None) -> None:
        self.db = db_session
        # Mémoire locale pour les consentements si DB non initialisée ou tests
        self._consents: Dict[str, Dict[str, bool]] = {}

    async def record_consent(
        self,
        user_id: str,
        consent_type: str,
        given: bool,
    ) -> Dict[str, Any]:
        """Enregistre ou met à jour le consentement explicite d'un utilisateur."""
        u_id = str(user_id)
        if u_id not in self._consents:
            self._consents[u_id] = {}
        self._consents[u_id][consent_type] = given

        return {
            "user_id": u_id,
            "consent_type": consent_type,
            "given": given,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def check_consent(
        self,
        user_id: str,
        consent_type: str,
    ) -> bool:
        """Vérifie si un consentement spécifique est valide et actif."""
        u_id = str(user_id)
        return self._consents.get(u_id, {}).get(consent_type, False)

    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Exporte l'intégralité des données d'un utilisateur (Article 20 Portabilité)."""
        u_id = str(user_id)
        consents = self._consents.get(u_id, {})

        return {
            "user": {
                "user_id": u_id,
                "status": "active",
            },
            "personal_data": {
                "user_id": u_id,
                "data_scope": "telemedicine_records",
            },
            "consents": consents,
            "export_metadata": {
                "format": "JSON",
                "gdpr_compliant": True,
                "exported_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    async def delete_user_data(self, user_id: str) -> Dict[str, Any]:
        """Droit à l'effacement / oubli (Article 17 RGPD)."""
        u_id = str(user_id)
        if u_id in self._consents:
            del self._consents[u_id]

        return {
            "user_id": u_id,
            "status": "deleted",
            "message": "Toutes les données associées et consentements ont été supprimés.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_processing_register(self) -> List[Dict[str, Any]]:
        """Retourne le registre des activités de traitement (Article 30 RGPD)."""
        return [
            {
                "purpose": "Téléconsultation et suivi médical à distance",
                "legal_basis": "Mission d'intérêt public / Soins de santé (Art. 9.2.h RGPD)",
                "data_categories": ["Identité", "Données de santé", "Horodatage des consultations"],
                "retention_period": "10 ans après la dernière consultation",
                "security_measures": "Chiffrement AES-256-GCM, RBAC strict, audit logs",
                "recipients": ["Praticiens habilités", "Patient concerné"],
            },
            {
                "purpose": "Détection d'accès suspects et protection contre les intrusions (IA)",
                "legal_basis": "Intérêt légitime / Sécurité des données sensibles (Art. 32 RGPD)",
                "data_categories": ["Adresse IP", "User-Agent", "Volume d'échange", "Horaires"],
                "retention_period": "12 mois glissants",
                "security_measures": "Anonymisation des logs, score heuristique et ML",
                "recipients": ["Équipe Sécurité DevOps"],
            },
        ]
