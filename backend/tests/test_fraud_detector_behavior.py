from __future__ import annotations

from datetime import date, datetime

from fraud_checker.fraud_detector import AcsNativeFraudDetector


def test_detector_skips_duplicate_guard_when_master_schema_is_legacy() -> None:
    class DummyRepo:
        def list_fraud_metric_rows(self, target_date: date):
            return {
                "checks": [],
                "tracks": [],
                "conversions": [
                    {
                        "id": "conv-1",
                        "user_id": "user-1",
                        "media_id": "media-1",
                        "program_id": "promo-1",
                        "conversion_time": datetime(2026, 4, 2, 12, 0, 0),
                        "click_time": datetime(2026, 4, 2, 11, 59, 55),
                        "state": "0",
                    }
                ],
                "click_metrics": [],
                "access_metrics": [],
                "imp_metrics": [],
            }

        def fetch_all(self, query, params=None):
            return []

        def fetch_one(self, query, params=None):
            if "FROM master_user" in query:
                return {"name": "User 1"}
            if "FROM master_media" in query:
                return {"name": "Media 1"}
            if "FROM master_promotion" in query:
                raise AssertionError("legacy schema should skip duplicate guard lookup")
            raise AssertionError(f"Unexpected query: {query}")

        def _column_exists(self, table_name: str, column_name: str) -> bool:
            return False

        def _table_exists(self, table_name: str) -> bool:
            return table_name == "master_promotion"

    settings = {
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
    }

    detector = AcsNativeFraudDetector(DummyRepo(), settings)

    assert detector.find_for_date(date(2026, 4, 2)) == []
