# backend/app/models.py

from pydantic import BaseModel
from typing import List, Optional, Any

class Meta(BaseModel):
    file_name: str
    analyzed_at: str
    duration_sec: int
    sample_count: int
    gnss_systems: List[str]

class Summary(BaseModel):
    total_anomalies: int
    spoofing_suspected_count: int
    jamming_suspected_count: int
    has_spoofing_suspected: bool
    has_jamming_suspected: bool

class AnalyzeResponse(BaseModel):
    meta: Meta
    summary: Summary
    track: Any
    anomalies: List[Any]
    satellite_stats: List[Any]
    ephemeris_consistency: Optional[Any]
