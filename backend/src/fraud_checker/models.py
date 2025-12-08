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


@dataclass
class ConversionLog:
    """成果ログ（ポストバック経由）"""
    conversion_id: str  # action_log_raw.id
    cid: Optional[str]  # check_log_raw（クリックID）
    conversion_time: datetime  # 成果発生日時
    click_time: Optional[datetime]  # クリック日時（あれば）
    media_id: str
    program_id: str
    user_id: Optional[str]  # アフィリエイターID
    # ポストバック経由のため、以下はポストバックサーバーのIP/UAになる
    postback_ipaddress: Optional[str]
    postback_useragent: Optional[str]
    # エントリー時（実ユーザー）のIP/UA - 成果ログから直接取得
    entry_ipaddress: Optional[str] = None
    entry_useragent: Optional[str] = None
    state: Optional[str] = None  # ステータス（承認/否認等）
    raw_payload: Any = None


@dataclass
class ConversionWithClickInfo:
    """クリック情報を突合した成果ログ（将来のクリックベース検知用に残置）"""
    conversion: ConversionLog
    click_ipaddress: str
    click_useragent: str
    click_time: datetime


@dataclass
class ConversionIpUaRollup:
    """成果ログのIP/UA別ロールアップ（エントリー時のIP/UAベース）"""
    date: date
    ipaddress: str  # エントリー時（実ユーザー）のIP
    useragent: str  # エントリー時（実ユーザー）のUA
    conversion_count: int  # 成果件数
    media_count: int
    program_count: int
    first_conversion_time: datetime
    last_conversion_time: datetime


@dataclass
class SuspiciousConversionFinding(ConversionIpUaRollup):
    """疑わしい成果のIP/UA"""
    reasons: List[str]
