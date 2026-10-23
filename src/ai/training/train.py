"""
Script d'entraînement du modèle IA de télémédecine.
"""

from pathlib import Path
from src.ai.models.suspicious_behavior_model import SuspiciousBehaviorModel
from src.ai.training.data_generator import generate_synthetic_dataset


def run_training() -> None:
    """Entraîne et valide le modèle d'anomalie."""
    print("Génération du jeu de données synthétique...")
    dataset = generate_synthetic_dataset(1500, 60)

    print("Entraînement de l'IsolationForest...")
    model = SuspiciousBehaviorModel()
    model.train(dataset)

    print("Test d'inférence...")
    normal_sample = dataset[0]
    anomaly_sample = dataset[-1]

    print(f"Score normal : {model.predict_anomaly_score(normal_sample):.4f}")
    print(f"Score anomalie : {model.predict_anomaly_score(anomaly_sample):.4f}")
    print("Modèle entraîné avec succès !")


if __name__ == "__main__":
    run_training()
