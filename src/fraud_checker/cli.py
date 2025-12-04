from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Optional
import logging

from .acs_client import AcsHttpClient
from .config import (
    AcsSettings,
    resolve_acs_settings,
    resolve_conversion_rules,
    resolve_db_path,
    resolve_rules,
    resolve_store_raw,
)
from .ingestion import ClickLogIngestor, ConversionIngestor
from .repository import SQLiteRepository
from .suspicious import (
    CombinedSuspiciousDetector,
    ConversionSuspiciousDetector,
    SuspiciousDetector,
)


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

    # 成果ログ取り込みコマンド
    ingest_conv = sub.add_parser(
        "ingest-conversions",
        help="Fetch conversion logs and match with click logs for IP/UA",
    )
    ingest_conv.add_argument("--date", required=True, help="Target date (YYYY-MM-DD)")
    ingest_conv.add_argument("--db", help="SQLite DB path (defaults to FRAUD_DB_PATH)")
    ingest_conv.add_argument("--base-url", help="ACS base URL (defaults to ACS_BASE_URL)")
    ingest_conv.add_argument("--access-key", help="ACS access key (defaults to ACS_ACCESS_KEY)")
    ingest_conv.add_argument("--secret-key", help="ACS secret key (defaults to ACS_SECRET_KEY)")
    ingest_conv.add_argument("--page-size", type=int, help="Page size for ACS API")

    # 成果ベースの不正検知コマンド
    susp_conv = sub.add_parser(
        "suspicious-conversions",
        help="List suspicious IP/UA based on conversion patterns (using click-time IP/UA)",
    )
    susp_conv.add_argument("--date", required=True, help="Target date (YYYY-MM-DD)")
    susp_conv.add_argument("--db", help="SQLite DB path (defaults to FRAUD_DB_PATH)")
    susp_conv.add_argument(
        "--conversion-threshold",
        type=int,
        help="Min conversions per IP/UA (default: 5)",
    )
    susp_conv.add_argument(
        "--media-threshold",
        type=int,
        help="Min media count per IP/UA (default: 2)",
    )
    susp_conv.add_argument(
        "--program-threshold",
        type=int,
        help="Min program count per IP/UA (default: 2)",
    )
    susp_conv.add_argument(
        "--burst-conversion-threshold",
        type=int,
        help="Min conversions for burst detection (default: 3)",
    )
    susp_conv.add_argument(
        "--burst-window-seconds",
        type=int,
        help="Burst window in seconds (default: 1800)",
    )
    susp_conv.add_argument(
        "--browser-only",
        action="store_true",
        default=None,
        help="Only include browser-derived UA/IP",
    )
    susp_conv.add_argument(
        "--exclude-datacenter-ip",
        action="store_true",
        default=None,
        help="Exclude known datacenter IPs",
    )

    # クリック＋成果の両方を処理するコマンド
    daily_full = sub.add_parser(
        "daily-full",
        help="Run daily ingest for clicks AND conversions, then combined suspicious report",
    )
    daily_full.add_argument(
        "--days-ago", type=int, default=1, help="How many days ago (default: 1)"
    )
    daily_full.add_argument("--db", help="SQLite DB path")
    daily_full.add_argument("--base-url", help="ACS base URL")
    daily_full.add_argument("--endpoint", help="ACS log endpoint for clicks")
    daily_full.add_argument("--access-key", help="ACS access key")
    daily_full.add_argument("--secret-key", help="ACS secret key")
    daily_full.add_argument("--page-size", type=int, help="Page size for ACS API")
    daily_full.add_argument(
        "--store-raw",
        action="store_true",
        default=None,
        help="Persist raw click logs (required for conversion matching)",
    )
    # クリック用の閾値
    daily_full.add_argument("--click-threshold", type=int, help="Click threshold")
    daily_full.add_argument("--media-threshold", type=int, help="Media threshold (clicks)")
    daily_full.add_argument("--program-threshold", type=int, help="Program threshold (clicks)")
    daily_full.add_argument("--burst-click-threshold", type=int, help="Burst click threshold")
    daily_full.add_argument("--burst-window-seconds", type=int, help="Burst window (clicks)")
    # 成果用の閾値
    daily_full.add_argument("--conversion-threshold", type=int, help="Conversion threshold")
    daily_full.add_argument("--conv-media-threshold", type=int, help="Media threshold (conversions)")
    daily_full.add_argument("--conv-program-threshold", type=int, help="Program threshold (conversions)")
    daily_full.add_argument("--browser-only", action="store_true", default=None)
    daily_full.add_argument("--exclude-datacenter-ip", action="store_true", default=None)

    # リフレッシュコマンド（最新24時間のデータを取り込み）
    refresh = sub.add_parser(
        "refresh",
        help="Fetch the latest 24 hours of data and merge with existing data (no duplicates)",
    )
    refresh.add_argument(
        "--hours",
        type=int,
        default=24,
        help="How many hours back to fetch (default: 24)",
    )
    refresh.add_argument("--db", help="SQLite DB path")
    refresh.add_argument("--base-url", help="ACS base URL")
    refresh.add_argument("--endpoint", help="ACS log endpoint for clicks")
    refresh.add_argument("--access-key", help="ACS access key")
    refresh.add_argument("--secret-key", help="ACS secret key")
    refresh.add_argument("--page-size", type=int, help="Page size for ACS API")
    refresh.add_argument(
        "--store-raw",
        action="store_true",
        default=None,
        help="Persist raw click logs (required for duplicate detection)",
    )
    refresh.add_argument(
        "--clicks-only",
        action="store_true",
        help="Only refresh click logs (skip conversions)",
    )
    refresh.add_argument(
        "--conversions-only",
        action="store_true",
        help="Only refresh conversion logs (skip clicks)",
    )
    # 検知も実行するオプション
    refresh.add_argument(
        "--detect",
        action="store_true",
        help="Run suspicious detection after refresh",
    )
    refresh.add_argument("--click-threshold", type=int, help="Click threshold for detection")
    refresh.add_argument("--media-threshold", type=int, help="Media threshold for detection")
    refresh.add_argument("--program-threshold", type=int, help="Program threshold for detection")
    refresh.add_argument("--conversion-threshold", type=int, help="Conversion threshold")
    refresh.add_argument("--browser-only", action="store_true", default=None)
    refresh.add_argument("--exclude-datacenter-ip", action="store_true", default=None)

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
        if args.command == "ingest-conversions":
            return _cmd_ingest_conversions(args, acs_client_factory)
        if args.command == "suspicious-conversions":
            return _cmd_suspicious_conversions(args)
        if args.command == "daily-full":
            return _cmd_daily_full(args, acs_client_factory)
        if args.command == "refresh":
            return _cmd_refresh(args, acs_client_factory)
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


