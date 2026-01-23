from __future__ import annotations

import argparse
import os
import sys
from datetime import timedelta

from .acs_client import AcsHttpClient
from .config import resolve_acs_settings, resolve_conversion_rules, resolve_rules, resolve_store_raw
from .ingestion import ClickLogIngestor, ConversionIngestor
from .repository_pg import PostgresRepository
from .suspicious import CombinedSuspiciousDetector
from .time_utils import now_local


def _require_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required for Postgres mode.")
    return database_url


def _build_repository(store_raw: bool) -> PostgresRepository:
    repo = PostgresRepository(_require_database_url())
    repo.ensure_schema(store_raw=store_raw)
    repo.ensure_conversion_schema()
    repo.ensure_master_schema()
    return repo


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

    refresh = sub.add_parser("refresh", help="Fetch ACS logs for the last N hours")
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

    sync = sub.add_parser("sync-masters", help="Sync master data from ACS")

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

    if not args.conversions_only:
        click_ingestor = ClickLogIngestor(
            client=client,
            repository=repository,
            page_size=settings.page_size,
            store_raw=store_raw,
        )
        click_new, click_skip = click_ingestor.run_for_time_range(start_time, end_time)
        print(f"Clicks: {click_new} new, {click_skip} skipped (already in DB)")

    if not args.clicks_only:
        conv_ingestor = ConversionIngestor(
            client=client,
            repository=repository,
            page_size=settings.page_size,
        )
        conv_new, conv_skip, conv_valid = conv_ingestor.run_for_time_range(
            start_time, end_time
        )
        print(
            f"Conversions: {conv_new} new, {conv_skip} skipped (already in DB), "
            f"{conv_valid} with valid entry IP/UA"
        )

    if args.detect:
        dates_to_check = set()
        current = start_time.date()
        while current <= end_time.date():
            dates_to_check.add(current)
            current += timedelta(days=1)

        click_rules = resolve_rules(
            click_threshold=None,
            media_threshold=None,
            program_threshold=None,
            burst_click_threshold=None,
            burst_window_seconds=None,
            browser_only=None,
            exclude_datacenter_ip=None,
        )
        conversion_rules = resolve_conversion_rules(
            conversion_threshold=None,
            media_threshold=None,
            program_threshold=None,
            burst_conversion_threshold=None,
            burst_window_seconds=None,
            browser_only=None,
            exclude_datacenter_ip=None,
            min_click_to_conv_seconds=None,
            max_click_to_conv_seconds=None,
        )

        print("\n--- Suspicious Detection ---")
        for target_date in sorted(dates_to_check):
            combined = CombinedSuspiciousDetector(
                repository=repository,
                click_rules=click_rules,
                conversion_rules=conversion_rules,
            )
            click_findings, conv_findings, high_risk = combined.find_for_date(target_date)
            if click_findings or conv_findings or high_risk:
                print(f"\n{target_date.isoformat()}:")
                print(f"  Suspicious clicks: {len(click_findings)}")
                print(f"  Suspicious conversions: {len(conv_findings)}")
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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "refresh":
        return _cmd_refresh(args)
    if args.command == "sync-masters":
        return _cmd_sync_masters()

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
