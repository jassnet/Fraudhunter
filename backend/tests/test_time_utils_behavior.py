from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import fraud_checker.time_utils as time_utils


def test_timezone_name_uses_default_when_env_is_missing(monkeypatch):
    # Given
    monkeypatch.delenv("FRAUD_TIMEZONE", raising=False)

    # When
    name = time_utils._timezone_name()

    # Then
    assert name == time_utils.DEFAULT_TIMEZONE


def test_timezone_name_trims_whitespace(monkeypatch):
    # Given
    monkeypatch.setenv("FRAUD_TIMEZONE", "  UTC  ")

    # When
    name = time_utils._timezone_name()

    # Then
    assert name == "UTC"


def test_get_timezone_falls_back_to_utc_when_resolution_fails(monkeypatch):
    # Given
    monkeypatch.setattr(time_utils, "_timezone_name", lambda: "Bad/Zone")
    monkeypatch.setattr(time_utils, "_get_tz", lambda name: (_ for _ in ()).throw(RuntimeError("bad tz")))

    # When
    tz = time_utils.get_timezone()

    # Then
    assert tz == timezone.utc


def test_now_local_returns_naive_datetime():
    # When
    now = time_utils.now_local()

    # Then
    assert isinstance(now, datetime)
    assert now.tzinfo is None


def test_parse_datetime_keeps_naive_datetime_as_is():
    # Given
    value = datetime(2026, 1, 1, 10, 0, 0)

    # When
    parsed = time_utils.parse_datetime(value)

    # Then
    assert parsed == value


def test_parse_datetime_converts_aware_datetime_to_local_naive(monkeypatch):
    # Given
    aware = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(time_utils, "get_timezone", lambda: ZoneInfo("Asia/Tokyo"))

    # When
    parsed = time_utils.parse_datetime(aware)

    # Then
    assert parsed == datetime(2026, 1, 1, 9, 0, 0)
    assert parsed.tzinfo is None


def test_parse_datetime_handles_epoch_seconds_and_milliseconds(monkeypatch):
    # Given
    monkeypatch.setattr(time_utils, "get_timezone", lambda: timezone.utc)
    sec = 1704067200
    msec = 1704067200000

    # When
    parsed_sec = time_utils.parse_datetime(sec)
    parsed_msec = time_utils.parse_datetime(msec)

    # Then
    assert parsed_sec == datetime(2024, 1, 1, 0, 0, 0)
    assert parsed_msec == datetime(2024, 1, 1, 0, 0, 0)


def test_parse_datetime_handles_iso_and_plain_format_strings(monkeypatch):
    # Given
    monkeypatch.setattr(time_utils, "get_timezone", lambda: timezone.utc)

    # When
    iso = time_utils.parse_datetime("2026-01-01T10:00:00Z")
    plain = time_utils.parse_datetime("2026-01-01 10:00:00")

    # Then
    assert iso == datetime(2026, 1, 1, 10, 0, 0)
    assert plain == datetime(2026, 1, 1, 10, 0, 0)


def test_parse_datetime_returns_now_for_invalid_or_empty_values(monkeypatch):
    # Given
    fixed = datetime(2026, 2, 2, 2, 2, 2)
    monkeypatch.setattr(time_utils, "now_local", lambda: fixed)

    # When
    parsed_empty = time_utils.parse_datetime("")
    parsed_invalid = time_utils.parse_datetime("not-a-date")
    parsed_other = time_utils.parse_datetime(object())

    # Then
    assert parsed_empty == fixed
    assert parsed_invalid == fixed
    assert parsed_other == fixed


def test_parse_numeric_and_normalize_epoch_cover_edge_cases():
    # When / Then
    assert time_utils._parse_numeric("12.5") == 12.5
    assert time_utils._parse_numeric("abc") is None
    assert time_utils._normalize_epoch(123.0) == 123.0
    assert time_utils._normalize_epoch(1e11) == 1e8


def test_today_local_uses_configured_timezone(monkeypatch):
    # Given
    class _FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 1, 1, 23, 30, tzinfo=timezone.utc).astimezone(tz)

    monkeypatch.setattr(time_utils, "datetime", _FixedDateTime)
    monkeypatch.setattr(time_utils, "get_timezone", lambda: timezone(timedelta(hours=9)))

    # When
    today = time_utils.today_local()

    # Then
    assert str(today) == "2026-01-02"
