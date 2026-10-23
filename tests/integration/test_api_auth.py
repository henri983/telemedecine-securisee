"""
Tests d'intégration pour l'API d'authentification.

Vérifie les endpoints d'inscription, de connexion, et la protection
des endpoints par tokens JWT.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestRegistration:
    """Tests d'inscription d'utilisateurs."""

    async def test_register_success(self, client: AsyncClient) -> None:
        """L'inscription avec des données valides réussit."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "nouveau.user@telemedecine.fr",
                "password": "S3cur1té!Forte",
                "full_name": "Nouveau Utilisateur",
                "role": "patient",
            },
        )

        assert response.status_code in (200, 201), (
            f"L'inscription devrait réussir (200/201), "
            f"obtenu: {response.status_code} - {response.text}"
        )
        data = response.json()
        assert "email" in data or "id" in data or "access_token" in data, (
            f"La réponse devrait contenir des informations utilisateur: {data}"
        )

    async def test_register_duplicate_email(self, client: AsyncClient) -> None:
        """L'inscription avec un email déjà utilisé est rejetée."""
        user_data = {
            "email": "doublon@telemedecine.fr",
            "password": "S3cur1té!Forte",
            "full_name": "Premier Utilisateur",
            "role": "patient",
        }

        # Première inscription
        await client.post("/api/v1/auth/register", json=user_data)

        # Deuxième inscription avec le même email
        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code in (400, 409, 422), (
            f"L'inscription en doublon devrait échouer (400/409/422), "
            f"obtenu: {response.status_code}"
        )

    async def test_register_weak_password(self, client: AsyncClient) -> None:
        """L'inscription avec un mot de passe faible est rejetée."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user.faible@telemedecine.fr",
                "password": "123",
                "full_name": "Mot De Passe Faible",
                "role": "patient",
            },
        )

        assert response.status_code in (400, 422), (
            f"Un mot de passe faible devrait être rejeté (400/422), "
            f"obtenu: {response.status_code}"
        )

    async def test_register_invalid_email(self, client: AsyncClient) -> None:
        """L'inscription avec un email invalide est rejetée."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "pas-un-email",
                "password": "S3cur1té!Forte",
                "full_name": "Email Invalide",
                "role": "patient",
            },
        )

        assert response.status_code in (400, 422), (
            f"Un email invalide devrait être rejeté (400/422), "
            f"obtenu: {response.status_code}"
        )

    async def test_register_missing_fields(self, client: AsyncClient) -> None:
        """L'inscription avec des champs manquants est rejetée."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "incomplet@test.fr"},
        )

        assert response.status_code == 422, (
            f"Des champs manquants devraient être rejetés (422), "
            f"obtenu: {response.status_code}"
        )


class TestLogin:
    """Tests de connexion."""

    async def test_login_success(self, client: AsyncClient) -> None:
        """La connexion avec des identifiants valides retourne un token."""
        # D'abord s'inscrire
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login.test@telemedecine.fr",
                "password": "S3cur1té!Forte",
                "full_name": "Login Test",
                "role": "patient",
            },
        )

        # Se connecter
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "login.test@telemedecine.fr",
                "password": "S3cur1té!Forte",
            },
        )

        assert response.status_code == 200, (
            f"La connexion devrait réussir (200), "
            f"obtenu: {response.status_code} - {response.text}"
        )
        data = response.json()
        assert "access_token" in data, (
            f"La réponse de connexion doit contenir un access_token: {data}"
        )
        assert data.get("token_type", "bearer").lower() == "bearer", (
            "Le type de token devrait être 'bearer'"
        )

    async def test_login_wrong_password(self, client: AsyncClient) -> None:
        """La connexion avec un mauvais mot de passe est rejetée."""
        # S'inscrire d'abord
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrong.pass@telemedecine.fr",
                "password": "S3cur1té!Forte",
                "full_name": "Wrong Password",
                "role": "patient",
            },
        )

        # Tenter de se connecter avec le mauvais mot de passe
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrong.pass@telemedecine.fr",
                "password": "MauvaisMotDePasse!123",
            },
        )

        assert response.status_code in (400, 401, 403), (
            f"Un mauvais mot de passe devrait être rejeté, "
            f"obtenu: {response.status_code}"
        )

    async def test_login_nonexistent_user(self, client: AsyncClient) -> None:
        """La connexion avec un utilisateur inexistant est rejetée."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nexiste.pas@telemedecine.fr",
                "password": "UnMotDePasse!123",
            },
        )

        assert response.status_code in (400, 401, 404), (
            f"Un utilisateur inexistant devrait être rejeté, "
            f"obtenu: {response.status_code}"
        )


class TestProtectedEndpoints:
    """Tests de protection des endpoints par authentification."""

    async def test_protected_endpoint_without_token(
        self, client: AsyncClient
    ) -> None:
        """Un endpoint protégé sans token retourne 401."""
        response = await client.get("/api/v1/patients/")

        assert response.status_code in (401, 403), (
            f"Un accès sans token devrait retourner 401/403, "
            f"obtenu: {response.status_code}"
        )

    async def test_protected_endpoint_with_invalid_token(
        self, client: AsyncClient
    ) -> None:
        """Un endpoint protégé avec un token invalide retourne 401."""
        response = await client.get(
            "/api/v1/patients/",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code in (401, 403), (
            f"Un token invalide devrait retourner 401/403, "
            f"obtenu: {response.status_code}"
        )

    async def test_protected_endpoint_with_expired_token(
        self, client: AsyncClient
    ) -> None:
        """Un endpoint protégé avec un token expiré retourne 401."""
        # Token JWT expiré (payload vide, expiré)
        expired_token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiJ1c2VyLTEyMyIsImV4cCI6MTAwMDAwMDAwMH0."
            "invalidsignature"
        )

        response = await client.get(
            "/api/v1/patients/",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code in (401, 403), (
            f"Un token expiré devrait retourner 401/403, "
            f"obtenu: {response.status_code}"
        )

    async def test_protected_endpoint_with_valid_token(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """Un endpoint protégé avec un token valide est accessible."""
        response = await client.get(
            "/api/v1/patients/",
            headers=praticien_auth_headers,
        )

        # Devrait retourner 200 (succès) ou 404 (pas de patients)
        assert response.status_code in (200, 404), (
            f"Un accès avec token valide devrait réussir, "
            f"obtenu: {response.status_code} - {response.text}"
        )

    async def test_missing_authorization_header(
        self, client: AsyncClient
    ) -> None:
        """L'absence totale du header Authorization retourne 401."""
        response = await client.get("/api/v1/patients/")

        assert response.status_code in (401, 403), (
            f"Pas de header Authorization => 401/403, "
            f"obtenu: {response.status_code}"
        )
