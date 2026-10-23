"""
Package IA - Détection de comportements suspects.

Exporte les composants d'analyse comportementale et de détection d'anomalies.
"""

from src.ai.anomaly_detector import AnomalyDetector, AnomalyResult
from src.ai.behavior_analyzer import BehaviorAnalyzer, BehaviorReport, Alert

__all__: list[str] = [
    "AnomalyDetector",
    "AnomalyResult",
    "BehaviorAnalyzer",
    "BehaviorReport",
    "Alert",
]
