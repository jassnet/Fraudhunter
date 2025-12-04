from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List

from .models import IpUaRollup, SuspiciousFinding
from .repository import SQLiteRepository


@dataclass
class SuspiciousRuleSet:
    click_threshold: int = 50
    media_threshold: int = 3
    program_threshold: int = 3
    burst_click_threshold: int = 20
    burst_window_seconds: int = 600  # 10 minutes
    browser_only: bool = False  # ブラウザ由来のUA/IPのみを対象とする
    exclude_datacenter_ip: bool = False  # データセンターIP（Google, AWS等）を除外する


class SuspiciousDetector:
    def __init__(self, repository: SQLiteRepository, rules: SuspiciousRuleSet | None = None):
        self.repository = repository
        self.rules = rules or SuspiciousRuleSet()

    def find_for_date(self, target_date: date) -> List[SuspiciousFinding]:
        rollups = self.repository.fetch_suspicious_rollups(
            target_date,
            click_threshold=self.rules.click_threshold,
            media_threshold=self.rules.media_threshold,
            program_threshold=self.rules.program_threshold,
            burst_click_threshold=self.rules.burst_click_threshold,
            browser_only=self.rules.browser_only,
            exclude_datacenter_ip=self.rules.exclude_datacenter_ip,
        )
        findings: List[SuspiciousFinding] = []
        for rollup in rollups:
            reasons = self._reasons_for_rollup(rollup)
            if reasons:
                findings.append(
                    SuspiciousFinding(
                        date=rollup.date,
                        ipaddress=rollup.ipaddress,
                        useragent=rollup.useragent,
                        total_clicks=rollup.total_clicks,
                        media_count=rollup.media_count,
                        program_count=rollup.program_count,
                        first_time=rollup.first_time,
                        last_time=rollup.last_time,
                        reasons=reasons,
                    )
                )
        return findings

    def _reasons_for_rollup(self, rollup: IpUaRollup) -> List[str]:
        reasons: List[str] = []
        if rollup.total_clicks >= self.rules.click_threshold:
            reasons.append(f"total_clicks >= {self.rules.click_threshold}")
        if rollup.media_count >= self.rules.media_threshold:
            reasons.append(f"media_count >= {self.rules.media_threshold}")
        if rollup.program_count >= self.rules.program_threshold:
            reasons.append(f"program_count >= {self.rules.program_threshold}")
        duration = (rollup.last_time - rollup.first_time).total_seconds()
        if (
            rollup.total_clicks >= self.rules.burst_click_threshold
            and duration <= self.rules.burst_window_seconds
        ):
            reasons.append(
                f"burst: {rollup.total_clicks} clicks in {int(duration)}s "
                f"(<= {self.rules.burst_window_seconds}s)"
            )
        return reasons
