# backend/app/main.py

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime    # ★これを追加

from .models import AnalyzeResponse, Meta, Summary
from .nmea_parser import parse_nmea_to_track

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

    # 簡易 summary（後でちゃんと計算する）
    summary = Summary(
        total_anomalies=0,
        spoofing_suspected_count=0,
        jamming_suspected_count=0,
        has_spoofing_suspected=False,
        has_jamming_suspected=False,
    )

    meta = Meta(
        file_name=file.filename or "unknown",
        analyzed_at=datetime.utcnow().isoformat() + "Z",
        duration_sec=len(samples),  # 仮: 1Hz と仮定
        sample_count=len(samples),
        gnss_systems=["GPS"],  # 後でちゃんと判定
    )

    return AnalyzeResponse(
        meta=meta,
        summary=summary,
        track={"samples": samples},
        anomalies=[],
        satellite_stats=[],
        ephemeris_consistency=None,
    )
