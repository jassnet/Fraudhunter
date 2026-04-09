from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta

import pytest

from fraud_checker import cli
from fraud_checker.models import ClickLog, ConversionIpUaRollup, ConversionLog


def _click(click_id: str, at: datetime) -> ClickLog:
    return ClickLog(
        click_id=click_id,
        click_time=at,
        media_id="m1",
        program_id="p1",
        ipaddress="1.1.1.1",
        useragent="Mozilla/5.0",
        referrer=None,
        raw_payload={},
    )


def _conversion(conversion_id: str, at: datetime) -> ConversionLog:
    return ConversionLog(
        conversion_id=conversion_id,
        cid="cid-1",
        conversion_time=at,
        click_time=at - timedelta(seconds=10),
        media_id="m1",
        program_id="p1",
        user_id="u1",
        postback_ipaddress="10.0.0.1",
        postback_useragent="postback",
        entry_ipaddress="2.2.2.2",
        entry_useragent="Mozilla/5.0",
        state="approved",
        raw_payload={},
    )


def test_require_database_url_raises_when_missing(monkeypatch):
    # Given
    monkeypatch.delenv("DATABASE_URL", raising=False)

    # When / Then
    with pytest.raises(SystemExit, match="DATABASE_URL is required"):
        cli._require_database_url()


def test_build_parser_accepts_refresh_sync_masters_and_worker():
    # Given
    parser = cli.build_parser()

    # When
    refresh_args = parser.parse_args(["refresh", "--hours", "3", "--detect"])
    sync_args = parser.parse_args(["sync-masters"])
    enqueue_refresh_args = parser.parse_args(["enqueue-refresh", "--hours", "2", "--detect"])
    enqueue_backfill_args = parser.parse_args(["enqueue-backfill", "--hours", "24", "--detect"])
    enqueue_sync_args = parser.parse_args(["enqueue-sync-masters"])
    worker_args = parser.parse_args(["run-worker", "--max-jobs", "2"])
    purge_args = parser.parse_args(["purge-data", "--execute", "--raw-days", "45"])

    # Then
    assert refresh_args.command == "refresh"
    assert refresh_args.hours == 3
    assert refresh_args.detect is True
    assert sync_args.command == "sync-masters"
    assert enqueue_refresh_args.command == "enqueue-refresh"
    assert enqueue_refresh_args.hours == 2
    assert enqueue_refresh_args.detect is True
    assert enqueue_backfill_args.command == "enqueue-backfill"
    assert enqueue_backfill_args.hours == 24
    assert enqueue_backfill_args.detect is True
    assert enqueue_sync_args.command == "enqueue-sync-masters"
    assert worker_args.command == "run-worker"
    assert worker_args.max_jobs == 2
    assert purge_args.command == "purge-data"
    assert purge_args.execute is True
    assert purge_args.raw_days == 45


def test_cmd_refresh_rejects_conflicting_flags():
    # Given
    args = argparse.Namespace(
        hours=1,
        clicks_only=True,
        conversions_only=True,
        detect=False,
        store_raw=None,
    )

    # When / Then
    with pytest.raises(SystemExit, match="Use only one"):
        cli._cmd_refresh(args)


