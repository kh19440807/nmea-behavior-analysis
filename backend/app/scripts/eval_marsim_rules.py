# app/scripts/eval_marsim_rules.py

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from app.nmea_parser import parse_nmea_to_track
from app.anomaly import detect_anomalies

# ★ あなたの生成先
MARSIM_NMEA_DIR = Path("/home/kazuhide/marsim/data/nmea")


def iter_marsim_files() -> List[Tuple[Path, bool]]:
    """
    MARSIMのNMEAファイルを列挙し、ファイル名からラベルを決める。
    - unspoofed が含まれる → False
    - spoofed が含まれる → True
    """
    items: List[Tuple[Path, bool]] = []

    for path in sorted(MARSIM_NMEA_DIR.glob("*.nmea")):
        name = path.name.lower()
        if "unspoofed" in name:
            items.append((path, False))
        elif "spoofed" in name:
            items.append((path, True))
        else:
            print(f"[WARN] skip unlabeled file: {path.name}")

    print(f"[INFO] total labeled NMEA files: {len(items)}")
    return items


def evaluate_once() -> Dict[str, float]:
    items = iter_marsim_files()

    tp = fp = tn = fn = 0

    for nmea_path, is_spoofed in items:
        text = nmea_path.read_text(encoding="utf-8", errors="ignore")
        samples = parse_nmea_to_track(text)

        _, summary, _ = detect_anomalies(samples)

        predicted_spoofed = summary["spoofing_suspected_count"] > 0

        if is_spoofed and predicted_spoofed:
            tp += 1
        elif (not is_spoofed) and (not predicted_spoofed):
            tn += 1
        elif (not is_spoofed) and predicted_spoofed:
            fp += 1
        elif is_spoofed and (not predicted_spoofed):
            fn += 1

    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0

    metrics = {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }

    print("\n=== SUMMARY ===")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    return metrics


def main():
    if not MARSIM_NMEA_DIR.exists():
        raise SystemExit(f"[ERROR] NMEA dir not found: {MARSIM_NMEA_DIR}")
    evaluate_once()


if __name__ == "__main__":
    main()