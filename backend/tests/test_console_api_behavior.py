from __future__ import annotations

import hmac
from datetime import date, datetime

from fastapi.testclient import TestClient
import pytest
import sqlalchemy as sa

from fraud_checker import api


def console_headers(
    user_id: str = "console-user",
    email: str = "console@example.com",
    request_id: str = "req-console",
) -> dict[str, str]:
    secret = "proxy-secret"
    signature = hmac.new(
        secret.encode("utf-8"),
        f"{user_id}\n{email}\n{request_id}".encode("utf-8"),
        "sha256",
    ).hexdigest()
    return {
        "X-Console-User-Id": user_id,
        "X-Console-User-Email": email,
        "X-Console-Request-Id": request_id,
        "X-Console-User-Signature": signature,
    }


def test_console_dashboard_endpoint_returns_business_payload(monkeypatch):
    from fraud_checker.api_routers import console as console_router
    monkeypatch.setenv("FC_INTERNAL_PROXY_SECRET", "proxy-secret")

    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    monkeypatch.setattr(
        console_router.console_service,
        "get_dashboard",
        lambda repo, target_date=None: {
            "date": "2026-04-05",
            "available_dates": ["2026-04-05", "2026-04-04"],
            "kpis": {
                "fraud_rate": {"value": 12.5, "label": "Fraud Rate", "unit": "%"},
                "unhandled_alerts": {"value": 18, "label": "Unhandled Alerts", "unit": "items"},
                "estimated_damage": {"value": 425000, "label": "Estimated Damage", "unit": "JPY"},
            },
            "trend": [
                {"date": "2026-04-01", "alerts": 8},
                {"date": "2026-04-02", "alerts": 11},
            ],
            "case_ranking": [
                {
                    "case_key": "case-001",
                    "risk_score": 97,
                    "risk_level": "critical",
                    "estimated_damage": 425000,
                    "affected_affiliate_count": 3,
                    "latest_detected_at": "2026-04-05T10:00:00+09:00",
                    "primary_reason": "Same IP generated repeated conversions",
                    "status": "unhandled",
                }
            ],
            "quality": {
                "findings": {
                    "stale": False,
                    "stale_reasons": [],
                }
            },
            "job_status_summary": {
                "status": "queued",
                "job_id": "job-123",
                "message": "queued",
                "queue": {"queued": 2, "retry_scheduled": 1, "running": 0, "failed": 0},
            },
        },
    )
    client = TestClient(api.app)

    response = client.get(
        "/api/console/dashboard",
        params={"target_date": "2026-04-05"},
        headers=console_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kpis"]["fraud_rate"]["value"] == 12.5
    assert payload["kpis"]["unhandled_alerts"]["value"] == 18
    assert payload["case_ranking"][0]["case_key"] == "case-001"
    assert payload["job_status_summary"]["queue"]["queued"] == 2


def test_console_job_status_endpoint_returns_normalized_queue_summary(monkeypatch):
    from fraud_checker.api_routers import console as console_router

    monkeypatch.setenv("FC_INTERNAL_PROXY_SECRET", "proxy-secret")

    class DummyStore:
        def get_by_id(self, job_id):
            return type(
                "Run",
                (),
                {
                    "id": job_id,
                    "status": "queued",
                    "message": "queued",
                    "started_at": None,
                    "finished_at": None,
                    "result": None,
                },
            )()

        def get_queue_metrics(self):
            return {
                "queued_jobs_count": 2,
                "retry_scheduled_jobs_count": 1,
                "running_jobs_count": 0,
                "failed_jobs_count": 1,
                "oldest_queued_at": None,
                "oldest_queued_age_seconds": 600,
            }

        def _serialize_queue_metrics(self, metrics):
            return {
                "queued": 2,
                "retry_scheduled": 1,
                "running": 0,
                "failed": 1,
                "oldest_queued_at": None,
                "oldest_queued_age_seconds": 600,
            }

    monkeypatch.setattr(console_router, "get_job_store", lambda: DummyStore())
    client = TestClient(api.app)

    response = client.get("/api/console/job-status/job-123", headers=console_headers())

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "queued"
    assert payload["queue"] == {
        "queued": 2,
        "retry_scheduled": 1,
        "running": 0,
        "failed": 1,
        "oldest_queued_at": None,
        "oldest_queued_age_seconds": 600,
    }


def test_console_alerts_endpoint_defaults_to_unhandled_status_and_risk_desc(monkeypatch):
    from fraud_checker.api_routers import console as console_router
    monkeypatch.setenv("FC_INTERNAL_PROXY_SECRET", "proxy-secret")

    captured: dict[str, object] = {}

    def fake_list_alerts(
        repo,
        *,
        status: str | None,
        risk_level: str | None,
        start_date: str | None,
        end_date: str | None,
        search: str | None,
        sort: str,
        page: int,
        page_size: int,
    ):
        captured["status"] = status
        captured["risk_level"] = risk_level
        captured["start_date"] = start_date
        captured["end_date"] = end_date
        captured["search"] = search
        captured["sort"] = sort
        captured["page"] = page
        captured["page_size"] = page_size
        return {
            "available_dates": ["2026-04-05"],
            "applied_filters": {
                "status": status or "all",
                "risk_level": risk_level,
                "start_date": start_date,
                "end_date": end_date,
                "sort": sort,
            },
            "status_counts": {
                "unhandled": 1,
                "investigating": 0,
                "confirmed_fraud": 0,
                "white": 0,
            },
            "items": [
                {
                    "finding_key": "finding-001",
                    "detected_at": "2026-04-05T12:00:00",
                    "affiliate_id": "aff-001",
                    "affiliate_name": "Affiliate Alpha",
                    "outcome_type": "Program Alpha",
                    "risk_score": 97,
                    "pattern": "Same IP generated repeated conversions",
                    "status": "unhandled",
                }
            ],
            "total": 1,
            "page": page,
            "page_size": page_size,
            "has_next": False,
        }

    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    monkeypatch.setattr(console_router.console_service, "list_alerts", fake_list_alerts)
    client = TestClient(api.app)

    response = client.get("/api/console/alerts", headers=console_headers())

    assert response.status_code == 200
    assert captured == {
        "status": "unhandled",
        "risk_level": None,
        "start_date": None,
        "end_date": None,
        "search": None,
        "sort": "risk_desc",
        "page": 1,
        "page_size": 50,
    }
    assert response.json()["items"][0]["risk_score"] == 97


def test_console_alert_detail_endpoint_returns_reasons_transactions_and_actions(monkeypatch):
    from fraud_checker.api_routers import console as console_router
    monkeypatch.setenv("FC_INTERNAL_PROXY_SECRET", "proxy-secret")

    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    monkeypatch.setattr(
        console_router.console_service,
        "get_alert_detail",
        lambda repo, finding_key, access_context=None: {
            "finding_key": finding_key,
            "affiliate_id": "aff-001",
            "affiliate_name": "Affiliate Alpha",
            "risk_score": 97,
            "status": "investigating",
            "reward_amount": 58000,
            "reasons": [
                "47 conversions from the same IP within 24 hours",
                "Average conversion gap was 2.3 seconds",
            ],
            "transactions": [
                {
                    "transaction_id": "txn-001",
                    "occurred_at": "2026-04-05T11:58:00",
                    "outcome_type": "Program Alpha",
                    "reward_amount": 12000,
                    "state": "approved",
                }
            ],
            "actions": ["confirmed_fraud", "white", "investigating"],
        },
    )
    client = TestClient(api.app)

    response = client.get("/api/console/alerts/finding-001", headers=console_headers())

    assert response.status_code == 200
    payload = response.json()
    assert payload["affiliate_id"] == "aff-001"
    assert len(payload["reasons"]) == 2
    assert payload["transactions"][0]["transaction_id"] == "txn-001"


def test_console_alerts_endpoint_forwards_pagination_params(monkeypatch):
    from fraud_checker.api_routers import console as console_router
    monkeypatch.setenv("FC_INTERNAL_PROXY_SECRET", "proxy-secret")

    captured: dict[str, object] = {}

    def fake_list_alerts(repo, **kwargs):
        captured.update(kwargs)
        return {
            "available_dates": [],
            "applied_filters": {
                "status": kwargs["status"] or "all",
                "risk_level": kwargs.get("risk_level"),
                "start_date": kwargs["start_date"],
                "end_date": kwargs["end_date"],
                "search": kwargs["search"],
                "sort": kwargs["sort"],
            },
            "status_counts": {
                "unhandled": 0,
                "investigating": 0,
                "confirmed_fraud": 0,
                "white": 0,
            },
            "items": [],
            "total": 0,
            "page": kwargs["page"],
            "page_size": kwargs["page_size"],
            "has_next": False,
        }

    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    monkeypatch.setattr(console_router.console_service, "list_alerts", fake_list_alerts)
    client = TestClient(api.app)

    response = client.get(
        "/api/console/alerts",
        params={
            "status": "all",
            "start_date": "2026-04-01",
            "end_date": "2026-04-05",
            "search": "alpha",
            "page": 3,
            "page_size": 25,
        },
        headers=console_headers(),
    )

    assert response.status_code == 200
    assert captured["status"] == "all"
    assert captured["search"] == "alpha"
    assert captured["page"] == 3
    assert captured["page_size"] == 25


def test_console_export_endpoint_returns_csv(monkeypatch):
    from fraud_checker.api_routers import console as console_router
    monkeypatch.setenv("FC_INTERNAL_PROXY_SECRET", "proxy-secret")

    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    monkeypatch.setattr(
        console_router.console_service,
        "export_alerts_csv",
        lambda repo, **kwargs: "finding_key,affiliate_name\nfk-001,Alpha\n",
    )
    client = TestClient(api.app)

    response = client.get(
        "/api/console/alerts/export",
        params={"start_date": "2026-04-05"},
        headers=console_headers(),
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'fraud-alerts-2026-04-05.csv' in response.headers["content-disposition"]
    assert "fk-001" in response.text


def test_console_review_endpoint_returns_mutation_result_for_authenticated_viewers(monkeypatch):
    from fraud_checker.api_routers import console as console_router

    monkeypatch.setenv("FC_INTERNAL_PROXY_SECRET", "proxy-secret")
    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    monkeypatch.setattr(
        console_router.console_service,
        "apply_review_action",
        lambda repo, finding_keys, status, access_context=None, reason=None, filters=None: {
            "requested_count": len(finding_keys),
            "matched_current_count": len(finding_keys),
            "updated_count": len(finding_keys),
            "missing_keys": [],
            "status": status,
        },
    )
    client = TestClient(api.app)

    response = client.post(
        "/api/console/alerts/review",
        headers=console_headers(),
        json={"case_keys": ["case-001", "case-002"], "status": "confirmed_fraud", "reason": "bulk review"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "requested_count": 2,
        "matched_current_count": 2,
        "updated_count": 2,
        "missing_keys": [],
        "status": "confirmed_fraud",
    }


def test_console_review_endpoint_forwards_filter_scope(monkeypatch):
    from fraud_checker.api_routers import console as console_router

    monkeypatch.setenv("FC_INTERNAL_PROXY_SECRET", "proxy-secret")
    captured: dict[str, object] = {}

    def fake_apply_review_action(
        repo,
        finding_keys,
        status,
        access_context=None,
        reason=None,
        filters=None,
    ):
        captured["finding_keys"] = finding_keys
        captured["status"] = status
        captured["reason"] = reason
        captured["filters"] = filters
        captured["access_context"] = {
            "user_id": access_context.user_id,
            "request_id": access_context.request_id,
        }
        return {
            "requested_count": 3,
            "matched_current_count": 3,
            "updated_count": 3,
            "missing_keys": [],
            "status": status,
        }

    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    monkeypatch.setattr(console_router.console_service, "apply_review_action", fake_apply_review_action)
    client = TestClient(api.app)

    response = client.post(
        "/api/console/alerts/review",
        headers=console_headers(),
        json={
            "case_keys": [],
            "status": "investigating",
            "reason": "scope review",
            "filters": {
                "status": "unhandled",
                "risk_level": "high",
                "start_date": "2026-04-01",
                "end_date": "2026-04-05",
                "search": "alpha",
                "sort": "damage_desc",
            },
        },
    )

    assert response.status_code == 200
    assert captured == {
        "finding_keys": [],
        "status": "investigating",
        "reason": "scope review",
        "filters": {
            "status": "unhandled",
            "risk_level": "high",
            "start_date": "2026-04-01",
            "end_date": "2026-04-05",
            "search": "alpha",
            "sort": "damage_desc",
        },
        "access_context": {
            "user_id": "console-user",
            "request_id": "req-console",
        },
    }


def test_console_assign_endpoint_forwards_case_keys_and_actor(monkeypatch):
    from fraud_checker.api_routers import console as console_router

    monkeypatch.setenv("FC_INTERNAL_PROXY_SECRET", "proxy-secret")
    captured: dict[str, object] = {}

    def fake_assign_alert_cases(repo, finding_keys, access_context=None, action=None):
        captured["finding_keys"] = finding_keys
        captured["action"] = action
        captured["access_context"] = {
            "user_id": access_context.user_id,
            "request_id": access_context.request_id,
        }
        return {"updated_count": 2, "action": action}

    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    monkeypatch.setattr(console_router.console_service, "assign_alert_cases", fake_assign_alert_cases)
    client = TestClient(api.app)

    response = client.post(
        "/api/console/alerts/assign",
        headers=console_headers(user_id="assignee-user", email="assignee@example.com", request_id="req-assignee"),
        json={"case_keys": ["case-001", "case-002"], "action": "claim"},
    )

    assert response.status_code == 200
    assert response.json() == {"updated_count": 2, "action": "claim"}
    assert captured == {
        "finding_keys": ["case-001", "case-002"],
        "action": "claim",
        "access_context": {
            "user_id": "assignee-user",
            "request_id": "req-assignee",
        },
    }


def test_console_follow_up_endpoint_returns_404_when_task_is_missing(monkeypatch):
    from fraud_checker.api_routers import console as console_router

    monkeypatch.setenv("FC_INTERNAL_PROXY_SECRET", "proxy-secret")

    def fake_update_followup_task_status(repo, task_id, status, access_context=None):
        raise ValueError("Follow-up task not found")

    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    monkeypatch.setattr(
        console_router.console_service,
        "update_followup_task_status",
        fake_update_followup_task_status,
    )
    client = TestClient(api.app)

    response = client.post(
        "/api/console/alerts/follow-up",
        headers=console_headers(),
        json={"task_id": "task-001", "status": "completed"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Follow-up task not found"


def test_console_follow_up_endpoint_returns_updated_task(monkeypatch):
    from fraud_checker.api_routers import console as console_router

    monkeypatch.setenv("FC_INTERNAL_PROXY_SECRET", "proxy-secret")
    captured: dict[str, object] = {}

    def fake_update_followup_task_status(repo, task_id, status, access_context=None):
        captured["task_id"] = task_id
        captured["status"] = status
        captured["access_context"] = {
            "user_id": access_context.user_id,
            "request_id": access_context.request_id,
        }
        return {
            "task_id": task_id,
            "case_key": "case-001",
            "task_type": "payment_hold",
            "status": status,
        }

    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    monkeypatch.setattr(
        console_router.console_service,
        "update_followup_task_status",
        fake_update_followup_task_status,
    )
    client = TestClient(api.app)

    response = client.post(
        "/api/console/alerts/follow-up",
        headers=console_headers(user_id="followup-user", email="followup@example.com", request_id="req-followup"),
        json={"task_id": "task-001", "status": "completed"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "task-001",
        "case_key": "case-001",
        "task_type": "payment_hold",
        "status": "completed",
    }
    assert captured == {
        "task_id": "task-001",
        "status": "completed",
        "access_context": {
            "user_id": "followup-user",
            "request_id": "req-followup",
        },
    }


def test_console_settings_endpoint_returns_payload_for_authenticated_viewers(monkeypatch):
    from fraud_checker.api_routers import console as console_router

    monkeypatch.setenv("FC_INTERNAL_PROXY_SECRET", "proxy-secret")
    monkeypatch.setattr(
        console_router.settings_service,
        "get_settings",
        lambda repo: {"click_threshold": 50, "browser_only": False},
    )
    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    client = TestClient(api.app)

    response = client.get("/api/console/settings", headers=console_headers())

    assert response.status_code == 200
    assert response.json()["click_threshold"] == 50


def test_console_settings_update_endpoint_forwards_payload(monkeypatch):
    from fraud_checker.api_routers import console as console_router

    monkeypatch.setenv("FC_INTERNAL_PROXY_SECRET", "proxy-secret")
    captured: dict[str, object] = {}

    def fake_update_settings(repo, settings):
        captured["settings"] = settings
        return {
            "success": True,
            "persisted": True,
            "settings": settings,
            "settings_version_id": "settings-v1",
        }

    monkeypatch.setattr(console_router.settings_service, "update_settings", fake_update_settings)
    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    client = TestClient(api.app)

    response = client.post(
        "/api/console/settings",
        headers=console_headers(),
        json={
            "click_threshold": 70,
            "media_threshold": 4,
            "program_threshold": 4,
            "burst_click_threshold": 25,
            "burst_window_seconds": 600,
            "conversion_threshold": 6,
            "conv_media_threshold": 2,
            "conv_program_threshold": 2,
            "burst_conversion_threshold": 3,
            "burst_conversion_window_seconds": 1800,
            "min_click_to_conv_seconds": 5,
            "max_click_to_conv_seconds": 2592000,
            "fraud_check_min_total": 10,
            "fraud_check_invalid_rate": 30,
            "fraud_check_duplicate_plid_count": 3,
            "fraud_check_duplicate_plid_rate": 10,
            "fraud_track_min_total": 20,
            "fraud_track_auth_error_rate": 5,
            "fraud_track_auth_ip_ua_rate": 50,
            "fraud_action_min_total": 10,
            "fraud_action_short_gap_seconds": 5,
            "fraud_action_short_gap_count": 3,
            "fraud_action_cancel_rate": 30,
            "fraud_action_fixed_gap_min_count": 3,
            "fraud_action_fixed_gap_max_unique": 2,
            "fraud_spike_multiplier": 3,
            "fraud_spike_lookback_days": 7,
            "browser_only": True,
            "exclude_datacenter_ip": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["settings_version_id"] == "settings-v1"
    assert captured["settings"]["click_threshold"] == 70
    assert captured["settings"]["browser_only"] is True


def test_console_endpoints_require_signed_viewer_headers(monkeypatch):
    monkeypatch.setenv("FC_INTERNAL_PROXY_SECRET", "proxy-secret")
    client = TestClient(api.app)

    response = client.get("/api/console/dashboard")

    assert response.status_code == 401


def test_console_dashboard_uses_migrated_review_table(tmp_path, monkeypatch):
    import fraud_checker.db.models  # noqa: F401

    from fraud_checker.db import Base
    from fraud_checker.repository_pg import PostgresRepository
    from fraud_checker.services import console as console_service

    database_path = tmp_path / "console-dashboard.db"
    repo = PostgresRepository(f"sqlite:///{database_path}")

    suspicious_findings = Base.metadata.tables["suspicious_conversion_findings"]
    review_table = Base.metadata.tables["fraud_alert_reviews"]
    Base.metadata.create_all(repo.engine, tables=[suspicious_findings, review_table])

    with repo.engine.begin() as conn:
        conn.execute(
            suspicious_findings.insert(),
            {
                "finding_key": "finding-001",
                "date": datetime(2026, 4, 5).date(),
                "ipaddress": "203.0.113.10",
                "useragent": "Mozilla/5.0 Chrome/123.0",
                "ua_hash": "ua-hash-1",
                "media_ids_json": '["media-001"]',
                "program_ids_json": '["promo-001"]',
                "media_names_json": '["Media Alpha"]',
                "program_names_json": '["Program Alpha"]',
                "affiliate_ids_json": '["aff-001"]',
                "affiliate_names_json": '["Affiliate Alpha"]',
                "risk_level": "high",
                "risk_score": 97,
                "reasons_json": '["Same IP generated repeated conversions"]',
                "reasons_formatted_json": '["Same IP generated repeated conversions"]',
                "metrics_json": "{}",
                "total_conversions": 1,
                "media_count": 1,
                "program_count": 1,
                "min_click_to_conv_seconds": None,
                "max_click_to_conv_seconds": None,
                "first_time": datetime(2026, 4, 5, 9, 50, 0),
                "last_time": datetime(2026, 4, 5, 10, 0, 0),
                "rule_version": "test",
                "computed_at": datetime(2026, 4, 5, 10, 0, 0),
                "computed_by_job_id": None,
                "settings_updated_at_snapshot": None,
                "source_click_watermark": None,
                "source_conversion_watermark": None,
                "estimated_damage_yen": 3000,
                "damage_unit_price_source": "program_observed",
                "damage_evidence_json": "[]",
                "generation_id": None,
                "is_current": True,
                "search_text": "affiliate alpha",
            },
        )

    monkeypatch.setattr(
        console_service.reporting,
        "get_summary",
        lambda repo, target_date=None: {
            "date": "2026-04-05",
            "stats": {"conversions": {"total": 10}},
        },
    )
    monkeypatch.setattr(
        console_service.reporting,
        "get_available_dates",
        lambda repo: ["2026-04-05"],
    )
    monkeypatch.setattr(
        console_service.reporting,
        "get_daily_stats",
        lambda repo, days, resolved_date: [
            {"date": "2026-04-04", "suspicious_conversions": 0},
            {"date": "2026-04-05", "suspicious_conversions": 1},
        ],
    )
    payload = console_service.get_dashboard(repo, target_date="2026-04-05")

    assert payload["kpis"]["unhandled_alerts"]["value"] == 1
    assert payload["case_ranking"][0]["case_key"] == "finding-001"
    assert payload["kpis"]["estimated_damage"]["value"] == 3000


def test_apply_alert_reviews_persists_case_state_and_history(tmp_path):
    import fraud_checker.db.models  # noqa: F401

    from fraud_checker.db import Base
    from fraud_checker.repository_pg import PostgresRepository

    database_path = tmp_path / "review-state.db"
    repo = PostgresRepository(f"sqlite:///{database_path}")

    suspicious_findings = Base.metadata.tables["suspicious_conversion_findings"]
    review_states = Base.metadata.tables["fraud_alert_review_states"]
    review_events = Base.metadata.tables["fraud_alert_review_events"]
    Base.metadata.create_all(repo.engine, tables=[suspicious_findings, review_states, review_events])

    with repo.engine.begin() as conn:
        conn.execute(
            suspicious_findings.insert(),
            {
                "finding_key": "finding-001",
                "case_key": "case-001",
                "date": datetime(2026, 4, 5).date(),
                "ipaddress": "203.0.113.10",
                "useragent": "Mozilla/5.0 Chrome/123.0",
                "ua_hash": "ua-hash-1",
                "media_ids_json": '["media-001"]',
                "program_ids_json": '["promo-001"]',
                "media_names_json": '["Media Alpha"]',
                "program_names_json": '["Program Alpha"]',
                "affiliate_ids_json": '["aff-001"]',
                "affiliate_names_json": '["Affiliate Alpha"]',
                "risk_level": "high",
                "risk_score": 97,
                "reasons_json": '["Same IP generated repeated conversions"]',
                "reasons_formatted_json": '["Same IP generated repeated conversions"]',
                "metrics_json": "{}",
                "total_conversions": 1,
                "media_count": 1,
                "program_count": 1,
                "min_click_to_conv_seconds": None,
                "max_click_to_conv_seconds": None,
                "first_time": datetime(2026, 4, 5, 9, 50, 0),
                "last_time": datetime(2026, 4, 5, 10, 0, 0),
                "rule_version": "test",
                "computed_at": datetime(2026, 4, 5, 10, 0, 0),
                "computed_by_job_id": None,
                "settings_updated_at_snapshot": None,
                "source_click_watermark": None,
                "source_conversion_watermark": None,
                "estimated_damage_yen": 3000,
                "damage_unit_price_source": "program_observed",
                "damage_evidence_json": "[]",
                "generation_id": None,
                "is_current": True,
                "search_text": "affiliate alpha",
            },
        )

    updated_count = repo.apply_alert_reviews(
        ["finding-001"],
        status="white",
        updated_at=datetime(2026, 4, 5, 12, 0, 0),
        reason="manual review",
        reviewed_by="admin-user",
        source_surface="console",
        request_id="req-1",
    )

    assert updated_count == 1

    with repo.engine.begin() as conn:
        state_row = conn.execute(sa.text("SELECT * FROM fraud_alert_review_states")).mappings().one()
        event_row = conn.execute(sa.text("SELECT * FROM fraud_alert_review_events")).mappings().one()

    assert state_row["case_key"] == "case-001"
    assert state_row["review_status"] == "white"
    assert state_row["reason"] == "manual review"
    assert state_row["reviewed_by"] == "admin-user"
    assert state_row["request_id"] == "req-1"
    assert event_row["case_key"] == "case-001"
    assert event_row["finding_key_at_review"] == "finding-001"


def test_apply_alert_reviews_creates_and_cancels_followup_tasks(tmp_path):
    import fraud_checker.db.models  # noqa: F401

    from fraud_checker.db import Base
    from fraud_checker.repository_pg import PostgresRepository

    database_path = tmp_path / "review-followups.db"
    repo = PostgresRepository(f"sqlite:///{database_path}")

    suspicious_findings = Base.metadata.tables["suspicious_conversion_findings"]
    review_states = Base.metadata.tables["fraud_alert_review_states"]
    review_events = Base.metadata.tables["fraud_alert_review_events"]
    followup_tasks = Base.metadata.tables["fraud_alert_followup_tasks"]
    Base.metadata.create_all(
        repo.engine,
        tables=[suspicious_findings, review_states, review_events, followup_tasks],
    )

    with repo.engine.begin() as conn:
        conn.execute(
            suspicious_findings.insert(),
            {
                "finding_key": "finding-001",
                "case_key": "case-001",
                "date": datetime(2026, 4, 5).date(),
                "ipaddress": "203.0.113.10",
                "useragent": "Mozilla/5.0 Chrome/123.0",
                "ua_hash": "ua-hash-1",
                "media_ids_json": '["media-001"]',
                "program_ids_json": '["promo-001"]',
                "media_names_json": '["Media Alpha"]',
                "program_names_json": '["Program Alpha"]',
                "affiliate_ids_json": '["aff-001"]',
                "affiliate_names_json": '["Affiliate Alpha"]',
                "risk_level": "high",
                "risk_score": 97,
                "reasons_json": '["Same IP generated repeated conversions"]',
                "reasons_formatted_json": '["Same IP generated repeated conversions"]',
                "metrics_json": "{}",
                "total_conversions": 1,
                "media_count": 1,
                "program_count": 1,
                "min_click_to_conv_seconds": None,
                "max_click_to_conv_seconds": None,
                "first_time": datetime(2026, 4, 5, 9, 50, 0),
                "last_time": datetime(2026, 4, 5, 10, 0, 0),
                "rule_version": "test",
                "computed_at": datetime(2026, 4, 5, 10, 0, 0),
                "computed_by_job_id": None,
                "settings_updated_at_snapshot": None,
                "source_click_watermark": None,
                "source_conversion_watermark": None,
                "estimated_damage_yen": 3000,
                "damage_unit_price_source": "program_observed",
                "damage_evidence_json": "[]",
                "generation_id": None,
                "is_current": True,
                "search_text": "affiliate alpha",
            },
        )

    repo.apply_alert_reviews(
        ["finding-001"],
        status="confirmed_fraud",
        updated_at=datetime(2026, 4, 5, 12, 0, 0),
        reason="manual fraud review",
        reviewed_by="admin-user",
        source_surface="console",
        request_id="req-1",
    )

    with repo.engine.begin() as conn:
        confirmed_rows = conn.execute(
            sa.text(
                """
                SELECT case_key, task_type, task_status, due_at
                FROM fraud_alert_followup_tasks
                ORDER BY task_type ASC
                """
            )
        ).mappings().all()

    normalized_confirmed_rows = [
        {
            **row,
            "due_at": datetime.fromisoformat(str(row["due_at"])),
        }
        for row in confirmed_rows
    ]

    assert normalized_confirmed_rows == [
        {
            "case_key": "case-001",
            "task_type": "evidence_preservation",
            "task_status": "open",
            "due_at": datetime(2026, 4, 6, 12, 0, 0),
        },
        {
            "case_key": "case-001",
            "task_type": "partner_notice",
            "task_status": "open",
            "due_at": datetime(2026, 4, 5, 16, 0, 0),
        },
        {
            "case_key": "case-001",
            "task_type": "payout_hold",
            "task_status": "open",
            "due_at": datetime(2026, 4, 5, 13, 0, 0),
        },
    ]

    repo.apply_alert_reviews(
        ["finding-001"],
        status="white",
        updated_at=datetime(2026, 4, 5, 12, 30, 0),
        reason="cleared after review",
        reviewed_by="admin-user",
        source_surface="console",
        request_id="req-2",
    )

    with repo.engine.begin() as conn:
        cancelled_rows = conn.execute(
            sa.text(
                """
                SELECT task_type, task_status
                FROM fraud_alert_followup_tasks
                ORDER BY task_type ASC
                """
            )
        ).mappings().all()

    assert cancelled_rows == [
        {"task_type": "evidence_preservation", "task_status": "cancelled"},
        {"task_type": "partner_notice", "task_status": "cancelled"},
        {"task_type": "payout_hold", "task_status": "cancelled"},
    ]


def test_build_alert_item_prefers_snapshot_damage_and_affiliate_fields():
    from fraud_checker.services import console as console_service

    item = console_service._build_alert_item(
        {
            "finding_key": "finding-001",
            "computed_at": datetime(2026, 4, 5, 10, 0, 0),
            "last_time": datetime(2026, 4, 5, 10, 0, 0),
            "program_names_json": ["Program Alpha"],
            "affiliate_ids_json": ["aff-001"],
            "affiliate_names_json": ["Affiliate Alpha"],
            "reasons_json": ["Same IP generated repeated conversions"],
            "risk_score": 97,
            "risk_level": "high",
            "review_status": "unhandled",
            "estimated_damage_yen": 42000,
            "total_conversions": 7,
        },
        {
            "transaction_count": 3,
            "reward_amount": 12000,
            "affiliate_id": "fallback-aff",
            "affiliate_name": "Fallback Affiliate",
            "outcome_type": "Fallback Program",
        },
    )

    assert item["case_key"] == "finding-001"
    assert item["affected_affiliate_count"] == 1
    assert item["affected_affiliates"][0]["id"] == "aff-001"
    assert item["affected_affiliates"][0]["name"] == "Affiliate Alpha"
    assert item["outcome_type"] == "Program Alpha"
    assert item["reward_amount"] == 42000
    assert item["transaction_count"] == 7


def test_alert_transaction_summary_falls_back_to_program_unit_price_times_total_conversions():
    from fraud_checker.services import console as console_service

    class DummyRepo:
        def _table_exists(self, name):
            assert name == "conversion_raw"
            return True

        def fetch_all(self, query, params=None):
            if "WITH target_entities" in query:
                return []
            if "SELECT conversion_time, program_id, raw_payload" in " ".join(query.split()):
                return [
                    {
                        "conversion_time": datetime(2026, 4, 5, 9, 30, 0),
                        "program_id": "program-1",
                        "raw_payload": {"reward_amount": 12000},
                    }
                ]
            raise AssertionError(f"Unexpected query: {query}")

    summary = console_service._fetch_alert_transaction_summary(
        DummyRepo(),
        [
            {
                "finding_key": "finding-001",
                "date": date(2026, 4, 5),
                "ipaddress": "203.0.113.10",
                "useragent": "Mozilla/5.0",
                "program_ids_json": ["program-1"],
                "program_names_json": ["Program Alpha"],
                "affiliate_names_json": ["Affiliate Alpha"],
                "total_conversions": 3,
                "last_time": datetime(2026, 4, 5, 10, 0, 0),
                "computed_at": datetime(2026, 4, 5, 10, 5, 0),
            }
        ],
    )

    assert summary["finding-001"]["transaction_count"] == 3
    assert summary["finding-001"]["reward_amount"] == 36000
    assert summary["finding-001"]["affiliate_name"] == "Affiliate Alpha"
    assert summary["finding-001"]["outcome_type"] == "Program Alpha"


def test_alert_transaction_summary_backfills_missing_matches_with_direct_unit_price():
    from fraud_checker.services import console as console_service

    class DummyRepo:
        def _table_exists(self, name):
            assert name == "conversion_raw"
            return True

        def fetch_all(self, query, params=None):
            if "WITH target_entities" in query:
                return [
                    {
                        "finding_key": "finding-001",
                        "transaction_id": "conv-1",
                        "conversion_time": datetime(2026, 4, 5, 10, 0, 0),
                        "state": "approved",
                        "raw_payload": {"reward_amount": 8000},
                        "user_id": "aff-1",
                        "affiliate_name": "Affiliate Alpha",
                        "program_id": "program-1",
                        "promotion_name": "Program Alpha",
                    }
                ]
            if "SELECT conversion_time, program_id, raw_payload" in " ".join(query.split()):
                return []
            raise AssertionError(f"Unexpected query: {query}")

    summary = console_service._fetch_alert_transaction_summary(
        DummyRepo(),
        [
            {
                "finding_key": "finding-001",
                "date": date(2026, 4, 5),
                "ipaddress": "203.0.113.10",
                "useragent": "Mozilla/5.0",
                "program_ids_json": ["program-1"],
                "program_names_json": ["Program Alpha"],
                "affiliate_names_json": ["Affiliate Alpha"],
                "total_conversions": 3,
                "last_time": datetime(2026, 4, 5, 10, 0, 0),
                "computed_at": datetime(2026, 4, 5, 10, 5, 0),
            }
        ],
    )

    assert summary["finding-001"]["transaction_count"] == 3
    assert summary["finding-001"]["reward_amount"] == 24000
    assert summary["finding-001"]["affiliate_id"] == "aff-1"


def test_fetch_alert_rows_logs_sqlalchemy_errors(monkeypatch):
    from fraud_checker.services import console as console_service

    captured: list[str] = []

    class DummyRepo:
        def fetch_all(self, query, params=None):
            raise console_service.sa.exc.SQLAlchemyError("boom")

    monkeypatch.setattr(console_service.logger, "exception", lambda message: captured.append(message))

    with pytest.raises(console_service.sa.exc.SQLAlchemyError):
        console_service._fetch_alert_rows(
            DummyRepo(),
            start_date="2026-04-05",
            end_date="2026-04-05",
            status="unhandled",
            sort="risk_desc",
        )

    assert captured == ["Failed to fetch console alert rows"]
