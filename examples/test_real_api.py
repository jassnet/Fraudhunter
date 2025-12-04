"""
実際のACS APIを使った統合テスト。

使い方:
  python examples/test_real_api.py --date 2024-01-01

環境変数 (.env) の ACS_BASE_URL / ACS_ACCESS_KEY / ACS_SECRET_KEY を利用します。
テスト用のDBは自動作成され、テスト終了後に削除されます（--keep-dbで保持可能）。

テスト内容:
  1. クリックログ取得テスト
  2. 成果ログ取得テスト
  3. クリックと成果の突合テスト
  4. フルフローテスト（クリック+成果+検知）
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
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
from fraud_checker.suspicious import (
    CombinedSuspiciousDetector,
    ConversionSuspiciousDetector,
    SuspiciousDetector,
)


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.message = ""
        self.details: dict = {}

    def success(self, message: str = "", **details):
        self.passed = True
        self.message = message
        self.details = details

    def fail(self, message: str, **details):
        self.passed = False
        self.message = message
        self.details = details


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def test_click_log_fetch(client: AcsHttpClient, target_date: date) -> TestResult:
    """クリックログ取得テスト"""
    result = TestResult("クリックログ取得")
    try:
        records = list(client.fetch_click_logs(target_date, page=1, limit=10))
        if records:
            first = records[0]
            result.success(
                f"{len(records)}件取得成功",
                count=len(records),
                sample_ip=first.ipaddress,
                sample_ua=first.useragent[:50] if first.useragent else None,
                sample_media=first.media_id,
                sample_program=first.program_id,
            )
        else:
            result.success("0件（データなし）", count=0)
    except Exception as e:
        result.fail(f"エラー: {e}")
    return result


def test_conversion_log_fetch(client: AcsHttpClient, target_date: date) -> TestResult:
    """成果ログ取得テスト"""
    result = TestResult("成果ログ取得")
    try:
        records = list(client.fetch_conversion_logs(target_date, page=1, limit=10))
        if records:
            first = records[0]
            cid_count = sum(1 for r in records if r.cid)
            result.success(
                f"{len(records)}件取得成功（cid有り: {cid_count}件）",
                count=len(records),
                cid_count=cid_count,
                sample_cid=first.cid,
                sample_media=first.media_id,
                sample_program=first.program_id,
            )
        else:
            result.success("0件（データなし）", count=0)
    except Exception as e:
        result.fail(f"エラー: {e}")
    return result


def test_click_ingestion(
    client: AcsHttpClient, repository: SQLiteRepository, target_date: date
) -> TestResult:
    """クリックログ取り込みテスト"""
    result = TestResult("クリックログ取り込み")
    try:
        ingestor = ClickLogIngestor(
            client=client,
            repository=repository,
            page_size=100,
            store_raw=True,  # 成果突合のため必須
        )
        count = ingestor.run_for_date(target_date)
        result.success(f"{count}件取り込み完了", ingested=count)
    except Exception as e:
        result.fail(f"エラー: {e}")
    return result


def test_conversion_ingestion(
    client: AcsHttpClient, repository: SQLiteRepository, target_date: date
) -> TestResult:
    """成果ログ取り込み＆突合テスト"""
    result = TestResult("成果ログ取り込み＆突合")
    try:
        ingestor = ConversionIngestor(
            client=client,
            repository=repository,
            page_size=100,
        )
        total, enriched = ingestor.run_for_date(target_date)
        match_rate = (enriched / total * 100) if total > 0 else 0
        result.success(
            f"{total}件取得、{enriched}件突合成功（{match_rate:.1f}%）",
            total=total,
            enriched=enriched,
            match_rate=f"{match_rate:.1f}%",
        )
    except Exception as e:
        result.fail(f"エラー: {e}")
    return result


def test_click_suspicious(repository: SQLiteRepository, target_date: date) -> TestResult:
    """クリックベースの不正検知テスト"""
    result = TestResult("クリックベース不正検知")
    try:
        rules = resolve_rules(
            click_threshold=None,
            media_threshold=None,
            program_threshold=None,
            burst_click_threshold=None,
            burst_window_seconds=None,
        )
        detector = SuspiciousDetector(repository, rules)
        findings = detector.find_for_date(target_date)
        if findings:
            result.success(
                f"{len(findings)}件の疑わしいIP/UA検出",
                count=len(findings),
                top_ip=findings[0].ipaddress if findings else None,
                top_clicks=findings[0].total_clicks if findings else None,
            )
        else:
            result.success("疑わしいIP/UAなし", count=0)
    except Exception as e:
        result.fail(f"エラー: {e}")
    return result


def test_conversion_suspicious(
    repository: SQLiteRepository, target_date: date
) -> TestResult:
    """成果ベースの不正検知テスト"""
    result = TestResult("成果ベース不正検知")
    try:
        rules = resolve_conversion_rules(
            conversion_threshold=None,
            media_threshold=None,
            program_threshold=None,
        )
        detector = ConversionSuspiciousDetector(repository, rules)
        findings = detector.find_for_date(target_date)
        if findings:
            result.success(
                f"{len(findings)}件の疑わしいIP/UA検出",
                count=len(findings),
                top_ip=findings[0].ipaddress if findings else None,
                top_conversions=findings[0].conversion_count if findings else None,
            )
        else:
            result.success("疑わしいIP/UAなし", count=0)
    except Exception as e:
        result.fail(f"エラー: {e}")
    return result


def test_combined_detection(
    repository: SQLiteRepository, target_date: date
) -> TestResult:
    """統合検知テスト"""
    result = TestResult("統合検知（高リスク判定）")
    try:
        click_rules = resolve_rules(
            click_threshold=None,
            media_threshold=None,
            program_threshold=None,
            burst_click_threshold=None,
            burst_window_seconds=None,
        )
        conv_rules = resolve_conversion_rules(
            conversion_threshold=None,
            media_threshold=None,
            program_threshold=None,
        )
        detector = CombinedSuspiciousDetector(
            repository=repository,
            click_rules=click_rules,
            conversion_rules=conv_rules,
        )
        click_findings, conv_findings, high_risk = detector.find_for_date(target_date)
        result.success(
            f"クリック: {len(click_findings)}件, 成果: {len(conv_findings)}件, "
            f"高リスク: {len(high_risk)}件",
            click_suspicious=len(click_findings),
            conversion_suspicious=len(conv_findings),
            high_risk=len(high_risk),
            high_risk_list=high_risk[:5] if high_risk else [],
        )
    except Exception as e:
        result.fail(f"エラー: {e}")
    return result


def print_result(result: TestResult, verbose: bool = False):
    """テスト結果を表示"""
    status = "[PASS]" if result.passed else "[FAIL]"
    print(f"{status} {result.name}: {result.message}")
    if verbose and result.details:
        for key, value in result.details.items():
            print(f"       {key}: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description="実際のACS APIを使った統合テスト")
    parser.add_argument(
        "--date",
        help="対象日付 (YYYY-MM-DD)。省略時は昨日",
    )
    parser.add_argument(
        "--db",
        help="テスト用DBパス。省略時は一時ファイル",
    )
    parser.add_argument(
        "--keep-db",
        action="store_true",
        help="テスト後もDBを保持する",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="詳細情報を表示",
    )
    parser.add_argument(
        "--test",
        choices=["all", "click", "conversion", "ingestion", "detection", "full"],
        default="all",
        help="実行するテスト (default: all)",
    )
    args = parser.parse_args()

    # 環境変数を読み込み
    load_env()

    # 対象日付
    if args.date:
        target_date = _parse_date(args.date)
    else:
        target_date = date.today() - timedelta(days=1)

    # DBパス
    if args.db:
        db_path = Path(args.db)
        temp_db = None
    else:
        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_path = Path(temp_db.name)
        temp_db.close()

    print("=" * 60)
    print("ACS API 統合テスト")
    print("=" * 60)
    print(f"対象日付: {target_date.isoformat()}")
    print(f"DBパス: {db_path}")
    print()

    # ACSクライアント初期化
    try:
        settings = resolve_acs_settings(
            base_url=None,
            access_key=None,
            secret_key=None,
            page_size=100,
            log_endpoint=None,
        )
        client = AcsHttpClient(
            base_url=settings.base_url,
            access_key=settings.access_key,
            secret_key=settings.secret_key,
            endpoint_path=settings.log_endpoint,
        )
        print(f"ACS接続先: {settings.base_url}")
        print(f"エンドポイント: {settings.log_endpoint}")
        print()
    except ValueError as e:
        print(f"[ERROR] 設定エラー: {e}")
        print("   .envファイルにACS_BASE_URL, ACS_ACCESS_KEY, ACS_SECRET_KEYを設定してください。")
        return 1

    # リポジトリ初期化
    repository = SQLiteRepository(db_path)
    repository.ensure_schema(store_raw=True)
    repository.ensure_conversion_schema()

    results: list[TestResult] = []

    # テスト実行
    print("-" * 60)
    print("テスト実行中...")
    print("-" * 60)

    test_mode = args.test

    if test_mode in ("all", "click"):
        print("\n[1] クリックログ取得テスト")
        result = test_click_log_fetch(client, target_date)
        results.append(result)
        print_result(result, args.verbose)

    if test_mode in ("all", "conversion"):
        print("\n[2] 成果ログ取得テスト")
        result = test_conversion_log_fetch(client, target_date)
        results.append(result)
        print_result(result, args.verbose)

    if test_mode in ("all", "ingestion", "full"):
        print("\n[3] クリックログ取り込みテスト")
        result = test_click_ingestion(client, repository, target_date)
        results.append(result)
        print_result(result, args.verbose)

        print("\n[4] 成果ログ取り込み＆突合テスト")
        result = test_conversion_ingestion(client, repository, target_date)
        results.append(result)
        print_result(result, args.verbose)

    if test_mode in ("all", "detection", "full"):
        print("\n[5] クリックベース不正検知テスト")
        result = test_click_suspicious(repository, target_date)
        results.append(result)
        print_result(result, args.verbose)

        print("\n[6] 成果ベース不正検知テスト")
        result = test_conversion_suspicious(repository, target_date)
        results.append(result)
        print_result(result, args.verbose)

        print("\n[7] 統合検知テスト")
        result = test_combined_detection(repository, target_date)
        results.append(result)
        print_result(result, args.verbose)

    # 結果サマリー
    print()
    print("=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    print(f"PASSED: {passed}, FAILED: {failed}, TOTAL: {len(results)}")

    if failed > 0:
        print("\n失敗したテスト:")
        for r in results:
            if not r.passed:
                print(f"  - {r.name}: {r.message}")

    # DB処理
    if temp_db and not args.keep_db:
        try:
            os.unlink(db_path)
            print(f"\n一時DBを削除しました: {db_path}")
        except Exception:
            pass
    elif args.keep_db or args.db:
        print(f"\nDBを保持しました: {db_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

