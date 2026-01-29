from datetime import date, datetime, timedelta

from fraud_checker.models import ConversionIpUaRollup
from fraud_checker.suspicious import ConversionSuspiciousDetector, ConversionSuspiciousRuleSet


class _StubRepo:
    def __init__(self, rollup: ConversionIpUaRollup):
        self.rollup = rollup
        self.called_burst_threshold = None

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
    ):
        self.called_burst_threshold = burst_conversion_threshold
        return [self.rollup]

    def fetch_click_to_conversion_gaps(self, target_date: date):
        return {}

    def fetch_conversion_rollups(self, target_date: date):
        return []


def test_conversion_burst_threshold_is_used():
    target_date = date(2026, 1, 1)
    start_time = datetime(2026, 1, 1, 0, 0, 0)
    rollup = ConversionIpUaRollup(
        date=target_date,
        ipaddress="1.1.1.1",
        useragent="Mozilla/5.0",
        conversion_count=3,
        media_count=1,
        program_count=1,
        first_conversion_time=start_time,
        last_conversion_time=start_time + timedelta(seconds=10),
    )
    rules = ConversionSuspiciousRuleSet(
        conversion_threshold=99,
        media_threshold=99,
        program_threshold=99,
        burst_conversion_threshold=3,
        burst_window_seconds=1800,
    )
    repo = _StubRepo(rollup)
    detector = ConversionSuspiciousDetector(repo, rules)

    findings = detector.find_for_date(target_date)

    assert repo.called_burst_threshold == 3
    assert len(findings) == 1
    assert any(reason.startswith("burst:") for reason in findings[0].reasons)
