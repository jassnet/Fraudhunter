from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from fraud_checker.models import ConversionIpUaRollup
from fraud_checker.suspicious import ConversionSuspiciousDetector, ConversionSuspiciousRuleSet


@dataclass
class _StubRepo:
    conversion_rollups: list[ConversionIpUaRollup]
    all_conversion_rollups: list[ConversionIpUaRollup]
    gap_stats: dict[tuple[str, str], dict[str, float]]
    padding_stats: dict[tuple[str, str], dict[str, object]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.conversion_call_args: dict | None = None

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
        self,
        target_date: date,
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
        return {key: self.padding_stats[key] for key in ip_ua_pairs if key in self.padding_stats}


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


def test_conversion_detector_adds_gap_only_findings():
    candidate = _conversion_rollup(
        conversion_count=1,
        media_count=1,
        program_count=1,
        ipaddress="2.2.2.2",
        useragent="Mozilla/5.0 Safari/605.1",
    )
    repo = _StubRepo(
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

    findings = detector.find_for_date(date(2026, 1, 1))

    assert len(findings) == 1
    assert any(reason.startswith("click_to_conversion_seconds <=") for reason in findings[0].reasons)
    assert repo.conversion_call_args is not None
    assert repo.conversion_call_args["burst_conversion_threshold"] == 99


def test_conversion_detector_respects_browser_and_datacenter_filters():
    filtered_candidate = _conversion_rollup(
        ipaddress="3.10.10.10",
        useragent="python-requests/2.31.0",
    )
    repo = _StubRepo(
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

    findings = detector.find_for_date(date(2026, 1, 1))

    assert findings == []


def test_conversion_detector_adds_max_gap_reason():
    candidate = _conversion_rollup(
        conversion_count=1,
        media_count=1,
        program_count=1,
        ipaddress="7.7.7.7",
        useragent="Mozilla/5.0 Chrome/121.0",
    )
    repo = _StubRepo(
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

    findings = detector.find_for_date(date(2026, 1, 1))

    assert len(findings) == 1
    assert any(reason.startswith("click_to_conversion_seconds >=") for reason in findings[0].reasons)


def test_conversion_detector_adds_click_padding_linked_ratio_reason():
    candidate = _conversion_rollup(
        conversion_count=5,
        media_count=1,
        program_count=1,
        ipaddress="4.4.4.4",
        useragent="Mozilla/5.0 Chrome/121.0",
    )
    repo = _StubRepo(
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
    assert any(reason.startswith("click_padding_linked_ratio >=") for reason in findings[0].reasons)
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
    assert any(reason.startswith("click_padding_extra_window >=") for reason in findings[0].reasons)
    assert any(
        reason.startswith("click_padding_non_browser_ratio >=") for reason in findings[0].reasons
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


def test_conversion_detector_skips_padding_lookup_when_repository_does_not_support_it():
    candidate = _conversion_rollup(conversion_count=5)

    class RepoWithoutPadding:
        def __init__(self):
            self.called_padding = False

        def fetch_suspicious_conversion_rollups(self, *args, **kwargs):
            return [candidate]

        def fetch_click_to_conversion_gaps(self, target_date):
            return {}

        def fetch_conversion_rollups(self, target_date):
            return []

    repo = RepoWithoutPadding()
    detector = ConversionSuspiciousDetector(repo, ConversionSuspiciousRuleSet(conversion_threshold=5))

    findings = detector.find_for_date(date(2026, 1, 1))

    assert len(findings) == 1
