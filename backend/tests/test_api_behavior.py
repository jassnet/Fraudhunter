from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from fraud_checker import api
from fraud_checker.job_status_pg import JobStatus
from fraud_checker.models import SuspiciousFinding


def test_health_requires_admin_token(monkeypatch):
    # Given
    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")
    client = TestClient(api.app)

    # When
    response = client.get("/api/health")

    # Then
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_ingest_clicks_rejects_invalid_date(monkeypatch):
    # Given
    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")
    client = TestClient(api.app)

    # When
    response = client.post(
        "/api/ingest/clicks",
        headers={"X-API-Key": "secret"},
        json={"date": "2026-99-99"},
    )

    # Then
    assert response.status_code == 400
    assert "Invalid date format" in response.json()["detail"]


def test_refresh_returns_conflict_when_job_is_running(monkeypatch):
    # Given
    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")

    def raise_conflict(*args, **kwargs):
        raise api.JobConflictError("busy")

    monkeypatch.setattr(api, "enqueue_job", raise_conflict)
    client = TestClient(api.app)

    # When
    response = client.post(
        "/api/refresh",
        headers={"X-API-Key": "secret"},
        json={"hours": 1, "clicks": True, "conversions": True, "detect": False},
    )

    # Then
    assert response.status_code == 409
    assert response.json()["detail"] == "Another job is already running"


def test_suspicious_clicks_returns_business_friendly_fields(monkeypatch):
    # Given
    class DummyDetector:
        def __init__(self, repo, rules):
            pass

        def find_for_date(self, target_date):
            first = datetime(2026, 1, 1, 10, 0, 0)
            return [
                SuspiciousFinding(
                    date=target_date,
                    ipaddress="8.8.8.8",
                    useragent="Mozilla/5.0 Chrome/120.0",
                    total_clicks=60,
                    media_count=2,
                    program_count=1,
                    first_time=first,
                    last_time=first + timedelta(seconds=120),
                    reasons=[
                        "total_clicks >= 50",
                        "burst: 60 clicks in 120s (<= 600s)",
                    ],
                )
            ]

    monkeypatch.setattr(api, "get_repository", lambda: object())
    monkeypatch.setattr(api.settings_service, "build_rule_sets", lambda repo: ("click_rules", "conv_rules"))
    monkeypatch.setattr(api, "SuspiciousDetector", DummyDetector)
    client = TestClient(api.app)

    # When
    response = client.get(
        "/api/suspicious/clicks",
        params={"date": "2026-01-01", "include_names": False},
    )

    # Then
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    row = payload["data"][0]
    assert row["risk_level"] == "high"
    assert row["risk_label"] == "高リスク"
    assert "クリック数過多（50回以上）" in row["reasons_formatted"]
    assert "短時間クリック集中（バースト検知）" in row["reasons_formatted"]


def test_suspicious_conversions_rejects_invalid_date(monkeypatch):
    # Given
    monkeypatch.setattr(api, "get_repository", lambda: object())
    client = TestClient(api.app)

    # When
    response = client.get("/api/suspicious/conversions", params={"date": "bad-date"})

    # Then
    assert response.status_code == 400
    assert "Invalid date format" in response.json()["detail"]


def test_format_reasons_and_risk_scoring_reflect_business_priority():
    # Given
    reasons = [
        "conversion_count >= 5",
        "burst: 5 conversions in 10s (<= 1800s)",
        "click_to_conversion_seconds <= 5s (min=1s)",
    ]

    # When
    formatted = api.format_reasons(reasons)
    risk = api.calculate_risk_level(reasons, count=5, is_conversion=True)

    # Then
    assert "成果数過多（5件以上）" in formatted
    assert "短時間成果集中（バースト検知）" in formatted
    assert "クリック→成果までが短すぎ（閾値5秒）" in formatted
    assert risk["level"] == "high"
    assert risk["score"] >= 80


def test_root_returns_running_message():
    # Given
    client = TestClient(api.app)

    # When
    response = client.get("/")

    # Then
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_refresh_accepts_request_when_job_can_be_enqueued(monkeypatch):
    # Given
    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")
    captured = {}

    def fake_enqueue_job(**kwargs):
        captured["job_id"] = kwargs["job_id"]
        return None

    monkeypatch.setattr(api, "enqueue_job", fake_enqueue_job)
    client = TestClient(api.app)

    # When
    response = client.post(
        "/api/refresh",
        headers={"X-API-Key": "secret"},
        json={"hours": 4, "clicks": True, "conversions": False, "detect": True},
    )

    # Then
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["details"]["hours"] == 4
    assert captured["job_id"] == "refresh_4h"


def test_summary_endpoint_returns_payload(monkeypatch):
    # Given
    monkeypatch.setattr(api, "get_repository", lambda: object())
    monkeypatch.setattr(
        api.reporting,
        "get_summary",
        lambda repo, target_date: {"date": "2026-01-03", "stats": {"clicks": {"total": 12}}},
    )
    client = TestClient(api.app)

    # When
    response = client.get("/api/summary", params={"target_date": "2026-01-03"})

    # Then
    assert response.status_code == 200
    assert response.json()["date"] == "2026-01-03"


