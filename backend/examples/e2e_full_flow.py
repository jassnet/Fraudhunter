"""
E2E フルフローテスト: クリック取り込み → 成果取り込み＆突合 → 検知

使い方:
  python examples/e2e_full_flow.py --date 2024-01-01 --db ./test_e2e.db

環境変数 (.env) の ACS_BASE_URL / ACS_ACCESS_KEY / ACS_SECRET_KEY を利用します。
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

from fraud_checker.acs_client import AcsHttpClient
from fraud_checker.config import (
    resolve_acs_settings,
    resolve_conversion_rules,
    resolve_rules,
)
from fraud_checker.env import load_env
from fraud_checker.ingestion import ClickLogIngestor, ConversionIngestor
from fraud_checker.repository import SQLiteRepository
from fraud_checker.suspicious import CombinedSuspiciousDetector


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="E2Eフルフローテスト")
    parser.add_argument(
        "--date",
        help="対象日付 (YYYY-MM-DD)。省略時は昨日",
    )
    parser.add_argument(
        "--db",
        required=True,
        help="DBパス（必須）",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=500,
        help="APIページサイズ (default: 500)",
    )
    # 検知閾値のオプション
    parser.add_argument("--click-threshold", type=int, help="クリック数閾値")
    parser.add_argument("--conversion-threshold", type=int, help="成果数閾値")
    args = parser.parse_args()

    load_env()

    target_date = _parse_date(args.date) if args.date else date.today() - timedelta(days=1)
    db_path = Path(args.db)

    print("=" * 70)
    print("E2E フルフローテスト")
    print("=" * 70)
    print(f"対象日付: {target_date.isoformat()}")
    print(f"DBパス: {db_path}")
    print()

    # 設定解決
    try:
        settings = resolve_acs_settings(
            base_url=None,
            access_key=None,
            secret_key=None,
            page_size=args.page_size,
            log_endpoint=None,
        )
    except ValueError as e:
        print(f"[ERROR] 設定エラー: {e}")
        return 1

    print(f"ACS接続先: {settings.base_url}")
    print(f"エンドポイント: {settings.log_endpoint}")
    print()

    # クライアント・リポジトリ初期化
    client = AcsHttpClient(
        base_url=settings.base_url,
        access_key=settings.access_key,
        secret_key=settings.secret_key,
        endpoint_path=settings.log_endpoint,
    )
    repository = SQLiteRepository(db_path)
    repository.ensure_schema(store_raw=True)
    repository.ensure_conversion_schema()

    # ========================================
    # Step 1: クリックログ取り込み
    # ========================================
    print("-" * 70)
    print("Step 1: クリックログ取り込み")
    print("-" * 70)

    click_ingestor = ClickLogIngestor(
        client=client,
        repository=repository,
        page_size=settings.page_size,
        store_raw=True,
    )
    click_count = click_ingestor.run_for_date(target_date)
    print(f"[OK] クリックログ取り込み完了: {click_count}件")
    print()

    # ========================================
    # Step 2: 成果ログ取り込み＆突合
    # ========================================
    print("-" * 70)
    print("Step 2: 成果ログ取り込み＆クリックログ突合")
    print("-" * 70)

    conv_ingestor = ConversionIngestor(
        client=client,
        repository=repository,
        page_size=settings.page_size,
    )
    conv_total, conv_enriched = conv_ingestor.run_for_date(target_date)

    if conv_total > 0:
        match_rate = conv_enriched / conv_total * 100
        print(f"[OK] 成果ログ取り込み完了: {conv_total}件")
        print(f"   - クリック情報突合: {conv_enriched}件 ({match_rate:.1f}%)")
        print(f"   - 突合失敗（cidなし or クリックなし）: {conv_total - conv_enriched}件")
    else:
        print("[INFO] 成果ログ: 0件（対象日のデータなし）")
    print()

    # ========================================
    # Step 3: フラウド検知
    # ========================================
    print("-" * 70)
    print("Step 3: フラウド検知")
    print("-" * 70)

    click_rules = resolve_rules(
        click_threshold=args.click_threshold,
        media_threshold=None,
        program_threshold=None,
        burst_click_threshold=None,
        burst_window_seconds=None,
    )
    conv_rules = resolve_conversion_rules(
        conversion_threshold=args.conversion_threshold,
        media_threshold=None,
        program_threshold=None,
    )

    print(f"クリック閾値: clicks>={click_rules.click_threshold}, "
          f"media>={click_rules.media_threshold}, program>={click_rules.program_threshold}")
    print(f"成果閾値: conversions>={conv_rules.conversion_threshold}, "
          f"media>={conv_rules.media_threshold}, program>={conv_rules.program_threshold}")
    print()

    detector = CombinedSuspiciousDetector(
        repository=repository,
        click_rules=click_rules,
        conversion_rules=conv_rules,
    )
    click_findings, conv_findings, high_risk = detector.find_for_date(target_date)

    print(f"[DETECT] クリックベース検出: {len(click_findings)}件")
    print(f"[DETECT] 成果ベース検出: {len(conv_findings)}件")
    print(f"[ALERT] 高リスク（両方で検出）: {len(high_risk)}件")
    print()

    # ========================================
    # 結果詳細
    # ========================================
    if high_risk:
        print("=" * 70)
        print("[ALERT] 高リスク IP/UA（クリックと成果の両方で検出）")
        print("=" * 70)
        for ip_ua in high_risk[:10]:
            print(f"  - {ip_ua}")
        if len(high_risk) > 10:
            print(f"  ... 他 {len(high_risk) - 10}件")
        print()

    if click_findings:
        print("=" * 70)
        print("[DETECT] クリックベース検出（上位10件）")
        print("=" * 70)
        for f in sorted(click_findings, key=lambda x: x.total_clicks, reverse=True)[:10]:
            print(f"  IP: {f.ipaddress}")
            print(f"     clicks={f.total_clicks}, media={f.media_count}, "
                  f"programs={f.program_count}")
            print(f"     reasons: {'; '.join(f.reasons)}")
            print()

    if conv_findings:
        print("=" * 70)
        print("[DETECT] 成果ベース検出（上位10件）")
        print("=" * 70)
        for f in sorted(conv_findings, key=lambda x: x.conversion_count, reverse=True)[:10]:
            print(f"  IP: {f.ipaddress}")
            print(f"     conversions={f.conversion_count}, media={f.media_count}, "
                  f"programs={f.program_count}")
            print(f"     reasons: {'; '.join(f.reasons)}")
            print()

    # ========================================
    # サマリー
    # ========================================
    print("=" * 70)
    print("サマリー")
    print("=" * 70)
    print(f"対象日: {target_date.isoformat()}")
    print(f"クリック取り込み: {click_count}件")
    print(f"成果取り込み: {conv_total}件（突合成功: {conv_enriched}件）")
    print(f"クリック不正: {len(click_findings)}件")
    print(f"成果不正: {len(conv_findings)}件")
    print(f"高リスク: {len(high_risk)}件")
    print(f"DBパス: {db_path}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())

