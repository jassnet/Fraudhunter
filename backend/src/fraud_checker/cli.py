from __future__ import annotations

import argparse
import os
import sys
from datetime import timedelta

from .acs_client import AcsHttpClient
from .config import resolve_acs_settings, resolve_store_raw
from .env import load_env
from .ingestion import ClickLogIngestor, ConversionIngestor
from .job_status_pg import JobStatusStorePG
from .repository_pg import PostgresRepository
from .suspicious import CombinedSuspiciousDetector
from .services import findings as findings_service, lifecycle, settings as settings_service
from .services.jobs import (
    enqueue_master_sync_job,
    enqueue_refresh_job,
    process_queued_jobs,
    process_queued_jobs_after_cli_enqueue,
)
from .time_utils import now_local

DEFAULT_BACKFILL_HOURS = 24


def _require_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required for Postgres mode.")
    return database_url


def _build_repository(store_raw: bool) -> PostgresRepository:
    del store_raw
    return PostgresRepository(_require_database_url())


def _build_client() -> tuple[AcsHttpClient, object]:
    settings = resolve_acs_settings()
    client = AcsHttpClient(
        base_url=settings.base_url,
        access_key=settings.access_key,
        secret_key=settings.secret_key,
        endpoint_path=settings.log_endpoint,
    )
    return client, settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fraud checker maintenance tasks")
    sub = parser.add_subparsers(dest="command")

    refresh = sub.add_parser("refresh", help="Fetch ACS logs for the last N hours (break-glass inline run)")
    refresh.add_argument("--hours", type=int, default=1, help="Lookback window in hours")
    refresh.add_argument("--clicks-only", action="store_true", help="Only ingest clicks")
    refresh.add_argument("--conversions-only", action="store_true", help="Only ingest conversions")
    refresh.add_argument("--detect", action="store_true", help="Run suspicious detection after ingest")
    refresh.add_argument(
        "--store-raw",
        action="store_true",
        default=None,
        help="Persist raw click logs (overrides FRAUD_STORE_RAW)",
    )

    sync = sub.add_parser("sync-masters", help="Sync master data from ACS (break-glass inline run)")

    enqueue_refresh = sub.add_parser(
        "enqueue-refresh",
        help="Enqueue ACS log refresh as a durable job",
    )
    enqueue_refresh.add_argument("--hours", type=int, default=1, help="Lookback window in hours")
    enqueue_refresh.add_argument("--clicks-only", action="store_true", help="Only ingest clicks")
    enqueue_refresh.add_argument(
        "--conversions-only",
        action="store_true",
        help="Only ingest conversions",
    )
    enqueue_refresh.add_argument("--detect", action="store_true", help="Run suspicious detection after ingest")

    enqueue_backfill = sub.add_parser(
        "enqueue-backfill",
        help="Enqueue wider ACS backfill for initial sync or gap recovery",
    )
    enqueue_backfill.add_argument(
        "--hours",
        type=int,
        default=DEFAULT_BACKFILL_HOURS,
        help="Lookback window in hours",
    )
    enqueue_backfill.add_argument("--clicks-only", action="store_true", help="Only ingest clicks")
    enqueue_backfill.add_argument(
        "--conversions-only",
        action="store_true",
        help="Only ingest conversions",
    )
    enqueue_backfill.add_argument("--detect", action="store_true", help="Run suspicious detection after ingest")

    sub.add_parser(
        "enqueue-sync-masters",
        help="Enqueue master sync as a durable job",
    )

    worker = sub.add_parser("run-worker", help="Run queued durable jobs")
    worker.add_argument("--max-jobs", type=int, default=1, help="Maximum jobs to process")

    purge = sub.add_parser("purge-data", help="Purge old monitoring data by retention policy")
    purge.add_argument("--execute", action="store_true", help="Delete matching rows instead of dry-run")
    purge.add_argument("--raw-days", type=int, default=None, help="Retention days for raw tables")
    purge.add_argument(
        "--aggregate-days",
        type=int,
        default=None,
        help="Retention days for aggregate tables",
    )
    purge.add_argument(
        "--findings-days",
        type=int,
        default=None,
        help="Retention days for persisted findings",
    )
    purge.add_argument(
        "--job-run-days",
        type=int,
        default=None,
        help="Retention days for finished job runs",
    )

    return parser


