# backend/app/nmea_parser.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date, time, timezone
from typing import Dict, List, Optional


@dataclass
class TrackSampleRaw:
    t: datetime
    lat: Optional[float] = None
    lon: Optional[float] = None
    alt_m: Optional[float] = None
    speed_mps: Optional[float] = None
    heading_deg: Optional[float] = None
    num_sats: Optional[int] = None
    hdop: Optional[float] = None
    vdop: Optional[float] = None
    pdop: Optional[float] = None
    cn0_values: List[float] = field(default_factory=list)


def _parse_lat(lat_str: str, hemi: str) -> Optional[float]:
    # 例: "3723.2475","N" → 37 + 23.2475/60
    if not lat_str or not hemi:
        return None
    try:
        ddmm = float(lat_str)
    except ValueError:
        return None
    deg = int(ddmm // 100)
    minutes = ddmm - deg * 100
    value = deg + minutes / 60.0
    if hemi.upper() == "S":
        value = -value
    return value


def _parse_lon(lon_str: str, hemi: str) -> Optional[float]:
    # 例: "12202.3456","E"
    if not lon_str or not hemi:
        return None
    try:
        dddmm = float(lon_str)
    except ValueError:
        return None
    deg = int(dddmm // 100)
    minutes = dddmm - deg * 100
    value = deg + minutes / 60.0
    if hemi.upper() == "W":
        value = -value
    return value


def _parse_time_utc(time_str: str) -> Optional[time]:
    # hhmmss.sss
    if not time_str:
        return None
    try:
        if "." in time_str:
            base, frac = time_str.split(".", 1)
            frac = (frac + "000")[:3]  # ミリ秒3桁
            ms = int(frac)
        else:
            base = time_str
            ms = 0
        base = base.zfill(6)
        hh = int(base[0:2])
        mm = int(base[2:4])
        ss = int(base[4:6])
        return time(hour=hh, minute=mm, second=ss, microsecond=ms * 1000)
    except Exception:
        return None


def _parse_date_utc(date_str: str) -> Optional[date]:
    # ddmmyy
    if not date_str:
        return None
    try:
        dd = int(date_str[0:2])
        mm = int(date_str[2:4])
        yy = int(date_str[4:6])
        # 2000年代前提（GPSログならまず問題なし）
        year = 2000 + yy if yy < 80 else 1900 + yy
        return date(year=year, month=mm, day=dd)
    except Exception:
        return None


def _get_or_create_sample(
    samples: Dict[datetime, TrackSampleRaw],
    dt: datetime,
) -> TrackSampleRaw:
    if dt not in samples:
        samples[dt] = TrackSampleRaw(t=dt)
    return samples[dt]


def parse_nmea_to_track(text: str) -> List[dict]:
    """
    NMEAテキスト全体から、track.samples 用の dict のリストを返す。
    ここでは GGA / RMC / GSA / GSV に対応。
    """
    samples: Dict[datetime, TrackSampleRaw] = {}
    current_date: Optional[date] = None

    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("$"):
            continue

        # チェックサム除去
        if "*" in line:
            payload, _cs = line.split("*", 1)
        else:
            payload = line
        fields = payload.split(",")
        if not fields:
            continue

        head = fields[0]
        msg_type = head[3:6]  # "GGA","RMC","GSA","GSV" など

        # --- RMC: 日付・速度・コースなど ---
        if msg_type == "RMC" and len(fields) >= 10:
            time_str = fields[1]
            status = fields[2]  # A: valid, V: void
            lat_str, lat_hemi = fields[3], fields[4]
            lon_str, lon_hemi = fields[5], fields[6]
            speed_knots = fields[7]
            track_angle = fields[8]
            date_str = fields[9]

            t_utc = _parse_time_utc(time_str)
            d_utc = _parse_date_utc(date_str) or current_date
            if d_utc is None or t_utc is None:
                continue
            current_date = d_utc
            dt = datetime.combine(d_utc, t_utc, tzinfo=timezone.utc)

            sample = _get_or_create_sample(samples, dt)

            if status == "A":
                lat = _parse_lat(lat_str, lat_hemi)
                lon = _parse_lon(lon_str, lon_hemi)
                if lat is not None:
                    sample.lat = lat
                if lon is not None:
                    sample.lon = lon

                try:
                    if speed_knots:
                        v_knots = float(speed_knots)
                        sample.speed_mps = v_knots * 0.514444
                except ValueError:
                    pass

                try:
                    if track_angle:
                        sample.heading_deg = float(track_angle)
                except ValueError:
                    pass

        # --- GGA: 高度・衛星数・HDOP ---
        elif msg_type == "GGA" and len(fields) >= 10:
            time_str = fields[1]
            lat_str, lat_hemi = fields[2], fields[3]
            lon_str, lon_hemi = fields[4], fields[5]
            fix_type_str = fields[6]
            num_sats_str = fields[7]
            hdop_str = fields[8]
            alt_str = fields[9]

            t_utc = _parse_time_utc(time_str)
            d_utc = current_date or date.today()
            if t_utc is None:
                continue
            dt = datetime.combine(d_utc, t_utc, tzinfo=timezone.utc)
            sample = _get_or_create_sample(samples, dt)

            lat = _parse_lat(lat_str, lat_hemi)
            lon = _parse_lon(lon_str, lon_hemi)
            if lat is not None:
                sample.lat = lat
            if lon is not None:
                sample.lon = lon

            try:
                if alt_str:
                    sample.alt_m = float(alt_str)
            except ValueError:
                pass

            try:
                if num_sats_str:
                    sample.num_sats = int(num_sats_str)
            except ValueError:
                pass

            try:
                if hdop_str:
                    sample.hdop = float(hdop_str)
            except ValueError:
                pass

            # fix_type は GSA で上書きする想定なのでここでは使わなくてもOK

        # --- GSA: DOP + fix type ---
        elif msg_type == "GSA" and len(fields) >= 17:
            # fields[1]: mode（M/A）
            fix_type_str = fields[2]  # 1: no fix, 2: 2D, 3: 3D
            pdop_str = fields[15] if len(fields) > 15 else ""
            hdop_str = fields[16] if len(fields) > 16 else ""
            vdop_str = fields[17] if len(fields) > 17 else ""

            # GSA は時刻情報を持たないので「最新サンプルに書き込む」
            if not samples:
                continue
            latest_dt = max(samples.keys())
            sample = samples[latest_dt]

            try:
                if pdop_str:
                    sample.pdop = float(pdop_str)
            except ValueError:
                pass
            try:
                if hdop_str:
                    sample.hdop = float(hdop_str)
            except ValueError:
                pass
            try:
                if vdop_str:
                    sample.vdop = float(vdop_str)
            except ValueError:
                pass
            # fix_type 自体は必要になったら拡張

        # --- GSV: C/N0 ---
        elif msg_type == "GSV" and len(fields) >= 4:
            # 構造: $GxGSV,total_msgs,msg_num,total_sats, sat1_prn, sat1_el, sat1_az, sat1_snr, sat2_..., ...
            # ここでは snr 部分だけ使ってサンプルの cn0_values に積む
            if not samples:
                continue
            latest_dt = max(samples.keys())
            sample = samples[latest_dt]

            # 4番目以降が衛星情報、4つセットで1衛星
            # index: 4..7, 8..11, 12..15, ...
            for i in range(4, len(fields), 4):
                if i + 3 >= len(fields):
                    break
                snr_str = fields[i + 3]
                if not snr_str:
                    continue
                try:
                    snr = float(snr_str)
                except ValueError:
                    continue
                if snr > 0:
                    sample.cn0_values.append(snr)

    # dict -> 時系列ソートされた List[dict] に変換
    track_samples: List[dict] = []
    for dt in sorted(samples.keys()):
        s = samples[dt]
        if s.cn0_values:
            cn0_mean = sum(s.cn0_values) / len(s.cn0_values)
            cn0_min = min(s.cn0_values)
            cn0_max = max(s.cn0_values)
        else:
            cn0_mean = cn0_min = cn0_max = None

        track_samples.append(
            {
                "t": s.t.isoformat(),
                "lat": s.lat,
                "lon": s.lon,
                "alt_m": s.alt_m,
                "speed_mps": s.speed_mps,
                "heading_deg": s.heading_deg,
                "num_sats": s.num_sats,
                "hdop": s.hdop,
                "vdop": s.vdop,
                "pdop": s.pdop,
                "cn0_mean_dbhz": cn0_mean,
                "cn0_min_dbhz": cn0_min,
                "cn0_max_dbhz": cn0_max,
                "anomaly_flags": [],
            }
        )

    return track_samples
