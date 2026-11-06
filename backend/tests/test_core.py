import numpy as np
from app.services.data_service import generate_synthetic, validate_dataset
from app.services.pipeline import DataPipeline
from app.federated.engine import FederatedEngine

def test_synthetic_dataset_and_validation():
    df = generate_synthetic(600, 7)
    result = validate_dataset(df)
    assert result["valid"]
    assert len(df) == 600
    assert {"Normal", "Botnet"}.issubset(set(df["label"]))

def test_preprocessing_is_numeric():
    df = generate_synthetic(300, 3)
    pipeline = DataPipeline()
    X, y, classes = pipeline.fit(df, "label")
    assert X.shape[0] == len(df)
    assert len(classes) > 1
    assert np.isfinite(X).all()

def test_federated_training_changes_accuracy_and_history():
    df = generate_synthetic(900, 11)
    pipeline = DataPipeline()
    X, y, _ = pipeline.fit(df, "label")
    initial = np.zeros_like(X[0])
    engine = FederatedEngine()
    result = engine.train(X, y, clients=3, rounds=3, epochs=1, adaptive=True)
    assert len(result["rounds"]) == 3
    assert engine.global_model is not None
    assert result["accuracy"] > 0.6

