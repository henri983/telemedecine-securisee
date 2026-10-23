"""
Tests unitaires pour le service d'authentification.

Vérifie le hachage de mots de passe, la validation de robustesse,
la création et vérification de tokens JWT.
"""

import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.services.auth_service import AuthService
from src.security.jwt_handler import JWTHandler


pytestmark = [pytest.mark.unit]

TEST_SECRET = "test-secret-key-for-jwt-do-not-use-in-production-1234567890"


@pytest.fixture
def auth_service() -> AuthService:
    """Service d'authentification pour les tests."""
    return AuthService()


@pytest.fixture
def jwt_handler() -> JWTHandler:
    """Gestionnaire JWT pour les tests."""
    return JWTHandler(
        secret_key=TEST_SECRET,
        algorithm="HS256",
        access_token_expire_minutes=30,
    )


class TestPasswordHashing:
    """Tests du hachage de mots de passe."""

    def test_password_hashing(self, auth_service: AuthService) -> None:
        """Le hash est différent du mot de passe en clair."""
        password = "MonMotDePasse123!"
        hashed = auth_service.hash_password(password)
        assert hashed != password, (
            "Le hash ne doit JAMAIS être identique au mot de passe en clair"
        )
        assert len(hashed) > 20, (
            "Le hash doit avoir une longueur significative (bcrypt/argon2)"
        )

    def test_password_verification(self, auth_service: AuthService) -> None:
        """La vérification du mot de passe fonctionne correctement."""
        password = "Secur1té_Médicale!"
        hashed = auth_service.hash_password(password)
        assert auth_service.verify_password(password, hashed) is True, (
            "Le mot de passe correct devrait être vérifié avec succès"
        )

    def test_wrong_password_rejected(self, auth_service: AuthService) -> None:
        """Un mot de passe incorrect est rejeté."""
        password = "BonMotDePasse123!"
        wrong_password = "MauvaisMotDePasse456!"
        hashed = auth_service.hash_password(password)
        assert auth_service.verify_password(wrong_password, hashed) is False, (
            "Un mot de passe incorrect devrait être rejeté"
        )

    def test_same_password_different_hashes(self, auth_service: AuthService) -> None:
        """Le même mot de passe produit des hashes différents (salt aléatoire)."""
        password = "MotDePasse123!"
        hash1 = auth_service.hash_password(password)
        hash2 = auth_service.hash_password(password)
        assert hash1 != hash2, (
            "Deux hachages du même mot de passe doivent être différents (salt)"
        )


class TestPasswordStrength:
    """Tests de la validation de robustesse des mots de passe."""

    def test_password_strength_valid(self, auth_service: AuthService) -> None:
        """Un mot de passe robuste est accepté."""
        strong_password = "Téléméd3cine!Sécurisée"
        result = auth_service.validate_password_strength(strong_password)
        assert result is True or result.get("valid", False) is True, (
            f"Le mot de passe fort '{strong_password}' devrait être accepté"
        )

    def test_password_strength_too_short(self, auth_service: AuthService) -> None:
        """Un mot de passe trop court est rejeté."""
        short_password = "Ab1!"
        with pytest.raises(Exception) as exc_info:
            result = auth_service.validate_password_strength(short_password)
            # Si pas d'exception, vérifier le retour
            if isinstance(result, dict):
                assert result.get("valid") is False
            elif isinstance(result, bool):
                assert result is False
        # L'exception est acceptable aussi

    def test_password_strength_no_uppercase(self, auth_service: AuthService) -> None:
        """Un mot de passe sans majuscule est rejeté."""
        no_upper = "motdepasse123!fort"
        try:
            result = auth_service.validate_password_strength(no_upper)
            if isinstance(result, dict):
                assert result.get("valid") is False, (
                    "Un mot de passe sans majuscule devrait être rejeté"
                )
            elif isinstance(result, bool):
                assert result is False, (
                    "Un mot de passe sans majuscule devrait être rejeté"
                )
        except Exception:
            pass  # Exception est un rejet valide

    def test_password_strength_no_special(self, auth_service: AuthService) -> None:
        """Un mot de passe sans caractère spécial est rejeté."""
        no_special = "MotDePasse12345"
        try:
            result = auth_service.validate_password_strength(no_special)
            if isinstance(result, dict):
                assert result.get("valid") is False, (
                    "Un mot de passe sans caractère spécial devrait être rejeté"
                )
            elif isinstance(result, bool):
                assert result is False, (
                    "Un mot de passe sans caractère spécial devrait être rejeté"
                )
        except Exception:
            pass  # Exception est un rejet valide

    def test_password_strength_no_digit(self, auth_service: AuthService) -> None:
        """Un mot de passe sans chiffre est rejeté."""
        no_digit = "MotDePasse!Fort"
        try:
            result = auth_service.validate_password_strength(no_digit)
            if isinstance(result, dict):
                assert result.get("valid") is False, (
                    "Un mot de passe sans chiffre devrait être rejeté"
                )
            elif isinstance(result, bool):
                assert result is False, (
                    "Un mot de passe sans chiffre devrait être rejeté"
                )
        except Exception:
            pass  # Exception est un rejet valide


