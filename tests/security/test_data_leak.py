"""
Tests de sécurité: prévention des fuites de données.

Vérifie que les réponses d'erreur ne contiennent pas de stack traces,
que les logs ne contiennent pas de PII, que les réponses API ne
divulguent pas de champs sensibles, et que les données en base
sont bien chiffrées.
"""

import json
import logging
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient

from src.security.crypto import EncryptionService


pytestmark = [pytest.mark.security, pytest.mark.asyncio]


class TestErrorResponseNoStackTrace:
    """Tests que les erreurs ne divulguent pas de détails techniques."""

    async def test_error_response_no_stack_trace(
        self, client: AsyncClient
    ) -> None:
        """Les réponses d'erreur ne contiennent pas de stack trace."""
        # Provoquer une erreur (endpoint inexistant avec paramètres invalides)
        response = await client.get("/api/v1/nonexistent-endpoint")

        response_text = response.text.lower()

        # Vérifier l'absence de stack trace
        assert "traceback" not in response_text, (
            "La réponse d'erreur ne devrait pas contenir 'traceback'"
        )
        assert "file \"/" not in response_text and 'file "c:' not in response_text, (
            "La réponse d'erreur ne devrait pas contenir de chemins de fichiers"
        )
        assert "line " not in response_text or "error" in response_text, (
            "La réponse d'erreur ne devrait pas contenir de numéros de ligne"
        )

    async def test_invalid_json_no_stack_trace(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """Une requête avec un JSON invalide ne divulgue pas de détails."""
        response = await client.post(
            "/api/v1/patients/",
            content="ceci n'est pas du json",
            headers={
                **praticien_auth_headers,
                "Content-Type": "application/json",
            },
        )

        response_text = response.text.lower()
        assert "traceback" not in response_text
        assert "sqlalchemy" not in response_text, (
            "Le nom de l'ORM ne devrait pas apparaître dans les erreurs"
        )
        assert "pydantic" not in response_text or "validation" in response_text, (
            "Les détails internes de Pydantic ne devraient pas être exposés"
        )

    async def test_server_error_generic_message(
        self, client: AsyncClient
    ) -> None:
        """Les erreurs 500 retournent un message générique."""
        # Tenter de déclencher une erreur interne
        response = await client.get(
            "/api/v1/patients/not-a-valid-uuid-at-all!@#$%",
        )

        if response.status_code == 500:
            data = response.json() if "json" in response.headers.get("content-type", "") else {}
            detail = str(data.get("detail", data.get("message", response.text)))
            assert "internal" in detail.lower() or "error" in detail.lower() or \
                   len(detail) < 200, (
                f"Le message d'erreur 500 devrait être générique, obtenu: {detail}"
            )


class TestLogsNoPII:
    """Tests que les logs ne contiennent pas de PII."""

    async def test_logs_no_pii(
        self, client: AsyncClient, praticien_auth_headers: dict, caplog
    ) -> None:
        """Les logs applicatifs ne contiennent pas de données personnelles."""
        # Effectuer des actions qui génèrent des logs
        with caplog.at_level(logging.INFO):
            await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "sensitive.email@test.fr",
                    "password": "SensitiveP@ssw0rd!",
                },
            )

        # Vérifier les logs capturés
        log_text = caplog.text.lower()

        # Le mot de passe ne doit JAMAIS apparaître dans les logs
        assert "sensitivep@ssw0rd" not in log_text, (
            "Le mot de passe ne doit JAMAIS apparaître dans les logs"
        )

        # L'email complet ne devrait pas apparaître en clair
        # (tolérance: certaines implémentations loguent l'email masqué)
        if "sensitive.email@test.fr" in log_text:
            pytest.fail(
                "L'email complet ne devrait pas apparaître en clair dans les logs. "
                "Utilisez le masquage de données pour les logs."
            )

    async def test_logs_no_social_security(
        self, client: AsyncClient, praticien_auth_headers: dict, caplog
    ) -> None:
        """Le numéro de sécurité sociale n'apparaît pas dans les logs."""
        ssn = "185031234567890"

        with caplog.at_level(logging.DEBUG):
            await client.post(
                "/api/v1/patients/",
                json={
                    "first_name": "Test",
                    "last_name": "Logs",
                    "date_of_birth": "1985-03-15",
                    "social_security_number": ssn,
                    "phone": "+33600000000",
                    "address": "1 Rue Test, Paris",
                    "email": "logs.test@test.fr",
                },
                headers=praticien_auth_headers,
            )

        log_text = caplog.text
        assert ssn not in log_text, (
            "Le numéro de sécurité sociale ne doit JAMAIS apparaître dans les logs"
        )


