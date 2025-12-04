from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Callable, Optional
import logging

from .acs_client import AcsHttpClient
from .config import (
    AcsSettings,
    resolve_acs_settings,
    resolve_db_path,
    resolve_rules,
    resolve_store_raw,
)
from .ingestion import ClickLogIngestor
from .repository import SQLiteRepository
from .suspicious import SuspiciousDetector


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ACS click log fraud checker")
    sub = parser.add_subparsers(dest="command")

    ingest = sub.add_parser("ingest", help="Fetch click logs and aggregate per IP/UA")
    ingest.add_argument("--date", required=True, help="Target date (YYYY-MM-DD)")
    ingest.add_argument("--db", help="SQLite DB path (defaults to FRAUD_DB_PATH)")
    ingest.add_argument("--base-url", help="ACS base URL (defaults to ACS_BASE_URL)")
    ingest.add_argument(
        "--endpoint",
        help="ACS log endpoint path (defaults to ACS_LOG_ENDPOINT or access_log/search)",
    )
    ingest.add_argument("--access-key", help="ACS access key (defaults to ACS_ACCESS_KEY)")
    ingest.add_argument("--secret-key", help="ACS secret key (defaults to ACS_SECRET_KEY)")
    ingest.add_argument("--page-size", type=int, help="Page size for ACS API (FRAUD_PAGE_SIZE)")
    ingest.add_argument(
        "--store-raw",
        action="store_true",
        default=None,
        help="Persist raw click logs into click_raw table (overrides FRAUD_STORE_RAW)",
    )

    suspicious = sub.add_parser("suspicious", help="List suspicious IP/UA combinations")
    suspicious.add_argument("--date", required=True, help="Target date (YYYY-MM-DD)")
    suspicious.add_argument("--db", help="SQLite DB path (defaults to FRAUD_DB_PATH)")
    suspicious.add_argument("--click-threshold", type=int, help="Override FRAUD_CLICK_THRESHOLD")
    suspicious.add_argument("--media-threshold", type=int, help="Override FRAUD_MEDIA_THRESHOLD")
    suspicious.add_argument("--program-threshold", type=int, help="Override FRAUD_PROGRAM_THRESHOLD")
    suspicious.add_argument("--burst-click-threshold", type=int, help="Override FRAUD_BURST_CLICK_THRESHOLD")
    suspicious.add_argument("--burst-window-seconds", type=int, help="Override FRAUD_BURST_WINDOW_SECONDS")
    suspicious.add_argument(
        "--browser-only",
        action="store_true",
        default=None,
        help="Only include browser-derived UA/IP (excludes postback/server traffic)",
    )
    suspicious.add_argument(
        "--exclude-datacenter-ip",
        action="store_true",
        default=None,
        help="Exclude known datacenter IPs (Google, AWS, Azure, GCP)",
    )

    daily = sub.add_parser("daily", help="Run daily ingest (yesterday by default) then suspicious report")
    daily.add_argument("--days-ago", type=int, default=1, help="How many days ago to target (default: 1)")
    daily.add_argument("--db", help="SQLite DB path (defaults to FRAUD_DB_PATH)")
    daily.add_argument("--base-url", help="ACS base URL (defaults to ACS_BASE_URL)")
    daily.add_argument(
        "--endpoint",
        help="ACS log endpoint path (defaults to ACS_LOG_ENDPOINT or access_log/search)",
    )
    daily.add_argument("--access-key", help="ACS access key (defaults to ACS_ACCESS_KEY)")
    daily.add_argument("--secret-key", help="ACS secret key (defaults to ACS_SECRET_KEY)")
    daily.add_argument("--page-size", type=int, help="Page size for ACS API (FRAUD_PAGE_SIZE)")
    daily.add_argument(
        "--store-raw",
        action="store_true",
        default=None,
        help="Persist raw click logs into click_raw table (overrides FRAUD_STORE_RAW)",
    )
    daily.add_argument("--click-threshold", type=int, help="Override FRAUD_CLICK_THRESHOLD")
    daily.add_argument("--media-threshold", type=int, help="Override FRAUD_MEDIA_THRESHOLD")
    daily.add_argument("--program-threshold", type=int, help="Override FRAUD_PROGRAM_THRESHOLD")
    daily.add_argument("--burst-click-threshold", type=int, help="Override FRAUD_BURST_CLICK_THRESHOLD")
    daily.add_argument("--burst-window-seconds", type=int, help="Override FRAUD_BURST_WINDOW_SECONDS")
    daily.add_argument(
        "--browser-only",
        action="store_true",
        default=None,
        help="Only include browser-derived UA/IP (excludes postback/server traffic)",
    )
    daily.add_argument(
        "--exclude-datacenter-ip",
        action="store_true",
        default=None,
        help="Exclude known datacenter IPs (Google, AWS, Azure, GCP)",
    )

    return parser


