# backend/app/main.py

from fastapi import FastAPI, UploadFile, File
from .models import AnalyzeResponse, Meta, Summary

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_log(file: UploadFile = File(...)):
    text = (await file.read()).decode("utf-8", errors="ignore")

    # MVPではまずダミーを返しておく
    return AnalyzeResponse(
        meta=Meta(
            file_name=file.filename,
            analyzed_at="2025-01-01T00:00:00Z",
            duration_sec=0,
            sample_count=0,
            gnss_systems=["GPS"],
        ),
        summary=Summary(
            total_anomalies=0,
            spoofing_suspected_count=0,
            jamming_suspected_count=0,
            has_spoofing_suspected=False,
            has_jamming_suspected=False,
        ),
        track={"samples": []},
        anomalies=[],
        satellite_stats=[],
        ephemeris_consistency=None,
    )
