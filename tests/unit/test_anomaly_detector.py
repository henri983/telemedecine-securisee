"""
Tests unitaires pour le détecteur d'anomalies IA.

Vérifie la détection de comportements suspects: accès nocturnes,
taux de requêtes élevé, accès massif aux dossiers patients,
exfiltration de données.
"""

from datetime import datetime, timezone

import pytest

from src.ai.anomaly_detector import AnomalyDetector, AnomalyResult


pytestmark = [pytest.mark.unit]


@pytest.fixture
def detector() -> AnomalyDetector:
    """Détecteur d'anomalies pour les tests."""
    return AnomalyDetector()


def _make_event(
    hour: int = 10,
    request_count: int = 5,
    patients_accessed: int = 1,
    data_volume_mb: float = 0.5,
    user_role: str = "praticien",
    ip_address: str = "192.168.1.100",
    endpoint: str = "/api/v1/patients",
    method: str = "GET",
) -> dict:
    """Crée un événement de comportement pour le détecteur."""
    return {
        "user_id": "user-test-123",
        "user_role": user_role,
        "timestamp": datetime(2024, 6, 15, hour, 30, 0, tzinfo=timezone.utc).isoformat(),
        "hour": hour,
        "request_count": request_count,
        "patients_accessed": patients_accessed,
        "data_volume_mb": data_volume_mb,
        "ip_address": ip_address,
        "endpoint": endpoint,
        "method": method,
    }


class TestNormalBehavior:
    """Tests de comportement normal (non suspect)."""

    def test_normal_behavior_low_risk(self, detector: AnomalyDetector) -> None:
        """Un comportement normal en heures de bureau => score de risque bas."""
        event = _make_event(
            hour=10,
            request_count=5,
            patients_accessed=1,
            data_volume_mb=0.1,
        )
        result: AnomalyResult = detector.analyze(event)

        assert result.risk_score < 0.5, (
            f"Un comportement normal devrait avoir un score de risque < 0.5, "
            f"obtenu: {result.risk_score}"
        )
        assert result.is_suspicious is False, (
            "Un comportement normal ne devrait pas être marqué comme suspect"
        )

    def test_normal_business_hours(self, detector: AnomalyDetector) -> None:
        """Un accès pendant les heures normales (8h-19h) est considéré normal."""
        for hour in [8, 9, 12, 14, 17, 18]:
            event = _make_event(
                hour=hour,
                request_count=10,
                patients_accessed=3,
            )
            result: AnomalyResult = detector.analyze(event)
            assert result.risk_score < 0.7, (
                f"Un accès à {hour}h en heures de bureau ne devrait pas être "
                f"à haut risque (score: {result.risk_score})"
            )

    def test_low_request_count_normal(self, detector: AnomalyDetector) -> None:
        """Un faible nombre de requêtes est normal."""
        event = _make_event(request_count=3, patients_accessed=1)
        result: AnomalyResult = detector.analyze(event)
        assert result.is_suspicious is False


class TestNightAccess:
    """Tests d'accès nocturne."""

    def test_night_access_high_risk(self, detector: AnomalyDetector) -> None:
        """Un accès de nuit (2h-5h) => score de risque élevé."""
        event = _make_event(hour=3, request_count=15)
        result: AnomalyResult = detector.analyze(event)

        assert result.risk_score > 0.5, (
            f"Un accès à 3h du matin devrait avoir un score de risque élevé, "
            f"obtenu: {result.risk_score}"
        )

    def test_late_night_access_suspicious(self, detector: AnomalyDetector) -> None:
        """Un accès à 2h du matin avec beaucoup de requêtes est suspect."""
        event = _make_event(
            hour=2,
            request_count=50,
            patients_accessed=10,
        )
        result: AnomalyResult = detector.analyze(event)
        assert result.is_suspicious is True, (
            "Un accès massif à 2h du matin devrait être suspect"
        )

    def test_early_morning_access(self, detector: AnomalyDetector) -> None:
        """Un accès à 4h du matin est anormal."""
        event = _make_event(hour=4, request_count=20)
        result: AnomalyResult = detector.analyze(event)
        assert result.risk_score > 0.4, (
            "Un accès à 4h devrait augmenter le score de risque"
        )


class TestHighRequestRate:
    """Tests de taux de requêtes élevé."""

    def test_high_request_rate_suspicious(self, detector: AnomalyDetector) -> None:
        """Un taux de requêtes très élevé est suspect."""
        event = _make_event(
            request_count=200,
            patients_accessed=5,
        )
        result: AnomalyResult = detector.analyze(event)

        assert result.risk_score > 0.5, (
            f"200 requêtes devraient être suspectes, "
            f"score obtenu: {result.risk_score}"
        )

    def test_extreme_request_rate(self, detector: AnomalyDetector) -> None:
        """Un taux de requêtes extrême est hautement suspect."""
        event = _make_event(request_count=1000)
        result: AnomalyResult = detector.analyze(event)
        assert result.is_suspicious is True, (
            "1000 requêtes devraient déclencher une alerte"
        )