def main(
    argv: Optional[list[str]] = None,
    acs_client_factory: Optional[Callable[[AcsSettings], object]] = None,
) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "ingest":
            return _cmd_ingest(args, acs_client_factory)
        if args.command == "suspicious":
            return _cmd_suspicious(args)
        if args.command == "daily":
            return _cmd_daily(args, acs_client_factory)
    except ValueError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    parser.print_help()
    return 1


def _cmd_ingest(args: argparse.Namespace, acs_client_factory: Optional[Callable]) -> int:
    target_date = _parse_date(args.date)
    db_path = resolve_db_path(args.db)
    store_raw = resolve_store_raw(args.store_raw)
    acs_settings = resolve_acs_settings(
        base_url=args.base_url,
        access_key=args.access_key,
        secret_key=args.secret_key,
        page_size=args.page_size,
        log_endpoint=args.endpoint,
    )

    repository = SQLiteRepository(db_path)
    repository.ensure_schema(store_raw=store_raw)
    factory = acs_client_factory or (
        lambda settings: AcsHttpClient(
            base_url=settings.base_url,
            access_key=settings.access_key,
            secret_key=settings.secret_key,
            endpoint_path=settings.log_endpoint,
        )
    )
    client = factory(acs_settings)
    ingestor = ClickLogIngestor(
        client=client,
        repository=repository,
        page_size=acs_settings.page_size,
        store_raw=store_raw,
    )
    count = ingestor.run_for_date(target_date)
    print(f"Ingested {count} click(s) for {target_date.isoformat()}")
    return 0


def _cmd_suspicious(args: argparse.Namespace) -> int:
    target_date = _parse_date(args.date)
    db_path = resolve_db_path(args.db)
    rules = resolve_rules(
        click_threshold=args.click_threshold,
        media_threshold=args.media_threshold,
        program_threshold=args.program_threshold,
        burst_click_threshold=args.burst_click_threshold,
        burst_window_seconds=args.burst_window_seconds,
        browser_only=args.browser_only,
        exclude_datacenter_ip=args.exclude_datacenter_ip,
    )

    repository = SQLiteRepository(db_path)
    repository.ensure_schema(store_raw=False)
    detector = SuspiciousDetector(repository, rules)
    findings = detector.find_for_date(target_date)
    for finding in findings:
        print(
            f"{finding.date} {finding.ipaddress} UA='{finding.useragent}' "
            f"clicks={finding.total_clicks} media={finding.media_count} "
            f"programs={finding.program_count} "
            f"window={(finding.last_time - finding.first_time)} "
            f"reasons={'; '.join(finding.reasons)}"
        )
    print(f"Found {len(findings)} suspicious IP/UA for {target_date.isoformat()}")
    return 0


def _cmd_daily(args: argparse.Namespace, acs_client_factory: Optional[Callable]) -> int:
    target_date = date.today() - timedelta(days=args.days_ago)
    db_path = resolve_db_path(args.db)
    store_raw = resolve_store_raw(args.store_raw)
    acs_settings = resolve_acs_settings(
        base_url=args.base_url,
        access_key=args.access_key,
        secret_key=args.secret_key,
        page_size=args.page_size,
        log_endpoint=args.endpoint,
    )
    rules = resolve_rules(
        click_threshold=args.click_threshold,
        media_threshold=args.media_threshold,
        program_threshold=args.program_threshold,
        burst_click_threshold=args.burst_click_threshold,
        burst_window_seconds=args.burst_window_seconds,
        browser_only=args.browser_only,
        exclude_datacenter_ip=args.exclude_datacenter_ip,
    )

    repository = SQLiteRepository(db_path)
    repository.ensure_schema(store_raw=store_raw)
    factory = acs_client_factory or (
        lambda settings: AcsHttpClient(
            base_url=settings.base_url,
            access_key=settings.access_key,
            secret_key=settings.secret_key,
        )
    )
    client = factory(acs_settings)
    ingestor = ClickLogIngestor(
        client=client,
        repository=repository,
        page_size=acs_settings.page_size,
        store_raw=store_raw,
    )
    ingested = ingestor.run_for_date(target_date)

    detector = SuspiciousDetector(repository, rules)
    findings = detector.find_for_date(target_date)

    print(
        f"Daily run for {target_date.isoformat()}: "
        f"{ingested} ingested, {len(findings)} suspicious."
    )
    for finding in findings:
        print(
            f"{finding.date} {finding.ipaddress} UA='{finding.useragent}' "
            f"clicks={finding.total_clicks} media={finding.media_count} "
            f"programs={finding.program_count} "
            f"window={(finding.last_time - finding.first_time)} "
            f"reasons={'; '.join(finding.reasons)}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
