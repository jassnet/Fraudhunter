from __future__ import annotations

import hmac
from datetime import date, datetime

from fastapi.testclient import TestClient

from fraud_checker import api


def console_headers(role: str = "analyst") -> dict[str, str]:
    secret = "proxy-secret"
    request_id = f"req-{role}"
    user_id = f"{role}-user"
    email = f"{role}@example.com"
    signature = hmac.new(
        secret.encode("utf-8"),
        f"{user_id}\n{email}\n{role}\n{request_id}".encode("utf-8"),
        "sha256",
    ).hexdigest()
    return {
        "X-Console-User-Id": user_id,
        "X-Console-User-Email": email,
        "X-Console-User-Role": role,
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
            "kpis": {
                "fraud_rate": {"value": 12.5, "label": "Fraud Rate", "unit": "%"},
                "unhandled_alerts": {"value": 18, "label": "Unhandled Alerts", "unit": "items"},
                "estimated_damage": {"value": 425000, "label": "Estimated Damage", "unit": "JPY"},
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

    response = client.get(
        "/api/console/dashboard",
        params={"target_date": "2026-04-05"},
        headers=console_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kpis"]["fraud_rate"]["value"] == 12.5
    assert payload["kpis"]["unhandled_alerts"]["value"] == 18
    assert payload["ranking"][0]["affiliate_name"] == "Affiliate Alpha"


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


def test_console_review_endpoint_requires_admin_and_returns_mutation_result(monkeypatch):
    from fraud_checker.api_routers import console as console_router

    monkeypatch.setenv("FC_INTERNAL_PROXY_SECRET", "proxy-secret")
    monkeypatch.setattr(console_router, "get_repository", lambda: object())
    monkeypatch.setattr(
        console_router.console_service,
        "apply_review_action",
        lambda repo, finding_keys, status, access_context=None: {
            "updated_count": len(finding_keys),
            "status": status,
        },
    )
    client = TestClient(api.app)

    unauthorized = client.post(
        "/api/console/alerts/review",
        json={"finding_keys": ["finding-001", "finding-002"], "status": "confirmed_fraud"},
        headers=console_headers("analyst"),
    )
    authorized = client.post(
        "/api/console/alerts/review",
        headers=console_headers("admin"),
        json={"finding_keys": ["finding-001", "finding-002"], "status": "confirmed_fraud"},
    )

    assert unauthorized.status_code == 403
    assert authorized.status_code == 200
    assert authorized.json() == {"updated_count": 2, "status": "confirmed_fraud"}


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
    monkeypatch.setattr(
        console_service,
        "_fetch_affiliate_conversion_totals",
        lambda repo, target_date: {"aff-001": 10},
    )

    payload = console_service.get_dashboard(repo, target_date="2026-04-05")

    assert payload["kpis"]["unhandled_alerts"]["value"] == 1
    assert payload["ranking"][0]["affiliate_id"] == "aff-001"
    assert payload["kpis"]["estimated_damage"]["value"] == 3000


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

    assert item["affiliate_id"] == "aff-001"
    assert item["affiliate_name"] == "Affiliate Alpha"
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
            if "SELECT\n            conversion_time," in query:
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
            if "SELECT\n            conversion_time," in query:
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

    rows = console_service._fetch_alert_rows(
        DummyRepo(),
        start_date="2026-04-05",
        end_date="2026-04-05",
        status="unhandled",
        sort="risk_desc",
    )

    assert rows == []
    assert captured == ["Failed to fetch console alert rows"]
