# app/scripts/train_marsim_classifier.py

from __future__ import annotations
from pathlib import Path
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

from app.nmea_parser import parse_nmea_to_track
from app.anomaly import detect_anomalies
from app.feature_extractor import extract_file_features
import joblib, json

MARSIM_NMEA_DIR = Path("/home/kazuhide/marsim/data/nmea")


def load_dataset():
    rows = []

    for path in sorted(MARSIM_NMEA_DIR.glob("*.nmea")):
        name = path.name.lower()
        if "unspoofed" in name:
            label = 0
        elif "spoofed" in name:
            label = 1
        else:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        samples = parse_nmea_to_track(text)
        _, _, _, code_counts = detect_anomalies(samples)

        feats = extract_file_features(samples, code_counts)
        feats["label"] = label
        feats["file"] = path.name

        rows.append(feats)

    df = pd.DataFrame(rows).fillna(0.0)
    return df


def main():
    df = load_dataset()

    X = df.drop(columns=["label", "file"])
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("\n=== Logistic Regression ===")
    logreg = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(class_weight="balanced", max_iter=2000)),
        ]
    )
    logreg.fit(X_train, y_train)
    print(classification_report(y_test, logreg.predict(X_test)))

    print("\n=== Random Forest ===")
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        class_weight="balanced",
        random_state=42,
    )
    rf.fit(X_train, y_train)
    print(classification_report(y_test, rf.predict(X_test)))

    # 重要度表示
    importances = pd.Series(
        rf.feature_importances_, index=X.columns
    ).sort_values(ascending=False)
    print("\nTop 20 feature importances:")
    print(importances.head(20))
    
    joblib.dump(rf, "model_rf.joblib")
    with open("feature_columns.json", "w") as f:
        json.dump(X.columns.tolist(), f, indent=2)

    print("[INFO] saved model_rf.joblib and feature_columns.json")


if __name__ == "__main__":
    main()