def _cmd_ingest_conversions(
    args: argparse.Namespace, acs_client_factory: Optional[Callable]
) -> int:
    """成果ログを取り込み、クリックログと突合"""
    target_date = _parse_date(args.date)
    db_path = resolve_db_path(args.db)
    acs_settings = resolve_acs_settings(
        base_url=args.base_url,
        access_key=args.access_key,
        secret_key=args.secret_key,
        page_size=args.page_size,
        log_endpoint=None,  # 成果ログはaction_log_rawを使用
    )

    repository = SQLiteRepository(db_path)
    repository.ensure_conversion_schema()

    factory = acs_client_factory or (
        lambda settings: AcsHttpClient(
            base_url=settings.base_url,
            access_key=settings.access_key,
            secret_key=settings.secret_key,
        )
    )
    client = factory(acs_settings)
    ingestor = ConversionIngestor(
        client=client,
        repository=repository,
        page_size=acs_settings.page_size,
    )

    total, enriched = ingestor.run_for_date(target_date)
    print(
        f"Ingested {total} conversion(s) for {target_date.isoformat()}, "
        f"{enriched} matched with click IP/UA"
    )
    return 0


def _cmd_suspicious_conversions(args: argparse.Namespace) -> int:
    """成果ベースの不正検知"""
    target_date = _parse_date(args.date)
    db_path = resolve_db_path(args.db)
    rules = resolve_conversion_rules(
        conversion_threshold=args.conversion_threshold,
        media_threshold=args.media_threshold,
        program_threshold=args.program_threshold,
        burst_conversion_threshold=args.burst_conversion_threshold,
        burst_window_seconds=args.burst_window_seconds,
        browser_only=args.browser_only,
        exclude_datacenter_ip=args.exclude_datacenter_ip,
    )

    repository = SQLiteRepository(db_path)
    detector = ConversionSuspiciousDetector(repository, rules)
    findings = detector.find_for_date(target_date)

    for finding in findings:
        window = finding.last_conversion_time - finding.first_conversion_time
        print(
            f"{finding.date} {finding.ipaddress} UA='{finding.useragent}' "
            f"conversions={finding.conversion_count} media={finding.media_count} "
            f"programs={finding.program_count} window={window} "
            f"reasons={'; '.join(finding.reasons)}"
        )
    print(
        f"Found {len(findings)} suspicious conversion IP/UA for {target_date.isoformat()}"
    )
    return 0


