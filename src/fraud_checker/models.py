from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, List, Optional


@dataclass
class ClickLog:
    click_id: Optional[str]
    click_time: datetime
    media_id: str
    program_id: str
    ipaddress: str
    useragent: str
    referrer: Optional[str]
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
class IpUaRollup:
    date: date
    ipaddress: str
    useragent: str
    total_clicks: int
    media_count: int
    program_count: int
    first_time: datetime
    last_time: datetime


@dataclass
class SuspiciousFinding(IpUaRollup):
    reasons: List[str]
