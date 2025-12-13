# app/feature_extractor.py

from __future__ import annotations
from typing import Dict, List
from datetime import datetime
import numpy as np


def _parse_time(t: str) -> float:
    # ISO8601 -> epoch seconds
    return datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()


def extract_file_features(
    samples: List[dict],
    code_counts: Dict[str, int] | None = None,
) -> Dict[str, float]:
    """
    1つのNMEAファイル（samples）から特徴量を作る
    """

    if len(samples) < 2:
        return {}

    # ---- 時刻 ----
    times = np.array([_parse_time(s["t"]) for s in samples])
    dts = np.diff(times)
    dts = dts[dts > 0]

    # ---- 位置由来速度 ----
    lats = np.array([s["lat"] for s in samples])
    lons = np.array([s["lon"] for s in samples])

    def haversine_m(lat1, lon1, lat2, lon2):
        R = 6371000.0
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = phi2 - phi1
        dl = np.radians(lon2 - lon1)
        a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dl / 2) ** 2
        return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    distances = haversine_m(lats[:-1], lons[:-1], lats[1:], lons[1:])
    speeds_pos = distances / dts

    # ---- RMC速度 ----
    speeds_rmc = np.array(
        [s["speed_mps"] for s in samples if s["speed_mps"] is not None]
    )

    # ---- Heading ----
    headings = np.array(
        [s["heading_deg"] for s in samples if s["heading_deg"] is not None]
    )
    heading_rates = np.abs(np.diff(headings))

    # ---- 信号品質 ----
    cn0_mean = np.array(
        [s["cn0_mean_dbhz"] for s in samples if s["cn0_mean_dbhz"] is not None]
    )
    cn0_min = np.array(
        [s["cn0_min_dbhz"] for s in samples if s["cn0_min_dbhz"] is not None]
    )

    hdop = np.array([s["hdop"] for s in samples if s["hdop"] is not None])
    num_sats = np.array([s["num_sats"] for s in samples if s["num_sats"] is not None])

    feats: Dict[str, float] = {}

    # ---- 時刻系 ----
    feats["dt_p50"] = np.median(dts)
    feats["dt_p95"] = np.percentile(dts, 95)

    # ---- 速度系 ----
    feats["speed_pos_p95"] = np.percentile(speeds_pos, 95)
    feats["speed_pos_max"] = np.max(speeds_pos)

    if len(speeds_rmc) > 0:
        feats["speed_rmc_p95"] = np.percentile(speeds_rmc, 95)
        feats["speed_rmc_max"] = np.max(speeds_rmc)
        # 不一致
        n = min(len(speeds_pos), len(speeds_rmc))
        feats["speed_mismatch_p95"] = np.percentile(
            np.abs(speeds_pos[:n] - speeds_rmc[:n]), 95
        )
    else:
        feats["speed_rmc_p95"] = 0.0
        feats["speed_rmc_max"] = 0.0
        feats["speed_mismatch_p95"] = 0.0

    # ---- Heading ----
    if len(heading_rates) > 0:
        feats["heading_rate_p95"] = np.percentile(heading_rates, 95)
    else:
        feats["heading_rate_p95"] = 0.0

    # ---- 信号 ----
    if len(cn0_mean) > 0:
        feats["cn0_mean_p50"] = np.median(cn0_mean)
        feats["cn0_mean_p95"] = np.percentile(cn0_mean, 95)
        feats["cn0_min_p05"] = np.percentile(cn0_min, 5)
    else:
        feats["cn0_mean_p50"] = 0.0
        feats["cn0_mean_p95"] = 0.0
        feats["cn0_min_p05"] = 0.0

    if len(hdop) > 0:
        feats["hdop_p95"] = np.percentile(hdop, 95)
    else:
        feats["hdop_p95"] = 0.0

    if len(num_sats) > 0:
        feats["num_sats_min"] = np.min(num_sats)
        feats["num_sats_p05"] = np.percentile(num_sats, 5)
    else:
        feats["num_sats_min"] = 0.0
        feats["num_sats_p05"] = 0.0

    # ---- ルール発火回数 ----
    if code_counts:
        for k, v in code_counts.items():
            feats[f"rule_{k}"] = float(v)

    feats["n_samples"] = float(len(samples))

    return feats
