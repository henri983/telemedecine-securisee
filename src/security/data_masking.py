"""
Module de masquage et anonymisation des données personnelles.
"""

import re
from copy import deepcopy
from typing import Any, List, Optional, Set


def mask_email(email: str) -> str:
    """Masque une adresse email."""
    if not email or "@" not in email:
        return "***@***.***"

    local_part, domain = email.rsplit("@", 1)
    domain_parts: list[str] = domain.split(".")

    masked_local: str = f"{local_part[0]}***" if local_part else "***"

    if len(domain_parts) >= 2:
        masked_domain: str = f"{domain_parts[0][0]}***.{domain_parts[-1]}"
    else:
        masked_domain = "***"

    return f"{masked_local}@{masked_domain}"


def mask_name(name: str) -> str:
    """Masque un nom."""
    if not name or not name.strip():
        return "***"

    words: list[str] = name.strip().split()
    masked_words: list[str] = []

    for word in words:
        if word:
            masked_words.append(f"{word[0]}***")
        else:
            masked_words.append("***")

    return " ".join(masked_words)


DEFAULT_PII_FIELDS: Set[str] = {
    "email",
    "name",
    "full_name",
    "first_name",
    "last_name",
    "patient_name",
    "phone",
    "telephone",
    "address",
    "adresse",
    "date_of_birth",
    "social_security",
    "ssn",
}


def mask_pii(data: dict[str, Any], fields: Optional[List[str]] = None) -> dict[str, Any]:
    """Masque les champs PII dans un dictionnaire."""
    masked_data: dict[str, Any] = deepcopy(data)
    target_fields = set(fields) if fields is not None else DEFAULT_PII_FIELDS

    for field in target_fields:
        if field not in masked_data:
            continue

        value: Any = masked_data[field]
        if not isinstance(value, str):
            masked_data[field] = "***"
            continue

        if not value:
            masked_data[field] = ""
            continue

        if "@" in value:
            masked_data[field] = mask_email(value)
        elif any(n in field for n in ["name", "nom"]):
            masked_data[field] = mask_name(value)
        else:
            if len(value) > 2:
                masked_data[field] = f"{value[:2]}{'*' * min(len(value) - 2, 8)}"
            else:
                masked_data[field] = "***"

    return masked_data


def anonymize_for_logs(data: dict[str, Any]) -> dict[str, Any]:
    """Anonymise un dictionnaire pour le logging sans PII."""
    sensitive_keywords = {
        "password",
        "hashed",
        "token",
        "secret",
        "key",
        "credit_card",
        "ssn",
        "social_security",
    }

    pii_keywords = {
        "email",
        "name",
        "phone",
        "tel",
        "address",
        "adresse",
        "birth",
        "patient",
    }

    anonymized: dict[str, Any] = deepcopy(data)

    for key in list(anonymized.keys()):
        key_lower: str = key.lower()

        if any(sk in key_lower for sk in sensitive_keywords):
            anonymized[key] = "[REDACTED]"
        elif any(pk in key_lower for pk in pii_keywords):
            value = anonymized[key]
            if isinstance(value, str):
                if "@" in value:
                    anonymized[key] = mask_email(value)
                elif "name" in key_lower:
                    anonymized[key] = mask_name(value)
                else:
                    anonymized[key] = "[PII_MASKED]"
            else:
                anonymized[key] = "[PII_MASKED]"
        elif isinstance(anonymized[key], dict):
            anonymized[key] = anonymize_for_logs(anonymized[key])

    return anonymized
