import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from app.services.data_service import FEATURES
from app.services.data_service import validate_dataset

MODEL_DIR = Path(__file__).resolve().parents[2] / "model_artifacts"
MODEL_DIR.mkdir(exist_ok=True)

class DataPipeline:
    def fit(self, df: pd.DataFrame, label_column="label"):
        validation = validate_dataset(df)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))
        available = [c for c in FEATURES if c in df.columns]
        numeric = [c for c in available if c != "protocol_type"]
        categorical = ["protocol_type"] if "protocol_type" in available else []
        transformers = []
        if numeric:
            transformers.append(("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric))
        if categorical:
            transformers.append(("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), categorical))
        self.preprocessor = ColumnTransformer(transformers)
        X = self.preprocessor.fit_transform(df[available])
        y = df[label_column].astype(str).fillna("Unknown").to_numpy()
        classes = sorted(np.unique(y).tolist())
        self.feature_names = available
        return X, y, classes

    def transform(self, df: pd.DataFrame):
        available = [c for c in self.feature_names if c in df.columns]
        if available != self.feature_names:
            raise ValueError("Input is missing trained feature columns")
        return self.preprocessor.transform(df[available])

    def save(self, name="current_pipeline.joblib"):
        joblib.dump(self, MODEL_DIR / name)

    @staticmethod
    def load(name="current_pipeline.joblib"):
        return joblib.load(MODEL_DIR / name)
