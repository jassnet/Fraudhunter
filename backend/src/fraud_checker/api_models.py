from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    date: str
    stats: dict


class DailyStatsItem(BaseModel):
    date: str
    clicks: int
    conversions: int
    suspicious_clicks: int = 0
    suspicious_conversions: int = 0


class DailyStatsResponse(BaseModel):
    data: list[DailyStatsItem]


class SuspiciousResponse(BaseModel):
    date: str
    data: list[dict]
    total: int = 0
    limit: int = 500
    offset: int = 0


class IngestRequest(BaseModel):
    date: str  # YYYY-MM-DD


class RefreshRequest(BaseModel):
    hours: int = 24
    clicks: bool = True
    conversions: bool = True
    detect: bool = False


class IngestResponse(BaseModel):
    success: bool
    message: str
    details: Optional[dict] = None


class JobStatusResponse(BaseModel):
    status: str
    job_id: Optional[str] = None
    message: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[dict] = None


class SettingsModel(BaseModel):
    click_threshold: int = 50
    media_threshold: int = 3
    program_threshold: int = 3
    burst_click_threshold: int = 20
    burst_window_seconds: int = 600
    conversion_threshold: int = 5
    conv_media_threshold: int = 2
    conv_program_threshold: int = 2
    burst_conversion_threshold: int = 3
    burst_conversion_window_seconds: int = 1800
    min_click_to_conv_seconds: int = 5
    max_click_to_conv_seconds: int = 2592000
    browser_only: bool = False
    exclude_datacenter_ip: bool = False
