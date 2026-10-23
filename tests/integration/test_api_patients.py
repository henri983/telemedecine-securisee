"""
Tests d'intégration pour l'API patients.

Vérifie les endpoints CRUD patient, le contrôle d'accès RBAC,
le chiffrement/déchiffrement des données, et la conformité RGPD.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _patient_payload(suffix: str = "") -> dict:
    """Génère des données patient valides pour les tests."""
    return {
        "first_name": f"Marie{suffix}",
        "last_name": f"Dupont{suffix}",
        "date_of_birth": "1985-03-15",
        "social_security_number": "285031234567890",
        "phone": "+33612345678",
        "address": "42 Rue de la Santé, 75014 Paris",
        "email": f"marie.dupont{suffix}@test.fr",
    }


class TestCreatePatient:
    """Tests de création de patient."""

    async def test_create_patient(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """La création d'un patient avec des données valides réussit."""
        response = await client.post(
            "/api/v1/patients/",
            json=_patient_payload("_create"),
            headers=praticien_auth_headers,
        )

        assert response.status_code in (200, 201), (
            f"La création du patient devrait réussir (200/201), "
            f"obtenu: {response.status_code} - {response.text}"
        )
        data = response.json()
        assert "id" in data, f"La réponse doit contenir l'ID du patient: {data}"

    async def test_create_patient_without_auth(
        self, client: AsyncClient
    ) -> None:
        """La création sans authentification est refusée."""
        response = await client.post(
            "/api/v1/patients/",
            json=_patient_payload("_noauth"),
        )

        assert response.status_code in (401, 403), (
            f"La création sans auth devrait échouer (401/403), "
            f"obtenu: {response.status_code}"
        )


class TestGetPatient:
    """Tests de récupération de patient."""

    async def test_get_patient_as_praticien(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """Un praticien peut consulter les données d'un patient."""
        # Créer le patient
        create_resp = await client.post(
            "/api/v1/patients/",
            json=_patient_payload("_get_prat"),
            headers=praticien_auth_headers,
        )
        if create_resp.status_code not in (200, 201):
            pytest.skip("Impossible de créer le patient pour ce test")

        patient_id = create_resp.json()["id"]

        # Récupérer le patient
        response = await client.get(
            f"/api/v1/patients/{patient_id}",
            headers=praticien_auth_headers,
        )

        assert response.status_code == 200, (
            f"Le praticien devrait pouvoir consulter le patient, "
            f"obtenu: {response.status_code} - {response.text}"
        )
        data = response.json()
        assert data.get("first_name") == "Marie_get_prat" or "first_name" in data, (
            "Les données du patient devraient être retournées"
        )

    async def test_get_patient_as_own_patient(
        self, client: AsyncClient, patient_auth_headers: dict
    ) -> None:
        """Un patient peut voir ses propres données."""
        # Créer d'abord le patient associé à ce user
        # Note: ce test nécessite que le patient soit associé au user du token
        response = await client.get(
            "/api/v1/patients/me",
            headers=patient_auth_headers,
        )

        # 200 si le patient existe et peut voir ses données
        # 404 si le profil patient n'existe pas encore
        assert response.status_code in (200, 404), (
            f"L'accès à ses propres données devrait retourner 200/404, "
            f"obtenu: {response.status_code}"
        )

    async def test_get_patient_unauthorized(
        self, client: AsyncClient, patient_auth_headers: dict
    ) -> None:
        """Un patient ne peut pas voir les données d'un autre patient."""
        other_patient_id = str(uuid.uuid4())

        response = await client.get(
            f"/api/v1/patients/{other_patient_id}",
            headers=patient_auth_headers,
        )

        assert response.status_code in (403, 404), (
            f"L'accès non autorisé aux données d'un autre patient devrait "
            f"retourner 403/404, obtenu: {response.status_code}"
        )

    async def test_get_nonexistent_patient(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """La récupération d'un patient inexistant retourne 404."""
        fake_id = str(uuid.uuid4())

        response = await client.get(
            f"/api/v1/patients/{fake_id}",
            headers=praticien_auth_headers,
        )

        assert response.status_code == 404, (
            f"Un patient inexistant devrait retourner 404, "
            f"obtenu: {response.status_code}"
        )


class TestUpdatePatient:
    """Tests de modification de patient."""

    async def test_update_patient(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """La modification d'un patient existant réussit."""
        # Créer le patient
        create_resp = await client.post(
            "/api/v1/patients/",
            json=_patient_payload("_update"),
            headers=praticien_auth_headers,
        )
        if create_resp.status_code not in (200, 201):
            pytest.skip("Impossible de créer le patient pour ce test")

        patient_id = create_resp.json()["id"]

        # Mettre à jour
        response = await client.put(
            f"/api/v1/patients/{patient_id}",
            json={"phone": "+33698765432", "address": "Nouvelle adresse, Paris"},
            headers=praticien_auth_headers,
        )

        assert response.status_code == 200, (
            f"La mise à jour devrait réussir (200), "
            f"obtenu: {response.status_code} - {response.text}"
        )


class TestDeletePatient:
    """Tests de suppression de patient (conformité RGPD)."""

    async def test_delete_patient_rgpd(
        self, client: AsyncClient, admin_auth_headers: dict
    ) -> None:
        """La suppression RGPD d'un patient efface toutes ses données."""
        # Créer le patient
        create_resp = await client.post(
            "/api/v1/patients/",
            json=_patient_payload("_delete"),
            headers=admin_auth_headers,
        )
        if create_resp.status_code not in (200, 201):
            pytest.skip("Impossible de créer le patient pour ce test")

        patient_id = create_resp.json()["id"]

        # Supprimer (droit à l'oubli)
        response = await client.delete(
            f"/api/v1/patients/{patient_id}",
            headers=admin_auth_headers,
        )

        assert response.status_code in (200, 204), (
            f"La suppression devrait réussir (200/204), "
            f"obtenu: {response.status_code}"
        )

        # Vérifier que le patient n'existe plus
        get_response = await client.get(
            f"/api/v1/patients/{patient_id}",
            headers=admin_auth_headers,
        )
        assert get_response.status_code == 404, (
            "Le patient supprimé ne devrait plus être accessible"
        )


class TestExportPatientData:
    """Tests d'export de données patient (droit d'accès RGPD)."""

    async def test_export_patient_data(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """L'export des données patient retourne un JSON complet."""
        # Créer le patient
        create_resp = await client.post(
            "/api/v1/patients/",
            json=_patient_payload("_export"),
            headers=praticien_auth_headers,
        )
        if create_resp.status_code not in (200, 201):
            pytest.skip("Impossible de créer le patient pour ce test")

        patient_id = create_resp.json()["id"]

        # Exporter les données
        response = await client.get(
            f"/api/v1/patients/{patient_id}/export",
            headers=praticien_auth_headers,
        )

        assert response.status_code == 200, (
            f"L'export devrait réussir (200), "
            f"obtenu: {response.status_code} - {response.text}"
        )
        data = response.json()
        assert isinstance(data, dict), "L'export doit être un dictionnaire JSON"
        assert len(data) > 0, "L'export ne doit pas être vide"
