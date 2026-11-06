# Architecture

The backend is a modular FastAPI application using SQLAlchemy for persistence and Joblib for local model artifacts. The frontend is a Vite React application. API calls flow through `/api`, while Vite proxies development traffic to FastAPI on port 8000.

## Backend responsibilities

- `app/services/data_service.py`: synthetic profiles, validation, upload labels.
- `app/services/pipeline.py`: imputation, encoding, scaling, artifact persistence.
- `app/federated/engine.py`: local models and FedAvg.
- `app/main.py`: API orchestration and in-memory research state.
- `app/database`: SQLAlchemy models and SQLite initialization.

## Data boundary

The app partitions a pandas frame into NumPy local arrays and does not write individual client datasets. This is a simulation; it does not implement remote machines, authenticated channels, secure transport, or secure aggregation.

## Restart behavior

Experiments, rounds, client state, detections, and settings are stored in SQLite. Current trained model state is held in memory and reload behavior should be restored by retraining after restarting or by loading the saved Joblib artifacts through a future service enhancement.
