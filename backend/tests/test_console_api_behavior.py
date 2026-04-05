from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from fastapi.testclient import TestClient

from fraud_checker import api


def test_console_dashboard_endpoint_returns_business_payload(monkeypatch):
    from fraud_checker.api_routers import console as console_router

    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    monkeypatch.setattr(
        console_router.console_service,
        "get_dashboard",
        lambda repo, target_date=None: {
            "date": "2026-04-05",
            "kpis": {
                "fraud_rate": {"value": 12.5, "label": "全体フラウド率", "unit": "%"},
                "unhandled_alerts": {"value": 18, "label": "未対応アラート件数", "unit": "件"},
                "estimated_damage": {"value": 425000, "label": "被害推定額", "unit": "円"},
            },
            "trend": [
                {"date": "2026-04-01", "alerts": 8},
                {"date": "2026-04-02", "alerts": 11},
            ],
            "ranking": [
                {
                    "affiliate_id": "aff-001",
                    "affiliate_name": "Affiliate Alpha",
                    "fraud_rate": 31.2,
                }
            ],
        },
    )
    client = TestClient(api.app)

    response = client.get("/api/console/dashboard", params={"target_date": "2026-04-05"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["kpis"]["fraud_rate"]["value"] == 12.5
    assert payload["kpis"]["unhandled_alerts"]["value"] == 18
    assert payload["ranking"][0]["affiliate_name"] == "Affiliate Alpha"


def test_console_alerts_endpoint_defaults_to_unhandled_status_and_risk_desc(monkeypatch):
    from fraud_checker.api_routers import console as console_router

    captured: dict[str, object] = {}

    def fake_list_alerts(
        repo,
        *,
        status: str | None,
        start_date: str | None,
        end_date: str | None,
        sort: str,
    ):
        captured["status"] = status
        captured["start_date"] = start_date
        captured["end_date"] = end_date
        captured["sort"] = sort
        return {
            "items": [
                {
                    "finding_key": "fraud-001",
                    "detected_at": "2026-04-05T12:00:00",
                    "affiliate_id": "aff-001",
                    "affiliate_name": "Affiliate Alpha",
                    "outcome_type": "会員登録",
                    "risk_score": 97,
                    "pattern": "同一IPからの異常集中",
                    "status": "unhandled",
                }
            ],
            "total": 1,
        }

    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    monkeypatch.setattr(console_router.console_service, "list_alerts", fake_list_alerts)
    client = TestClient(api.app)

    response = client.get("/api/console/alerts")

    assert response.status_code == 200
    assert captured == {
        "status": "unhandled",
        "start_date": None,
        "end_date": None,
        "sort": "risk_desc",
    }
    assert response.json()["items"][0]["risk_score"] == 97


def test_console_alert_detail_endpoint_returns_reasons_transactions_and_actions(monkeypatch):
    from fraud_checker.api_routers import console as console_router

    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    monkeypatch.setattr(
        console_router.console_service,
        "get_alert_detail",
        lambda repo, finding_key: {
            "finding_key": finding_key,
            "affiliate_id": "aff-001",
            "affiliate_name": "Affiliate Alpha",
            "risk_score": 97,
            "status": "investigating",
            "reward_amount": 58000,
            "reasons": [
                "同一IPから24時間以内に47件のCV",
                "CV間隔が平均2.3秒",
            ],
            "transactions": [
                {
                    "transaction_id": "txn-001",
                    "occurred_at": "2026-04-05T11:58:00",
                    "outcome_type": "会員登録",
                    "reward_amount": 12000,
                    "state": "approved",
                }
            ],
            "actions": ["confirmed_fraud", "white", "investigating"],
        },
    )
    client = TestClient(api.app)

    response = client.get("/api/console/alerts/fraud-001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["affiliate_id"] == "aff-001"
    assert len(payload["reasons"]) == 2
    assert payload["transactions"][0]["transaction_id"] == "txn-001"


def test_console_review_endpoint_requires_admin_and_returns_mutation_result(monkeypatch):
    from fraud_checker.api_routers import console as console_router

    monkeypatch.setenv("FC_ADMIN_API_KEY", "admin-secret")
    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    monkeypatch.setattr(
        console_router.console_service,
        "apply_review_action",
        lambda repo, finding_keys, status: {
            "updated_count": len(finding_keys),
            "status": status,
        },
    )
    client = TestClient(api.app)

    unauthorized = client.post(
        "/api/console/alerts/review",
        json={"finding_keys": ["fraud-001", "fraud-002"], "status": "confirmed_fraud"},
    )
    authorized = client.post(
        "/api/console/alerts/review",
        headers={"X-API-Key": "admin-secret"},
        json={"finding_keys": ["fraud-001", "fraud-002"], "status": "confirmed_fraud"},
    )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
    assert authorized.json() == {"updated_count": 2, "status": "confirmed_fraud"}


def test_console_dashboard_creates_review_table_when_missing(tmp_path, monkeypatch):
    import fraud_checker.db.models  # noqa: F401

    from fraud_checker.db import Base
    from fraud_checker.repository_pg import PostgresRepository
    from fraud_checker.services import console as console_service

    database_path = tmp_path / "console-dashboard.db"
    repo = PostgresRepository(f"sqlite:///{database_path}")

    fraud_findings = Base.metadata.tables["fraud_findings"]
    Base.metadata.create_all(repo.engine, tables=[fraud_findings])

    with repo.engine.begin() as conn:
        conn.execute(
            fraud_findings.insert(),
            {
                "finding_key": "fraud-001",
                "date": datetime(2026, 4, 5).date(),
                "user_id": "aff-001",
                "media_id": "media-001",
                "promotion_id": "promo-001",
                "user_name": "Affiliate Alpha",
                "media_name": "Media Alpha",
                "promotion_name": "Program Alpha",
                "risk_level": "high",
                "risk_score": 97,
                "reasons_json": '["同一IPから大量CV"]',
                "reasons_formatted_json": '["同一IPから大量CV"]',
                "metrics_json": "{}",
                "primary_metric": 47,
                "first_time": None,
                "last_time": None,
                "rule_version": "test",
                "computed_at": datetime(2026, 4, 5, 10, 0, 0),
                "computed_by_job_id": None,
                "settings_updated_at_snapshot": None,
                "source_click_watermark": None,
                "source_conversion_watermark": None,
                "generation_id": None,
                "is_current": True,
                "search_text": "aff-001",
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
            {"date": "2026-04-04", "fraud_findings": 0},
            {"date": "2026-04-05", "fraud_findings": 1},
        ],
    )
    monkeypatch.setattr(
        console_service,
        "_fetch_alert_transaction_summary",
        lambda repo, rows: {
            "fraud-001": {
                "transaction_count": 1,
                "reward_amount": 3000,
                "latest_occurred_at": "2026-04-05T10:00:00",
            }
        },
    )
    monkeypatch.setattr(
        console_service,
        "_fetch_affiliate_conversion_totals",
        lambda repo, target_date: {"aff-001": 10},
    )

    payload = console_service.get_dashboard(repo, target_date="2026-04-05")

    assert repo._table_exists("fraud_alert_reviews") is True
    assert payload["kpis"]["unhandled_alerts"]["value"] == 1
    assert payload["ranking"][0]["affiliate_id"] == "aff-001"
