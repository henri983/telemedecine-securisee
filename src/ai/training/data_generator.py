"""
Générateur de données synthétiques pour l'entraînement et le benchmark de l'IA.
"""

import numpy as np


def generate_synthetic_dataset(n_normal: int = 1000, n_anomalies: int = 50) -> np.ndarray:
    """
    Génère un dataset simulé de comportements télémédecine.
    Features : [hour (0-23), request_count, patients_accessed, data_volume_mb]
    """
    np.random.seed(42)

    # Comportement normal : heures de bureau (8-19h), peu de requêtes, peu de patients
    normal_hours = np.random.normal(13, 3, n_normal).clip(8, 19)
    normal_reqs = np.random.exponential(5, n_normal) + 1
    normal_patients = np.random.exponential(2, n_normal) + 1
    normal_volume = np.random.exponential(0.5, n_normal) + 0.1
    normal_data = np.column_stack([normal_hours, normal_reqs, normal_patients, normal_volume])

    # Anomalies : nuit (1-5h), burst requêtes, exfiltration, scan de patients
    anom_hours = np.random.choice([2, 3, 4], n_anomalies)
    anom_reqs = np.random.uniform(150, 800, n_anomalies)
    anom_patients = np.random.uniform(40, 150, n_anomalies)
    anom_volume = np.random.uniform(50, 400, n_anomalies)
    anom_data = np.column_stack([anom_hours, anom_reqs, anom_patients, anom_volume])

    return np.vstack([normal_data, anom_data])
