from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import CheckConstraint, Index
from . import Base


class ClickIpuaDaily(Base):
    __tablename__ = "click_ipua_daily"
    __table_args__ = (
        Index("idx_click_ipua_daily_date", "date"),
        Index("idx_click_ipua_daily_date_ip", "date", "ipaddress"),
        Index("idx_click_ipua_daily_date_ip_ua", "date", "ipaddress", "useragent"),
        Index("idx_click_ipua_daily_media", "date", "media_id"),
        Index("idx_click_ipua_daily_program", "date", "program_id"),
    )

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    media_id: Mapped[str] = mapped_column(Text, primary_key=True)
    program_id: Mapped[str] = mapped_column(Text, primary_key=True)
    ipaddress: Mapped[str] = mapped_column(Text, primary_key=True)
    useragent: Mapped[str] = mapped_column(Text, primary_key=True)
    click_count: Mapped[int] = mapped_column(Integer, nullable=False)
    first_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ClickRaw(Base):
    __tablename__ = "click_raw"
    __table_args__ = (
        Index("idx_click_raw_time", "click_time"),
        Index("idx_click_raw_media", "media_id", "click_time"),
        Index("idx_click_raw_program", "program_id", "click_time"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    click_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    media_id: Mapped[str | None] = mapped_column(Text)
    program_id: Mapped[str | None] = mapped_column(Text)
    ipaddress: Mapped[str | None] = mapped_column(Text)
    useragent: Mapped[str | None] = mapped_column(Text)
    referrer: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ConversionRaw(Base):
    __tablename__ = "conversion_raw"
    __table_args__ = (
        Index("idx_conversion_raw_time", "conversion_time"),
        Index("idx_conversion_raw_cid", "cid"),
        Index("idx_conversion_raw_media", "media_id", "conversion_time"),
        Index("idx_conversion_raw_program", "program_id", "conversion_time"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    cid: Mapped[str | None] = mapped_column(Text)
    conversion_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    click_time: Mapped[datetime | None] = mapped_column(DateTime)
    media_id: Mapped[str | None] = mapped_column(Text)
    program_id: Mapped[str | None] = mapped_column(Text)
    user_id: Mapped[str | None] = mapped_column(Text)
    postback_ipaddress: Mapped[str | None] = mapped_column(Text)
    postback_useragent: Mapped[str | None] = mapped_column(Text)
    entry_ipaddress: Mapped[str | None] = mapped_column(Text)
    entry_useragent: Mapped[str | None] = mapped_column(Text)
    click_ipaddress: Mapped[str | None] = mapped_column(Text)
    click_useragent: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ConversionIpuaDaily(Base):
    __tablename__ = "conversion_ipua_daily"
    __table_args__ = (
        Index("idx_conversion_ipua_daily_date", "date"),
        Index("idx_conversion_ipua_daily_date_ip", "date", "ipaddress"),
        Index("idx_conversion_ipua_daily_date_ip_ua", "date", "ipaddress", "useragent"),
        Index("idx_conversion_ipua_daily_media", "date", "media_id"),
        Index("idx_conversion_ipua_daily_program", "date", "program_id"),
    )

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    media_id: Mapped[str] = mapped_column(Text, primary_key=True)
    program_id: Mapped[str] = mapped_column(Text, primary_key=True)
    ipaddress: Mapped[str] = mapped_column(Text, primary_key=True)
    useragent: Mapped[str] = mapped_column(Text, primary_key=True)
    conversion_count: Mapped[int] = mapped_column(Integer, nullable=False)
    first_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class CheckRaw(Base):
    __tablename__ = "check_raw"
    __table_args__ = (
        Index("idx_check_raw_time", "regist_time"),
        Index("idx_check_raw_user", "affiliate_user_id", "regist_time"),
        Index("idx_check_raw_state", "state", "regist_time"),
        Index("idx_check_raw_plid", "plid"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    affiliate_user_id: Mapped[str | None] = mapped_column(Text)
    plid: Mapped[str | None] = mapped_column(Text)
    state: Mapped[int | None] = mapped_column(Integer)
    regist_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    raw_payload: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class TrackRaw(Base):
    __tablename__ = "track_raw"
    __table_args__ = (
        Index("idx_track_raw_time", "regist_time"),
        Index("idx_track_raw_action", "action_log_raw_id"),
        Index("idx_track_raw_auth_type", "auth_type", "regist_time"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    action_log_raw_id: Mapped[str | None] = mapped_column(Text)
    auth_type: Mapped[str | None] = mapped_column(Text)
    auth_get_type: Mapped[str | None] = mapped_column(Text)
    state: Mapped[int | None] = mapped_column(Integer)
    regist_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    raw_payload: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ClickSumDaily(Base):
    __tablename__ = "click_sum_daily"
    __table_args__ = (
        Index("idx_click_sum_daily_date", "date"),
        Index("idx_click_sum_daily_user", "date", "user_id"),
        Index("idx_click_sum_daily_media", "date", "media_id"),
        Index("idx_click_sum_daily_promotion", "date", "promotion_id"),
    )

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    user_id: Mapped[str] = mapped_column(Text, primary_key=True)
    media_id: Mapped[str] = mapped_column(Text, primary_key=True)
    promotion_id: Mapped[str] = mapped_column(Text, primary_key=True)
    click_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class AccessSumDaily(Base):
    __tablename__ = "access_sum_daily"
    __table_args__ = (
        Index("idx_access_sum_daily_date", "date"),
        Index("idx_access_sum_daily_user", "date", "user_id"),
        Index("idx_access_sum_daily_media", "date", "media_id"),
        Index("idx_access_sum_daily_promotion", "date", "promotion_id"),
    )

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    user_id: Mapped[str] = mapped_column(Text, primary_key=True)
    media_id: Mapped[str] = mapped_column(Text, primary_key=True)
    promotion_id: Mapped[str] = mapped_column(Text, primary_key=True)
    access_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ImpSumDaily(Base):
    __tablename__ = "imp_sum_daily"
    __table_args__ = (
        Index("idx_imp_sum_daily_date", "date"),
        Index("idx_imp_sum_daily_user", "date", "user_id"),
        Index("idx_imp_sum_daily_media", "date", "media_id"),
        Index("idx_imp_sum_daily_promotion", "date", "promotion_id"),
    )

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    user_id: Mapped[str] = mapped_column(Text, primary_key=True)
    media_id: Mapped[str] = mapped_column(Text, primary_key=True)
    promotion_id: Mapped[str] = mapped_column(Text, primary_key=True)
    imp_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class MasterMedia(Base):
    __tablename__ = "master_media"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class MasterPromotion(Base):
    __tablename__ = "master_promotion"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str | None] = mapped_column(Text)
    action_double_state: Mapped[int | None] = mapped_column(Integer)
    action_double_type_json: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class MasterUser(Base):
    __tablename__ = "master_user"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class SettingsVersion(Base):
    __tablename__ = "settings_versions"
    __table_args__ = (
        Index("idx_settings_versions_created_at", "created_at"),
        Index("idx_settings_versions_fingerprint", "fingerprint"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class JobStatus(Base):
    __tablename__ = "job_status"
    __table_args__ = (CheckConstraint("id = 1", name="job_status_singleton"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    job_id: Mapped[str | None] = mapped_column(Text)
    message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    result_json: Mapped[str | None] = mapped_column(Text)


class JobRun(Base):
    __tablename__ = "job_runs"
    __table_args__ = (
        Index("idx_job_runs_status_queued_at", "status", "queued_at"),
        Index("idx_job_runs_job_type_queued_at", "job_type", "queued_at"),
        Index("idx_job_runs_locked_until", "locked_until"),
        Index("idx_job_runs_queue_scan", "status", "next_retry_at", "priority", "queued_at"),
        Index("idx_job_runs_dedupe_status", "dedupe_key", "status", "queued_at"),
        Index("idx_job_runs_concurrency_status", "concurrency_key", "status", "queued_at"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    job_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    params_json: Mapped[str | None] = mapped_column(Text)
    result_json: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    message: Mapped[str | None] = mapped_column(Text)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime)
    dedupe_key: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    concurrency_key: Mapped[str | None] = mapped_column(Text)
    queued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime)
    worker_id: Mapped[str | None] = mapped_column(Text)


class FindingsGeneration(Base):
    __tablename__ = "findings_generations"
    __table_args__ = (
        Index("idx_findings_generations_type_date_current", "finding_type", "target_date", "is_current"),
        Index("idx_findings_generations_generation_id", "generation_id"),
        Index("idx_findings_generations_settings_version", "settings_version_id"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    generation_id: Mapped[str] = mapped_column(Text, nullable=False)
    finding_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    computed_by_job_id: Mapped[str | None] = mapped_column(Text)
    settings_version_id: Mapped[str | None] = mapped_column(Text)
    settings_fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    detector_code_version: Mapped[str] = mapped_column(Text, nullable=False)
    source_click_watermark: Mapped[datetime | None] = mapped_column(DateTime)
    source_conversion_watermark: Mapped[datetime | None] = mapped_column(DateTime)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class SuspiciousConversionFindingRecord(Base):
    __tablename__ = "suspicious_conversion_findings"
    __table_args__ = (
        Index("idx_scof_date_current", "date", "is_current"),
        Index("idx_scof_date_current_risk", "date", "is_current", "risk_level"),
        Index("idx_scof_date_current_computed", "date", "is_current", "computed_at"),
        Index("idx_scof_case_current", "case_key", "is_current"),
    )

    finding_key: Mapped[str] = mapped_column(Text, primary_key=True)
    case_key: Mapped[str | None] = mapped_column(Text)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    ipaddress: Mapped[str] = mapped_column(Text, nullable=False)
    useragent: Mapped[str] = mapped_column(Text, nullable=False)
    ua_hash: Mapped[str] = mapped_column(Text, nullable=False)
    media_ids_json: Mapped[str | None] = mapped_column(Text)
    program_ids_json: Mapped[str | None] = mapped_column(Text)
    media_names_json: Mapped[str | None] = mapped_column(Text)
    program_names_json: Mapped[str | None] = mapped_column(Text)
    affiliate_ids_json: Mapped[str | None] = mapped_column(Text)
    affiliate_names_json: Mapped[str | None] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(Text, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    reasons_json: Mapped[str] = mapped_column(Text, nullable=False)
    reasons_formatted_json: Mapped[str] = mapped_column(Text, nullable=False)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False)
    total_conversions: Mapped[int] = mapped_column(Integer, nullable=False)
    media_count: Mapped[int] = mapped_column(Integer, nullable=False)
    program_count: Mapped[int] = mapped_column(Integer, nullable=False)
    min_click_to_conv_seconds: Mapped[int | None] = mapped_column(Integer)
    max_click_to_conv_seconds: Mapped[int | None] = mapped_column(Integer)
    first_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    rule_version: Mapped[str] = mapped_column(Text, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    computed_by_job_id: Mapped[str | None] = mapped_column(Text)
    settings_updated_at_snapshot: Mapped[datetime | None] = mapped_column(DateTime)
    source_click_watermark: Mapped[datetime | None] = mapped_column(DateTime)
    source_conversion_watermark: Mapped[datetime | None] = mapped_column(DateTime)
    estimated_damage_yen: Mapped[int | None] = mapped_column(Integer)
    damage_unit_price_source: Mapped[str | None] = mapped_column(Text)
    damage_evidence_json: Mapped[str | None] = mapped_column(Text)
    generation_id: Mapped[str | None] = mapped_column(Text)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    search_text: Mapped[str] = mapped_column(Text, nullable=False)


class FraudFindingRecord(Base):
    __tablename__ = "fraud_findings"
    __table_args__ = (
        Index("idx_ff_date_current", "date", "is_current"),
        Index("idx_ff_date_current_risk", "date", "is_current", "risk_level"),
        Index("idx_ff_date_current_entity", "date", "is_current", "user_id", "media_id", "promotion_id"),
        Index("idx_ff_date_current_computed", "date", "is_current", "computed_at"),
    )

    finding_key: Mapped[str] = mapped_column(Text, primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    user_id: Mapped[str] = mapped_column(Text, nullable=False)
    media_id: Mapped[str] = mapped_column(Text, nullable=False)
    promotion_id: Mapped[str] = mapped_column(Text, nullable=False)
    user_name: Mapped[str | None] = mapped_column(Text)
    media_name: Mapped[str | None] = mapped_column(Text)
    promotion_name: Mapped[str | None] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(Text, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    reasons_json: Mapped[str] = mapped_column(Text, nullable=False)
    reasons_formatted_json: Mapped[str] = mapped_column(Text, nullable=False)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False)
    primary_metric: Mapped[int] = mapped_column(Integer, nullable=False)
    first_time: Mapped[datetime | None] = mapped_column(DateTime)
    last_time: Mapped[datetime | None] = mapped_column(DateTime)
    rule_version: Mapped[str] = mapped_column(Text, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    computed_by_job_id: Mapped[str | None] = mapped_column(Text)
    settings_updated_at_snapshot: Mapped[datetime | None] = mapped_column(DateTime)
    source_click_watermark: Mapped[datetime | None] = mapped_column(DateTime)
    source_conversion_watermark: Mapped[datetime | None] = mapped_column(DateTime)
    generation_id: Mapped[str | None] = mapped_column(Text)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    search_text: Mapped[str] = mapped_column(Text, nullable=False)


class FraudAlertReview(Base):
    __tablename__ = "fraud_alert_reviews"
    __table_args__ = (
        Index("idx_fraud_alert_reviews_status_updated", "review_status", "updated_at"),
    )

    finding_key: Mapped[str] = mapped_column(Text, primary_key=True)
    review_status: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class FraudAlertReviewState(Base):
    __tablename__ = "fraud_alert_review_states"
    __table_args__ = (
        Index("idx_fraud_alert_review_states_status_updated", "review_status", "updated_at"),
    )

    case_key: Mapped[str] = mapped_column(Text, primary_key=True)
    review_status: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    reviewed_by: Mapped[str] = mapped_column(Text, nullable=False)
    reviewed_role: Mapped[str] = mapped_column(Text, nullable=False)
    source_surface: Mapped[str] = mapped_column(Text, nullable=False)
    request_id: Mapped[str] = mapped_column(Text, nullable=False)
    finding_key_at_review: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class FraudAlertReviewEvent(Base):
    __tablename__ = "fraud_alert_review_events"
    __table_args__ = (
        Index("idx_fraud_alert_review_events_case_reviewed", "case_key", "reviewed_at"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    case_key: Mapped[str] = mapped_column(Text, nullable=False)
    finding_key_at_review: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    reviewed_by: Mapped[str] = mapped_column(Text, nullable=False)
    reviewed_role: Mapped[str] = mapped_column(Text, nullable=False)
    source_surface: Mapped[str] = mapped_column(Text, nullable=False)
    request_id: Mapped[str] = mapped_column(Text, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
