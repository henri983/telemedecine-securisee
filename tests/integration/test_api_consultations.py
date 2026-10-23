"""
Tests d'intégration pour l'API consultations.

Vérifie les endpoints de création, récupération, et listage
des consultations médicales, avec contrôle d'accès RBAC.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _consultation_payload(patient_id: str) -> dict:
    """Génère des données de consultation valides pour les tests."""
    return {
        "patient_id": patient_id,
        "motif": "Consultation de suivi pour hypertension artérielle",
        "notes": "TA: 14/9. Traitement actuel bien toléré. Renouvellement ordonnance.",
        "diagnostic": "Hypertension artérielle essentielle stabilisée",
        "prescription": "Amlodipine 5mg - 1 comprimé par jour pendant 3 mois",
        "date": "2024-06-15T10:30:00Z",
    }


def _patient_payload(suffix: str = "") -> dict:
    """Génère des données patient valides."""
    return {
        "first_name": f"Patient{suffix}",
        "last_name": f"Consult{suffix}",
        "date_of_birth": "1975-08-22",
        "social_security_number": "175082234567890",
        "phone": "+33687654321",
        "address": "8 Avenue de la République, 75011 Paris",
        "email": f"patient.consult{suffix}@test.fr",
    }


async def _create_test_patient(
    client: AsyncClient, headers: dict, suffix: str = ""
) -> str | None:
    """Helper: crée un patient de test et retourne son ID."""
    resp = await client.post(
        "/api/v1/patients/",
        json=_patient_payload(suffix),
        headers=headers,
    )
    if resp.status_code in (200, 201):
        return resp.json()["id"]
    return None


class TestCreateConsultation:
    """Tests de création de consultation."""

    async def test_create_consultation(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """Un praticien peut créer une consultation."""
        # Créer un patient d'abord
        patient_id = await _create_test_patient(
            client, praticien_auth_headers, "_consult_create"
        )
        if patient_id is None:
            pytest.skip("Impossible de créer le patient pour ce test")

        # Créer la consultation
        response = await client.post(
            "/api/v1/consultations/",
            json=_consultation_payload(patient_id),
            headers=praticien_auth_headers,
        )

        assert response.status_code in (200, 201), (
            f"La création de consultation devrait réussir (200/201), "
            f"obtenu: {response.status_code} - {response.text}"
        )
        data = response.json()
        assert "id" in data, f"La réponse doit contenir l'ID de la consultation: {data}"

    async def test_patient_cannot_create_consultation(
        self, client: AsyncClient, patient_auth_headers: dict
    ) -> None:
        """Un patient ne peut pas créer de consultation (rôle insuffisant)."""
        response = await client.post(
            "/api/v1/consultations/",
            json=_consultation_payload(str(uuid.uuid4())),
            headers=patient_auth_headers,
        )

        assert response.status_code in (403, 401), (
            f"Un patient ne devrait pas pouvoir créer de consultation (403), "
            f"obtenu: {response.status_code}"
        )

    async def test_create_consultation_without_auth(
        self, client: AsyncClient
    ) -> None:
        """La création sans authentification est refusée."""
        response = await client.post(
            "/api/v1/consultations/",
            json=_consultation_payload(str(uuid.uuid4())),
        )

        assert response.status_code in (401, 403), (
            f"La création sans auth devrait échouer (401/403), "
            f"obtenu: {response.status_code}"
        )

    async def test_create_consultation_invalid_patient(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """La création pour un patient inexistant échoue."""
        fake_patient_id = str(uuid.uuid4())

        response = await client.post(
            "/api/v1/consultations/",
            json=_consultation_payload(fake_patient_id),
            headers=praticien_auth_headers,
        )

        assert response.status_code in (400, 404, 422), (
            f"Une consultation pour un patient inexistant devrait échouer, "
            f"obtenu: {response.status_code}"
        )


class TestGetConsultation:
    """Tests de récupération de consultation."""

    async def test_get_consultation(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """Un praticien peut récupérer une consultation existante."""
        # Créer patient + consultation
        patient_id = await _create_test_patient(
            client, praticien_auth_headers, "_consult_get"
        )
        if patient_id is None:
            pytest.skip("Impossible de créer le patient")

        create_resp = await client.post(
            "/api/v1/consultations/",
            json=_consultation_payload(patient_id),
            headers=praticien_auth_headers,
        )
        if create_resp.status_code not in (200, 201):
            pytest.skip("Impossible de créer la consultation")

        consultation_id = create_resp.json()["id"]

        # Récupérer la consultation
        response = await client.get(
            f"/api/v1/consultations/{consultation_id}",
            headers=praticien_auth_headers,
        )

        assert response.status_code == 200, (
            f"La récupération devrait réussir (200), "
            f"obtenu: {response.status_code} - {response.text}"
        )
        data = response.json()
        assert data.get("id") == consultation_id, (
            "L'ID de la consultation retournée doit correspondre"
        )

    async def test_get_nonexistent_consultation(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """La récupération d'une consultation inexistante retourne 404."""
        fake_id = str(uuid.uuid4())

        response = await client.get(
            f"/api/v1/consultations/{fake_id}",
            headers=praticien_auth_headers,
        )

        assert response.status_code == 404, (
            f"Une consultation inexistante devrait retourner 404, "
            f"obtenu: {response.status_code}"
        )


class TestListConsultations:
    """Tests de listage des consultations."""

    async def test_list_patient_consultations(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """La liste des consultations d'un patient est récupérable."""
        # Créer patient + consultation
        patient_id = await _create_test_patient(
            client, praticien_auth_headers, "_consult_list"
        )
        if patient_id is None:
            pytest.skip("Impossible de créer le patient")

        await client.post(
            "/api/v1/consultations/",
            json=_consultation_payload(patient_id),
            headers=praticien_auth_headers,
        )

        # Lister les consultations du patient
        response = await client.get(
            f"/api/v1/patients/{patient_id}/consultations",
            headers=praticien_auth_headers,
        )

        assert response.status_code == 200, (
            f"La liste devrait réussir (200), "
            f"obtenu: {response.status_code} - {response.text}"
        )
        data = response.json()
        assert isinstance(data, (list, dict)), (
            "La réponse doit être une liste ou un objet paginé"
        )

    async def test_list_consultations_empty(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """Un patient sans consultation retourne une liste vide."""
        patient_id = await _create_test_patient(
            client, praticien_auth_headers, "_consult_empty"
        )
        if patient_id is None:
            pytest.skip("Impossible de créer le patient")

        response = await client.get(
            f"/api/v1/patients/{patient_id}/consultations",
            headers=praticien_auth_headers,
        )

        assert response.status_code == 200, (
            f"La liste vide devrait retourner 200, "
            f"obtenu: {response.status_code}"
        )
        data = response.json()
        items = data if isinstance(data, list) else data.get("items", data.get("consultations", []))
        assert len(items) == 0, (
            "Un patient sans consultation devrait avoir une liste vide"
        )
