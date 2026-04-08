from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from .ip_filters import BROWSER_UA_INCLUDES, BOT_UA_MARKERS, is_datacenter_ip
from .models import ConversionIpUaRollup, SuspiciousConversionFinding
from .repository_pg import PostgresRepository

CLICK_PADDING_EXTRA_WINDOW_SECONDS = 1800
CLICK_PADDING_LINKED_RATIO_THRESHOLD = 2.0
CLICK_PADDING_EXTRA_WINDOW_THRESHOLD = 10
CLICK_PADDING_NON_BROWSER_RATIO_THRESHOLD = 0.7


def _is_browser_useragent(ua: str) -> bool:
    if not ua:
        return False
    ua_lower = ua.lower()
    if not any(key in ua_lower for key in BROWSER_UA_INCLUDES):
        return False
    return not any(marker in ua_lower for marker in BOT_UA_MARKERS)


def _is_datacenter_ip_conversion(ip: str) -> bool:
    return is_datacenter_ip(ip)


@dataclass
class SuspiciousRuleSet:
    click_threshold: int = 50
    media_threshold: int = 3
    program_threshold: int = 3
    burst_click_threshold: int = 20
    burst_window_seconds: int = 600
    browser_only: bool = False
    exclude_datacenter_ip: bool = False


@dataclass
class ConversionSuspiciousRuleSet:
    conversion_threshold: int = 5
    media_threshold: int = 2
    program_threshold: int = 2
    burst_conversion_threshold: int = 3
    burst_window_seconds: int = 1800
    min_click_to_conv_seconds: Optional[int] = 5
    max_click_to_conv_seconds: Optional[int] = 2592000
    browser_only: bool = False
    exclude_datacenter_ip: bool = False


