from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from fraud_checker import api
from fraud_checker import api_presenters
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


def test_health_requires_admin_token(monkeypatch):
    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")
    client = TestClient(api.app)

    response = client.get("/api/health")

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_public_health_is_available_without_auth(monkeypatch):
    monkeypatch.setenv("FC_ALLOW_PUBLIC_READ", "true")
    client = TestClient(api.app)

    response = client.get("/api/health/public")

    assert response.status_code == 200
    assert response.json()["service"] == "fraud-checker-api"
    assert response.json()["storage"] == "postgresql"


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


def test_refresh_returns_public_payload_when_request_is_accepted(monkeypatch):
    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")
    monkeypatch.setattr(
        jobs_router,
        "enqueue_refresh_job",
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
        "message": "直近4時間の再取得ジョブを登録しました",
        "details": {
            "job_id": "run-refresh-1",
            "hours": 4,
            "clicks": True,
            "conversions": False,
        },
    }


def test_refresh_returns_existing_job_id_when_enqueue_dedupes(monkeypatch):
    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")
    monkeypatch.setattr(
        jobs_router,
        "enqueue_refresh_job",
        lambda **kwargs: type("QueuedJob", (), {"id": "run-refresh-existing"})(),
    )
    client = TestClient(api.app)

    response = client.post(
        "/api/refresh",
        headers={"X-API-Key": "secret"},
        json={"hours": 1, "clicks": True, "conversions": True, "detect": False},
    )

    assert response.status_code == 200
    assert response.json()["details"]["job_id"] == "run-refresh-existing"


def _deprecated_test_suspicious_clicks_returns_business_friendly_fields(monkeypatch):
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
    assert row["ipaddress"] == "8.8.x.x"
    assert row["sensitive_values_masked"] is True
    assert row["risk_level"] == "high"
    assert row["risk_label"] == "高リスク"
    assert row["reasons_formatted"] == [
        "クリック数が閾値以上です（50件以上）",
        "短時間にクリックが集中しています（バースト検知）",
    ]


def test_suspicious_conversions_include_click_padding_metrics_from_metrics_json(monkeypatch):
    first = datetime(2026, 1, 1, 10, 0, 0)

    class DummyRepo:
        def list_conversion_findings(self, **kwargs):
            return (
                [
                    {
                        "finding_key": "cv-1",
                        "date": datetime(2026, 1, 1).date(),
                        "ipaddress": "9.9.9.9",
                        "useragent": "Mozilla/5.0 Chrome/120.0",
                        "total_conversions": 6,
                        "media_count": 2,
                        "program_count": 2,
                        "first_time": first,
                        "last_time": first + timedelta(seconds=60),
                        "reasons_json": [
                            "program_count >= 2",
                            "click_padding_linked_ratio >= 2.0 (actual=2.50)",
                        ],
                        "reasons_formatted_json": [
                            "同一 IP/UA で複数案件にまたがる成果があります（2案件以上）",
                            "不審CVに紐づくクリック数が多すぎます（CVあたり2.0件以上）",
                        ],
                        "metrics_json": {
                            "linked_click_count": 15,
                            "linked_clicks_per_conversion": 2.5,
                            "extra_window_click_count": 12,
                            "extra_window_non_browser_ratio": 0.75,
                        },
                        "risk_level": "high",
                        "risk_score": 140,
                        "media_names_json": ["Media 1"],
                        "program_names_json": ["Program 1"],
                        "affiliate_names_json": ["Affiliate 1"],
                    }
                ],
                1,
            )

        def get_suspicious_conversion_details_bulk(self, target_date, pairs):
            return {("9.9.9.9", "Mozilla/5.0 Chrome/120.0"): []}

    monkeypatch.setattr(suspicious_router, "get_repository", lambda: DummyRepo())
    client = TestClient(api.app)

    response = client.get("/api/suspicious/conversions", params={"date": "2026-01-01", "include_names": False})

    assert response.status_code == 200
    payload = response.json()
    row = payload["data"][0]
    assert row["linked_click_count"] == 15
    assert row["linked_clicks_per_conversion"] == 2.5
    assert row["extra_window_click_count"] == 12
    assert row["extra_window_non_browser_ratio"] == 0.75


def test_suspicious_conversions_rejects_invalid_date(monkeypatch):
    monkeypatch.setattr(suspicious_router, "get_repository", lambda: object())
    client = TestClient(api.app)

    response = client.get("/api/suspicious/conversions", params={"date": "bad-date"})

    assert response.status_code == 400
    assert response.json()["detail"] == "日付形式が不正です。YYYY-MM-DD を指定してください。"