class TestMassPatientAccess:
    """Tests d'accès massif aux dossiers patients."""

    def test_mass_patient_access_suspicious(self, detector: AnomalyDetector) -> None:
        """L'accès à trop de patients différents est suspect."""
        event = _make_event(
            patients_accessed=50,
            request_count=60,
        )
        result: AnomalyResult = detector.analyze(event)

        assert result.risk_score > 0.5, (
            f"L'accès à 50 patients devrait être suspect, "
            f"score obtenu: {result.risk_score}"
        )

    def test_moderate_patient_access_ok(self, detector: AnomalyDetector) -> None:
        """L'accès à quelques patients est normal pour un praticien."""
        event = _make_event(patients_accessed=5, request_count=15)
        result: AnomalyResult = detector.analyze(event)
        assert result.risk_score < 0.7, (
            "Accéder à 5 patients est normal pour un praticien"
        )


class TestDataExfiltration:
    """Tests de détection d'exfiltration de données."""

    def test_data_exfiltration_detected(self, detector: AnomalyDetector) -> None:
        """Un téléchargement massif de données est détecté."""
        event = _make_event(
            data_volume_mb=500.0,
            request_count=100,
            patients_accessed=50,
        )
        result: AnomalyResult = detector.analyze(event)

        assert result.is_suspicious is True, (
            "Un téléchargement de 500MB devrait être détecté comme exfiltration"
        )
        assert result.risk_score > 0.7, (
            f"L'exfiltration devrait avoir un score élevé, "
            f"obtenu: {result.risk_score}"
        )

    def test_small_download_normal(self, detector: AnomalyDetector) -> None:
        """Un petit téléchargement est normal."""
        event = _make_event(data_volume_mb=1.0, patients_accessed=1)
        result: AnomalyResult = detector.analyze(event)
        assert result.risk_score < 0.6, (
            "Un téléchargement de 1MB est normal"
        )


class TestCombinedBehaviors:
    """Tests de comportements suspects combinés."""

    def test_combined_suspicious_behavior(self, detector: AnomalyDetector) -> None:
        """Plusieurs facteurs suspects combinés augmentent le score."""
        event = _make_event(
            hour=3,                  # Nuit
            request_count=300,       # Taux élevé
            patients_accessed=100,   # Accès massif
            data_volume_mb=200.0,    # Gros volume
        )
        result: AnomalyResult = detector.analyze(event)

        assert result.is_suspicious is True, (
            "Plusieurs comportements suspects combinés doivent être détectés"
        )
        assert result.risk_score > 0.8, (
            f"Le score combiné devrait être très élevé, "
            f"obtenu: {result.risk_score}"
        )

    def test_single_factor_less_risky_than_combined(
        self, detector: AnomalyDetector
    ) -> None:
        """Un seul facteur de risque donne un score inférieur à plusieurs combinés."""
        single_event = _make_event(hour=3, request_count=5, patients_accessed=1)
        combined_event = _make_event(
            hour=3, request_count=200, patients_accessed=50, data_volume_mb=100
        )

        single_result = detector.analyze(single_event)
        combined_result = detector.analyze(combined_event)

        assert combined_result.risk_score > single_result.risk_score, (
            "Plusieurs facteurs combinés devraient donner un score plus élevé"
        )


class TestAnomalyResultStructure:
    """Tests de la structure du résultat d'analyse."""

    def test_result_has_required_fields(self, detector: AnomalyDetector) -> None:
        """Le résultat contient tous les champs requis."""
        event = _make_event()
        result: AnomalyResult = detector.analyze(event)

        assert hasattr(result, "risk_score"), "Le résultat doit avoir un risk_score"
        assert hasattr(result, "is_suspicious"), "Le résultat doit avoir is_suspicious"
        assert isinstance(result.risk_score, (int, float)), (
            "risk_score doit être un nombre"
        )
        assert isinstance(result.is_suspicious, bool), (
            "is_suspicious doit être un booléen"
        )

    def test_risk_score_in_valid_range(self, detector: AnomalyDetector) -> None:
        """Le score de risque est entre 0 et 1."""
        events = [
            _make_event(hour=10, request_count=1),
            _make_event(hour=3, request_count=1000, data_volume_mb=500),
        ]
        for event in events:
            result = detector.analyze(event)
            assert 0.0 <= result.risk_score <= 1.0, (
                f"Le score de risque doit être entre 0 et 1, "
                f"obtenu: {result.risk_score}"
            )
