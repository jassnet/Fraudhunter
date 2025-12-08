from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from .models import (
    ConversionIpUaRollup,
    IpUaRollup,
    SuspiciousConversionFinding,
    SuspiciousFinding,
)
from .repository import SQLiteRepository


def _is_browser_useragent(ua: str) -> bool:
    """ブラウザ由来のUAかどうかを簡易判定（SQLフィルタと同等の条件）。"""
    if not ua:
        return False
    browser_hits = [
        "chrome/",
        "firefox/",
        "safari/",
        "edg/",
        "edge/",
        "opera/",
        "opr/",
        "msie ",
        "trident/",
    ]
    ua_lower = ua.lower()
    if not any(key in ua_lower for key in browser_hits):
        return False
    bot_markers = [
        "bot",
        "crawler",
        "spider",
        "curl",
        "python",
        "axios",
        "node-fetch",
        "go-http-client",
        "java/",
        "apache-httpclient",
        "libwww-perl",
        "wget",
        "headlesschrome",
    ]
    return not any(marker in ua_lower for marker in bot_markers)


def _is_datacenter_ip_conversion(ip: str) -> bool:
    """成果検知で除外するデータセンターIPレンジ（SQLと同等）。"""
    if not ip:
        return False
    prefixes = ("35.", "34.", "13.", "52.", "54.")
    return ip.startswith(prefixes)


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
    # クリック→成果までの経過秒で判定（click_unix と regist_unix を利用）
    min_click_to_conv_seconds: Optional[int] = 5
    max_click_to_conv_seconds: Optional[int] = 2592000  # 30日
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

        # クリック→成果までの経過秒チェックを有効化する場合は、件数閾値を満たさないIP/UAも追加検査する。
        gap_rules_enabled = (
            self.rules.min_click_to_conv_seconds is not None
            or self.rules.max_click_to_conv_seconds is not None
        )
        gap_stats = (
            self.repository.fetch_click_to_conversion_gaps(target_date)
            if gap_rules_enabled
            else {}
        )
        if gap_rules_enabled and gap_stats:
            rollup_map = {(r.ipaddress, r.useragent): r for r in rollups}
            all_rollups = self.repository.fetch_conversion_rollups(target_date)
            for candidate in all_rollups:
                key = (candidate.ipaddress, candidate.useragent)
                if key not in gap_stats:
                    continue
                if key in rollup_map:
                    continue
                if not self._passes_filters(candidate):
                    continue
                rollups.append(candidate)
                rollup_map[key] = candidate

        findings: List[SuspiciousConversionFinding] = []
        for rollup in rollups:
            gap_info = gap_stats.get((rollup.ipaddress, rollup.useragent))
            reasons = self._reasons_for_rollup(rollup, gap_info)
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
                        min_click_to_conv_seconds=gap_info.get("min") if gap_info else None,
                        max_click_to_conv_seconds=gap_info.get("max") if gap_info else None,
                    )
                )
        return findings

    def _reasons_for_rollup(
        self,
        rollup: ConversionIpUaRollup,
        gap_info: Optional[dict] = None,
    ) -> List[str]:
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

        # クリック→成果までの経過秒チェック
        if gap_info:
            min_gap = gap_info.get("min")
            max_gap = gap_info.get("max")
            if (
                min_gap is not None
                and self.rules.min_click_to_conv_seconds is not None
                and min_gap < self.rules.min_click_to_conv_seconds
            ):
                reasons.append(
                    f"click_to_conversion_seconds <= {self.rules.min_click_to_conv_seconds}s "
                    f"(min={int(min_gap)}s)"
                )
            if (
                max_gap is not None
                and self.rules.max_click_to_conv_seconds is not None
                and max_gap > self.rules.max_click_to_conv_seconds
            ):
                reasons.append(
                    f"click_to_conversion_seconds >= {self.rules.max_click_to_conv_seconds}s "
                    f"(max={int(max_gap)}s)"
                )
        return reasons

    def _passes_filters(self, rollup: ConversionIpUaRollup) -> bool:
        """browser_only / datacenter除外のフィルタをPython側でも適用する。"""
        if self.rules.browser_only and not _is_browser_useragent(rollup.useragent):
            return False
        if self.rules.exclude_datacenter_ip and _is_datacenter_ip_conversion(rollup.ipaddress):
            return False
        return True


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
