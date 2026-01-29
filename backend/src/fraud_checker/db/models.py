from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, Text
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
