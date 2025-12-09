# backend/app/main.py

from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import AnalyzeResponse, Meta, Summary
from .nmea_parser import parse_nmea_to_track
from .anomaly import detect_anomalies  # ★ これを追加


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_log(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file name")

    raw = await file.read()
    text = raw.decode("utf-8", errors="ignore")

    # 1) NMEA をパースしてサンプル列に
    samples = parse_nmea_to_track(text)

    # 2) 異常検知ロジックを適用
    #    detect_anomalies は、前に作った anomaly.py の関数を想定
    #    戻り値: (samples_with_flags, summary_counts, anomalies)
    samples_with_flags, summary_counts, anomalies = detect_anomalies(samples)

    # 3) Summary を集計
    summary = Summary(
        total_anomalies=summary_counts["total_anomalies"],
        spoofing_suspected_count=summary_counts["spoofing_suspected_count"],
        jamming_suspected_count=summary_counts["jamming_suspected_count"],
        has_spoofing_suspected=summary_counts["spoofing_suspected_count"] > 0,
        has_jamming_suspected=summary_counts["jamming_suspected_count"] > 0,
    )

    # 4) Meta 情報
    meta = Meta(
        file_name=file.filename or "unknown",
        analyzed_at=datetime.utcnow().isoformat() + "Z",
        duration_sec=len(samples_with_flags),  # 仮に 1Hz とみなす
        sample_count=len(samples_with_flags),
        gnss_systems=["GPS"],  # TODO: 将来、GSV/GLONASS 等から判定
    )

    # 5) レスポンス組み立て
    return AnalyzeResponse(
        meta=meta,
        summary=summary,
        track={"samples": samples_with_flags},
        anomalies=anomalies,
        satellite_stats=[],
        ephemeris_consistency=None,
    )
