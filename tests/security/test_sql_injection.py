"""
Tests de sécurité: détection d'injections SQL.

Vérifie que l'application résiste aux tentatives d'injection SQL
sur les endpoints d'authentification, de recherche, et d'accès patient.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient


pytestmark = [pytest.mark.security, pytest.mark.asyncio]

# Payloads d'injection SQL classiques
SQL_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "' UNION SELECT * FROM users --",
    "1' OR '1'='1' --",
    "admin'--",
    "' OR 1=1 --",
    "'; INSERT INTO users (email) VALUES ('hacked@evil.com'); --",
    "1; UPDATE users SET role='admin' WHERE email='patient@test.fr'; --",
    "' UNION SELECT password FROM users WHERE '1'='1",
    "1 OR 1=1",
    "' OR ''='",
    "'; EXEC xp_cmdshell('whoami'); --",
]


class TestLoginSQLInjection:
    """Tests d'injection SQL sur l'endpoint de connexion."""

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS[:6])
    async def test_login_sql_injection_email(
        self, client: AsyncClient, payload: str
    ) -> None:
        """Les injections SQL dans le champ email sont neutralisées."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": payload,
                "password": "password123",
            },
        )

        # L'application ne doit PAS retourner 200 (succès)
        # ni 500 (erreur serveur qui indiquerait une faille)
        assert response.status_code != 200, (
            f"L'injection SQL '{payload}' ne devrait pas permettre la connexion"
        )
        assert response.status_code != 500, (
            f"L'injection SQL '{payload}' ne devrait pas causer une erreur serveur 500"
        )

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS[:6])
    async def test_login_sql_injection_password(
        self, client: AsyncClient, payload: str
    ) -> None:
        """Les injections SQL dans le champ password sont neutralisées."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@telemedecine.fr",
                "password": payload,
            },
        )

        assert response.status_code != 200, (
            f"L'injection SQL dans le mot de passe ne devrait pas fonctionner"
        )
        assert response.status_code != 500, (
            f"L'injection SQL '{payload}' ne devrait pas causer une erreur serveur"
        )


class TestSearchSQLInjection:
    """Tests d'injection SQL sur les endpoints de recherche."""

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS[:4])
    async def test_search_sql_injection(
        self, client: AsyncClient, praticien_auth_headers: dict, payload: str
    ) -> None:
        """Les injections SQL dans les paramètres de recherche sont neutralisées."""
        response = await client.get(
            "/api/v1/patients/",
            params={"search": payload},
            headers=praticien_auth_headers,
        )

        # Ne doit pas causer d'erreur serveur
        assert response.status_code != 500, (
            f"L'injection SQL dans la recherche '{payload}' "
            f"ne devrait pas causer d'erreur serveur"
        )
        # Si la requête retourne des résultats, ils ne doivent pas
        # contenir de données d'autres tables
        if response.status_code == 200:
            data = response.json()
            data_str = str(data).lower()
            assert "password" not in data_str or "hashed" in data_str, (
                "Les résultats ne doivent pas contenir de mots de passe"
            )


class TestPatientIdSQLInjection:
    """Tests d'injection SQL sur les identifiants patient."""

    @pytest.mark.parametrize("payload", [
        "' OR '1'='1",
        "1 OR 1=1",
        "'; DROP TABLE patients; --",
        "1 UNION SELECT * FROM users --",
    ])
    async def test_patient_id_sql_injection(
        self, client: AsyncClient, praticien_auth_headers: dict, payload: str
    ) -> None:
        """Les injections SQL dans les IDs patient sont neutralisées."""
        response = await client.get(
            f"/api/v1/patients/{payload}",
            headers=praticien_auth_headers,
        )

        # Doit retourner 400/404/422, PAS 200 ni 500
        assert response.status_code != 200, (
            f"L'injection SQL dans l'ID patient ne devrait pas retourner de données"
        )
        assert response.status_code != 500, (
            f"L'injection SQL '{payload}' dans l'ID ne devrait pas causer d'erreur serveur"
        )

    @pytest.mark.parametrize("payload", [
        "'; UPDATE patients SET last_name='HACKED'; --",
        "1; DELETE FROM patients; --",
    ])
    async def test_patient_id_destructive_injection(
        self, client: AsyncClient, praticien_auth_headers: dict, payload: str
    ) -> None:
        """Les injections SQL destructrices dans les IDs sont bloquées."""
        response = await client.get(
            f"/api/v1/patients/{payload}",
            headers=praticien_auth_headers,
        )

        assert response.status_code != 500, (
            f"L'injection destructrice '{payload}' ne devrait pas causer d'erreur serveur"
        )

    async def test_consultation_id_sql_injection(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """Les injections SQL dans les IDs consultation sont neutralisées."""
        payload = "' OR '1'='1' --"
        response = await client.get(
            f"/api/v1/consultations/{payload}",
            headers=praticien_auth_headers,
        )

        assert response.status_code != 200
        assert response.status_code != 500
