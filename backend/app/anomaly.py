# backend/app/anomaly.py

from __future__ import annotations

from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from typing import Dict, List, Tuple


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


def detect_anomalies(samples: List[dict]) -> Tuple[List[dict], Dict[str, int]]:
    """
    track.samples (dict list) を受け取り、
    - anomaly_flags を埋めた samples（時刻順）
    - summary カウンタ(dict) を返す
    """
    if len(samples) < 2:
        return samples, {
            "total_anomalies": 0,
            "spoofing_suspected_count": 0,
            "jamming_suspected_count": 0,
        }

    anomalies: List[dict] = []
    spoof_count = 0
    jam_count = 0

    # 念のため時刻順に並び替え（parse_nmea側でソート済みでも保険）
    samples_sorted = sorted(samples, key=lambda s: s["t"])
    index_map = {id(s): i for i, s in enumerate(samples_sorted)}

    for i in range(1, len(samples_sorted)):
        prev = samples_sorted[i - 1]
        curr = samples_sorted[i]

        prev.setdefault("anomaly_flags", [])
        curr.setdefault("anomaly_flags", [])

        # ============
        # 時刻差の取得
        # ============
        try:
            t_prev = _parse_time(prev["t"])
            t_curr = _parse_time(curr["t"])
        except Exception:
            # どちらかの t が壊れている
            continue

        dt = (t_curr - t_prev).total_seconds()

        # ========================
        # 時間異常：スプーフィング疑い
        # ========================

        # R_time_1: GNSS時刻が逆行（強い異常）
        if dt < -1.0:
            code = "time_backward"
            _add_anomaly(
                anomalies,
                sample=curr,
                index=index_map[id(curr)],
                type_="spoofing",  # スプーフィング疑いとしてカウント
                code=code,
                message=f"GNSS time went backwards by {abs(dt):.1f} seconds.",
                severity="critical",
            )
            curr["anomaly_flags"].append(code)
            spoof_count += 1

        # R_time_2: 良好な信号状態での大きな時間ジャンプ
        # （ログ欠損ではなく、時刻がおかしくなった可能性）
        if dt > 5.0:
            num_prev = prev.get("num_sats")
            num_curr = curr.get("num_sats")
            cn0_prev = prev.get("cn0_mean_dbhz")
            cn0_curr = curr.get("cn0_mean_dbhz")

            if (
                (num_prev is not None and num_prev >= 6)
                and (num_curr is not None and num_curr >= 6)
                and (cn0_prev is not None and cn0_prev >= 30.0)
                and (cn0_curr is not None and cn0_curr >= 30.0)
            ):
                code = "time_jump"
                _add_anomaly(
                    anomalies,
                    sample=curr,
                    index=index_map[id(curr)],
                    type_="spoofing",  # これもスプーフィング寄りとして扱う
                    code=code,
                    message=f"GNSS time jumped forward by {dt:.1f} seconds with good signal.",
                    severity="warning",
                )
                curr["anomaly_flags"].append(code)
                spoof_count += 1

        # ※ 時刻異常は「速度計算などに使う dt」としては扱いにくいので、
        #    あまりにも変ならここで以降の処理をスキップしても良い。
        #    ただし dt が少し大きいだけ（例: 6秒）なら、速度などに使うかどうかはポリシー次第。
        if dt <= 0 or dt > 10:
            # 解析に使う dt としてはスキップ（物理量のチェックには使わない）
            continue

        # ========================
        # 位置・速度・信号品質の取得
        # ========================
        lat1, lon1 = prev.get("lat"), prev.get("lon")
        lat2, lon2 = curr.get("lat"), curr.get("lon")

        distance_m = None
        inst_speed = None
        if (
            lat1 is not None
            and lon1 is not None
            and lat2 is not None
            and lon2 is not None
        ):
            distance_m = _haversine_m(lat1, lon1, lat2, lon2)
            inst_speed = distance_m / dt  # [m/s]

        speed_prev = prev.get("speed_mps")
        speed_curr = curr.get("speed_mps")

        num_prev = prev.get("num_sats")
        num_curr = curr.get("num_sats")

        cn0_prev = prev.get("cn0_mean_dbhz")
        cn0_curr = curr.get("cn0_mean_dbhz")

        hdop_prev = prev.get("hdop")
        hdop_curr = curr.get("hdop")

        # ================
        # スプーフィング疑い（位置・速度）
        # ================

        # R1: 物理的にありえない速度（地上車両・低空ドローン想定）
        if inst_speed is not None and inst_speed > 120.0:  # 約432 km/h
            code = "impossible_speed"
            _add_anomaly(
                anomalies,
                sample=curr,
                index=index_map[id(curr)],
                type_="spoofing",
                code=code,
                message=f"Impossible speed {inst_speed:.1f} m/s between samples.",
                severity="critical",
            )
            curr["anomaly_flags"].append(code)
            spoof_count += 1

        # R2: 静止付近なのに位置ジャンプ
        if (
            inst_speed is not None
            and distance_m is not None
            and distance_m > 20.0  # 1秒で20m以上
        ):
            if (speed_prev is not None and speed_prev < 1.0) and (
                speed_curr is not None and speed_curr < 1.0
            ):
                code = "static_jump"
                _add_anomaly(
                    anomalies,
                    sample=curr,
                    index=index_map[id(curr)],
                    type_="spoofing",
                    code=code,
                    message=f"Static-position jump: {distance_m:.1f} m while speed ~0.",
                    severity="warning",
                )
                curr["anomaly_flags"].append(code)
                spoof_count += 1

        # ================
        # ジャミング疑い
        # ================

        # R3: 衛星数が急減
        if (
            num_prev is not None
            and num_curr is not None
            and num_prev >= 6
            and num_curr <= 3
            and (num_prev - num_curr) >= 4
            and dt <= 2.0
        ):
            code = "sat_drop"
            _add_anomaly(
                anomalies,
                sample=curr,
                index=index_map[id(curr)],
                type_="jamming",
                code=code,
                message=f"Satellite count dropped from {num_prev} to {num_curr}.",
                severity="critical",
            )
            curr["anomaly_flags"].append(code)
            jam_count += 1

        # R4: C/N0 の急激な低下
        if (
            cn0_prev is not None
            and cn0_curr is not None
            and cn0_prev >= 30.0
            and cn0_curr <= 20.0
            and (cn0_prev - cn0_curr) >= 10.0
        ):
            code = "cn0_drop"
            _add_anomaly(
                anomalies,
                sample=curr,
                index=index_map[id(curr)],
                type_="jamming",
                code=code,
                message=f"C/N0 mean dropped from {cn0_prev:.1f} to {cn0_curr:.1f} dB-Hz.",
                severity="warning",
            )
            curr["anomaly_flags"].append(code)
            jam_count += 1

        # R5: HDOP スパイク
        if (
            hdop_prev is not None
            and hdop_curr is not None
            and hdop_prev <= 2.0
            and hdop_curr >= 4.0
            and hdop_curr >= hdop_prev * 2.5
        ):
            code = "hdop_spike"
            _add_anomaly(
                anomalies,
                sample=curr,
                index=index_map[id(curr)],
                type_="jamming",
                code=code,
                message=f"HDOP spiked from {hdop_prev:.2f} to {hdop_curr:.2f}.",
                severity="warning",
            )
            curr["anomaly_flags"].append(code)
            jam_count += 1

    summary = {
        "total_anomalies": len(anomalies),
        "spoofing_suspected_count": spoof_count,
        "jamming_suspected_count": jam_count,
    }

    return samples_sorted, summary


def _add_anomaly(
    anomalies: List[dict],
    sample: dict,
    index: int,
    type_: str,
    code: str,
    message: str,
    severity: str = "warning",
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