def _deprecated_test_suspicious_click_detail_returns_single_finding(monkeypatch):
    first = datetime(2026, 1, 1, 10, 0, 0)
    captured = {}

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

    def fake_log_event(logger, event, **fields):
        captured["event"] = event
        captured["fields"] = fields

    monkeypatch.setattr(suspicious_router, "get_repository", lambda: DummyRepo())
    monkeypatch.setattr(suspicious_router, "log_event", fake_log_event)
    monkeypatch.setattr(
        suspicious_router.suspicious_service.lifecycle,
        "describe_evidence_availability",
        lambda target_date: {
            "evidence_status": "available",
            "evidence_available": True,
            "evidence_expired": False,
            "evidence_retention_days": 90,
            "evidence_expires_on": "2026-03-31",
            "evidence_checked_on": "2026-01-01",
        },
    )
    client = TestClient(api.app)

    response = client.get("/api/suspicious/clicks/f-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["finding_key"] == "f-1"
    assert payload["ipaddress"] == "8.8.8.8"
    assert payload["sensitive_values_masked"] is False
    assert payload["details"][0]["media_name"] == "Media 1"
    assert captured["event"] == "sensitive_detail_access"
    assert captured["fields"]["finding_key"] == "f-1"
    assert captured["fields"]["finding_type"] == "click"
    assert captured["fields"]["access_level"] == "analyst"
    assert captured["fields"]["unmasked_access"] is True


def test_suspicious_conversion_detail_includes_click_padding_metrics(monkeypatch):
    first = datetime(2026, 1, 1, 10, 0, 0)

    class DummyRepo:
        def get_conversion_finding_by_key(self, finding_key):
            assert finding_key == "cv-1"
            return {
                "finding_key": "cv-1",
                "date": datetime(2026, 1, 1).date(),
                "ipaddress": "9.9.9.9",
                "useragent": "Mozilla/5.0 Chrome/120.0",
                "total_conversions": 6,
                "media_count": 2,
                "program_count": 2,
                "first_time": first,
                "last_time": first + timedelta(seconds=60),
                "reasons_json": ["click_padding_linked_ratio >= 2.0 (actual=2.50)"],
                "reasons_formatted_json": [
                    "不審CVに紐づくクリック数が多すぎます（CVあたり2.0件以上）"
                ],
                "metrics_json": {
                    "linked_click_count": 15,
                    "linked_clicks_per_conversion": 2.5,
                    "extra_window_click_count": 12,
                    "extra_window_non_browser_ratio": 0.75,
                },
                "risk_level": "high",
                "risk_score": 140,
                "media_names_json": ["Media 1"],
                "program_names_json": ["Program 1"],
                "affiliate_names_json": ["Affiliate 1"],
            }

        def get_suspicious_conversion_details_bulk(self, target_date, pairs):
            return {
                ("9.9.9.9", "Mozilla/5.0 Chrome/120.0"): [
                    {
                        "media_id": "m1",
                        "program_id": "p1",
                        "media_name": "Media 1",
                        "program_name": "Program 1",
                        "affiliate_name": "Affiliate 1",
                        "conversion_count": 6,
                    }
                ]
            }

    monkeypatch.setattr(suspicious_router, "get_repository", lambda: DummyRepo())
    monkeypatch.setattr(
        suspicious_router.suspicious_service.lifecycle,
        "describe_evidence_availability",
        lambda target_date: {
            "evidence_status": "available",
            "evidence_available": True,
            "evidence_expired": False,
            "evidence_retention_days": 90,
            "evidence_expires_on": "2026-03-31",
            "evidence_checked_on": "2026-01-01",
        },
    )
    client = TestClient(api.app)

    response = client.get("/api/suspicious/conversions/cv-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["linked_click_count"] == 15
    assert payload["linked_clicks_per_conversion"] == 2.5
    assert payload["extra_window_click_count"] == 12
    assert payload["extra_window_non_browser_ratio"] == 0.75


def _deprecated_test_suspicious_click_detail_masks_values_when_evidence_has_expired(monkeypatch):
    first = datetime(2025, 1, 1, 10, 0, 0)
    captured = {}

    class DummyRepo:
        def get_click_finding_by_key(self, finding_key):
            return {
                "finding_key": finding_key,
                "date": datetime(2025, 1, 1).date(),
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
            raise AssertionError("expired evidence should not load supporting details")

    def fake_log_event(logger, event, **fields):
        captured["event"] = event
        captured["fields"] = fields

    monkeypatch.setattr(suspicious_router, "get_repository", lambda: DummyRepo())
    monkeypatch.setattr(suspicious_router, "log_event", fake_log_event)
    monkeypatch.setattr(
        suspicious_router.lifecycle,
        "describe_evidence_availability",
        lambda target_date: {
            "evidence_status": "expired",
            "evidence_available": False,
            "evidence_expired": True,
            "evidence_retention_days": 90,
            "evidence_expires_on": "2025-04-01",
            "evidence_checked_on": "2025-06-01",
        },
    )
    client = TestClient(api.app)

    response = client.get("/api/suspicious/clicks/f-legacy")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ipaddress"] == "8.8.x.x"
    assert payload["sensitive_values_masked"] is True
    assert payload["evidence_status"] == "expired"
    assert payload["evidence_expired"] is True
    assert "details" not in payload
    assert captured["fields"]["unmasked_access"] is False


def test_format_reasons_and_risk_scoring_reflect_business_priority():
    reasons = [
        "conversion_count >= 5",
        "burst: 5 conversions in 10s (<= 1800s)",
        "click_to_conversion_seconds <= 5s (min=1s)",
    ]

    formatted = api_presenters.format_reasons(reasons)
    risk = api_presenters.calculate_risk_level(reasons, count=5, is_conversion=True)

    assert formatted == [
        "成果数が閾値以上です（5件以上）",
        "短時間に成果が集中しています（バースト検知）",
        "クリックから成果までの時間が短すぎます（5秒以下）",
    ]
    assert risk == {"level": "high", "score": 150, "label": "高リスク"}


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
        lambda repo, target_date: {
            "date": "2026-01-03",
            "stats": {"clicks": {"total": 12}},
            "quality": {"findings": {"stale": True}},
        },
    )
    client = TestClient(api.app)

    response = client.get("/api/summary", params={"target_date": "2026-01-03"})

    assert response.status_code == 200
    assert response.json()["date"] == "2026-01-03"
    assert response.json()["quality"]["findings"]["stale"] is True


def test_summary_endpoint_requires_read_api_key_when_enabled(monkeypatch):
    monkeypatch.setenv("FC_REQUIRE_READ_AUTH", "true")
    monkeypatch.setenv("FC_READ_API_KEY", "read-secret")
    monkeypatch.setattr(reporting_router, "get_repository", lambda: object())
    monkeypatch.setattr(
        reporting_router.reporting,
        "get_summary",
        lambda repo, target_date: {"date": "2026-01-03", "stats": {"clicks": {"total": 12}}},
    )
    client = TestClient(api.app)

    unauthorized = client.get("/api/summary", params={"target_date": "2026-01-03"})
    authorized = client.get(
        "/api/summary",
        params={"target_date": "2026-01-03"},
        headers={"X-Read-API-Key": "read-secret"},
    )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200


def test_read_auth_matrix_distinguishes_analyst_and_admin_only_endpoints(monkeypatch):
    monkeypatch.setenv("FC_REQUIRE_READ_AUTH", "true")
    monkeypatch.setenv("FC_READ_API_KEY", "read-secret")
    monkeypatch.setenv("FC_ADMIN_API_KEY", "admin-secret")
    monkeypatch.setattr(reporting_router, "get_repository", lambda: object())
    monkeypatch.setattr(reporting_router.reporting, "get_summary", lambda repo, target_date: {"date": "2026-01-03", "stats": {}})
    monkeypatch.setattr(settings_router, "get_repository", lambda: object())
    monkeypatch.setattr(settings_router.settings_service, "get_settings", lambda repo: {"click_threshold": 44})
    client = TestClient(api.app)

    summary_without_auth = client.get("/api/summary")
    summary_with_read = client.get("/api/summary", headers={"X-Read-API-Key": "read-secret"})
    settings_with_read = client.get("/api/settings", headers={"X-Read-API-Key": "read-secret"})
    settings_with_admin = client.get("/api/settings", headers={"X-API-Key": "admin-secret"})

    assert summary_without_auth.status_code == 401
    assert summary_with_read.status_code == 200
    assert settings_with_read.status_code == 401
    assert settings_with_admin.status_code == 200


def test_daily_stats_endpoint_returns_data(monkeypatch):
    monkeypatch.setattr(reporting_router, "get_repository", lambda: object())
    monkeypatch.setattr(
        reporting_router.reporting,
        "get_daily_stats",
        lambda repo, limit, target_date=None: [{"date": "2026-01-03", "clicks": 10, "conversions": 2}],
    )
    client = TestClient(api.app)

    response = client.get("/api/stats/daily", params={"limit": 7})

    assert response.status_code == 200
    assert response.json()["data"][0]["date"] == "2026-01-03"


def test_daily_stats_endpoint_forwards_target_date(monkeypatch):
    captured = {}

    def fake_get_daily_stats(repo, limit, target_date=None):
      captured["limit"] = limit
      captured["target_date"] = target_date
      return [{"date": "2026-01-10", "clicks": 10, "conversions": 2}]

    monkeypatch.setattr(reporting_router, "get_repository", lambda: object())
    monkeypatch.setattr(reporting_router.reporting, "get_daily_stats", fake_get_daily_stats)
    client = TestClient(api.app)

    response = client.get("/api/stats/daily", params={"limit": 14, "target_date": "2026-01-10"})

    assert response.status_code == 200
    assert captured == {"limit": 14, "target_date": "2026-01-10"}


def _deprecated_test_suspicious_clicks_returns_empty_when_latest_date_is_missing(monkeypatch):
    monkeypatch.setattr(suspicious_router, "get_repository", lambda: object())
    monkeypatch.setattr(suspicious_router.reporting, "get_latest_date", lambda repo, table: None)
    client = TestClient(api.app)

    response = client.get("/api/suspicious/clicks")

    assert response.status_code == 200
    assert response.json() == {"date": "", "data": [], "total": 0, "limit": 500, "offset": 0}


def test_suspicious_clicks_endpoint_is_removed():
    client = TestClient(api.app)

    response = client.get("/api/suspicious/clicks")

    assert response.status_code == 404


def test_suspicious_click_detail_endpoint_is_removed():
    client = TestClient(api.app)

    response = client.get("/api/suspicious/clicks/f-1")

    assert response.status_code == 404


def test_suspicious_click_detail_endpoint_is_removed_with_query_params():
    client = TestClient(api.app)

    response = client.get("/api/suspicious/clicks/f-legacy", params={"include_details": True})

    assert response.status_code == 404


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
        "queue": None,
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
        "result": None,
        "queue": None,
    }


def test_job_status_admin_endpoint_returns_result_payload(monkeypatch):
    monkeypatch.setenv("FC_ADMIN_API_KEY", "secret")

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

    response = client.get("/api/job/status/admin", headers={"X-API-Key": "secret"})

    assert response.status_code == 200
    assert response.json()["result"] == {"success": False, "error": "boom"}


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
    monkeypatch.setenv("FC_ALLOW_PUBLIC_READ", "true")
    monkeypatch.setattr(health_router, "get_repository", lambda: DummyRepo())
    monkeypatch.setattr(
        health_router,
        "get_job_store",
        lambda: type(
            "DummyStore",
            (),
            {
                "get_latest_successful_finished_at": lambda self, job_types: None,
                "get_queue_metrics": lambda self: {
                    "queued_jobs_count": 0,
                    "retry_scheduled_jobs_count": 0,
                    "running_jobs_count": 0,
                    "failed_jobs_count": 0,
                    "oldest_queued_at": None,
                    "oldest_queued_age_seconds": None,
                },
            },
        )(),
    )
    monkeypatch.setattr(
        health_router.reporting,
        "get_summary",
        lambda repo, target_date: {
            "quality": {
                "findings": {
                    "findings_last_computed_at": None,
                    "stale": False,
                    "stale_reasons": [],
                }
            }
        },
    )
    client = TestClient(api.app)

    response = client.get("/api/health", headers={"X-API-Key": "secret"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "warning"
    assert len(payload["issues"]) >= 1
    assert payload["config"]["database_url_configured"] is True
    assert payload["config"]["read_access_mode"] == "public"


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
        "enqueue_master_sync_job",
        lambda **kwargs: type("QueuedJob", (), {"id": "run-master-1"})(),
    )
    client = TestClient(api.app)

    response = client.post("/api/sync/masters", headers={"X-API-Key": "secret"})

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "マスタ同期ジョブを登録しました",
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


def test_masters_status_requires_analyst_auth_when_enabled(monkeypatch):
    monkeypatch.setenv("FC_REQUIRE_READ_AUTH", "true")
    monkeypatch.setenv("FC_READ_API_KEY", "read-secret")
    monkeypatch.setattr(
        masters_router,
        "get_repository",
        lambda: type("DummyRepo", (), {"get_all_masters": lambda self: {"user_count": 30}})(),
    )
    client = TestClient(api.app)

    unauthorized = client.get("/api/masters/status")
    authorized = client.get("/api/masters/status", headers={"X-Read-API-Key": "read-secret"})

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200


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