def test_daily_stats_endpoint_returns_data(monkeypatch):
    # Given
    monkeypatch.setattr(api, "get_repository", lambda: object())
    monkeypatch.setattr(
        api.reporting,
        "get_daily_stats",
        lambda repo, limit: [{"date": "2026-01-03", "clicks": 10, "conversions": 2}],
    )
    client = TestClient(api.app)

    # When
    response = client.get("/api/stats/daily", params={"limit": 7})

    # Then
    assert response.status_code == 200
    assert response.json()["data"][0]["date"] == "2026-01-03"


def test_suspicious_clicks_returns_empty_when_latest_date_is_missing(monkeypatch):
    # Given
    monkeypatch.setattr(api, "get_repository", lambda: object())
    monkeypatch.setattr(api.reporting, "get_latest_date", lambda repo, table: None)
    client = TestClient(api.app)

    # When
    response = client.get("/api/suspicious/clicks")

    # Then
    assert response.status_code == 200
    assert response.json()["date"] == ""
    assert response.json()["total"] == 0


def test_dates_endpoint_returns_available_dates(monkeypatch):
    # Given
    monkeypatch.setattr(api, "get_repository", lambda: object())
    monkeypatch.setattr(api.reporting, "get_available_dates", lambda repo: ["2026-01-03", "2026-01-02"])
    client = TestClient(api.app)

    # When
    response = client.get("/api/dates")

    # Then
    assert response.status_code == 200
    assert response.json()["dates"] == ["2026-01-03", "2026-01-02"]


def test_job_status_endpoint_maps_store_status(monkeypatch):
    # Given
    class DummyStore:
        def __init__(self, status):
            self._status = status

        def get(self):
            return self._status

    running = JobStatus(
        status="running",
        job_id="refresh_1h",
        message="running",
        started_at="2026-01-01T00:00:00",
        completed_at=None,
        result=None,
    )
    monkeypatch.setattr(api, "get_job_store", lambda: DummyStore(running))
    client = TestClient(api.app)

    # When
    response = client.get("/api/job/status")

    # Then
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "running"
    assert payload["job_id"] == "refresh_1h"


def test_job_status_endpoint_returns_completed_payload(monkeypatch):
    # Given
    class DummyStore:
        def get(self):
            return JobStatus(
                status="completed",
                job_id="refresh_2h",
                message="done",
                started_at="2026-01-01T00:00:00",
                completed_at="2026-01-01T00:05:00",
                result={"success": True},
            )

    monkeypatch.setattr(api, "get_job_store", lambda: DummyStore())
    client = TestClient(api.app)

    # When
    response = client.get("/api/job/status")

    # Then
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["result"]["success"] is True


def test_job_status_endpoint_returns_failed_payload(monkeypatch):
    # Given
    class DummyStore:
        def get(self):
            return JobStatus(
                status="failed",
                job_id="refresh_3h",
                message="failed",
                started_at="2026-01-01T00:00:00",
                completed_at="2026-01-01T00:05:00",
                result={"success": False, "error": "boom"},
            )

    monkeypatch.setattr(api, "get_job_store", lambda: DummyStore())
    client = TestClient(api.app)

    # When
    response = client.get("/api/job/status")

    # Then
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["result"]["error"] == "boom"


def test_health_returns_warning_when_data_is_missing(monkeypatch):
    # Given
    class DummyRepo:
        def fetch_one(self, query, params=None):
            return {"cnt": 0}

    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/db")
    monkeypatch.setenv("ACS_BASE_URL", "https://acs.example.com")
    monkeypatch.setenv("ACS_TOKEN", "a:b")
    monkeypatch.setattr(api, "get_repository", lambda: DummyRepo())
    client = TestClient(api.app)

    # When
    response = client.get("/api/health", headers={"X-API-Key": "secret"})

    # Then
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "warning"
    assert len(payload["issues"]) >= 1


def test_settings_endpoints_use_service_layer(monkeypatch):
    # Given
    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")
    monkeypatch.setattr(api, "get_repository", lambda: object())
    monkeypatch.setattr(api.settings_service, "get_settings", lambda repo: {"click_threshold": 44})
    monkeypatch.setattr(
        api.settings_service,
        "update_settings",
        lambda repo, settings: {"success": True, "settings": settings, "persisted": True},
    )
    client = TestClient(api.app)

    # When
    get_response = client.get("/api/settings", headers={"X-API-Key": "secret"})
    post_response = client.post(
        "/api/settings",
        headers={"X-API-Key": "secret"},
        json={
            "click_threshold": 70,
            "media_threshold": 3,
            "program_threshold": 3,
            "burst_click_threshold": 20,
            "burst_window_seconds": 600,
            "conversion_threshold": 5,
            "conv_media_threshold": 2,
            "conv_program_threshold": 2,
            "burst_conversion_threshold": 3,
            "burst_conversion_window_seconds": 1800,
            "min_click_to_conv_seconds": 5,
            "max_click_to_conv_seconds": 2592000,
            "browser_only": False,
            "exclude_datacenter_ip": False,
        },
    )

    # Then
    assert get_response.status_code == 200
    assert get_response.json()["click_threshold"] == 44
    assert post_response.status_code == 200
    assert post_response.json()["persisted"] is True


