from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.database.db import Base

class Experiment(Base):
    __tablename__ = "experiments"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    status = Column(String(40), default="completed")
    config_json = Column(Text, default="{}")
    metrics_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

class TrainingRound(Base):
    __tablename__ = "training_rounds"
    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, nullable=False)
    round_number = Column(Integer, nullable=False)
    accuracy = Column(Float)
    loss = Column(Float)
    participating_clients = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class ClientState(Base):
    __tablename__ = "client_states"
    id = Column(String(64), primary_key=True)
    status = Column(String(40), default="idle")
    record_count = Column(Integer, default=0)
    local_accuracy = Column(Float)
    last_training_at = Column(DateTime)

class Detection(Base):
    __tablename__ = "detections"
    id = Column(Integer, primary_key=True)
    predicted_label = Column(String(100), nullable=False)
    anomaly_score = Column(Float, nullable=False)
    is_suspicious = Column(Integer, default=0)
    details_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
