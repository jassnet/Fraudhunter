"""
Access Log 取得確認用の簡易スクリプト。

使い方:
  python examples/fetch_access_log_sample.py --date 2024-01-01
環境変数 (.env) の ACS_BASE_URL / ACS_ACCESS_KEY / ACS_SECRET_KEY / ACS_TOKEN / ACS_LOG_ENDPOINT を利用します。
"""

from __future__ import annotations

import argparse
from datetime import date

from fraud_checker.acs_client import AcsHttpClient
from fraud_checker.config import resolve_acs_settings


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Target date (YYYY-MM-DD)")
    parser.add_argument("--page-size", type=int, default=200, help="Page size (optional)")
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
        endpoint_path=settings.log_endpoint,
    )

    records = list(client.fetch_click_logs(target_date, page=1, limit=settings.page_size))
    print(f"[sample] date={target_date.isoformat()} endpoint={settings.log_endpoint}")
    print(f"[sample] fetched records: {len(records)} (page_size={settings.page_size})")
    for row in records[:5]:
        print(
            f"  time={row.click_time} media={row.media_id} program={row.program_id} "
            f"ip={row.ipaddress} ua={row.useragent[:40]}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