def _cmd_daily_full(
    args: argparse.Namespace, acs_client_factory: Optional[Callable]
) -> int:
    """クリック＋成果の両方を取り込み、統合検知を実行"""
    target_date = date.today() - timedelta(days=args.days_ago)
    db_path = resolve_db_path(args.db)
    # 成果と突合するためにstore_rawは必須
    store_raw = resolve_store_raw(args.store_raw)
    if not store_raw:
        print(
            "[warning] --store-raw is recommended for conversion matching. "
            "Set FRAUD_STORE_RAW=true or pass --store-raw"
        )
        store_raw = True  # 強制的に有効化

    acs_settings = resolve_acs_settings(
        base_url=args.base_url,
        access_key=args.access_key,
        secret_key=args.secret_key,
        page_size=args.page_size,
        log_endpoint=args.endpoint,
    )
    click_rules = resolve_rules(
        click_threshold=args.click_threshold,
        media_threshold=args.media_threshold,
        program_threshold=args.program_threshold,
        burst_click_threshold=args.burst_click_threshold,
        burst_window_seconds=args.burst_window_seconds,
        browser_only=args.browser_only,
        exclude_datacenter_ip=args.exclude_datacenter_ip,
    )
    conversion_rules = resolve_conversion_rules(
        conversion_threshold=args.conversion_threshold,
        media_threshold=args.conv_media_threshold,
        program_threshold=args.conv_program_threshold,
        browser_only=args.browser_only,
        exclude_datacenter_ip=args.exclude_datacenter_ip,
    )

    repository = SQLiteRepository(db_path)
    repository.ensure_schema(store_raw=store_raw)
    repository.ensure_conversion_schema()

    factory = acs_client_factory or (
        lambda settings: AcsHttpClient(
            base_url=settings.base_url,
            access_key=settings.access_key,
            secret_key=settings.secret_key,
            endpoint_path=settings.log_endpoint,
        )
    )
    client = factory(acs_settings)

    # 1. クリックログ取り込み
    click_ingestor = ClickLogIngestor(
        client=client,
        repository=repository,
        page_size=acs_settings.page_size,
        store_raw=store_raw,
    )
    click_count = click_ingestor.run_for_date(target_date)
    print(f"Ingested {click_count} click(s)")

    # 2. 成果ログ取り込み（クリックと突合）
    conv_ingestor = ConversionIngestor(
        client=client,
        repository=repository,
        page_size=acs_settings.page_size,
    )
    conv_total, conv_enriched = conv_ingestor.run_for_date(target_date)
    print(f"Ingested {conv_total} conversion(s), {conv_enriched} matched with click IP/UA")

    # 3. 統合検知
    combined = CombinedSuspiciousDetector(
        repository=repository,
        click_rules=click_rules,
        conversion_rules=conversion_rules,
    )
    click_findings, conv_findings, high_risk = combined.find_for_date(target_date)

    print(f"\n=== Daily Full Report for {target_date.isoformat()} ===")
    print(f"Clicks ingested: {click_count}")
    print(f"Conversions ingested: {conv_total} (matched: {conv_enriched})")
    print(f"Suspicious clicks: {len(click_findings)}")
    print(f"Suspicious conversions: {len(conv_findings)}")
    print(f"HIGH RISK (both click & conversion): {len(high_risk)}")

    if high_risk:
        print("\n--- HIGH RISK IP/UA (flagged in both clicks AND conversions) ---")
        for ip_ua in high_risk:
            print(f"  {ip_ua}")

    if click_findings:
        print("\n--- Suspicious Clicks ---")
        for f in click_findings[:10]:  # 上位10件
            print(
                f"  {f.ipaddress} clicks={f.total_clicks} media={f.media_count} "
                f"programs={f.program_count} reasons={'; '.join(f.reasons)}"
            )
        if len(click_findings) > 10:
            print(f"  ... and {len(click_findings) - 10} more")

    if conv_findings:
        print("\n--- Suspicious Conversions ---")
        for f in conv_findings[:10]:  # 上位10件
            print(
                f"  {f.ipaddress} conversions={f.conversion_count} media={f.media_count} "
                f"programs={f.program_count} reasons={'; '.join(f.reasons)}"
            )
        if len(conv_findings) > 10:
            print(f"  ... and {len(conv_findings) - 10} more")

    return 0


