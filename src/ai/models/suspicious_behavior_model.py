"""
Modèle scikit-learn IsolationForest pour la détection non-supervisée d'anomalies.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np


class SuspiciousBehaviorModel:
    """Modèle Machine Learning basé sur Isolation Forest."""

    def __init__(self) -> None:
        self.model = None
        self.is_trained = False

    def train(self, features: np.ndarray) -> None:
        """Entraîne le modèle sur des vecteurs de features."""
        from sklearn.ensemble import IsolationForest

        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
        )
        self.model.fit(features)
        self.is_trained = True

    def predict_anomaly_score(self, feature_vector: np.ndarray) -> float:
        """Retourne un score d'anomalie normalisé entre 0 et 1."""
        if not self.is_trained or self.model is None:
            # Fallback heuristique si pas entraîné
            return 0.1
        # IsolationForest decision_function : plus bas = plus anormal
        score = self.model.decision_function(feature_vector.reshape(1, -1))[0]
        # Mapper vers [0, 1] où 1 = très suspect
        risk = 1.0 / (1.0 + np.exp(score * 3.0))
        return float(np.clip(risk, 0.0, 1.0))
