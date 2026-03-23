from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from fraud_checker import api
from fraud_checker.api_routers import (
    health as health_router,
    jobs as jobs_router,
    masters as masters_router,
    reporting as reporting_router,
    settings as settings_router,
    suspicious as suspicious_router,
    testdata as testdata_router,
)
from fraud_checker.job_status_pg import JobStatus
from fraud_checker.models import SuspiciousFinding


def test_health_requires_admin_token(monkeypatch):
    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")
    client = TestClient(api.app)

    response = client.get("/api/health")

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_ingest_clicks_returns_japanese_message_for_invalid_date(monkeypatch):
    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")
    client = TestClient(api.app)

    response = client.post(
        "/api/ingest/clicks",
        headers={"X-API-Key": "secret"},
        json={"date": "2026-99-99"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "日付形式が不正です。YYYY-MM-DD を指定してください。"


def test_refresh_returns_conflict_when_job_is_running(monkeypatch):
    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")

    def raise_conflict(*args, **kwargs):
        raise api.JobConflictError("busy")

    monkeypatch.setattr(jobs_router, "enqueue_job", raise_conflict)
    client = TestClient(api.app)

    response = client.post(
        "/api/refresh",
        headers={"X-API-Key": "secret"},
        json={"hours": 1, "clicks": True, "conversions": True, "detect": False},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Another job is already running"


def test_refresh_returns_public_payload_when_request_is_accepted(monkeypatch):
    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")
    monkeypatch.setattr(
        jobs_router,
        "enqueue_job",
        lambda **kwargs: type("QueuedJob", (), {"id": "run-refresh-1"})(),
    )
    client = TestClient(api.app)

    response = client.post(
        "/api/refresh",
        headers={"X-API-Key": "secret"},
        json={"hours": 4, "clicks": True, "conversions": False, "detect": True},
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "直近4時間の再取得を開始しました",
        "details": {
            "job_id": "run-refresh-1",
            "hours": 4,
            "clicks": True,
            "conversions": False,
        },
    }


def test_suspicious_clicks_returns_business_friendly_fields(monkeypatch):
    first = datetime(2026, 1, 1, 10, 0, 0)

    class DummyRepo:
        def list_click_findings(self, **kwargs):
            return (
                [
                    {
                        "finding_key": "f-1",
                        "date": datetime(2026, 1, 1).date(),
                        "ipaddress": "8.8.8.8",
                        "useragent": "Mozilla/5.0 Chrome/120.0",
                        "total_clicks": 60,
                        "media_count": 2,
                        "program_count": 1,
                        "first_time": first,
                        "last_time": first + timedelta(seconds=120),
                        "reasons_json": [
                            "total_clicks >= 50",
                            "burst: 60 clicks in 120s (<= 600s)",
                        ],
                        "reasons_formatted_json": [
                            "クリック数が閾値以上です（50件以上）",
                            "短時間にクリックが集中しています（バースト検知）",
                        ],
                        "risk_level": "high",
                        "risk_score": 80,
                        "media_names_json": ["Media 1"],
                        "program_names_json": ["Program 1"],
                        "affiliate_names_json": ["Affiliate 1"],
                    }
                ],
                1,
            )

        def get_suspicious_click_details_bulk(self, target_date, pairs):
            return {("8.8.8.8", "Mozilla/5.0 Chrome/120.0"): []}

    monkeypatch.setattr(suspicious_router, "get_repository", lambda: DummyRepo())
    client = TestClient(api.app)

    response = client.get("/api/suspicious/clicks", params={"date": "2026-01-01", "include_names": False})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    row = payload["data"][0]
    assert row["risk_level"] == "high"
    assert row["risk_label"] == "高リスク"
    assert row["reasons_formatted"] == [
        "クリック数が閾値以上です（50件以上）",
        "短時間にクリックが集中しています（バースト検知）",
    ]


def test_suspicious_conversions_rejects_invalid_date(monkeypatch):
    monkeypatch.setattr(suspicious_router, "get_repository", lambda: object())
    client = TestClient(api.app)

    response = client.get("/api/suspicious/conversions", params={"date": "bad-date"})

    assert response.status_code == 400
    assert response.json()["detail"] == "日付形式が不正です。YYYY-MM-DD を指定してください。"


def test_suspicious_click_detail_returns_single_finding(monkeypatch):
    first = datetime(2026, 1, 1, 10, 0, 0)

    class DummyRepo:
        def get_click_finding_by_key(self, finding_key):
            assert finding_key == "f-1"
            return {
                "finding_key": "f-1",
                "date": datetime(2026, 1, 1).date(),
                "ipaddress": "8.8.8.8",
                "useragent": "Mozilla/5.0 Chrome/120.0",
                "total_clicks": 60,
                "media_count": 2,
                "program_count": 1,
                "first_time": first,
                "last_time": first + timedelta(seconds=120),
                "reasons_json": ["total_clicks >= 50"],
                "reasons_formatted_json": ["クリック数が閾値以上です（50件以上）"],
                "risk_level": "high",
                "risk_score": 80,
                "media_names_json": ["Media 1"],
                "program_names_json": ["Program 1"],
                "affiliate_names_json": ["Affiliate 1"],
            }

        def get_suspicious_click_details_bulk(self, target_date, pairs):
            return {
                ("8.8.8.8", "Mozilla/5.0 Chrome/120.0"): [
                    {
                        "media_id": "m1",
                        "program_id": "p1",
                        "media_name": "Media 1",
                        "program_name": "Program 1",
                        "affiliate_name": "Affiliate 1",
                        "click_count": 60,
                    }
                ]
            }

    monkeypatch.setattr(suspicious_router, "get_repository", lambda: DummyRepo())
    client = TestClient(api.app)

    response = client.get("/api/suspicious/clicks/f-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["finding_key"] == "f-1"
    assert payload["details"][0]["media_name"] == "Media 1"


def test_format_reasons_and_risk_scoring_reflect_business_priority():
    reasons = [
        "conversion_count >= 5",
        "burst: 5 conversions in 10s (<= 1800s)",
        "click_to_conversion_seconds <= 5s (min=1s)",
    ]

    formatted = api.format_reasons(reasons)
    risk = api.calculate_risk_level(reasons, count=5, is_conversion=True)

    assert formatted == [
        "成果数が閾値以上です（5件以上）",
        "短時間に成果が集中しています（バースト検知）",
        "クリックから成果までの時間が短すぎます（5秒以下）",
    ]
    assert risk == {"level": "high", "score": 135, "label": "高リスク"}


def test_root_returns_running_message():
    client = TestClient(api.app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"
    assert response.json()["storage"] == "postgresql"


def test_summary_endpoint_returns_payload(monkeypatch):
    monkeypatch.setattr(reporting_router, "get_repository", lambda: object())
    monkeypatch.setattr(
        reporting_router.reporting,
        "get_summary",
        lambda repo, target_date: {"date": "2026-01-03", "stats": {"clicks": {"total": 12}}},
    )
    client = TestClient(api.app)

    response = client.get("/api/summary", params={"target_date": "2026-01-03"})

    assert response.status_code == 200
    assert response.json()["date"] == "2026-01-03"


def test_daily_stats_endpoint_returns_data(monkeypatch):
    monkeypatch.setattr(reporting_router, "get_repository", lambda: object())
    monkeypatch.setattr(
        reporting_router.reporting,
        "get_daily_stats",
        lambda repo, limit: [{"date": "2026-01-03", "clicks": 10, "conversions": 2}],
    )
    client = TestClient(api.app)

    response = client.get("/api/stats/daily", params={"limit": 7})

    assert response.status_code == 200
    assert response.json()["data"][0]["date"] == "2026-01-03"


def test_suspicious_clicks_returns_empty_when_latest_date_is_missing(monkeypatch):
    monkeypatch.setattr(suspicious_router, "get_repository", lambda: object())
    monkeypatch.setattr(suspicious_router.reporting, "get_latest_date", lambda repo, table: None)
    client = TestClient(api.app)

    response = client.get("/api/suspicious/clicks")

    assert response.status_code == 200
    assert response.json() == {"date": "", "data": [], "total": 0, "limit": 500, "offset": 0}


def test_dates_endpoint_returns_available_dates(monkeypatch):
    monkeypatch.setattr(reporting_router, "get_repository", lambda: object())
    monkeypatch.setattr(reporting_router.reporting, "get_available_dates", lambda repo: ["2026-01-03", "2026-01-02"])
    client = TestClient(api.app)

    response = client.get("/api/dates")

    assert response.status_code == 200
    assert response.json()["dates"] == ["2026-01-03", "2026-01-02"]


def test_job_status_endpoint_returns_running_payload(monkeypatch):
    class DummyStore:
        def get(self):
            return JobStatus(
                status="running",
                job_id="refresh_1h",
                message="running",
                started_at="2026-01-01T00:00:00",
                completed_at=None,
                result=None,
            )

    monkeypatch.setattr(jobs_router, "get_job_store", lambda: DummyStore())
    client = TestClient(api.app)

    response = client.get("/api/job/status")

    assert response.status_code == 200
    assert response.json() == {
        "status": "running",
        "job_id": "refresh_1h",
        "message": "running",
        "started_at": "2026-01-01T00:00:00",
        "completed_at": None,
        "result": None,
    }


def test_job_status_endpoint_returns_failed_payload(monkeypatch):
    class DummyStore:
        def get(self):
            return JobStatus(
                status="failed",
                job_id="refresh_3h",
                message=None,
                started_at="2026-01-01T00:00:00",
                completed_at="2026-01-01T00:05:00",
                result={"success": False, "error": "boom"},
            )

    monkeypatch.setattr(jobs_router, "get_job_store", lambda: DummyStore())
    client = TestClient(api.app)

    response = client.get("/api/job/status")

    assert response.status_code == 200
    assert response.json() == {
        "status": "failed",
        "job_id": "refresh_3h",
        "message": "ジョブが失敗しました",
        "started_at": "2026-01-01T00:00:00",
        "completed_at": "2026-01-01T00:05:00",
        "result": {"success": False, "error": "boom"},
    }


def test_health_returns_warning_when_data_is_missing(monkeypatch):
    class DummyRepo:
        def fetch_one(self, query, params=None):
            return {"cnt": 0}

        def get_click_ipua_coverage(self, target_date):
            return None

        def get_conversion_click_enrichment(self, target_date):
            return None

        def get_all_masters(self):
            return {"media_count": 0, "promotion_count": 0, "user_count": 0, "last_synced_at": None}

    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/db")
    monkeypatch.setenv("ACS_BASE_URL", "https://acs.example.com")
    monkeypatch.setenv("ACS_TOKEN", "a:b")
    monkeypatch.setattr(health_router, "get_repository", lambda: DummyRepo())
    monkeypatch.setattr(
        health_router,
        "get_job_store",
        lambda: type("DummyStore", (), {"get_latest_successful_finished_at": lambda self, job_types: None})(),
    )
    client = TestClient(api.app)

    response = client.get("/api/health", headers={"X-API-Key": "secret"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "warning"
    assert len(payload["issues"]) >= 1
    assert payload["config"]["database_url_configured"] is True


def test_settings_endpoints_return_service_payloads(monkeypatch):
    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")
    monkeypatch.setattr(settings_router, "get_repository", lambda: object())
    monkeypatch.setattr(settings_router.settings_service, "get_settings", lambda repo: {"click_threshold": 44})
    monkeypatch.setattr(
        settings_router.settings_service,
        "update_settings",
        lambda repo, settings: {"success": True, "settings": settings, "persisted": True},
    )
    client = TestClient(api.app)

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

    assert get_response.status_code == 200
    assert get_response.json() == {"click_threshold": 44}
    assert post_response.status_code == 200
    assert post_response.json()["persisted"] is True


def test_sync_masters_returns_job_identifier(monkeypatch):
    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")
    monkeypatch.setattr(
        masters_router,
        "enqueue_job",
        lambda **kwargs: type("QueuedJob", (), {"id": "run-master-1"})(),
    )
    client = TestClient(api.app)

    response = client.post("/api/sync/masters", headers={"X-API-Key": "secret"})

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "マスタ同期を開始しました",
        "details": {"job_id": "run-master-1"},
    }


def test_masters_status_returns_repository_stats(monkeypatch):
    class DummyRepo:
        def get_all_masters(self):
            return {"media_count": 10, "promotion_count": 20, "user_count": 30}

    monkeypatch.setattr(masters_router, "get_repository", lambda: DummyRepo())
    client = TestClient(api.app)

    response = client.get("/api/masters/status")

    assert response.status_code == 200
    assert response.json()["user_count"] == 30


def test_test_data_endpoints_return_not_found_outside_test_env(monkeypatch):
    monkeypatch.setenv("FC_ENV", "development")
    monkeypatch.setenv("FC_E2E_TEST_KEY", "seed-key")
    client = TestClient(api.app)

    response = client.post("/api/test/reset", headers={"X-Test-Key": "seed-key"})

    assert response.status_code == 404


def test_test_data_endpoints_require_matching_test_key(monkeypatch):
    monkeypatch.setenv("FC_ENV", "test")
    monkeypatch.setenv("FC_E2E_TEST_KEY", "seed-key")
    client = TestClient(api.app)

    response = client.post("/api/test/reset", headers={"X-Test-Key": "wrong-key"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_reset_test_data_returns_success_payload(monkeypatch):
    monkeypatch.setenv("FC_ENV", "test")
    monkeypatch.setenv("FC_E2E_TEST_KEY", "seed-key")
    monkeypatch.setattr(testdata_router, "get_repository", lambda: object())
    monkeypatch.setattr(testdata_router.e2e_seed, "reset_all", lambda repo: {"deleted": {"click_ipua_daily": 0}})
    client = TestClient(api.app)

    response = client.post("/api/test/reset", headers={"X-Test-Key": "seed-key"})

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "テストデータの初期化が完了しました",
        "details": {"deleted": {"click_ipua_daily": 0}},
    }


def test_seed_baseline_endpoint_returns_seed_details(monkeypatch):
    monkeypatch.setenv("FC_ENV", "test")
    monkeypatch.setenv("FC_E2E_TEST_KEY", "seed-key")
    monkeypatch.setattr(testdata_router, "get_repository", lambda: object())
    monkeypatch.setattr(
        testdata_router.e2e_seed,
        "seed_baseline",
        lambda repo: {
            "target_date": "2026-01-21",
            "counts": {"click_ipua_daily": 57, "conversion_ipua_daily": 2},
        },
    )
    client = TestClient(api.app)

    response = client.post("/api/test/seed/baseline", headers={"X-Test-Key": "seed-key"})

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "ベースラインのテストデータを投入しました",
        "details": {
            "target_date": "2026-01-21",
            "counts": {"click_ipua_daily": 57, "conversion_ipua_daily": 2},
        },
    }
