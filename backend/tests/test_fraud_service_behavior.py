from __future__ import annotations

from fraud_checker.services import fraud


def test_get_fraud_findings_falls_back_to_dashboard_date_when_no_rows_exist(monkeypatch):
    class DummyRepo:
        def fetch_one(self, query, params=None):
            return {"last_date": None}

        def list_fraud_findings(self, **kwargs):
            return [], 0

    monkeypatch.setattr(fraud.reporting, "resolve_summary_date", lambda repo, target_date: "2026-04-03")

    payload = fraud.get_fraud_findings(
        DummyRepo(),
        target_date=None,
        limit=50,
        offset=0,
        search=None,
        risk_level=None,
        sort_by="count",
        sort_order="desc",
    )

    assert payload == {
        "date": "2026-04-03",
        "data": [],
        "total": 0,
        "limit": 50,
        "offset": 0,
    }
