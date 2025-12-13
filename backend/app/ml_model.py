# app/ml_model.py

from pathlib import Path
import json
import joblib
import numpy as np

from app.feature_extractor import extract_file_features
from app.anomaly import detect_anomalies

BASE = Path(__file__).parent
MODEL_PATH = BASE / "models" / "model_rf.joblib"
COLS_PATH = BASE / "models" / "feature_columns.json"

class SpoofingModel:
    def __init__(self):
        self.model = joblib.load(MODEL_PATH)
        with open(COLS_PATH, "r") as f:
            self.columns = json.load(f)

    def predict_score(self, samples: list[dict]) -> dict:
        _, summary, _, code_counts = detect_anomalies(samples)
        feats = extract_file_features(samples, code_counts)

        # 欠損を0で埋め、列順を合わせる
        x = np.array([[feats.get(c, 0.0) for c in self.columns]])

        prob = float(self.model.predict_proba(x)[0][1])  # spoofed確率
        return {
            "spoofing_score": prob,
            "rule_summary": summary,
        }

# アプリ起動時にロード
spoofing_model = SpoofingModel()
