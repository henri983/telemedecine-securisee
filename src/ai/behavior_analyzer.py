"""
Analyseur de sessions et agrégateur d'événements de sécurité.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from src.ai.anomaly_detector import AnomalyDetector, AnomalyResult


@dataclass
class Alert:
    """Structure d'alerte de sécurité."""

    user_id: str
    risk_score: float
    reasons: List[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class BehaviorReport:
    """Rapport d'analyse comportementale d'une session."""

    user_id: str
    total_requests: int
    unique_patients_accessed: int
    total_volume_mb: float
    max_risk_score: float
    is_flagged: bool
    alerts: List[str] = field(default_factory=list)


class BehaviorAnalyzer:
    """Analyse les sessions et détecte les tentatives d'exfiltration de données."""

    def __init__(self, detector: Optional[AnomalyDetector] = None) -> None:
        self.detector = detector or AnomalyDetector()

    def analyze_session(self, user_id: str, events: List[Dict[str, Any]]) -> BehaviorReport:
        """Évalue une suite d'actions au sein d'une même session utilisateur."""
        total_requests = len(events)
        patients_seen = set()
        total_volume = 0.0

        for ev in events:
            if "patient_id" in ev:
                patients_seen.add(ev["patient_id"])
            total_volume += float(ev.get("data_volume_mb", 0.05))

        max_risk = 0.0
        alerts = []
        for ev in events:
            res = self.detector.analyze(ev)
            if res.risk_score > max_risk:
                max_risk = res.risk_score
            if res.is_suspicious:
                alerts.extend(res.reasons)

        return BehaviorReport(
            user_id=user_id,
            total_requests=total_requests,
            unique_patients_accessed=len(patients_seen),
            total_volume_mb=total_volume,
            max_risk_score=max_risk,
            is_flagged=max_risk >= self.detector.threshold,
            alerts=list(set(alerts)),
        )

    def generate_alert(self, anomaly_result: AnomalyResult, user_id: str) -> Alert:
        """Génère une alerte formelle à partir d'une anomalie."""
        return Alert(
            user_id=user_id,
            risk_score=anomaly_result.risk_score,
            reasons=anomaly_result.reasons,
        )