def test_sync_masters_enqueues_background_job(monkeypatch):
    # Given
    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")
    called = {"value": False}

    def fake_enqueue_job(**kwargs):
        called["value"] = True
        assert kwargs["job_id"] == "sync_masters"

    monkeypatch.setattr(api, "enqueue_job", fake_enqueue_job)
    client = TestClient(api.app)

    # When
    response = client.post("/api/sync/masters", headers={"X-API-Key": "secret"})

    # Then
    assert response.status_code == 200
    assert called["value"] is True
    assert response.json()["details"]["job_id"] == "sync_masters"


def test_masters_status_returns_repository_stats(monkeypatch):
    # Given
    class DummyRepo:
        def get_all_masters(self):
            return {"media_count": 10, "promotion_count": 20, "user_count": 30}

    monkeypatch.setattr(api, "get_repository", lambda: DummyRepo())
    client = TestClient(api.app)

    # When
    response = client.get("/api/masters/status")

    # Then
    assert response.status_code == 200
    assert response.json()["user_count"] == 30


def test_test_data_endpoints_return_not_found_outside_test_env(monkeypatch):
    # Given
    monkeypatch.setenv("FC_ENV", "development")
    monkeypatch.setenv("FC_E2E_TEST_KEY", "seed-key")
    client = TestClient(api.app)

    # When
    response = client.post("/api/test/reset", headers={"X-Test-Key": "seed-key"})

    # Then
    assert response.status_code == 404


def test_test_data_endpoints_require_matching_test_key(monkeypatch):
    # Given
    monkeypatch.setenv("FC_ENV", "test")
    monkeypatch.setenv("FC_E2E_TEST_KEY", "seed-key")
    monkeypatch.setattr(api, "get_repository", lambda: object())
    monkeypatch.setattr(api.e2e_seed, "reset_all", lambda repo: {"deleted": {"click_ipua_daily": 0}})
    client = TestClient(api.app)

    # When
    response = client.post("/api/test/reset", headers={"X-Test-Key": "wrong-key"})

    # Then
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_seed_baseline_endpoint_returns_seed_details(monkeypatch):
    # Given
    monkeypatch.setenv("FC_ENV", "test")
    monkeypatch.setenv("FC_E2E_TEST_KEY", "seed-key")
    monkeypatch.setattr(api, "get_repository", lambda: object())
    monkeypatch.setattr(
        api.e2e_seed,
        "seed_baseline",
        lambda repo: {
            "target_date": "2026-01-21",
            "counts": {"click_ipua_daily": 57, "conversion_ipua_daily": 2},
        },
    )
    client = TestClient(api.app)

    # When
    response = client.post("/api/test/seed/baseline", headers={"X-Test-Key": "seed-key"})

    # Then
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["details"]["target_date"] == "2026-01-21"
    assert payload["details"]["counts"]["click_ipua_daily"] == 57


def test_extract_bearer_parses_authorization_header():
    # Given / When / Then
    assert api._extract_bearer("Bearer token-123") == "token-123"
    assert api._extract_bearer("bearer token-456") == "token-456"
    assert api._extract_bearer("Token raw") is None
    assert api._extract_bearer(None) is None


def test_require_admin_allows_dev_mode_without_admin_key(monkeypatch):
    # Given
    monkeypatch.delenv("FC_ADMIN_API_KEY", raising=False)
    monkeypatch.setenv("FC_ENV", "development")

    # When / Then
    api.require_admin(x_api_key=None, authorization=None)


def test_require_admin_raises_in_production_without_admin_key(monkeypatch):
    # Given
    monkeypatch.delenv("FC_ADMIN_API_KEY", raising=False)
    monkeypatch.delenv("FC_ALLOW_INSECURE_ADMIN", raising=False)
    monkeypatch.setenv("FC_ENV", "production")

    # When / Then
    with pytest.raises(HTTPException) as exc:
        api.require_admin(x_api_key=None, authorization=None)
    assert exc.value.status_code == 500


def test_filter_findings_matches_media_name_when_include_names_enabled():
    # Given
    class Finding:
        ipaddress = "1.1.1.1"
        useragent = "Mozilla/5.0"

    findings = [Finding()]
    details_cache = {
        ("1.1.1.1", "Mozilla/5.0"): [{"media_name": "Summer Campaign", "program_name": "A"}]
    }

    # When
    filtered = api._filter_findings(findings, details_cache, search="summer", include_names=True)

    # Then
    assert len(filtered) == 1


def test_format_dt_serializes_datetime_and_string():
    # Given
    dt = datetime(2026, 1, 1, 0, 0, 0)

    # When / Then
    assert api._format_dt(dt) == "2026-01-01T00:00:00"
    assert api._format_dt("2026-01-01T00:00:00") == "2026-01-01T00:00:00"
    assert api._format_dt(123) is None
