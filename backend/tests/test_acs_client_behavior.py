from __future__ import annotations

import json
from datetime import date, datetime

import pytest
import requests

from fraud_checker.acs_client import AcsHttpClient


class _DummyResponse:
    def __init__(self, status_code: int, body, *, url: str = "https://acs.example.com/api", text: str = ""):
        self.status_code = status_code
        self._body = body
        self.url = url
        self.text = text or (json.dumps(body) if isinstance(body, dict) else str(body))

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body

    def raise_for_status(self):
        raise requests.HTTPError(f"status={self.status_code}")


class _DummySession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def get(self, url, headers=None, params=None, timeout=None):
        self.calls.append(
            {
                "url": url,
                "headers": headers or {},
                "params": params or {},
                "timeout": timeout,
            }
        )
        if not self._responses:
            raise AssertionError("No dummy response left")
        return self._responses.pop(0)


def test_fetch_click_logs_returns_click_models_and_auth_header():
    # Given
    session = _DummySession(
        [
            _DummyResponse(
                200,
                {
                    "records": [
                        {
                            "track_cid": "cid-1",
                            "regist_unix": "2026-01-01 10:00:00",
                            "media_id": "m1",
                            "program_id": "p1",
                            "ipaddress": "1.1.1.1",
                            "useragent": "Mozilla/5.0",
                            "referrer": "https://example.com",
                        }
                    ]
                },
            )
        ]
    )
    client = AcsHttpClient(
        base_url="https://acs.example.com/",
        access_key="access",
        secret_key="secret",
        endpoint_path="/track_log/search",
        session=session,
        timeout=12,
    )

    # When
    rows = list(client.fetch_click_logs(date(2026, 1, 1), page=2, limit=100))

    # Then
    assert len(rows) == 1
    assert rows[0].click_id == "cid-1"
    assert rows[0].media_id == "m1"
    assert rows[0].program_id == "p1"
    assert rows[0].ipaddress == "1.1.1.1"
    assert rows[0].useragent == "Mozilla/5.0"
    call = session.calls[0]
    assert call["url"] == "https://acs.example.com/track_log/search"
    assert call["headers"]["X-Auth-Token"] == "access:secret"
    assert call["params"]["offset"] == 100
    assert call["timeout"] == 12


def test_fetch_click_logs_raises_http_error_when_status_is_not_200():
    # Given
    session = _DummySession([_DummyResponse(500, {"error": "ng"}, text="internal error")])
    client = AcsHttpClient(
        base_url="https://acs.example.com",
        access_key="access",
        secret_key="secret",
        session=session,
        retry_attempts=1,
    )

    # When / Then
    with pytest.raises(requests.HTTPError):
        list(client.fetch_click_logs(date(2026, 1, 1), page=1, limit=100))


def test_fetch_click_logs_retries_then_succeeds():
    session = _DummySession(
        [
            _DummyResponse(500, {"error": "ng"}, text="internal error"),
            _DummyResponse(200, {"records": []}),
        ]
    )
    client = AcsHttpClient(
        base_url="https://acs.example.com",
        access_key="access",
        secret_key="secret",
        session=session,
        retry_attempts=2,
        retry_backoff_seconds=0,
    )

    rows = list(client.fetch_click_logs(date(2026, 1, 1), page=1, limit=100))

    assert rows == []
    assert len(session.calls) == 2


def test_ping_returns_latency_payload():
    session = _DummySession([_DummyResponse(200, {"records": []})])
    client = AcsHttpClient(
        base_url="https://acs.example.com",
        access_key="access",
        secret_key="secret",
        session=session,
    )

    payload = client.ping()

    assert payload["ok"] is True
    assert isinstance(payload["latency_ms"], float)


def test_fetch_conversion_logs_maps_entry_fields():
    # Given
    session = _DummySession(
        [
            _DummyResponse(
                200,
                {
                    "records": [
                        {
                            "id": "conv-1",
                            "check_log_raw": "cid-1",
                            "regist_unix": "2026-01-01 12:00:00",
                            "click_unix": "2026-01-01 11:59:50",
                            "media": "m1",
                            "promotion": "p1",
                            "user": "u1",
                            "ipaddress": "10.0.0.1",
                            "useragent": "postback-agent",
                            "entry_ipaddress": "2.2.2.2",
                            "entry_useragent": "Mozilla/5.0",
                            "state": "approved",
                        }
                    ]
                },
            )
        ]
    )
    client = AcsHttpClient(
        base_url="https://acs.example.com",
        access_key="access",
        secret_key="secret",
        session=session,
    )

    # When
    rows = list(client.fetch_conversion_logs(date(2026, 1, 1), page=1, limit=200))

    # Then
    assert len(rows) == 1
    item = rows[0]
    assert item.conversion_id == "conv-1"
    assert item.cid == "cid-1"
    assert item.media_id == "m1"
    assert item.program_id == "p1"
    assert item.entry_ipaddress == "2.2.2.2"
    assert item.entry_useragent == "Mozilla/5.0"
    assert item.state == "approved"


