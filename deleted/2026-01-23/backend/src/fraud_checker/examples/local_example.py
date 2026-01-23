from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from fraud_checker.config import resolve_rules, resolve_store_raw
from fraud_checker.env import load_env
from fraud_checker.ingestion import ClickLogIngestor
from fraud_checker.models import ClickLog
from fraud_checker.repository import SQLiteRepository
from fraud_checker.suspicious import SuspiciousDetector


class ExampleAcsClient:
    """Simple in-memory ACS stub that respects paging."""

    def __init__(self, clicks: list[ClickLog]):
        self.clicks = clicks

    def fetch_click_logs(self, target_date: date, page: int, limit: int):
        start = (page - 1) * limit
        end = start + limit
        if start >= len(self.clicks):
            return []
        return self.clicks[start:end]


def _build_example_clicks(target_date: date) -> list[ClickLog]:
    base = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
    clicks: list[ClickLog] = []

    # High volume on a single IP/UA (triggers total_clicks threshold)
    for i in range(60):
        clicks.append(
            ClickLog(
                click_id=f"heavy-{i}",
                click_time=base + timedelta(seconds=i * 5),
                media_id="media-a",
                program_id="program-a",
                ipaddress="203.0.113.10",
                useragent="UA-heavy",
                referrer=None,
                raw_payload={"example": True, "type": "high-volume", "idx": i},
            )
        )

    # Cross-media presence on one IP/UA (triggers media_count threshold)
    for j, media in enumerate(["media-a", "media-b", "media-c"]):
        clicks.append(
            ClickLog(
                click_id=f"wide-{j}",
                click_time=base + timedelta(minutes=30, seconds=j * 10),
                media_id=media,
                program_id="program-b",
                ipaddress="198.51.100.2",
                useragent="UA-wide",
                referrer=None,
                raw_payload={"example": True, "type": "cross-media", "idx": j},
            )
        )

    # Burst of clicks in a short window (triggers burst rule)
    for k in range(20):
        clicks.append(
            ClickLog(
                click_id=f"burst-{k}",
                click_time=base + timedelta(seconds=k * 15),
                media_id="media-d",
                program_id="program-d",
                ipaddress="192.0.2.3",
                useragent="UA-burst",
                referrer=None,
                raw_payload={"example": True, "type": "burst", "idx": k},
            )
        )

    # Benign traffic (should not be flagged)
    clicks.append(
        ClickLog(
            click_id="benign-1",
            click_time=base + timedelta(hours=1),
            media_id="media-z",
            program_id="program-z",
            ipaddress="203.0.113.55",
            useragent="UA-normal",
            referrer=None,
            raw_payload={"example": True, "type": "benign"},
        )
    )

    return clicks


def main() -> None:
    load_env()
    target_date = date(2024, 1, 10)
    db_path_text = os.getenv("FRAUD_DB_PATH", ":memory:")
    db_path = Path(db_path_text)
    store_raw = resolve_store_raw(None)
    rules = resolve_rules(
        click_threshold=None,
        media_threshold=None,
        program_threshold=None,
        burst_click_threshold=None,
        burst_window_seconds=None,
    )

    clicks = _build_example_clicks(target_date)
    client = ExampleAcsClient(clicks)
    repository = SQLiteRepository(db_path)
    ingestor = ClickLogIngestor(client, repository, page_size=25, store_raw=store_raw)
    ingested = ingestor.run_for_date(target_date)

    detector = SuspiciousDetector(repository, rules)
    findings = detector.find_for_date(target_date)

    print(f"[example] target_date={target_date.isoformat()}")
    print(f"[example] db_path={db_path} (in-memory if ':memory:')")
    print(f"[example] ingested={ingested}")
    print(f"[example] suspicious_count={len(findings)}")
    for finding in findings:
        window = finding.last_time - finding.first_time
        print(
            f"  - {finding.date} {finding.ipaddress} UA='{finding.useragent}' "
            f"clicks={finding.total_clicks} media={finding.media_count} "
            f"programs={finding.program_count} window={window} "
            f"reasons={'; '.join(finding.reasons)}"
        )


if __name__ == "__main__":
    main()