class ConversionSuspiciousDetector:
    def __init__(
        self,
        repository: PostgresRepository,
        rules: ConversionSuspiciousRuleSet | None = None,
    ):
        self.repository = repository
        self.rules = rules or ConversionSuspiciousRuleSet()

    def find_for_date(self, target_date: date) -> list[SuspiciousConversionFinding]:
        rollups = self.repository.fetch_suspicious_conversion_rollups(
            target_date,
            conversion_threshold=self.rules.conversion_threshold,
            media_threshold=self.rules.media_threshold,
            program_threshold=self.rules.program_threshold,
            burst_conversion_threshold=self.rules.burst_conversion_threshold,
            browser_only=self.rules.browser_only,
            exclude_datacenter_ip=self.rules.exclude_datacenter_ip,
        )

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
                if key not in gap_stats or key in rollup_map:
                    continue
                if not self._passes_filters(candidate):
                    continue
                rollups.append(candidate)
                rollup_map[key] = candidate

        padding_fetcher = getattr(self.repository, "fetch_conversion_click_padding_metrics", None)
        padding_stats = (
            padding_fetcher(
                target_date,
                [(rollup.ipaddress, rollup.useragent) for rollup in rollups],
                extra_window_seconds=CLICK_PADDING_EXTRA_WINDOW_SECONDS,
            )
            if rollups and callable(padding_fetcher)
            else {}
        )

        findings: list[SuspiciousConversionFinding] = []
        for rollup in rollups:
            gap_info = gap_stats.get((rollup.ipaddress, rollup.useragent))
            padding_info = padding_stats.get((rollup.ipaddress, rollup.useragent))
            reasons = self._reasons_for_rollup(rollup, gap_info, padding_info)
            if not reasons:
                continue

            linked_click_count = (
                int(padding_info["linked_click_count"])
                if padding_info and padding_info.get("linked_click_count") is not None
                else None
            )
            extra_window_click_count = (
                int(padding_info["extra_window_click_count"])
                if padding_info and padding_info.get("extra_window_click_count") is not None
                else None
            )
            linked_clicks_per_conversion = (
                linked_click_count / rollup.conversion_count
                if linked_click_count is not None and rollup.conversion_count > 0
                else None
            )
            extra_window_non_browser_ratio = (
                padding_info.get("extra_window_non_browser_ratio")
                if padding_info
                else None
            )
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
                    linked_click_count=linked_click_count,
                    linked_clicks_per_conversion=linked_clicks_per_conversion,
                    extra_window_click_count=extra_window_click_count,
                    extra_window_non_browser_ratio=extra_window_non_browser_ratio,
                )
            )
        return findings

    def _reasons_for_rollup(
        self,
        rollup: ConversionIpUaRollup,
        gap_info: Optional[dict] = None,
        padding_info: Optional[dict] = None,
    ) -> list[str]:
        reasons: list[str] = []
        if rollup.conversion_count >= self.rules.conversion_threshold:
            reasons.append(f"conversion_count >= {self.rules.conversion_threshold}")
        if rollup.media_count >= self.rules.media_threshold:
            reasons.append(f"media_count >= {self.rules.media_threshold}")
        if rollup.program_count >= self.rules.program_threshold:
            reasons.append(f"program_count >= {self.rules.program_threshold}")

        duration = (rollup.last_conversion_time - rollup.first_conversion_time).total_seconds()
        if (
            rollup.conversion_count >= self.rules.burst_conversion_threshold
            and duration <= self.rules.burst_window_seconds
        ):
            reasons.append(
                f"burst: {rollup.conversion_count} conversions in {int(duration)}s "
                f"(<= {self.rules.burst_window_seconds}s)"
            )

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

        if padding_info:
            linked_click_count = padding_info.get("linked_click_count")
            linked_clicks_per_conversion = (
                linked_click_count / rollup.conversion_count
                if linked_click_count is not None and rollup.conversion_count > 0
                else None
            )
            if (
                linked_clicks_per_conversion is not None
                and linked_clicks_per_conversion >= CLICK_PADDING_LINKED_RATIO_THRESHOLD
            ):
                reasons.append(
                    "click_padding_linked_ratio >= "
                    f"{CLICK_PADDING_LINKED_RATIO_THRESHOLD:.1f} "
                    f"(actual={linked_clicks_per_conversion:.2f})"
                )

            extra_window_click_count = padding_info.get("extra_window_click_count")
            if (
                extra_window_click_count is not None
                and extra_window_click_count >= CLICK_PADDING_EXTRA_WINDOW_THRESHOLD
            ):
                reasons.append(
                    "click_padding_extra_window >= "
                    f"{CLICK_PADDING_EXTRA_WINDOW_THRESHOLD} in 30m "
                    f"(actual={int(extra_window_click_count)})"
                )

            extra_window_useragents = padding_info.get("extra_window_useragents") or []
            if extra_window_useragents:
                non_browser_count = sum(
                    1
                    for useragent in extra_window_useragents
                    if not _is_browser_useragent(useragent)
                )
                padding_info["extra_window_non_browser_ratio"] = (
                    non_browser_count / len(extra_window_useragents)
                )
            else:
                padding_info["extra_window_non_browser_ratio"] = None

            non_browser_ratio = padding_info.get("extra_window_non_browser_ratio")
            if (
                extra_window_click_count is not None
                and extra_window_click_count >= CLICK_PADDING_EXTRA_WINDOW_THRESHOLD
                and non_browser_ratio is not None
                and non_browser_ratio >= CLICK_PADDING_NON_BROWSER_RATIO_THRESHOLD
            ):
                reasons.append(
                    "click_padding_non_browser_ratio >= "
                    f"{CLICK_PADDING_NON_BROWSER_RATIO_THRESHOLD:.1f} "
                    f"(actual={non_browser_ratio:.2f})"
                )
        return reasons

    def _passes_filters(self, rollup: ConversionIpUaRollup) -> bool:
        if self.rules.browser_only and not _is_browser_useragent(rollup.useragent):
            return False
        if self.rules.exclude_datacenter_ip and _is_datacenter_ip_conversion(rollup.ipaddress):
            return False
        return True
