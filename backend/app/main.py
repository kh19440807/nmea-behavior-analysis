# backend/app/main.py

from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import AnalyzeResponse, Meta, Summary
from .nmea_parser import parse_nmea_to_track
from .anomaly import detect_anomalies  # ★ これを追加
from app.ml_model import spoofing_model

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
    text = (await file.read()).decode("utf-8", errors="ignore")
    samples = parse_nmea_to_track(text)

    # ML推論
    ml = spoofing_model.predict_score(samples)

    spoofing_score = ml["spoofing_score"]
    rule_summary = ml["rule_summary"]

    # しきい値（最初は保守的）
    TH = 0.6
    has_spoofing = spoofing_score >= TH

    summary = Summary(
        total_anomalies=rule_summary["total_anomalies"],
        spoofing_suspected_count=rule_summary["spoofing_suspected_count"],
        jamming_suspected_count=rule_summary["jamming_suspected_count"],
        has_spoofing_suspected=has_spoofing,
        has_jamming_suspected=rule_summary["jamming_suspected_count"] > 0,
    )

    meta = Meta(
        file_name=file.filename or "unknown",
        analyzed_at=datetime.utcnow().isoformat() + "Z",
        duration_sec=len(samples),
        sample_count=len(samples),
        gnss_systems=["GPS"],
    )

    return AnalyzeResponse(
        meta=meta,
        summary=summary,
        track={"samples": samples},
        anomalies=[],
        satellite_stats=[],
        ephemeris_consistency=None,
        spoofing_score=spoofing_score,   # ★追加
    )