def _cmd_refresh(args: argparse.Namespace) -> int:
    if args.clicks_only and args.conversions_only:
        raise SystemExit("Use only one of --clicks-only or --conversions-only.")

    end_time = now_local()
    start_time = end_time - timedelta(hours=args.hours)

    store_raw = resolve_store_raw(args.store_raw)
    if not store_raw and not args.conversions_only:
        print(
            "[warning] --store-raw is recommended for duplicate detection in clicks. "
            "Set FRAUD_STORE_RAW=true or pass --store-raw"
        )
        store_raw = True

    repository = _build_repository(store_raw)
    client, settings = _build_client()

    print(f"\n=== Refresh: {start_time.isoformat()} to {end_time.isoformat()} ===")
    print(f"(Last {args.hours} hours)")

    click_new = 0
    click_skip = 0
    conv_new = 0
    conv_skip = 0
    conv_valid = 0
    conv_click_enriched = 0
    dates_to_recompute: set[date] = set()

    if not args.conversions_only:
        click_ingestor = ClickLogIngestor(
            client=client,
            repository=repository,
            page_size=settings.page_size,
            store_raw=store_raw,
        )
        click_new, click_skip = click_ingestor.run_for_time_range(start_time, end_time)
        print(f"Clicks: {click_new} new, {click_skip} skipped (already in DB)")
        current = start_time.date()
        while current <= end_time.date():
            dates_to_recompute.add(current)
            current += timedelta(days=1)

    if not args.clicks_only:
        conv_ingestor = ConversionIngestor(
            client=client,
            repository=repository,
            page_size=settings.page_size,
        )
        conv_new, conv_skip, conv_valid, conv_click_enriched = conv_ingestor.run_for_time_range(
            start_time, end_time
        )
        print(
            f"Conversions: {conv_new} new, {conv_skip} skipped (already in DB), "
            f"{conv_valid} with valid entry IP/UA, "
            f"{conv_click_enriched} enriched from click data"
        )
        current = start_time.date()
        while current <= end_time.date():
            dates_to_recompute.add(current)
            current += timedelta(days=1)

    persisted = findings_service.recompute_findings_for_dates(repository, sorted(dates_to_recompute))

    if args.detect:
        click_rules, conversion_rules = settings_service.build_rule_sets(repository)

        print("\n--- Suspicious Detection ---")
        for target_date in sorted(dates_to_recompute):
            combined = CombinedSuspiciousDetector(
                repository=repository,
                click_rules=click_rules,
                conversion_rules=conversion_rules,
            )
            _, _, high_risk = combined.find_for_date(target_date)
            counts = persisted.get(target_date.isoformat(), {})
            click_count = counts.get("suspicious_clicks", 0)
            conv_count = counts.get("suspicious_conversions", 0)
            if click_count or conv_count or high_risk:
                print(f"\n{target_date.isoformat()}:")
                print(f"  Suspicious clicks: {click_count}")
                print(f"  Suspicious conversions: {conv_count}")
                print(f"  HIGH RISK (both): {len(high_risk)}")

    print("\n=== Refresh Complete ===")
    print(
        f"Total: {click_new + conv_new} new records added, {click_skip + conv_skip} duplicates skipped"
    )
    return 0


def _cmd_sync_masters() -> int:
    repository = _build_repository(store_raw=False)
    client, settings = _build_client()
    del settings

    print("=== Master Sync ===")
    media_list = client.fetch_all_media_master()
    media_count = repository.bulk_upsert_media(media_list)
    print(f"Media masters: {media_count} records updated")

    promo_list = client.fetch_all_promotion_master()
    promo_count = repository.bulk_upsert_promotions(promo_list)
    print(f"Promotion masters: {promo_count} records updated")

    user_list = client.fetch_all_user_master()
    user_count = repository.bulk_upsert_users(user_list)
    print(f"User masters: {user_count} records updated")

    print("=== Master Sync Complete ===")
    return 0


