import numpy as np
import pandas as pd

FEATURES = ["duration", "src_bytes", "dst_bytes", "packets", "failed_logins", "srv_count", "same_srv_rate", "dst_host_count", "dst_host_srv_rate", "protocol_type"]
ATTACKS = ["Normal", "DoS", "DDoS", "Brute Force", "Port Scan", "Botnet"]

# Synthetic profile means are deliberately simple and documented as simulated traffic.
PROFILES = {
    "Normal": [20, 700, 900, 18, 0, 8, 0.92, 12, 0.88, 0],
    "DoS": [1, 100, 2200, 800, 0, 120, 0.15, 200, 0.12, 1],
    "DDoS": [0.5, 90, 500, 1400, 0, 180, 0.08, 240, 0.08, 1],
    "Brute Force": [1800, 300, 120, 30, 18, 40, 0.25, 5, 0.2, 0],
    "Port Scan": [3, 80, 60, 60, 2, 200, 0.05, 220, 0.04, 1],
    "Botnet": [900, 220, 300, 300, 1, 90, 0.35, 180, 0.30, 2],
}

def generate_synthetic(rows: int = 6000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    labels = np.resize(np.array(ATTACKS), rows)
    rng.shuffle(labels)
    values = []
    for label in labels:
        base = np.array(PROFILES[str(label)], dtype=float)
        noise = np.array([20, 500, 700, max(base[3] * 0.12, 8), 2, 20, 0.08, 20, 0.08, 0.15])
        row = np.maximum(base + rng.normal(0, noise), 0)
        row[-1] = int(np.clip(np.round(row[-1]), 0, 2))
        values.append(row)
    df = pd.DataFrame(values, columns=FEATURES)
    df["label"] = labels
    # Preserve a tiny amount of missingness to exercise preprocessing.
    mask = rng.random(df.shape) < 0.002
    df.mask(mask, np.nan, inplace=True)
    df.loc[df["label"] == "Normal", "duration"] = df.loc[df["label"] == "Normal", "duration"].clip(upper=500)
    return df

def validate_dataset(df: pd.DataFrame):
    required_numeric = [name for name in FEATURES if name != "protocol_type"]
    errors = []
    for col in required_numeric:
        if col not in df.columns:
            errors.append(f"Missing feature: {col}")
    label_column = next((c for c in ("label", "Label", "attack_cat", "class") if c in df.columns), None)
    if label_column is None:
        errors.append("Missing label column (label, Label, attack_cat, or class)")
    return {"valid": not errors, "errors": errors, "label_column": label_column, "columns": list(df.columns)}
