from __future__ import annotations

from datetime import date, datetime

from fraud_checker.services import findings


def test_recompute_findings_persists_lineage_metadata_for_rows(monkeypatch):
    target_date = date(2026, 1, 21)
    settings_updated_at = datetime(2026, 1, 21, 8, 0, 0)
    click_watermark = datetime(2026, 1, 21, 9, 0, 0)
    conversion_watermark = datetime(2026, 1, 21, 10, 0, 0)
    captured: dict[str, list[dict]] = {}

    click_finding = type(
        "ClickFinding",
        (),
        {
            "ipaddress": "203.0.113.10",
            "useragent": "Mozilla/5.0 Chrome/120.0",
            "total_clicks": 80,
            "media_count": 2,
            "program_count": 1,
            "first_time": datetime(2026, 1, 21, 9, 0, 0),
            "last_time": datetime(2026, 1, 21, 9, 10, 0),
            "reasons": ["total_clicks >= 50"],
        },
    )()

    class DummyClickDetector:
        def __init__(self, repo, rules):
            pass

        def find_for_date(self, requested_date):
            assert requested_date == target_date
            return [click_finding]

    class DummyConversionDetector:
        def __init__(self, repo, rules):
            pass

        def find_for_date(self, requested_date):
            assert requested_date == target_date
            return []

    class DummyRepo:
        def get_settings_updated_at(self):
            return settings_updated_at

        def get_click_data_watermark(self, requested_date):
            assert requested_date == target_date
            return click_watermark

        def get_conversion_data_watermark(self, requested_date):
            assert requested_date == target_date
            return conversion_watermark

        def get_suspicious_click_details_bulk(self, requested_date, pairs):
            return {
                ("203.0.113.10", "Mozilla/5.0 Chrome/120.0"): [
                    {
                        "media_id": "m1",
                        "program_id": "p1",
                        "media_name": "Media 1",
                        "program_name": "Program 1",
                        "affiliate_name": "Affiliate 1",
                    }
                ]
            }

        def get_suspicious_conversion_details_bulk(self, requested_date, pairs):
            return {}

        def replace_click_findings(self, requested_date, rows):
            captured["click"] = rows

        def replace_conversion_findings(self, requested_date, rows):
            captured["conversion"] = rows

    monkeypatch.setattr(findings.settings_service, "get_settings", lambda repo: {"click_threshold": 50})
    monkeypatch.setattr(findings.settings_service, "build_rule_sets", lambda repo: (object(), object()))
    monkeypatch.setattr(findings, "SuspiciousDetector", DummyClickDetector)
    monkeypatch.setattr(findings, "ConversionSuspiciousDetector", DummyConversionDetector)

    findings.recompute_findings_for_dates(
        DummyRepo(),
        [target_date],
        computed_by_job_id="job-123",
        generation_id="gen-456",
    )

    row = captured["click"][0]
    assert row["computed_by_job_id"] == "job-123"
    assert row["generation_id"] == "gen-456"
    assert row["settings_updated_at_snapshot"] == settings_updated_at
    assert row["source_click_watermark"] == click_watermark
    assert row["source_conversion_watermark"] == conversion_watermark