def test_cmd_refresh_runs_ingestion_and_detection(monkeypatch, capsys):
    # Given
    class FakeSettings:
        page_size = 10

    class FakeClient:
        def fetch_click_logs_for_time_range(self, start_time, end_time, page, limit):
            if page == 1:
                return [_click("c1", datetime(2026, 1, 1, 0, 30, 0))]
            return []

        def fetch_conversion_logs_for_time_range(self, start_time, end_time, page, limit):
            if page == 1:
                return [_conversion("v1", datetime(2026, 1, 1, 0, 40, 0))]
            return []

    class FakeRepo:
        def __init__(self):
            self.store_raw_used = None

        def ensure_schema(self, store_raw=False):
            self.store_raw_used = store_raw

        def ensure_conversion_schema(self):
            return None

        def ensure_master_schema(self):
            return None

        def merge_clicks(self, clicks, *, store_raw):
            return len(list(clicks)), 0

        def merge_conversions(self, conversions):
            return len(list(conversions)), 0

        def enrich_conversions_with_click_info(self, conversions):
            return list(conversions)

        def load_settings(self):
            return {
                "click_threshold": 1,
                "media_threshold": 99,
                "program_threshold": 99,
                "burst_click_threshold": 99,
                "burst_window_seconds": 600,
                "conversion_threshold": 1,
                "conv_media_threshold": 99,
                "conv_program_threshold": 99,
                "burst_conversion_threshold": 99,
                "burst_conversion_window_seconds": 1800,
                "min_click_to_conv_seconds": None,
                "max_click_to_conv_seconds": None,
                "browser_only": False,
                "exclude_datacenter_ip": False,
            }

        def fetch_suspicious_conversion_rollups(
            self,
            target_date: date,
            *,
            conversion_threshold: int,
            media_threshold: int,
            program_threshold: int,
            burst_conversion_threshold: int,
            browser_only: bool,
            exclude_datacenter_ip: bool,
        ):
            start = datetime.combine(target_date, datetime.min.time())
            return [
                ConversionIpUaRollup(
                    date=target_date,
                    ipaddress="2.2.2.2",
                    useragent="Mozilla/5.0",
                    conversion_count=1,
                    media_count=1,
                    program_count=1,
                    first_conversion_time=start,
                    last_conversion_time=start + timedelta(seconds=10),
                )
            ]

        def fetch_click_to_conversion_gaps(self, target_date):
            return {}

        def fetch_conversion_rollups(self, target_date):
            return []

    fake_repo = FakeRepo()
    captured = {"store_raw_arg": None}
    monkeypatch.setattr(cli, "now_local", lambda: datetime(2026, 1, 1, 1, 0, 0))
    monkeypatch.setattr(cli, "resolve_store_raw", lambda explicit: False)

    def fake_build_repository(store_raw):
        captured["store_raw_arg"] = store_raw
        return fake_repo

    monkeypatch.setattr(cli, "_build_repository", fake_build_repository)
    monkeypatch.setattr(cli, "_build_client", lambda: (FakeClient(), FakeSettings()))
    monkeypatch.setattr(
        cli.findings_service,
        "recompute_findings_for_dates",
        lambda repo, dates: {
            target_date.isoformat(): {"suspicious_conversions": 1}
            for target_date in dates
        },
    )
    args = argparse.Namespace(
        hours=1,
        clicks_only=False,
        conversions_only=False,
        detect=True,
        store_raw=None,
    )

    # When
    code = cli._cmd_refresh(args)
    output = capsys.readouterr().out

    # Then
    assert code == 0
    assert captured["store_raw_arg"] is True
    assert "Clicks: 1 new, 0 skipped" in output
    assert "Conversions: 1 new, 0 skipped" in output
    assert "Suspicious conversions: 1" in output
    assert "Suspicious clicks" not in output


def test_cmd_refresh_skips_detection_when_detect_is_false(monkeypatch, capsys):
    # Given
    class FakeSettings:
        page_size = 10

    class FakeClient:
        def fetch_click_logs_for_time_range(self, start_time, end_time, page, limit):
            if page == 1:
                return [_click("c1", datetime(2026, 1, 1, 0, 30, 0))]
            return []

        def fetch_conversion_logs_for_time_range(self, start_time, end_time, page, limit):
            if page == 1:
                return [_conversion("v1", datetime(2026, 1, 1, 0, 40, 0))]
            return []

    class FakeRepo:
        def ensure_schema(self, store_raw=False):
            return None

        def ensure_conversion_schema(self):
            return None

        def ensure_master_schema(self):
            return None

        def merge_clicks(self, clicks, *, store_raw):
            return len(list(clicks)), 0

        def merge_conversions(self, conversions):
            return len(list(conversions)), 0

        def enrich_conversions_with_click_info(self, conversions):
            return list(conversions)

    recompute_calls: list[list[date]] = []
    monkeypatch.setattr(cli, "now_local", lambda: datetime(2026, 1, 1, 1, 0, 0))
    monkeypatch.setattr(cli, "resolve_store_raw", lambda explicit: True)
    monkeypatch.setattr(cli, "_build_repository", lambda store_raw: FakeRepo())
    monkeypatch.setattr(cli, "_build_client", lambda: (FakeClient(), FakeSettings()))
    monkeypatch.setattr(
        cli.findings_service,
        "recompute_findings_for_dates",
        lambda repo, dates: recompute_calls.append(dates) or {},
    )
    args = argparse.Namespace(
        hours=1,
        clicks_only=False,
        conversions_only=False,
        detect=False,
        store_raw=None,
    )

    # When
    code = cli._cmd_refresh(args)
    output = capsys.readouterr().out

    # Then
    assert code == 0
    assert recompute_calls == []
    assert "--- Suspicious Detection ---" not in output


