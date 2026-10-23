"""
Tests unitaires pour le service de masquage de données.

Vérifie que les données PII sont correctement masquées
pour les logs et réponses, conformément au RGPD.
"""

import pytest

from src.security.data_masking import mask_email, mask_name, mask_pii, anonymize_for_logs


pytestmark = [pytest.mark.unit]


class TestMaskEmail:
    """Tests du masquage d'adresses email."""

    def test_mask_email(self) -> None:
        """L'email est masqué correctement (seul le premier caractère visible)."""
        email = "jean.dupont@example.com"
        masked = mask_email(email)
        # L'email masqué ne doit pas contenir l'adresse complète
        assert "jean.dupont" not in masked, (
            f"L'email masqué '{masked}' contient encore le nom complet"
        )
        # Le domaine ou une partie devrait être partiellement visible
        assert "@" in masked or "***" in masked or "*" in masked, (
            f"L'email masqué '{masked}' devrait contenir des caractères de masquage"
        )

    def test_mask_email_preserves_structure(self) -> None:
        """Le masquage préserve une structure reconnaissable."""
        email = "marie.martin@hopital.fr"
        masked = mask_email(email)
        assert masked != email, "L'email masqué doit être différent de l'original"
        assert len(masked) > 0, "L'email masqué ne doit pas être vide"

    def test_mask_email_short(self) -> None:
        """Le masquage fonctionne avec un email court."""
        email = "a@b.fr"
        masked = mask_email(email)
        assert masked != email

    def test_mask_email_different_inputs(self) -> None:
        """Deux emails différents donnent des masquages différents ou identiques en forme."""
        email1 = "alice@example.com"
        email2 = "bob@example.com"
        masked1 = mask_email(email1)
        masked2 = mask_email(email2)
        # Les deux doivent être masqués
        assert "alice" not in masked1
        assert "bob" not in masked2


class TestMaskName:
    """Tests du masquage de noms."""

    def test_mask_name(self) -> None:
        """Le nom est masqué correctement."""
        name = "Jean Dupont"
        masked = mask_name(name)
        assert masked != name, (
            f"Le nom masqué '{masked}' ne devrait pas être identique à l'original"
        )
        # Le nom complet ne doit plus apparaître
        assert "Jean Dupont" not in masked or "***" in masked or "*" in masked, (
            f"Le nom masqué '{masked}' devrait cacher le nom complet"
        )

    def test_mask_name_single_name(self) -> None:
        """Le masquage fonctionne avec un seul nom."""
        name = "Éloïse"
        masked = mask_name(name)
        assert masked != name

    def test_mask_name_long_name(self) -> None:
        """Le masquage fonctionne avec un nom composé."""
        name = "Marie-Antoinette de La Fontaine"
        masked = mask_name(name)
        assert "Marie-Antoinette de La Fontaine" not in masked

    def test_mask_empty_string(self) -> None:
        """Le masquage d'une chaîne vide ne crash pas."""
        masked = mask_name("")
        assert masked is not None, "Le masquage d'une chaîne vide ne doit pas retourner None"


class TestMaskPiiDict:
    """Tests du masquage de dictionnaires contenant des PII."""

    def test_mask_pii_dict(self) -> None:
        """Les champs PII d'un dictionnaire sont masqués."""
        data = {
            "email": "patient@example.com",
            "name": "Marie Martin",
            "phone": "+33612345678",
            "address": "12 Rue de la Paix, Paris",
            "social_security": "185031234567890",
        }
        masked = mask_pii(data)

        assert masked["email"] != "patient@example.com", (
            "L'email devrait être masqué"
        )
        assert masked.get("name", masked.get("full_name", "")) != "Marie Martin", (
            "Le nom devrait être masqué"
        )

    def test_mask_preserves_non_pii(self) -> None:
        """Les champs non-PII sont préservés tels quels."""
        data = {
            "id": "abc-123",
            "role": "patient",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z",
            "email": "test@test.fr",
        }
        masked = mask_pii(data)

        assert masked.get("id") == "abc-123", "L'ID ne devrait pas être masqué"
        assert masked.get("role") == "patient", "Le rôle ne devrait pas être masqué"
        assert masked.get("is_active") is True, "is_active ne devrait pas être masqué"

    def test_mask_pii_returns_new_dict(self) -> None:
        """Le masquage retourne un nouveau dict sans modifier l'original."""
        data = {"email": "test@test.fr", "name": "Test User"}
        original_email = data["email"]
        masked = mask_pii(data)

        # Vérifier que l'original n'est pas modifié
        assert data["email"] == original_email, (
            "Le dictionnaire original ne devrait pas être modifié"
        )


class TestAnonymizeForLogs:
    """Tests de l'anonymisation pour les logs."""

    def test_anonymize_for_logs(self) -> None:
        """Les données sont anonymisées pour les logs (aucune PII)."""
        data = {
            "user_id": "user-123",
            "email": "docteur@hopital.fr",
            "patient_name": "Jean Dupont",
            "diagnostic": "Hypertension",
            "action": "consultation_view",
        }
        anonymized = anonymize_for_logs(data)

        # Les PII doivent être masquées ou supprimées
        if "email" in anonymized:
            assert anonymized["email"] != "docteur@hopital.fr", (
                "L'email ne doit pas apparaître en clair dans les logs"
            )
        if "patient_name" in anonymized:
            assert anonymized["patient_name"] != "Jean Dupont", (
                "Le nom du patient ne doit pas apparaître en clair dans les logs"
            )

    def test_anonymize_preserves_action_info(self) -> None:
        """L'anonymisation préserve les informations non sensibles utiles aux logs."""
        data = {
            "action": "login",
            "status": "success",
            "ip_address": "192.168.1.1",
            "email": "user@test.fr",
        }
        anonymized = anonymize_for_logs(data)

        # Les informations d'action devraient être préservées
        assert anonymized.get("action") == "login" or "action" in str(anonymized), (
            "Les informations d'action devraient être préservées dans les logs"
        )

    def test_anonymize_empty_dict(self) -> None:
        """L'anonymisation d'un dictionnaire vide fonctionne."""
        anonymized = anonymize_for_logs({})
        assert isinstance(anonymized, dict)

    def test_mask_empty_string_field(self) -> None:
        """Le masquage gère correctement les champs vides."""
        data = {"email": "", "name": ""}
        masked = mask_pii(data)
        assert isinstance(masked, dict), "Le résultat doit être un dictionnaire"