def _cmd_refresh(
    args: argparse.Namespace, acs_client_factory: Optional[Callable]
) -> int:
    """最新データを取り込み、既存データとマージ（重複なし）"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=args.hours)
    
    db_path = resolve_db_path(args.db)
    store_raw = resolve_store_raw(args.store_raw)
    
    # 重複検出のためにstore_rawを推奨
    if not store_raw and not args.conversions_only:
        print(
            "[warning] --store-raw is recommended for duplicate detection in clicks. "
            "Set FRAUD_STORE_RAW=true or pass --store-raw"
        )
        store_raw = True
    
    acs_settings = resolve_acs_settings(
        base_url=args.base_url,
        access_key=args.access_key,
        secret_key=args.secret_key,
        page_size=args.page_size,
        log_endpoint=args.endpoint,
    )

    repository = SQLiteRepository(db_path)
    repository.ensure_schema(store_raw=store_raw)
    repository.ensure_conversion_schema()

    factory = acs_client_factory or (
        lambda settings: AcsHttpClient(
            base_url=settings.base_url,
            access_key=settings.access_key,
            secret_key=settings.secret_key,
            endpoint_path=settings.log_endpoint,
        )
    )
    client = factory(acs_settings)

    print(f"\n=== Refresh: {start_time.isoformat()} to {end_time.isoformat()} ===")
    print(f"(Last {args.hours} hours)")

    click_new = 0
    click_skip = 0
    conv_new = 0
    conv_skip = 0
    conv_valid = 0

    # クリックログの取り込み
    if not args.conversions_only:
        click_ingestor = ClickLogIngestor(
            client=client,
            repository=repository,
            page_size=acs_settings.page_size,
            store_raw=store_raw,
        )
        click_new, click_skip = click_ingestor.run_for_time_range(start_time, end_time)
        print(f"Clicks: {click_new} new, {click_skip} skipped (already in DB)")

    # 成果ログの取り込み
    if not args.clicks_only:
        conv_ingestor = ConversionIngestor(
            client=client,
            repository=repository,
            page_size=acs_settings.page_size,
        )
        conv_new, conv_skip, conv_valid = conv_ingestor.run_for_time_range(
            start_time, end_time
        )
        print(
            f"Conversions: {conv_new} new, {conv_skip} skipped (already in DB), "
            f"{conv_valid} with valid entry IP/UA"
        )

    # 検知を実行（オプション）
    if args.detect:
        # 対象日付を特定（時間範囲に含まれる日付）
        dates_to_check = set()
        current = start_time.date()
        while current <= end_time.date():
            dates_to_check.add(current)
            current += timedelta(days=1)
        
        click_rules = resolve_rules(
            click_threshold=args.click_threshold,
            media_threshold=args.media_threshold,
            program_threshold=args.program_threshold,
            browser_only=args.browser_only,
            exclude_datacenter_ip=args.exclude_datacenter_ip,
        )
        conversion_rules = resolve_conversion_rules(
            conversion_threshold=args.conversion_threshold,
            media_threshold=args.media_threshold,
            program_threshold=args.program_threshold,
            browser_only=args.browser_only,
            exclude_datacenter_ip=args.exclude_datacenter_ip,
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
                
                if high_risk:
                    for ip_ua in high_risk[:5]:
                        print(f"    - {ip_ua}")
                    if len(high_risk) > 5:
                        print(f"    ... and {len(high_risk) - 5} more")

    print("\n=== Refresh Complete ===")
    print(f"Total: {click_new + conv_new} new records added, {click_skip + conv_skip} duplicates skipped")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
