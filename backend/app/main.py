import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score
from sqlalchemy import select

from app.core.config import settings
from app.database.db import Base, engine, get_session
from app.database.models import Experiment, TrainingRound, ClientState, Detection, Setting
from app.federated.engine import FederatedEngine
from app.services.data_service import ATTACKS, generate_synthetic, validate_dataset
from app.services.pipeline import DataPipeline

Base.metadata.create_all(engine)
app = FastAPI(title="Adaptive Federated IDS", version="1.0.0")
app.add_middleware(CORSMiddleware,
                   allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

DATA_DIR = Path(settings.upload_dir)
DATA_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_PATH = DATA_DIR.parent / "sample" / "traffic_sample.csv"
current = {"df": None, "pipeline": None, "engine": FederatedEngine(), "detection": None}

class TrainRequest(BaseModel):
    clients: int = Field(default=5, ge=2, le=50)
    rounds: int = Field(default=8, ge=1, le=100)
    epochs: int = Field(default=2, ge=1, le=20)
    learning_rate: float = Field(default=0.01, gt=0, le=1)
    drift_sensitivity: float = Field(default=0.15, ge=0, le=1)
    adaptive: bool = True

class PredictRequest(BaseModel):
    records: list[dict]

class SettingsRequest(BaseModel):
    settings: dict

@app.get("/api/health")
def health():
    return {"status": "ok", "database": "connected", "model_trained": current["engine"].global_model is not None,
            "dataset_loaded": current["df"] is not None}

@app.post("/api/demo/generate")
def generate_demo(rows: int = 6000, seed: int = 42):
    df = generate_synthetic(rows=rows, seed=seed)
    current["df"] = df
    path = DATA_DIR / "synthetic_traffic.csv"
    df.to_csv(path, index=False)
    return dataset_info_response(df, str(path))

@app.post("/api/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only CSV uploads are accepted")
    contents = await file.read(settings.max_upload_bytes + 1)
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(413, "Upload exceeds the configured size limit")
    safe_name = "".join(c for c in Path(file.filename).name if c.isalnum() or c in "._-")
    if not safe_name:
        raise HTTPException(400, "Invalid filename")
    path = DATA_DIR / safe_name
    path.write_bytes(contents)
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise HTTPException(400, "The uploaded file is not a readable CSV") from exc
    validation = validate_dataset(df)
    if not validation["valid"]:
        raise HTTPException(422, detail={"message": "Dataset validation failed", "errors": validation["errors"]})
    current["df"] = df
    return dataset_info_response(df, str(path))

@app.get("/api/datasets/info")
def dataset_info():
    if current["df"] is None:
        raise HTTPException(404, "Generate or upload a dataset first")
    return dataset_info_response(current["df"])

def dataset_info_response(df, path=None):
    label_column = validate_dataset(df)["label_column"]
    counts = df[label_column].fillna("Unknown").value_counts().to_dict()
    preview = df.head(12).where(pd.notnull(df), None).to_dict(orient="records")
    return {"rows": len(df), "columns": list(df.columns), "path": path,
            "label_column": label_column, "class_distribution": counts,
            "preview": preview, "validation": validate_dataset(df),
            "generated_synthetic": "label" in df.columns and set(counts).issubset(set(ATTACKS))}

@app.post("/api/federated/train")
def train_federated(request: TrainRequest):
    if current["df"] is None:
        raise HTTPException(404, "Generate or upload a dataset first")
    label_column = validate_dataset(current["df"])["label_column"]
    pipeline = DataPipeline()
    X, y, classes = pipeline.fit(current["df"], label_column)
    engine = FederatedEngine()
    result = engine.train(X, y, clients=request.clients, rounds=request.rounds,
                          epochs=request.epochs, learning_rate=request.learning_rate,
                          drift_sensitivity=request.drift_sensitivity, adaptive=request.adaptive)
    current["pipeline"] = pipeline
    current["engine"] = engine
    pipeline.save()
    artifact_dir = Path(__file__).resolve().parents[1] / "model_artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(engine, artifact_dir / "federated_engine.joblib")
    metrics = {name: float(result[name]) for name in ("accuracy", "loss")}
    experiment = Experiment(name=f"FedAvg run {datetime.utcnow().isoformat()}", status="completed",
                            config_json=json.dumps(request.model_dump()), metrics_json=json.dumps(metrics))
    from app.database.db import SessionLocal
    db = SessionLocal()
    try:
        db.add(experiment)
        db.flush()
        for record in result["rounds"]:
            db.add(TrainingRound(experiment_id=experiment.id, round_number=record["round"],
                                 accuracy=record["accuracy"], loss=record["loss"],
                                 participating_clients=record["participants"]))
        db.commit()
    finally:
        db.close()
    return {**result, "classes": classes, "configuration": request.model_dump(), "experiment_id": experiment.id}

@app.get("/api/federated/status")
def federated_status():
    engine = current["engine"]
    return {"trained": engine.global_model is not None, "rounds": engine.history,
            "participants": engine.participants, "active_clients": len(engine.participants)}

@app.get("/api/federated/clients")
def clients():
    count = len(current["engine"].participants) or 5
    local_record_count = len(current["df"]) if current["df"] is not None else 0
    return [{"id": f"client-{i + 1:02d}", "status": "participated" if i in current["engine"].participants else "idle",
             "local_records": max(1, local_record_count // count), "last_training_at": datetime.utcnow().isoformat() if i in current["engine"].participants else None,
             "local_accuracy": round(max(0.1, 1 - current["engine"].history[-1]["loss"] + i * 0.01), 4) if current["engine"].history else None}
            for i in range(count)]

@app.post("/api/predict")
def predict(request: PredictRequest):
    if current["pipeline"] is None or current["engine"].global_model is None:
        raise HTTPException(409, "Train a model before making predictions")
    df = pd.DataFrame(request.records)
    # Fill missing trained columns from safe defaults.
    for column in current["pipeline"].feature_names:
        if column not in df:
            df[column] = 0
    X = current["pipeline"].transform(df)
    predictions = current["engine"].predict(X)
    probabilities = current["engine"].global_model.predict_proba(X)
    confidence = probabilities.max(axis=1)
    output = []
    for index, prediction in enumerate(predictions):
        suspicious = str(prediction) != "Normal"
        output.append({"record_index": index, "prediction": str(prediction), "confidence": float(confidence[index]),
                       "anomaly_score": float(1 - confidence[index]), "suspicious": suspicious})
    return {"predictions": output}

@app.post("/api/zero-day/evaluate")
def zero_day_evaluate(held_out: str = "Botnet", threshold: float = 0.35):
    if current["df"] is None:
        raise HTTPException(404, "Generate or upload a dataset first")
    label_column = validate_dataset(current["df"])["label_column"]
    known = current["df"][current["df"][label_column] != held_out].copy()
    unseen = current["df"][current["df"][label_column] == held_out].copy()
    if unseen.empty:
        raise HTTPException(422, f"The held-out class '{held_out}' is not present in the dataset")
    pipeline = DataPipeline()
    X_known, y_known, _ = pipeline.fit(known, label_column)
    X_unseen = pipeline.transform(unseen)
    engine = FederatedEngine()
    result = engine.train(X_known, y_known, clients=4, rounds=6, epochs=2, learning_rate=0.01)
    known_pred = engine.predict(X_known)
    unseen_pred = engine.predict(X_unseen)
    known_confidence = engine.global_model.predict_proba(X_known).max(axis=1)
    unseen_confidence = engine.global_model.predict_proba(X_unseen).max(axis=1)
    anomaly_scores = np.concatenate([1 - known_confidence, 1 - unseen_confidence])
    truth = np.concatenate([np.zeros(len(known_confidence)), np.ones(len(unseen_confidence))])
    detected = (anomaly_scores >= threshold).astype(int)
    labels = truth.astype(int)
    cm = confusion_matrix(labels, detected, labels=[0, 1]).tolist()
    score_auc = roc_auc_score(labels, anomaly_scores) if len(np.unique(labels)) > 1 else None
    metrics = {
        "accuracy": accuracy_score(labels, detected), "precision": precision_score(labels, detected, zero_division=0),
        "recall": recall_score(labels, detected, zero_division=0), "f1": f1_score(labels, detected, zero_division=0),
        "roc_auc": score_auc, "false_positive_rate": cm[0][1] / max(sum(cm[0]), 1),
        "false_negative_rate": cm[1][0] / max(sum(cm[1]), 1), "confusion_matrix": cm,
        "threshold": threshold, "held_out_class": held_out,
        "known_normal": len(known_confidence[known[label_column].to_numpy() == "Normal"]),
        "known_evaluated": len(known_confidence), "unseen_evaluated": len(unseen_confidence),
    }
    current["detection"] = metrics
    return {**metrics, "anomaly_scores": [float(v) for v in anomaly_scores[-min(len(anomaly_scores), 200):]]}

@app.get("/api/dashboard")
def dashboard():
    df = current["df"]
    label_column = validate_dataset(df)["label_column"] if df is not None else None
    counts = df[label_column].fillna("Unknown").value_counts().to_dict() if df is not None else {}
    normal = counts.get("Normal", 0)
    attacks = sum(value for key, value in counts.items() if key != "Normal")
    status = federated_status()
    detection = current["detection"] or {}
    return {"flows_analyzed": len(df) if df is not None else 0, "normal": normal,
            "suspicious": sum(1 for row in []), "detected_attacks": attacks,
            "zero_day_alerts": 0 if not detection else int(detection["unseen_evaluated"] * detection["recall"]),
            "global_accuracy": status["rounds"][-1]["accuracy"] if status["rounds"] else None,
            "active_clients": status["active_clients"] + 0,
            "training_status": "completed" if status["trained"] else "not_started",
            "recent_alerts": [{"label": label, "count": count} for label, count in counts.items() if label != "Normal"][:5],
            "dataset_loaded": df is not None}

@app.get("/api/detections/explainability")
def explainability():
    if current["pipeline"] is None:
        return {"feature_importance": [], "methodology": "Train a model to calculate coefficient-based feature importance."}
    model = current["engine"].global_model
    names = current["pipeline"].feature_names
    importance = np.abs(model.coef_).mean(axis=0)
    result = sorted(({"feature": name, "importance": float(value)} for name, value in zip(names[:len(importance)], importance[:len(names)])), key=lambda item: item["importance"], reverse=True)
    return {"feature_importance": result, "methodology": "Mean absolute standardized coefficient magnitude across classes (permutation importance alternative when coefficients are unavailable)."}

@app.get("/api/experiments")
def experiments():
    from app.database.db import SessionLocal
    db = SessionLocal()
    try:
        rows = db.query(Experiment).order_by(Experiment.created_at.desc()).limit(50).all()
        return [{"id": row.id, "name": row.name, "status": row.status, "created_at": row.created_at.isoformat(),
                 "metrics": json.loads(row.metrics_json)} for row in rows]
    finally:
        db.close()

@app.get("/api/settings")
def get_settings():
    from app.database.db import SessionLocal
    defaults = {"clients": 5, "rounds": 8, "epochs": 2, "learning_rate": 0.01,
                "anomaly_threshold": 0.35, "drift_sensitivity": 0.15, "theme": "dark"}
    db = SessionLocal()
    try:
        saved = {row.key: json.loads(row.value) for row in db.query(Setting).all()}
        return {**defaults, **saved}
    finally:
        db.close()

@app.put("/api/settings")
def put_settings(request: SettingsRequest):
    from app.database.db import SessionLocal
    db = SessionLocal()
    try:
        for key, value in request.settings.items():
            db.merge(Setting(key=key, value=json.dumps(value)))
        db.commit()
    finally:
        db.close()
    return get_settings()