def _cmd_enqueue_refresh(args: argparse.Namespace) -> int:
    if args.clicks_only and args.conversions_only:
        raise SystemExit("Use only one of --clicks-only or --conversions-only.")

    clicks = not args.conversions_only
    conversions = not args.clicks_only
    job = enqueue_refresh_job(
        hours=args.hours,
        clicks=clicks,
        conversions=conversions,
        detect=args.detect,
    )
    print("=== Refresh Enqueued ===")
    print(f"Job ID: {job.id}")
    print(f"Hours: {args.hours}")
    print(f"Clicks: {clicks}")
    print(f"Conversions: {conversions}")
    print(f"Detect: {args.detect}")
    processed = process_queued_jobs_after_cli_enqueue(max_jobs=1)
    if processed:
        print(f"Processed {processed} queued job(s) (dev in-process kick)")
    return 0


def _cmd_enqueue_backfill(args: argparse.Namespace) -> int:
    if args.clicks_only and args.conversions_only:
        raise SystemExit("Use only one of --clicks-only or --conversions-only.")

    clicks = not args.conversions_only
    conversions = not args.clicks_only
    job = enqueue_refresh_job(
        hours=args.hours,
        clicks=clicks,
        conversions=conversions,
        detect=args.detect,
    )
    print("=== Backfill Enqueued ===")
    print(f"Job ID: {job.id}")
    print(f"Hours: {args.hours}")
    print(f"Clicks: {clicks}")
    print(f"Conversions: {conversions}")
    print(f"Detect: {args.detect}")
    processed = process_queued_jobs_after_cli_enqueue(max_jobs=1)
    if processed:
        print(f"Processed {processed} queued job(s) (dev in-process kick)")
    return 0


def _cmd_enqueue_sync_masters() -> int:
    job = enqueue_master_sync_job()
    print("=== Master Sync Enqueued ===")
    print(f"Job ID: {job.id}")
    processed = process_queued_jobs_after_cli_enqueue(max_jobs=1)
    if processed:
        print(f"Processed {processed} queued job(s) (dev in-process kick)")
    return 0


def _cmd_run_worker(args: argparse.Namespace) -> int:
    processed = process_queued_jobs(max_jobs=args.max_jobs)
    print(f"Processed {processed} queued job(s)")
    return 0


def _cmd_purge_data(args: argparse.Namespace) -> int:
    repository = _build_repository(store_raw=False)
    job_store = JobStatusStorePG(_require_database_url())
    policy = lifecycle.resolve_retention_policy(
        raw_days=args.raw_days,
        aggregate_days=args.aggregate_days,
        findings_days=args.findings_days,
        job_run_days=args.job_run_days,
    )
    result = lifecycle.purge_old_data(
        repository,
        job_store,
        policy=policy,
        execute=args.execute,
    )

    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print(f"=== Data Lifecycle Purge ({mode}) ===")
    print(f"Reference time: {result['reference_time']}")
    print(f"Raw cutoff: {result['cutoffs']['raw_before']}")
    print(f"Aggregate cutoff: {result['cutoffs']['aggregates_before']}")
    print(f"Findings cutoff: {result['cutoffs']['findings_before']}")
    print(f"Job runs cutoff: {result['cutoffs']['job_runs_before']}")
    print(f"Raw rows: {result['counts']['raw']}")
    print(f"Aggregate rows: {result['counts']['aggregates']}")
    print(f"Findings rows: {result['counts']['findings']}")
    print(f"Job runs: {result['counts']['job_runs']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    load_env()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "refresh":
        return _cmd_refresh(args)
    if args.command == "sync-masters":
        return _cmd_sync_masters()
    if args.command == "enqueue-refresh":
        return _cmd_enqueue_refresh(args)
    if args.command == "enqueue-backfill":
        return _cmd_enqueue_backfill(args)
    if args.command == "enqueue-sync-masters":
        return _cmd_enqueue_sync_masters()
    if args.command == "run-worker":
        return _cmd_run_worker(args)
    if args.command == "purge-data":
        return _cmd_purge_data(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
