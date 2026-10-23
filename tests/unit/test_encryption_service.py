"""
Tests unitaires pour le service de chiffrement AES-256-GCM.

Vérifie le chiffrement/déchiffrement, la résistance aux altérations,
et le support des différents types de données.
"""

import os
import pytest

from src.security.crypto import EncryptionService


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

# Clé de test valide (32 bytes = 64 caractères hex)
TEST_KEY_HEX = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
ALT_KEY_HEX = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"


@pytest.fixture
def crypto() -> EncryptionService:
    """Service de chiffrement avec clé de test."""
    return EncryptionService(key_hex=TEST_KEY_HEX)


@pytest.fixture
def crypto_alt() -> EncryptionService:
    """Service de chiffrement avec une clé alternative."""
    return EncryptionService(key_hex=ALT_KEY_HEX)


class TestEncryptDecryptRoundtrip:
    """Tests de chiffrement/déchiffrement aller-retour."""

    def test_encrypt_decrypt_roundtrip(self, crypto: EncryptionService) -> None:
        """Chiffrer puis déchiffrer retourne les données originales."""
        plaintext = "Données médicales confidentielles du patient"
        ciphertext = crypto.encrypt(plaintext)
        decrypted = crypto.decrypt(ciphertext)
        assert decrypted == plaintext, (
            f"Le texte déchiffré '{decrypted}' ne correspond pas "
            f"au texte original '{plaintext}'"
        )

    def test_encrypt_decrypt_roundtrip_bytes(self, crypto: EncryptionService) -> None:
        """Le roundtrip fonctionne aussi avec des données binaires si supporté."""
        plaintext = "Résultat d'analyse sanguine: Hb=14.2 g/dL"
        ciphertext = crypto.encrypt(plaintext)
        decrypted = crypto.decrypt(ciphertext)
        assert decrypted == plaintext


class TestNonceRandomness:
    """Tests de l'unicité des chiffrements (nonce aléatoire)."""

    def test_encrypt_produces_different_ciphertexts(
        self, crypto: EncryptionService
    ) -> None:
        """Deux chiffrements du même texte donnent des résultats différents."""
        plaintext = "Même donnée chiffrée deux fois"
        ciphertext1 = crypto.encrypt(plaintext)
        ciphertext2 = crypto.encrypt(plaintext)
        assert ciphertext1 != ciphertext2, (
            "Deux chiffrements du même texte ont produit le même résultat. "
            "Le nonce doit être aléatoire pour garantir la sécurité."
        )

    def test_multiple_encryptions_all_unique(
        self, crypto: EncryptionService
    ) -> None:
        """Dix chiffrements du même texte sont tous uniques."""
        plaintext = "Donnée répétée"
        ciphertexts = {crypto.encrypt(plaintext) for _ in range(10)}
        assert len(ciphertexts) == 10, (
            "Certains chiffrements sont identiques — nonce potentiellement réutilisé"
        )


class TestDecryptionFailures:
    """Tests d'échec de déchiffrement."""

    def test_decrypt_with_wrong_key_fails(
        self, crypto: EncryptionService, crypto_alt: EncryptionService
    ) -> None:
        """Le déchiffrement avec une mauvaise clé doit échouer."""
        plaintext = "Données sensibles"
        ciphertext = crypto.encrypt(plaintext)
        with pytest.raises(Exception) as exc_info:
            crypto_alt.decrypt(ciphertext)
        # On vérifie qu'une exception est bien levée
        assert exc_info.value is not None, (
            "Le déchiffrement avec une mauvaise clé aurait dû échouer"
        )

    def test_decrypt_tampered_ciphertext_fails(
        self, crypto: EncryptionService
    ) -> None:
        """Le déchiffrement de données altérées doit échouer (intégrité GCM)."""
        plaintext = "Données intègres"
        ciphertext = crypto.encrypt(plaintext)

        # Altérer le ciphertext (modifier un octet au milieu)
        ciphertext_bytes = bytearray(
            ciphertext.encode("latin-1")
            if isinstance(ciphertext, str)
            else ciphertext
        )
        # Tenter de modifier quelques bytes du ciphertext
        if len(ciphertext_bytes) > 20:
            ciphertext_bytes[20] ^= 0xFF
        else:
            ciphertext_bytes[-1] ^= 0xFF

        tampered = bytes(ciphertext_bytes)
        # Convertir en même type que l'entrée
        if isinstance(ciphertext, str):
            tampered_str = tampered.decode("latin-1")
        else:
            tampered_str = tampered

        with pytest.raises(Exception) as exc_info:
            crypto.decrypt(tampered_str)
        assert exc_info.value is not None, (
            "Le déchiffrement de données altérées aurait dû échouer "
            "(vérification d'intégrité GCM)"
        )

    def test_decrypt_invalid_data_fails(self, crypto: EncryptionService) -> None:
        """Le déchiffrement de données invalides doit échouer proprement."""
        with pytest.raises(Exception):
            crypto.decrypt("ceci-nest-pas-un-ciphertext-valide")


class TestEdgeCases:
    """Tests des cas limites."""

    def test_encrypt_empty_string(self, crypto: EncryptionService) -> None:
        """Le chiffrement d'une chaîne vide fonctionne correctement."""
        ciphertext = crypto.encrypt("")
        decrypted = crypto.decrypt(ciphertext)
        assert decrypted == "", (
            "Le chiffrement/déchiffrement d'une chaîne vide a échoué"
        )

    def test_encrypt_unicode(self, crypto: EncryptionService) -> None:
        """Le chiffrement de caractères unicode/accents fonctionne."""
        plaintext = "Prénom: Éloïse, Adresse: 42 Rue François-Müller, Côte d'Azur 🏥"
        ciphertext = crypto.encrypt(plaintext)
        decrypted = crypto.decrypt(ciphertext)
        assert decrypted == plaintext, (
            "Le chiffrement/déchiffrement de texte unicode a échoué"
        )

    def test_encrypt_special_characters(self, crypto: EncryptionService) -> None:
        """Le chiffrement de caractères spéciaux fonctionne."""
        plaintext = "N° Sécu: 1 85 03 12 345 678 90\nGroupe: O+\tRh: positif"
        ciphertext = crypto.encrypt(plaintext)
        decrypted = crypto.decrypt(ciphertext)
        assert decrypted == plaintext

    def test_encrypt_large_data(self, crypto: EncryptionService) -> None:
        """Le chiffrement de données volumineuses fonctionne (ex: rapport médical)."""
        # Simuler un rapport médical de ~100KB
        plaintext = "Rapport médical détaillé. " * 5000
        assert len(plaintext) > 100_000, "Le texte de test doit faire > 100KB"

        ciphertext = crypto.encrypt(plaintext)
        decrypted = crypto.decrypt(ciphertext)
        assert decrypted == plaintext, (
            "Le chiffrement/déchiffrement de données volumineuses a échoué"
        )
        assert len(ciphertext) >= len(plaintext), (
            "Le ciphertext devrait être au moins aussi long que le plaintext "
            "(avec nonce + tag)"
        )

    def test_encrypt_json_data(self, crypto: EncryptionService) -> None:
        """Le chiffrement de données JSON fonctionne."""
        import json
        data = json.dumps({
            "diagnostic": "Hypertension artérielle",
            "traitement": "Amlodipine 5mg",
            "notes": "Contrôle dans 3 mois",
        })
        ciphertext = crypto.encrypt(data)
        decrypted = crypto.decrypt(ciphertext)
        assert json.loads(decrypted) == json.loads(data)
