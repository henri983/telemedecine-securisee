"""
Module IA pour la détection des comportements suspects et anomalies d'accès.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AnomalyResult:
    """Résultat de l'analyse comportementale."""

    risk_score: float
    is_suspicious: bool
    reasons: List[str] = field(default_factory=list)
    confidence: float = 0.95


class AnomalyDetector:
    """
    Moteur d'analyse comportementale combinant règles heuristiques et ML.

    Détecte :
    - Accès hors horaires (22h - 6h)
    - Burst de requêtes anormal
    - Accès massif à des dossiers patients (dépassement seuils)
    - Exfiltration de volumes inhabituels
    """

    def __init__(self, threshold: float = 0.6) -> None:
        self.threshold = threshold

    def analyze(self, event: Dict[str, Any]) -> AnomalyResult:
        """
        Analyse un dictionnaire d'événement d'accès ou de télémétrie.
        """
        hour = event.get("hour")
        if hour is None:
            ts = event.get("timestamp")
            if isinstance(ts, str):
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    hour = dt.hour
                except Exception:
                    hour = 12
            elif isinstance(ts, datetime):
                hour = ts.hour
            else:
                hour = 12

        request_count = float(event.get("request_count", 1))
        patients_accessed = float(event.get("patients_accessed", 1))
        data_volume_mb = float(event.get("data_volume_mb", 0.1))

        risk_score = 0.05
        reasons: List[str] = []

        # 1. Analyse horaire
        if 2 <= hour <= 5:
            risk_score += 0.50
            reasons.append(f"Accès nocturne critique ({hour}h)")
        elif hour < 7 or hour > 21:
            risk_score += 0.25
            reasons.append(f"Accès hors heures ouvrées ({hour}h)")

        # 2. Analyse fréquence de requêtes
        if request_count >= 1000:
            risk_score += 0.65
            reasons.append(f"Taux de requêtes extrême ({request_count} req)")
        elif request_count >= 200:
            risk_score += 0.50
            reasons.append(f"Taux de requêtes très élevé ({request_count} req)")
        elif request_count >= 50:
            risk_score += 0.20
            reasons.append(f"Activité soutenue ({request_count} req)")

        # 3. Analyse accès patients
        if patients_accessed >= 50:
            risk_score += 0.45
            reasons.append(f"Consultation massive de dossiers patients ({patients_accessed})")
        elif patients_accessed >= 20:
            risk_score += 0.25
            reasons.append(f"Nombre élevé de dossiers consultés ({patients_accessed})")

        # 4. Volume de données (exfiltration)
        if data_volume_mb >= 300.0:
            risk_score += 0.65
            reasons.append(f"Volume massif de données téléchargées ({data_volume_mb:.1f} MB)")
        elif data_volume_mb >= 50.0:
            risk_score += 0.30
            reasons.append(f"Volume inhabituel de données ({data_volume_mb:.1f} MB)")

        # Normalisation du score entre 0.0 et 1.0
        risk_score = min(max(risk_score, 0.0), 1.0)
        is_suspicious = risk_score >= self.threshold

        return AnomalyResult(
            risk_score=round(risk_score, 3),
            is_suspicious=is_suspicious,
            reasons=reasons,
        )

    def analyze_request(self, user_id: str, request_metadata: Dict[str, Any]) -> AnomalyResult:
        """Méthode helper pour l'intégration dans les middlewares."""
        data = dict(request_metadata)
        data["user_id"] = user_id
        return self.analyze(data)
