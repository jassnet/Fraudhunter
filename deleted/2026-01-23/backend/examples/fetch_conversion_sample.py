"""
成果ログ（Conversion Log）取得確認用の簡易スクリプト。

使い方:
  python examples/fetch_conversion_sample.py --date 2024-01-01

環境変数 (.env) の ACS_BASE_URL / ACS_ACCESS_KEY / ACS_SECRET_KEY を利用します。
"""

from __future__ import annotations

import argparse
from datetime import date

from fraud_checker.acs_client import AcsHttpClient
from fraud_checker.config import resolve_acs_settings


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="成果ログ取得サンプル")
    parser.add_argument("--date", required=True, help="対象日付 (YYYY-MM-DD)")
    parser.add_argument("--page-size", type=int, default=100, help="ページサイズ")
    parser.add_argument("--pages", type=int, default=1, help="取得ページ数")
    args = parser.parse_args()

    target_date = _parse_date(args.date)
    settings = resolve_acs_settings(
        base_url=None,
        access_key=None,
        secret_key=None,
        page_size=args.page_size,
        log_endpoint=None,
    )
    client = AcsHttpClient(
        base_url=settings.base_url,
        access_key=settings.access_key,
        secret_key=settings.secret_key,
    )

    print(f"[sample] 成果ログ取得: date={target_date.isoformat()}")
    print(f"[sample] ACS URL: {settings.base_url}")
    print()

    all_records = []
    for page in range(1, args.pages + 1):
        records = list(
            client.fetch_conversion_logs(target_date, page=page, limit=args.page_size)
        )
        if not records:
            break
        all_records.extend(records)
        print(f"[page {page}] {len(records)}件取得")

    print()
    print(f"[sample] 取得総数: {len(all_records)}件")

    # cid（クリックID）の有無を集計
    with_cid = [r for r in all_records if r.cid]
    without_cid = [r for r in all_records if not r.cid]
    print(f"[sample] cid有り: {len(with_cid)}件, cid無し: {len(without_cid)}件")

    # サンプル表示
    print()
    print("=" * 70)
    print("サンプルデータ（先頭5件）")
    print("=" * 70)
    for i, row in enumerate(all_records[:5], 1):
        print(f"\n--- 成果 {i} ---")
        print(f"  ID: {row.conversion_id}")
        print(f"  cid (クリックID): {row.cid or '(なし)'}")
        print(f"  成果日時: {row.conversion_time}")
        print(f"  クリック日時: {row.click_time or '(なし)'}")
        print(f"  媒体: {row.media_id}")
        print(f"  案件: {row.program_id}")
        print(f"  ユーザー: {row.user_id or '(なし)'}")
        print(f"  ポストバックIP: {row.postback_ipaddress or '(なし)'}")
        print(f"  ポストバックUA: {(row.postback_useragent or '')[:50]}...")
        print(f"  ステータス: {row.state or '(なし)'}")

    # cidが有る成果のサンプル
    if with_cid:
        print()
        print("=" * 70)
        print("cid有りの成果サンプル（突合可能）")
        print("=" * 70)
        for i, row in enumerate(with_cid[:3], 1):
            print(f"\n--- cid有り成果 {i} ---")
            print(f"  成果ID: {row.conversion_id}")
            print(f"  cid: {row.cid}")
            print(f"  媒体: {row.media_id}")
            print(f"  案件: {row.program_id}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

