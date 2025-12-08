from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List

from .models import (
    ConversionIpUaRollup,
    IpUaRollup,
    SuspiciousConversionFinding,
    SuspiciousFinding,
)
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


@dataclass
class ConversionSuspiciousRuleSet:
    """成果ベースの不正検知ルールセット"""
    conversion_threshold: int = 5  # 同一IP/UAからの成果数閾値
    media_threshold: int = 2  # 複数媒体への成果閾値
    program_threshold: int = 2  # 複数案件への成果閾値
    burst_conversion_threshold: int = 3  # 短時間での成果数閾値
    burst_window_seconds: int = 1800  # バースト判定の時間窓（30分）
    browser_only: bool = False
    exclude_datacenter_ip: bool = False


class ConversionSuspiciousDetector:
    """
    成果ログベースの不正検知を行う。
    クリック時点のIP/UAを使って、ポストバック経由の成果でも検知可能。
    """

    def __init__(
        self,
        repository: SQLiteRepository,
        rules: ConversionSuspiciousRuleSet | None = None,
    ):
        self.repository = repository
        self.rules = rules or ConversionSuspiciousRuleSet()

    def find_for_date(self, target_date: date) -> List[SuspiciousConversionFinding]:
        """指定日の疑わしい成果IP/UAを抽出"""
        rollups = self.repository.fetch_suspicious_conversion_rollups(
            target_date,
            conversion_threshold=self.rules.conversion_threshold,
            media_threshold=self.rules.media_threshold,
            program_threshold=self.rules.program_threshold,
            browser_only=self.rules.browser_only,
            exclude_datacenter_ip=self.rules.exclude_datacenter_ip,
        )

        findings: List[SuspiciousConversionFinding] = []
        for rollup in rollups:
            reasons = self._reasons_for_rollup(rollup)
            if reasons:
                findings.append(
                    SuspiciousConversionFinding(
                        date=rollup.date,
                        ipaddress=rollup.ipaddress,
                        useragent=rollup.useragent,
                        conversion_count=rollup.conversion_count,
                        media_count=rollup.media_count,
                        program_count=rollup.program_count,
                        first_conversion_time=rollup.first_conversion_time,
                        last_conversion_time=rollup.last_conversion_time,
                        reasons=reasons,
                    )
                )
        return findings

    def _reasons_for_rollup(self, rollup: ConversionIpUaRollup) -> List[str]:
        reasons: List[str] = []
        if rollup.conversion_count >= self.rules.conversion_threshold:
            reasons.append(f"conversion_count >= {self.rules.conversion_threshold}")
        if rollup.media_count >= self.rules.media_threshold:
            reasons.append(f"media_count >= {self.rules.media_threshold}")
        if rollup.program_count >= self.rules.program_threshold:
            reasons.append(f"program_count >= {self.rules.program_threshold}")

        # バースト判定
        duration = (
            rollup.last_conversion_time - rollup.first_conversion_time
        ).total_seconds()
        if (
            rollup.conversion_count >= self.rules.burst_conversion_threshold
            and duration <= self.rules.burst_window_seconds
        ):
            reasons.append(
                f"burst: {rollup.conversion_count} conversions in {int(duration)}s "
                f"(<= {self.rules.burst_window_seconds}s)"
            )
        return reasons


class CombinedSuspiciousDetector:
    """
    クリックログと成果ログを組み合わせた不正検知を行う。
    同じIP/UAがクリックでも成果でも疑わしい場合、より強い証拠となる。
    """

    def __init__(
        self,
        repository: SQLiteRepository,
        click_rules: SuspiciousRuleSet | None = None,
        conversion_rules: ConversionSuspiciousRuleSet | None = None,
    ):
        self.repository = repository
        self.click_detector = SuspiciousDetector(repository, click_rules)
        self.conversion_detector = ConversionSuspiciousDetector(
            repository, conversion_rules
        )

    def find_for_date(
        self, target_date: date
    ) -> tuple[List[SuspiciousFinding], List[SuspiciousConversionFinding], List[str]]:
        """
        指定日の疑わしいIP/UAを検出。

        Returns:
            tuple containing:
            - クリックベースの疑わしいIP/UA
            - 成果ベースの疑わしいIP/UA
            - 両方で検出されたIP/UAのリスト（高リスク）
        """
        click_findings = self.click_detector.find_for_date(target_date)
        conversion_findings = self.conversion_detector.find_for_date(target_date)

        # 両方で検出されたIP/UAを特定（高リスク）
        click_ip_uas = {(f.ipaddress, f.useragent) for f in click_findings}
        conversion_ip_uas = {(f.ipaddress, f.useragent) for f in conversion_findings}
        high_risk_ip_uas = click_ip_uas & conversion_ip_uas

        high_risk_list = [f"{ip} | {ua}" for ip, ua in high_risk_ip_uas]

        return click_findings, conversion_findings, high_risk_list