def test_cmd_refresh_conversions_only_skips_click_warning(monkeypatch, capsys):
    # Given
    class FakeSettings:
        page_size = 10

    class FakeClient:
        def fetch_conversion_logs_for_time_range(self, start_time, end_time, page, limit):
            if page == 1:
                return [_conversion("v1", datetime(2026, 1, 1, 0, 40, 0))]
            return []

    class FakeRepo:
        def ensure_schema(self, store_raw=False):
            return None

        def ensure_conversion_schema(self):
            return None

        def ensure_master_schema(self):
            return None

        def merge_conversions(self, conversions):
            return len(list(conversions)), 0

        def enrich_conversions_with_click_info(self, conversions):
            return list(conversions)

    monkeypatch.setattr(cli, "now_local", lambda: datetime(2026, 1, 1, 1, 0, 0))
    monkeypatch.setattr(cli, "resolve_store_raw", lambda explicit: False)
    monkeypatch.setattr(cli, "_build_repository", lambda store_raw: FakeRepo())
    monkeypatch.setattr(cli, "_build_client", lambda: (FakeClient(), FakeSettings()))
    monkeypatch.setattr(
        cli.findings_service,
        "recompute_findings_for_dates",
        lambda repo, dates: {
            target_date.isoformat(): {"suspicious_conversions": 1}
            for target_date in dates
        },
    )
    args = argparse.Namespace(
        hours=1,
        clicks_only=False,
        conversions_only=True,
        detect=False,
        store_raw=None,
    )

    # When
    code = cli._cmd_refresh(args)
    output = capsys.readouterr().out

    # Then
    assert code == 0
    assert "[warning] --store-raw" not in output
    assert "Conversions: 1 new, 0 skipped" in output


def test_cmd_sync_masters_updates_all_master_types(monkeypatch, capsys):
    # Given
    class FakeClient:
        def fetch_all_media_master(self):
            return [{"id": "m1"}]

        def fetch_all_promotion_master(self):
            return [{"id": "p1"}, {"id": "p2"}]

        def fetch_all_user_master(self):
            return [{"id": "u1"}, {"id": "u2"}, {"id": "u3"}]

    class FakeRepo:
        def bulk_upsert_media(self, media_list):
            return len(media_list)

        def bulk_upsert_promotions(self, promo_list):
            return len(promo_list)

        def bulk_upsert_users(self, user_list):
            return len(user_list)

    monkeypatch.setattr(cli, "_build_repository", lambda store_raw: FakeRepo())
    monkeypatch.setattr(cli, "_build_client", lambda: (FakeClient(), object()))

    # When
    code = cli._cmd_sync_masters()
    output = capsys.readouterr().out

    # Then
    assert code == 0
    assert "Media masters: 1 records updated" in output
    assert "Promotion masters: 2 records updated" in output
    assert "User masters: 3 records updated" in output