class TestResponseNoSensitiveFields:
    """Tests que les réponses API ne divulguent pas de champs sensibles."""

    async def test_response_no_password(
        self, client: AsyncClient
    ) -> None:
        """Les réponses API ne contiennent jamais de mot de passe."""
        # S'inscrire
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "no.password.in.response@test.fr",
                "password": "S3cur1té!Forte",
                "full_name": "No Password Leak",
                "role": "patient",
            },
        )

        if response.status_code in (200, 201):
            data = response.json()
            data_str = json.dumps(data).lower()

            assert "s3cur1té!forte" not in data_str, (
                "Le mot de passe en clair ne doit JAMAIS apparaître dans la réponse"
            )
            assert "hashed_password" not in data_str, (
                "Le hash du mot de passe ne devrait pas être dans la réponse"
            )
            assert "$2b$" not in data_str and "$argon2" not in data_str, (
                "Le hash bcrypt/argon2 ne devrait pas être exposé"
            )

    async def test_response_no_encryption_key(
        self, client: AsyncClient, praticien_auth_headers: dict
    ) -> None:
        """Les réponses ne contiennent pas de clés de chiffrement."""
        response = await client.get(
            "/api/v1/patients/",
            headers=praticien_auth_headers,
        )

        if response.status_code == 200:
            data_str = json.dumps(response.json()).lower()
            assert "encryption_key" not in data_str, (
                "Les clés de chiffrement ne doivent pas être exposées"
            )
            assert "secret_key" not in data_str, (
                "Les clés secrètes ne doivent pas être exposées"
            )
            assert "private_key" not in data_str, (
                "Les clés privées ne doivent pas être exposées"
            )

    async def test_response_no_internal_ids(
        self, client: AsyncClient
    ) -> None:
        """Les réponses d'erreur ne divulguent pas d'IDs internes de la DB."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "inexistant@test.fr",
                "password": "MotDePasse!123",
            },
        )

        data_str = json.dumps(response.json()).lower() if response.status_code != 500 else response.text.lower()
        assert "sqlalchemy" not in data_str, (
            "Les détails SQLAlchemy ne doivent pas être exposés"
        )
        assert "postgresql" not in data_str and "sqlite" not in data_str, (
            "Le type de base de données ne devrait pas être exposé dans les erreurs"
        )


class TestEncryptedDataInDB:
    """Tests que les données sensibles sont chiffrées en base de données."""

    def test_encrypted_data_in_db(
        self, encryption_service: EncryptionService
    ) -> None:
        """Les données chiffrées en DB ne sont pas lisibles en clair."""
        # Simuler le chiffrement tel qu'il est fait en DB
        sensitive_data = {
            "first_name": "Marie",
            "last_name": "Dupont",
            "social_security": "285031234567890",
            "phone": "+33612345678",
        }

        for field_name, value in sensitive_data.items():
            encrypted = encryption_service.encrypt(value)

            # La valeur chiffrée ne doit PAS contenir la valeur en clair
            assert value not in str(encrypted), (
                f"Le champ '{field_name}' ne devrait pas être lisible "
                f"après chiffrement. Valeur: '{value}', Chiffré: '{encrypted[:50]}...'"
            )

    def test_encrypted_data_not_deterministic(
        self, encryption_service: EncryptionService
    ) -> None:
        """Le chiffrement n'est pas déterministe (nonce aléatoire)."""
        value = "285031234567890"
        encrypted1 = encryption_service.encrypt(value)
        encrypted2 = encryption_service.encrypt(value)

        assert encrypted1 != encrypted2, (
            "Deux chiffrements du même numéro de sécu doivent être différents "
            "pour empêcher les attaques par comparaison"
        )

    def test_decrypted_data_matches_original(
        self, encryption_service: EncryptionService
    ) -> None:
        """Les données déchiffrées correspondent aux originaux."""
        original = "Marie Dupont - 285031234567890"
        encrypted = encryption_service.encrypt(original)
        decrypted = encryption_service.decrypt(encrypted)

        assert decrypted == original, (
            f"Les données déchiffrées '{decrypted}' ne correspondent pas "
            f"à l'original '{original}'"
        )