def test_fetch_click_logs_for_time_range_uses_date_bounds():
    # Given
    session = _DummySession([_DummyResponse(200, {"records": []})])
    client = AcsHttpClient(
        base_url="https://acs.example.com",
        access_key="access",
        secret_key="secret",
        endpoint_path="track_log/search",
        session=session,
    )
    start = datetime(2026, 1, 1, 23, 0, 0)
    end = datetime(2026, 1, 2, 1, 0, 0)

    # When
    rows = list(client.fetch_click_logs_for_time_range(start, end, page=1, limit=50))

    # Then
    assert rows == []
    params = session.calls[0]["params"]
    assert params["regist_unix_A_Y"] == 2026
    assert params["regist_unix_A_D"] == 1
    assert params["regist_unix_B_D"] == 2


def test_fetch_conversion_logs_for_time_range_uses_date_bounds():
    # Given
    session = _DummySession([_DummyResponse(200, {"records": []})])
    client = AcsHttpClient(
        base_url="https://acs.example.com",
        access_key="access",
        secret_key="secret",
        session=session,
    )
    start = datetime(2026, 1, 1, 23, 0, 0)
    end = datetime(2026, 1, 2, 1, 0, 0)

    # When
    rows = list(client.fetch_conversion_logs_for_time_range(start, end, page=1, limit=50))

    # Then
    assert rows == []
    params = session.calls[0]["params"]
    assert params["regist_unix_A_D"] == 1
    assert params["regist_unix_B_D"] == 2


def test_fetch_master_endpoints_map_records():
    # Given
    session = _DummySession(
        [
            _DummyResponse(200, {"records": [{"id": "m1", "name": "Media", "user": "u1", "state": "on"}]}),
            _DummyResponse(200, {"records": [{"id": "p1", "name": "Promo", "state": "on"}]}),
            _DummyResponse(200, {"records": [{"id": "u1", "name": "User", "company": "Acme", "state": "on"}]}),
        ]
    )
    client = AcsHttpClient(
        base_url="https://acs.example.com",
        access_key="access",
        secret_key="secret",
        session=session,
    )

    # When
    media = client.fetch_media_master()
    promos = client.fetch_promotion_master()
    users = client.fetch_user_master()

    # Then
    assert media == [{"id": "m1", "name": "Media", "user": "u1", "state": "on"}]
    assert promos == [
        {
            "id": "p1",
            "name": "Promo",
            "state": "on",
            "action_double_state": None,
            "action_double_type_json": None,
        }
    ]
    assert users == [{"id": "u1", "name": "User", "company": "Acme", "state": "on"}]


def test_fetch_all_master_methods_iterate_pages_until_short_page():
    # Given
    client = AcsHttpClient(
        base_url="https://acs.example.com",
        access_key="access",
        secret_key="secret",
    )
    calls = {"media": [], "promo": [], "user": []}

    def fake_media(page=1, limit=500):
        calls["media"].append(page)
        return [{"id": "m"}] * 500 if page == 1 else [{"id": "m2"}]

    def fake_promo(page=1, limit=500):
        calls["promo"].append(page)
        return [{"id": "p"}] * 500 if page == 1 else []

    def fake_user(page=1, limit=500):
        calls["user"].append(page)
        return [{"id": "u"}]

    client.fetch_media_master = fake_media  # type: ignore[method-assign]
    client.fetch_promotion_master = fake_promo  # type: ignore[method-assign]
    client.fetch_user_master = fake_user  # type: ignore[method-assign]

    # When
    all_media = client.fetch_all_media_master()
    all_promos = client.fetch_all_promotion_master()
    all_users = client.fetch_all_user_master()

    # Then
    assert len(all_media) == 501
    assert len(all_promos) == 500
    assert len(all_users) == 1
    assert calls["media"] == [1, 2]
    assert calls["promo"] == [1, 2]
    assert calls["user"] == [1]