def test_cmd_enqueue_refresh_registers_durable_job(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "enqueue_refresh_job",
        lambda **kwargs: type("QueuedJob", (), {"id": "job-refresh-1"})(),
    )
    monkeypatch.setattr(cli, "process_queued_jobs_after_cli_enqueue", lambda max_jobs=1: 0)

    code = cli._cmd_enqueue_refresh(
        argparse.Namespace(
            hours=2,
            clicks_only=False,
            conversions_only=True,
            detect=True,
        )
    )
    output = capsys.readouterr().out

    assert code == 0
    assert "=== Refresh Enqueued ===" in output
    assert "Job ID: job-refresh-1" in output
    assert "Clicks: False" in output
    assert "Conversions: True" in output


def test_cmd_enqueue_backfill_registers_durable_job(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "enqueue_refresh_job",
        lambda **kwargs: type("QueuedJob", (), {"id": "job-backfill-1"})(),
    )
    monkeypatch.setattr(cli, "process_queued_jobs_after_cli_enqueue", lambda max_jobs=1: 0)

    code = cli._cmd_enqueue_backfill(
        argparse.Namespace(
            hours=24,
            clicks_only=False,
            conversions_only=False,
            detect=True,
        )
    )
    output = capsys.readouterr().out

    assert code == 0
    assert "=== Backfill Enqueued ===" in output
    assert "Job ID: job-backfill-1" in output
    assert "Hours: 24" in output
    assert "Clicks: True" in output
    assert "Conversions: True" in output


def test_cmd_enqueue_sync_masters_registers_durable_job(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "enqueue_master_sync_job",
        lambda: type("QueuedJob", (), {"id": "job-master-1"})(),
    )
    monkeypatch.setattr(cli, "process_queued_jobs_after_cli_enqueue", lambda max_jobs=1: 0)

    code = cli._cmd_enqueue_sync_masters()
    output = capsys.readouterr().out

    assert code == 0
    assert "=== Master Sync Enqueued ===" in output
    assert "Job ID: job-master-1" in output


def test_main_prints_help_and_returns_1_for_unknown_command(capsys):
    # When
    code = cli.main([])
    output = capsys.readouterr().out

    # Then
    assert code == 1
    assert "Fraud checker maintenance tasks" in output


def test_cmd_run_worker_delegates_to_job_processor(monkeypatch, capsys):
    monkeypatch.setattr(cli, "process_queued_jobs", lambda max_jobs: 2)

    code = cli._cmd_run_worker(argparse.Namespace(max_jobs=3))
    output = capsys.readouterr().out

    assert code == 0
    assert "Processed 2 queued job(s)" in output


def test_cmd_purge_data_runs_lifecycle_service(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_build_repository", lambda store_raw: object())
    monkeypatch.setattr(cli, "_require_database_url", lambda: "postgresql://example/db")
    monkeypatch.setattr(cli, "JobStatusStorePG", lambda database_url: object())
    monkeypatch.setattr(
        cli.lifecycle,
        "resolve_retention_policy",
        lambda **kwargs: type("Policy", (), kwargs)(),
    )
    monkeypatch.setattr(
        cli.lifecycle,
        "purge_old_data",
        lambda repo, job_store, policy, execute: {
            "reference_time": "2026-03-24T00:00:00",
            "cutoffs": {
                "raw_before": "2025-12-24T00:00:00",
                "aggregates_before": "2025-03-24",
                "findings_before": "2025-03-24",
                "job_runs_before": "2026-02-23T00:00:00",
            },
            "counts": {
                "raw": {"click_raw": 10},
                "aggregates": {"click_ipua_daily": 20},
                "findings": {"suspicious_conversion_findings": 5},
                "job_runs": {"job_runs": 3},
            },
        },
    )

    code = cli._cmd_purge_data(
        argparse.Namespace(
            execute=False,
            raw_days=90,
            aggregate_days=365,
            findings_days=365,
            job_run_days=30,
        )
    )
    output = capsys.readouterr().out

    assert code == 0
    assert "=== Data Lifecycle Purge (DRY-RUN) ===" in output
    assert "Raw rows: {'click_raw': 10}" in output
    assert "Job runs: {'job_runs': 3}" in output
