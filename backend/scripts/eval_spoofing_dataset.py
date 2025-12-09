#!/usr/bin/env python
"""
NMEA スプーフィングデータセットを一括評価するスクリプト（プロトタイプ）

使い方:
    cd backend
    source .venv/bin/activate
    python -m app.scripts.eval_spoofing_dataset ../tests/datasets/spoofing
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional

from app.nmea_parser import parse_nmea_to_track
from app.anomaly import detect_anomalies


def load_ground_truth(meta_path: Path) -> Dict:
    """
    メタデータ (JSON) のフォーマット例:

    {
      "scenario": "marsim_scenario_01",
      "label": "spoofed",   // or "normal"
      "spoofing_intervals": [
        {"start": "2020-01-01T10:00:30Z", "end": "2020-01-01T10:05:00Z"}
      ]
    }

    まだ用意していなくてもOK。無ければ空dictを返す。
    """
    if not meta_path.exists():
        return {}
    with meta_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_nmea_file(nmea_path: Path) -> Tuple[Dict, List[dict]]:
    """
    単一の NMEA ファイルに対して、
    - anomaly サマリ（counts）
    - anomalies リスト
    を返す。
    """
    text = nmea_path.read_text(encoding="utf-8", errors="ignore")

    samples = parse_nmea_to_track(text)
    samples_with_flags, summary_counts, anomalies = detect_anomalies(samples)

    # anomaly code ごとのカウント
    code_counter = Counter(a["code"] for a in anomalies)
    type_counter = Counter(a["type"] for a in anomalies)

    result = {
        "file": str(nmea_path),
        "sample_count": len(samples_with_flags),
        "total_anomalies": summary_counts["total_anomalies"],
        "spoofing_suspected_count": summary_counts["spoofing_suspected_count"],
        "jamming_suspected_count": summary_counts["jamming_suspected_count"],
        "by_code": dict(code_counter),
        "by_type": dict(type_counter),
    }
    return result, anomalies


def main(root_dir: str) -> None:
    root = Path(root_dir)
    if not root.exists():
        print(f"[ERROR] directory not found: {root}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Evaluating NMEA spoofing dataset under: {root}")

    # *.nmea / *.log あたりを全部拾う
    nmea_files = sorted(
        [p for p in root.rglob("*") if p.suffix.lower() in {".nmea", ".log", ".txt"}]
    )

    if not nmea_files:
        print("[WARN] No NMEA-like files (*.nmea, *.log, *.txt) found.")
        sys.exit(0)

    overall_code_counter = Counter()
    overall_type_counter = Counter()
    per_file_results: List[Dict] = []

    for nmea_path in nmea_files:
        print(f"\n[INFO] === {nmea_path.name} ===")

        meta_path = nmea_path.with_suffix(".meta.json")
        meta = load_ground_truth(meta_path)

        result, anomalies = evaluate_nmea_file(nmea_path)

        # ground truth があればここで簡単な比較をする余地がある
        # 例: meta["label"] == "spoofed" なのに total_anomalies == 0 なら危険 etc.
        if meta:
            result["meta"] = meta

        per_file_results.append(result)

        # 集計
        overall_code_counter.update(result["by_code"])
        overall_type_counter.update(result["by_type"])

        # 簡単にコンソールに要約を出す
        print(f"  samples            : {result['sample_count']}")
        print(f"  total_anomalies    : {result['total_anomalies']}")
        print(f"  spoofing_suspected : {result['spoofing_suspected_count']}")
        print(f"  jamming_suspected  : {result['jamming_suspected_count']}")
        print(f"  by_type            : {result['by_type']}")
        print(f"  by_code            : {result['by_code']}")

    # 全体集計
    print("\n[INFO] === Overall summary ===")
    print(f"  files evaluated : {len(per_file_results)}")
    print(f"  anomalies by type : {dict(overall_type_counter)}")
    print(f"  anomalies by code : {dict(overall_code_counter)}")

    # 必要なら JSON に保存（将来 README の表に貼るため）
    out_path = root / "eval_summary.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "per_file": per_file_results,
                "overall_by_type": dict(overall_type_counter),
                "overall_by_code": dict(overall_code_counter),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"[INFO] Saved summary JSON to: {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.scripts.eval_spoofing_dataset <root_dir>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
