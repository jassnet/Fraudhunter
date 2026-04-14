from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SummaryResponse(BaseModel):
    date: str
    stats: dict
    quality: dict | None = None


class DailyStatsItem(BaseModel):
    date: str
    clicks: int
    conversions: int
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


class TestDataResponse(BaseModel):
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
    queue: Optional[dict] = None


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
    fraud_check_min_total: int = 10
    fraud_check_invalid_rate: int = 30
    fraud_check_duplicate_plid_count: int = 3
    fraud_check_duplicate_plid_rate: int = 10
    fraud_track_min_total: int = 20
    fraud_track_auth_error_rate: int = 5
    fraud_track_auth_ip_ua_rate: int = 50
    fraud_action_min_total: int = 10
    fraud_action_short_gap_seconds: int = 5
    fraud_action_short_gap_count: int = 3
    fraud_action_cancel_rate: int = 30
    fraud_action_fixed_gap_min_count: int = 3
    fraud_action_fixed_gap_max_unique: int = 2
    fraud_spike_multiplier: int = 3
    fraud_spike_lookback_days: int = 7
    browser_only: bool = False
    exclude_datacenter_ip: bool = False


class ConsoleReviewRequest(BaseModel):
    case_keys: list[str] = Field(default_factory=list)
    status: str
    reason: str
    filters: Optional[dict] = None


class ConsoleAssignmentRequest(BaseModel):
    case_keys: list[str]
    action: str


class ConsoleFollowUpTaskUpdateRequest(BaseModel):
    task_id: str
    status: str


class ConsoleReviewResponse(BaseModel):
    requested_count: int
    matched_current_count: int
    updated_count: int
    missing_keys: list[str]
    status: str
