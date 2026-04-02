from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class ClickLog:
    click_id: str | None
    click_time: datetime
    media_id: str
    program_id: str
    ipaddress: str
    useragent: str
    referrer: str | None
    raw_payload: Any


@dataclass
class AggregatedRow:
    date: date
    media_id: str
    program_id: str
    ipaddress: str
    useragent: str
    click_count: int
    first_time: datetime
    last_time: datetime
    created_at: datetime
    updated_at: datetime


@dataclass
class ConversionLog:
    conversion_id: str
    cid: str | None
    conversion_time: datetime
    click_time: datetime | None
    media_id: str
    program_id: str
    user_id: str | None
    postback_ipaddress: str | None
    postback_useragent: str | None
    entry_ipaddress: str | None = None
    entry_useragent: str | None = None
    click_ipaddress: str | None = None
    click_useragent: str | None = None
    state: str | None = None
    raw_payload: Any = None


@dataclass
class ConversionWithClickInfo:
    conversion: ConversionLog
    click_ipaddress: str
    click_useragent: str
    click_time: datetime


@dataclass
class ConversionIpUaRollup:
    date: date
    ipaddress: str
    useragent: str
    conversion_count: int
    media_count: int
    program_count: int
    first_conversion_time: datetime
    last_conversion_time: datetime


@dataclass
class SuspiciousConversionFinding(ConversionIpUaRollup):
    reasons: list[str]
    min_click_to_conv_seconds: float | None = None
    max_click_to_conv_seconds: float | None = None
    linked_click_count: int | None = None
    linked_clicks_per_conversion: float | None = None
    extra_window_click_count: int | None = None
    extra_window_non_browser_ratio: float | None = None


@dataclass
class CheckLog:
    check_id: str
    affiliate_user_id: str | None
    plid: str | None
    state: int | None
    regist_time: datetime
    raw_payload: Any = None


@dataclass
class TrackLog:
    track_id: str
    action_log_raw_id: str | None
    auth_type: str | None
    auth_get_type: str | None
    state: int | None
    regist_time: datetime
    raw_payload: Any = None


@dataclass
class EntityDailyMetric:
    metric_id: str
    metric_date: date
    user_id: str | None
    media_id: str | None
    promotion_id: str | None
    count: int
    raw_payload: Any = None


@dataclass
class FraudFinding:
    date: date
    user_id: str
    media_id: str
    promotion_id: str
    user_name: str | None
    media_name: str | None
    promotion_name: str | None
    primary_metric: int
    reasons: list[str]
    metrics: dict[str, Any] = field(default_factory=dict)
    first_event_time: datetime | None = None
    last_event_time: datetime | None = None
