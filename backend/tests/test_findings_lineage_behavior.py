from __future__ import annotations

from datetime import date, datetime

from fraud_checker.services import findings


def test_recompute_findings_persists_lineage_metadata_for_conversion_rows(monkeypatch):
    target_date = date(2026, 1, 21)
    settings_updated_at = datetime(2026, 1, 21, 8, 0, 0)
    click_watermark = datetime(2026, 1, 21, 9, 0, 0)
    conversion_watermark = datetime(2026, 1, 21, 10, 0, 0)
    captured: dict[str, list[dict]] = {}
    captured_generations: dict[str, dict] = {}

    conversion_finding = type(
        "ConversionFinding",
        (),
        {
            "ipaddress": "203.0.113.10",
            "useragent": "Mozilla/5.0 Chrome/120.0",
            "conversion_count": 6,
            "media_count": 2,
            "program_count": 1,
            "first_conversion_time": datetime(2026, 1, 21, 11, 0, 0),
            "last_conversion_time": datetime(2026, 1, 21, 11, 10, 0),
            "reasons": ["conversion_count >= 5"],
            "min_click_to_conv_seconds": 10,
            "max_click_to_conv_seconds": 30,
            "linked_click_count": 12,
            "linked_clicks_per_conversion": 2.0,
            "extra_window_click_count": 0,
            "extra_window_non_browser_ratio": None,
        },
    )()

    class DummyConversionDetector:
        def __init__(self, repo, rules):
            pass

        def find_for_date(self, requested_date):
            assert requested_date == target_date
            return [conversion_finding]

    class DummyRepo:
        def get_settings_updated_at(self):
            return settings_updated_at

        def ensure_settings_version(self, settings, fingerprint):
            assert fingerprint
            return "settings-ver-1"

        def get_click_data_watermark(self, requested_date):
            assert requested_date == target_date
            return click_watermark

        def get_conversion_data_watermark(self, requested_date):
            assert requested_date == target_date
            return conversion_watermark

        def get_suspicious_conversion_details_bulk(self, requested_date, pairs):
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

        def replace_conversion_findings(self, requested_date, rows, *, generation_metadata):
            captured["conversion"] = rows
            captured_generations["conversion"] = generation_metadata

    monkeypatch.setattr(findings.settings_service, "get_settings", lambda repo: {"conversion_threshold": 5})
    monkeypatch.setattr(findings.settings_service, "build_rule_sets", lambda repo: (object(), object()))
    monkeypatch.setattr(findings, "ConversionSuspiciousDetector", DummyConversionDetector)

    findings.recompute_findings_for_dates(
        DummyRepo(),
        [target_date],
        computed_by_job_id="job-123",
        generation_id="gen-456",
    )

    row = captured["conversion"][0]
    assert row["computed_by_job_id"] == "job-123"
    assert row["generation_id"] == "gen-456"
    assert row["settings_updated_at_snapshot"] == settings_updated_at
    assert row["source_click_watermark"] == click_watermark
    assert row["source_conversion_watermark"] == conversion_watermark
    assert captured_generations["conversion"]["settings_version_id"] == "settings-ver-1"
    assert captured_generations["conversion"]["generation_id"] == "gen-456"
    assert captured_generations["conversion"]["source_click_watermark"] == click_watermark
    assert captured_generations["conversion"]["source_conversion_watermark"] == conversion_watermark
    assert captured_generations["conversion"]["row_count"] == 1
