from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from fraud_checker.models import ConversionIpUaRollup, IpUaRollup
from fraud_checker.suspicious import (
    CombinedSuspiciousDetector,
    ConversionSuspiciousDetector,
    ConversionSuspiciousRuleSet,
    SuspiciousDetector,
    SuspiciousRuleSet,
)


@dataclass
class _StubRepo:
    click_rollups: list[IpUaRollup]
    conversion_rollups: list[ConversionIpUaRollup]
    all_conversion_rollups: list[ConversionIpUaRollup]
    gap_stats: dict[tuple[str, str], dict[str, float]]
    padding_stats: dict[tuple[str, str], dict[str, object]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.click_call_args: dict | None = None
        self.conversion_call_args: dict | None = None

    def fetch_suspicious_rollups(
        self,
        target_date: date,
        *,
        click_threshold: int,
        media_threshold: int,
        program_threshold: int,
        burst_click_threshold: int,
        browser_only: bool,
        exclude_datacenter_ip: bool,
    ) -> list[IpUaRollup]:
        self.click_call_args = {
            "target_date": target_date,
            "click_threshold": click_threshold,
            "media_threshold": media_threshold,
            "program_threshold": program_threshold,
            "burst_click_threshold": burst_click_threshold,
            "browser_only": browser_only,
            "exclude_datacenter_ip": exclude_datacenter_ip,
        }
        return self.click_rollups

    def fetch_suspicious_conversion_rollups(
        self,
        target_date: date,
        *,
        conversion_threshold: int,
        media_threshold: int,
        program_threshold: int,
        burst_conversion_threshold: int,
        browser_only: bool,
        exclude_datacenter_ip: bool,
    ) -> list[ConversionIpUaRollup]:
        self.conversion_call_args = {
            "target_date": target_date,
            "conversion_threshold": conversion_threshold,
            "media_threshold": media_threshold,
            "program_threshold": program_threshold,
            "burst_conversion_threshold": burst_conversion_threshold,
            "browser_only": browser_only,
            "exclude_datacenter_ip": exclude_datacenter_ip,
        }
        return self.conversion_rollups

    def fetch_click_to_conversion_gaps(
        self, target_date: date
    ) -> dict[tuple[str, str], dict[str, float]]:
        return self.gap_stats

    def fetch_conversion_rollups(self, target_date: date) -> list[ConversionIpUaRollup]:
        return self.all_conversion_rollups

    def fetch_conversion_click_padding_metrics(
        self,
        target_date: date,
        ip_ua_pairs: list[tuple[str, str]],
        *,
        extra_window_seconds: int,
    ) -> dict[tuple[str, str], dict[str, object]]:
        return {
            key: self.padding_stats[key]
            for key in ip_ua_pairs
            if key in self.padding_stats
        }


def _click_rollup(
    *,
    total_clicks: int = 60,
    media_count: int = 2,
    program_count: int = 1,
    ipaddress: str = "1.1.1.1",
    useragent: str = "Mozilla/5.0 Chrome/120.0",
) -> IpUaRollup:
    start = datetime(2026, 1, 1, 10, 0, 0)
    return IpUaRollup(
        date=date(2026, 1, 1),
        ipaddress=ipaddress,
        useragent=useragent,
        total_clicks=total_clicks,
        media_count=media_count,
        program_count=program_count,
        first_time=start,
        last_time=start + timedelta(seconds=120),
    )


def _conversion_rollup(
    *,
    conversion_count: int = 1,
    media_count: int = 1,
    program_count: int = 1,
    ipaddress: str = "1.1.1.1",
    useragent: str = "Mozilla/5.0 Chrome/120.0",
) -> ConversionIpUaRollup:
    start = datetime(2026, 1, 1, 10, 0, 0)
    return ConversionIpUaRollup(
        date=date(2026, 1, 1),
        ipaddress=ipaddress,
        useragent=useragent,
        conversion_count=conversion_count,
        media_count=media_count,
        program_count=program_count,
        first_conversion_time=start,
        last_conversion_time=start + timedelta(seconds=60),
    )


def test_click_detector_applies_threshold_and_burst_reason():
    # Given
    rules = SuspiciousRuleSet(
        click_threshold=50,
        media_threshold=2,
        program_threshold=2,
        burst_click_threshold=20,
        burst_window_seconds=600,
        browser_only=True,
        exclude_datacenter_ip=True,
    )
    repo = _StubRepo(
        click_rollups=[_click_rollup(total_clicks=60, media_count=2, program_count=1)],
        conversion_rollups=[],
        all_conversion_rollups=[],
        gap_stats={},
    )
    detector = SuspiciousDetector(repo, rules)

    # When
    findings = detector.find_for_date(date(2026, 1, 1))

    # Then
    assert len(findings) == 1
    assert any(reason.startswith("total_clicks >=") for reason in findings[0].reasons)
    assert any(reason.startswith("burst:") for reason in findings[0].reasons)
    assert repo.click_call_args is not None
    assert repo.click_call_args["burst_click_threshold"] == 20
    assert repo.click_call_args["browser_only"] is True
    assert repo.click_call_args["exclude_datacenter_ip"] is True


def test_conversion_detector_adds_gap_only_findings():
    # Given
    candidate = _conversion_rollup(
        conversion_count=1,
        media_count=1,
        program_count=1,
        ipaddress="2.2.2.2",
        useragent="Mozilla/5.0 Safari/605.1",
    )
    repo = _StubRepo(
        click_rollups=[],
        conversion_rollups=[],
        all_conversion_rollups=[candidate],
        gap_stats={("2.2.2.2", "Mozilla/5.0 Safari/605.1"): {"min": 1.0, "max": 50.0}},
    )
    rules = ConversionSuspiciousRuleSet(
        conversion_threshold=99,
        media_threshold=99,
        program_threshold=99,
        burst_conversion_threshold=99,
        burst_window_seconds=1800,
        min_click_to_conv_seconds=5,
        max_click_to_conv_seconds=3600,
    )
    detector = ConversionSuspiciousDetector(repo, rules)

    # When
    findings = detector.find_for_date(date(2026, 1, 1))

    # Then
    assert len(findings) == 1
    reasons = findings[0].reasons
    assert any(reason.startswith("click_to_conversion_seconds <=") for reason in reasons)
    assert repo.conversion_call_args is not None
    assert repo.conversion_call_args["burst_conversion_threshold"] == 99


def test_conversion_detector_respects_browser_and_datacenter_filters():
    # Given
    filtered_candidate = _conversion_rollup(
        ipaddress="3.10.10.10",
        useragent="python-requests/2.31.0",
    )
    repo = _StubRepo(
        click_rollups=[],
        conversion_rollups=[],
        all_conversion_rollups=[filtered_candidate],
        gap_stats={("3.10.10.10", "python-requests/2.31.0"): {"min": 1.0, "max": 10.0}},
    )
    rules = ConversionSuspiciousRuleSet(
        conversion_threshold=99,
        media_threshold=99,
        program_threshold=99,
        burst_conversion_threshold=99,
        browser_only=True,
        exclude_datacenter_ip=True,
    )
    detector = ConversionSuspiciousDetector(repo, rules)

    # When
    findings = detector.find_for_date(date(2026, 1, 1))

    # Then
    assert findings == []


def test_combined_detector_marks_intersection_as_high_risk():
    # Given
    shared_ip = "9.9.9.9"
    shared_ua = "Mozilla/5.0 Firefox/122.0"
    repo = _StubRepo(
        click_rollups=[
            _click_rollup(
                total_clicks=70,
                media_count=1,
                program_count=1,
                ipaddress=shared_ip,
                useragent=shared_ua,
            )
        ],
        conversion_rollups=[
            _conversion_rollup(
                conversion_count=6,
                media_count=1,
                program_count=1,
                ipaddress=shared_ip,
                useragent=shared_ua,
            )
        ],
        all_conversion_rollups=[],
        gap_stats={},
    )
    click_rules = SuspiciousRuleSet(click_threshold=50, burst_click_threshold=200)
    conversion_rules = ConversionSuspiciousRuleSet(
        conversion_threshold=5,
        burst_conversion_threshold=99,
    )
    detector = CombinedSuspiciousDetector(repo, click_rules, conversion_rules)

    # When
    click_findings, conversion_findings, high_risk = detector.find_for_date(date(2026, 1, 1))

    # Then
    assert len(click_findings) == 1
    assert len(conversion_findings) == 1
    assert high_risk == [f"{shared_ip} | {shared_ua}"]


def test_click_detector_adds_media_and_program_reasons():
    # Given
    rollup = _click_rollup(
        total_clicks=10,
        media_count=3,
        program_count=4,
    )
    repo = _StubRepo(
        click_rollups=[rollup],
        conversion_rollups=[],
        all_conversion_rollups=[],
        gap_stats={},
    )
    rules = SuspiciousRuleSet(
        click_threshold=999,
        media_threshold=3,
        program_threshold=4,
        burst_click_threshold=999,
    )
    detector = SuspiciousDetector(repo, rules)

    # When
    findings = detector.find_for_date(date(2026, 1, 1))

    # Then
    assert len(findings) == 1
    reasons = findings[0].reasons
    assert any(reason.startswith("media_count >=") for reason in reasons)
    assert any(reason.startswith("program_count >=") for reason in reasons)


def test_conversion_detector_adds_max_gap_reason():
    # Given
    candidate = _conversion_rollup(
        conversion_count=1,
        media_count=1,
        program_count=1,
        ipaddress="7.7.7.7",
        useragent="Mozilla/5.0 Chrome/121.0",
    )
    repo = _StubRepo(
        click_rollups=[],
        conversion_rollups=[],
        all_conversion_rollups=[candidate],
        gap_stats={("7.7.7.7", "Mozilla/5.0 Chrome/121.0"): {"min": 10.0, "max": 1000.0}},
    )
    rules = ConversionSuspiciousRuleSet(
        conversion_threshold=99,
        media_threshold=99,
        program_threshold=99,
        burst_conversion_threshold=99,
        min_click_to_conv_seconds=None,
        max_click_to_conv_seconds=300,
    )
    detector = ConversionSuspiciousDetector(repo, rules)

    # When
    findings = detector.find_for_date(date(2026, 1, 1))

    # Then
    assert len(findings) == 1
    assert any(
        reason.startswith("click_to_conversion_seconds >=")
        for reason in findings[0].reasons
    )


def test_conversion_detector_adds_click_padding_linked_ratio_reason():
    candidate = _conversion_rollup(
        conversion_count=5,
        media_count=1,
        program_count=1,
        ipaddress="4.4.4.4",
        useragent="Mozilla/5.0 Chrome/121.0",
    )
    repo = _StubRepo(
        click_rollups=[],
        conversion_rollups=[candidate],
        all_conversion_rollups=[],
        gap_stats={},
        padding_stats={
            ("4.4.4.4", "Mozilla/5.0 Chrome/121.0"): {
                "linked_click_count": 12,
                "extra_window_click_count": 0,
                "extra_window_useragents": [],
            }
        },
    )
    rules = ConversionSuspiciousRuleSet(
        conversion_threshold=5,
        media_threshold=99,
        program_threshold=99,
        burst_conversion_threshold=99,
    )
    detector = ConversionSuspiciousDetector(repo, rules)

    findings = detector.find_for_date(date(2026, 1, 1))

    assert len(findings) == 1
    assert any(
        reason.startswith("click_padding_linked_ratio >=")
        for reason in findings[0].reasons
    )
    assert findings[0].linked_click_count == 12
    assert findings[0].linked_clicks_per_conversion == 12 / 5


def test_conversion_detector_adds_extra_window_and_non_browser_padding_reasons():
    candidate = _conversion_rollup(
        conversion_count=5,
        media_count=1,
        program_count=1,
        ipaddress="5.5.5.5",
        useragent="Mozilla/5.0 Chrome/121.0",
    )
    repo = _StubRepo(
        click_rollups=[],
        conversion_rollups=[candidate],
        all_conversion_rollups=[],
        gap_stats={},
        padding_stats={
            ("5.5.5.5", "Mozilla/5.0 Chrome/121.0"): {
                "linked_click_count": 5,
                "extra_window_click_count": 12,
                "extra_window_useragents": [
                    "leafworks/1.0",
                    "leafworks/1.0",
                    "Kickback/1.0",
                    "Kickback/1.0",
                    "tracking system(at-m.net/sf-a.jp)",
                    "tracking system(at-m.net/sf-a.jp)",
                    "admage",
                    "admage",
                    "Mozilla/5.0 Chrome/121.0",
                    "Mozilla/5.0 Safari/605.1",
                ],
            }
        },
    )
    rules = ConversionSuspiciousRuleSet(
        conversion_threshold=5,
        media_threshold=99,
        program_threshold=99,
        burst_conversion_threshold=99,
    )
    detector = ConversionSuspiciousDetector(repo, rules)

    findings = detector.find_for_date(date(2026, 1, 1))

    assert len(findings) == 1
    assert any(
        reason.startswith("click_padding_extra_window >=")
        for reason in findings[0].reasons
    )
    assert any(
        reason.startswith("click_padding_non_browser_ratio >=")
        for reason in findings[0].reasons
    )
    assert findings[0].extra_window_click_count == 12
    assert findings[0].extra_window_non_browser_ratio == 0.8


def test_conversion_detector_does_not_create_padding_only_findings():
    candidate = _conversion_rollup(
        conversion_count=1,
        media_count=1,
        program_count=1,
        ipaddress="6.6.6.6",
        useragent="Mozilla/5.0 Chrome/121.0",
    )
    repo = _StubRepo(
        click_rollups=[],
        conversion_rollups=[],
        all_conversion_rollups=[candidate],
        gap_stats={},
        padding_stats={
            ("6.6.6.6", "Mozilla/5.0 Chrome/121.0"): {
                "linked_click_count": 5,
                "extra_window_click_count": 12,
                "extra_window_useragents": ["leafworks/1.0"] * 12,
            }
        },
    )
    rules = ConversionSuspiciousRuleSet(
        conversion_threshold=5,
        media_threshold=99,
        program_threshold=99,
        burst_conversion_threshold=99,
        min_click_to_conv_seconds=None,
        max_click_to_conv_seconds=None,
    )
    detector = ConversionSuspiciousDetector(repo, rules)

    findings = detector.find_for_date(date(2026, 1, 1))

    assert findings == []
