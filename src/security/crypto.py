"""
Service de chiffrement AES-256-GCM.

Fournit le chiffrement et le déchiffrement des données médicales sensibles
en utilisant AES-256-GCM (Galois/Counter Mode) via la bibliothèque cryptography.

Format du ciphertext: nonce (12 bytes) || ciphertext || tag (16 bytes)
"""

import os
from typing import Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionService:
    """
    Service de chiffrement/déchiffrement AES-256-GCM.

    Utilise AES-256-GCM qui offre à la fois confidentialité et
    authenticité des données (AEAD).
    """

    NONCE_SIZE: int = 12

    def __init__(self, key: Union[bytes, str, None] = None, key_hex: Union[str, None] = None) -> None:
        """
        Initialise le service de chiffrement.

        Args:
            key: Clé AES-256 de 32 bytes ou chaîne hex de 64 caractères.
            key_hex: Clé au format hexadécimal (64 caractères).
        """
        raw_key: bytes
        if key_hex is not None:
            raw_key = bytes.fromhex(key_hex)
        elif isinstance(key, str):
            if len(key) == 64:
                try:
                    raw_key = bytes.fromhex(key)
                except ValueError:
                    raw_key = key.encode("utf-8")[:32]
            else:
                raw_key = key.encode("utf-8")
        elif isinstance(key, bytes):
            raw_key = key
        else:
            raise ValueError("Une clé valide (bytes ou hex) doit être fournie.")

        if len(raw_key) != 32:
            raise ValueError(
                f"La clé AES-256 doit faire exactement 32 bytes (256 bits), reçu {len(raw_key)} bytes."
            )

        self._aesgcm = AESGCM(raw_key)
        self._key = raw_key

    def encrypt(self, plaintext: str) -> bytes:
        """Chiffre un texte en clair avec AES-256-GCM."""
        if plaintext is None:
            raise ValueError("Le texte en clair ne peut pas être None.")

        nonce: bytes = os.urandom(self.NONCE_SIZE)
        ciphertext_with_tag: bytes = self._aesgcm.encrypt(
            nonce=nonce,
            data=plaintext.encode("utf-8"),
            associated_data=None,
        )
        return nonce + ciphertext_with_tag

    def decrypt(self, ciphertext: bytes) -> str:
        """Déchiffre des données chiffrées en AES-256-GCM."""
        if ciphertext is None or len(ciphertext) < self.NONCE_SIZE + 16:
            raise ValueError(
                "Les données chiffrées sont trop courtes (minimum nonce 12 + tag 16 = 28 bytes)."
            )

        nonce: bytes = ciphertext[: self.NONCE_SIZE]
        encrypted_data: bytes = ciphertext[self.NONCE_SIZE :]

        plaintext_bytes: bytes = self._aesgcm.decrypt(
            nonce=nonce,
            data=encrypted_data,
            associated_data=None,
        )

        return plaintext_bytes.decode("utf-8")
