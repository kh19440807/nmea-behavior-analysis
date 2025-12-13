# backend/app/anomaly.py

from __future__ import annotations
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from typing import Dict, List, Tuple


DEFAULT_PARAMS: Dict[str, float] = {
    "dt_min_for_speed": 0.5,
    "dt_max_for_speed": 10.0,
    "impossible_speed_mps": 200.0,      # 720 km/h
    "static_jump_distance_m": 50.0,
    "static_speed_threshold_mps": 0.3,
    "time_backward_sec": -1.0,
    "time_jump_sec": 5.0,
    "time_jump_min_sats": 6,
    "time_jump_min_cn0": 30.0,
    "sat_drop_min_prev": 6,
    "sat_drop_max_curr": 3,
    "sat_drop_delta": 4,
    "sat_drop_dt_max": 2.0,
    "cn0_drop_min_prev": 30.0,
    "cn0_drop_max_curr": 20.0,
    "cn0_drop_delta": 10.0,
    "hdop_spike_prev_max": 2.0,
    "hdop_spike_curr_min": 4.0,
    "hdop_spike_ratio": 2.5,
}


def _parse_time(s: str) -> datetime:
    """
    ISO8601文字列をdatetimeに変換。
    末尾が "Z" の場合にも対応。
    """
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    2点間の距離[m]を計算（WGS84球近似）
    """
    R = 6371000.0  # 地球半径[m]
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)

    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def detect_anomalies(
    samples: List[dict],
    params: Dict[str, float] | None = None,
) -> Tuple[List[dict], Dict[str, int], List[dict]]:

    if params is None:
        params = DEFAULT_PARAMS

    if len(samples) < 2:
        return samples, {
            "total_anomalies": 0,
            "spoofing_suspected_count": 0,
            "jamming_suspected_count": 0,
        }, []

    anomalies: List[dict] = []
    spoof_count = 0
    jam_count = 0
    code_counts: Dict[str, int] = {}

    samples_sorted = sorted(samples, key=lambda s: s["t"])
    index_map = {id(s): i for i, s in enumerate(samples_sorted)}

    for i in range(1, len(samples_sorted)):
        prev = samples_sorted[i - 1]
        curr = samples_sorted[i]

        prev.setdefault("anomaly_flags", [])
        curr.setdefault("anomaly_flags", [])

        # --- 時刻差 ---
        try:
            t_prev = _parse_time(prev["t"])
            t_curr = _parse_time(curr["t"])
        except Exception:
            continue

        dt = (t_curr - t_prev).total_seconds()

        # R_time_1: 逆行
        if dt < params["time_backward_sec"]:
            code = "time_backward"
            _add_anomaly(anomalies, curr, index_map[id(curr)],
                         "spoofing", code,
                         f"GNSS time went backwards by {abs(dt):.1f} s.",
                         "critical", code_counts)
            curr["anomaly_flags"].append(code)
            spoof_count += 1

        # R_time_2: 大きな時間ジャンプ（良好C/N0 & 多数衛星）
        if dt > params["time_jump_sec"]:
            num_prev = prev.get("num_sats")
            num_curr = curr.get("num_sats")
            cn0_prev = prev.get("cn0_mean_dbhz")
            cn0_curr = curr.get("cn0_mean_dbhz")

            if (
                num_prev is not None and num_prev >= params["time_jump_min_sats"]
                and num_curr is not None and num_curr >= params["time_jump_min_sats"]
                and cn0_prev is not None and cn0_prev >= params["time_jump_min_cn0"]
                and cn0_curr is not None and cn0_curr >= params["time_jump_min_cn0"]
            ):
                code = "time_jump"
                _add_anomaly(anomalies, curr, index_map[id(curr)],
                             "spoofing", code,
                             f"GNSS time jumped by {dt:.1f} s with good signal.",
                             "warning", code_counts)
                curr["anomaly_flags"].append(code)
                spoof_count += 1

        # dt が速度評価に使える範囲かどうか
        if dt <= params["dt_min_for_speed"] or dt > params["dt_max_for_speed"]:
            continue

        # --- 位置・速度 ---
        lat1, lon1 = prev.get("lat"), prev.get("lon")
        lat2, lon2 = curr.get("lat"), curr.get("lon")

        distance_m = None
        inst_speed = None
        if None not in (lat1, lon1, lat2, lon2):
            distance_m = _haversine_m(lat1, lon1, lat2, lon2)
            inst_speed = distance_m / dt

        speed_prev = prev.get("speed_mps")
        speed_curr = curr.get("speed_mps")

        num_prev = prev.get("num_sats")
        num_curr = curr.get("num_sats")

        cn0_prev = prev.get("cn0_mean_dbhz")
        cn0_curr = curr.get("cn0_mean_dbhz")

        hdop_prev = prev.get("hdop")
        hdop_curr = curr.get("hdop")

        # --- R1: impossible speed ---
        if inst_speed is not None and inst_speed > params["impossible_speed_mps"]:
            code = "impossible_speed"
            _add_anomaly(anomalies, curr, index_map[id(curr)],
                         "spoofing", code,
                         f"Impossible speed {inst_speed:.1f} m/s.",
                         "critical", code_counts)
            curr["anomaly_flags"].append(code)
            spoof_count += 1

        # --- R2: 静止ジャンプ ---
        if (
            inst_speed is not None and distance_m is not None
            and distance_m > params["static_jump_distance_m"]
        ):
            if (
                speed_prev is not None and speed_prev < params["static_speed_threshold_mps"]
                and speed_curr is not None and speed_curr < params["static_speed_threshold_mps"]
            ):
                code = "static_jump"
                _add_anomaly(anomalies, curr, index_map[id(curr)],
                             "spoofing", code,
                             f"Static jump {distance_m:.1f} m while speed ~0.",
                             "warning", code_counts)
                curr["anomaly_flags"].append(code)
                spoof_count += 1

        # --- R3: 衛星数急減 ---
        if (
            num_prev is not None and num_curr is not None
            and num_prev >= params["sat_drop_min_prev"]
            and num_curr <= params["sat_drop_max_curr"]
            and (num_prev - num_curr) >= params["sat_drop_delta"]
            and dt <= params["sat_drop_dt_max"]
        ):
            code = "sat_drop"
            _add_anomaly(anomalies, curr, index_map[id(curr)],
                         "jamming", code,
                         f"Satellite count dropped {num_prev}->{num_curr}.",
                         "critical", code_counts)
            curr["anomaly_flags"].append(code)
            jam_count += 1

        # --- R4: C/N0 drop ---
        if (
            cn0_prev is not None and cn0_curr is not None
            and cn0_prev >= params["cn0_drop_min_prev"]
            and cn0_curr <= params["cn0_drop_max_curr"]
            and (cn0_prev - cn0_curr) >= params["cn0_drop_delta"]
        ):
            code = "cn0_drop"
            _add_anomaly(anomalies, curr, index_map[id(curr)],
                         "jamming", code,
                         f"C/N0 {cn0_prev:.1f}->{cn0_curr:.1f} dB-Hz.",
                         "warning", code_counts)
            curr["anomaly_flags"].append(code)
            jam_count += 1

        # --- R5: HDOP spike ---
        if (
            hdop_prev is not None and hdop_curr is not None
            and hdop_prev <= params["hdop_spike_prev_max"]
            and hdop_curr >= params["hdop_spike_curr_min"]
            and hdop_curr >= hdop_prev * params["hdop_spike_ratio"]
        ):
            code = "hdop_spike"
            _add_anomaly(anomalies, curr, index_map[id(curr)],
                         "jamming", code,
                         f"HDOP {hdop_prev:.2f}->{hdop_curr:.2f}.",
                         "warning", code_counts)
            curr["anomaly_flags"].append(code)
            jam_count += 1

    summary = {
        "total_anomalies": len(anomalies),
        "spoofing_suspected_count": spoof_count,
        "jamming_suspected_count": jam_count,
    }

    print("[DEBUG] anomaly code counts:", code_counts)

    return samples_sorted, summary, anomalies, code_counts


def _add_anomaly(
    anomalies: List[dict],
    sample: dict,
    index: int,
    type_: str,
    code: str,
    message: str,
    severity: str = "warning",
    code_counts: Dict[str, int] | None = None,
) -> None:
    anomalies.append(
        {
            "t": sample.get("t"),
            "index": index,
            "type": type_,
            "code": code,
            "severity": severity,
            "message": message,
        }
    )
    if code_counts is not None:
        code_counts[code] = code_counts.get(code, 0) + 1