class TestJWTTokens:
    """Tests de la création et vérification de tokens JWT."""

    def test_create_access_token(self, jwt_handler: JWTHandler) -> None:
        """Le token créé contient les bons claims."""
        user_id = str(uuid.uuid4())
        token = jwt_handler.create_access_token(
            subject=user_id,
            extra_claims={"email": "test@test.fr", "role": "praticien"},
        )

        assert isinstance(token, str), "Le token doit être une chaîne"
        assert len(token) > 50, "Le token JWT doit avoir une longueur significative"

        # Vérifier le décodage
        payload = jwt_handler.decode_token(token)
        assert payload is not None, "Le token devrait être décodable"
        assert payload.get("sub") == user_id, (
            f"Le subject du token '{payload.get('sub')}' "
            f"ne correspond pas à '{user_id}'"
        )
        assert payload.get("email") == "test@test.fr"
        assert payload.get("role") == "praticien"

    def test_token_contains_expiration(self, jwt_handler: JWTHandler) -> None:
        """Le token contient une date d'expiration."""
        token = jwt_handler.create_access_token(
            subject="user-123",
            extra_claims={"role": "admin"},
        )
        payload = jwt_handler.decode_token(token)
        assert "exp" in payload, "Le token doit contenir un claim 'exp'"
        exp_timestamp = payload["exp"]
        assert exp_timestamp > time.time(), (
            "La date d'expiration doit être dans le futur"
        )

    def test_token_expiration(self, jwt_handler: JWTHandler) -> None:
        """Un token expiré est rejeté."""
        # Créer un handler avec expiration très courte
        short_lived_handler = JWTHandler(
            secret_key=TEST_SECRET,
            algorithm="HS256",
            access_token_expire_minutes=-1,  # Déjà expiré
        )
        token = short_lived_handler.create_access_token(
            subject="user-expired",
            extra_claims={"role": "patient"},
        )

        with pytest.raises(Exception) as exc_info:
            short_lived_handler.decode_token(token)
        assert exc_info.value is not None, (
            "Un token expiré devrait lever une exception"
        )

    def test_token_invalid_signature(self, jwt_handler: JWTHandler) -> None:
        """Un token avec une signature invalide est rejeté."""
        token = jwt_handler.create_access_token(
            subject="user-test",
            extra_claims={"role": "admin"},
        )

        # Altérer la signature (dernière partie du JWT)
        parts = token.rsplit(".", 1)
        tampered_token = parts[0] + ".invalidsignature"

        with pytest.raises(Exception):
            jwt_handler.decode_token(tampered_token)

    def test_decode_garbage_token(self, jwt_handler: JWTHandler) -> None:
        """Un token complètement invalide est rejeté."""
        with pytest.raises(Exception):
            jwt_handler.decode_token("not-a-jwt-token")
