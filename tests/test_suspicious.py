from datetime import date, datetime, timedelta, timezone

from fraud_checker.models import ClickLog
from fraud_checker.repository import SQLiteRepository
from fraud_checker.suspicious import SuspiciousDetector, SuspiciousRuleSet


def _click(
    idx: int,
    *,
    click_date: date,
    seconds: int,
    media: str = "m1",
    program: str = "p1",
    ip: str = "1.1.1.1",
    ua: str = "UA",
):
    base = datetime.combine(click_date, datetime.min.time(), tzinfo=timezone.utc)
    return ClickLog(
        click_id=f"c{idx}",
        click_time=base + timedelta(seconds=seconds),
        media_id=media,
        program_id=program,
        ipaddress=ip,
        useragent=ua,
        referrer=None,
        raw_payload=None,
    )


def test_detects_high_volume_cross_media_and_burst(tmp_path):
    repo = SQLiteRepository(tmp_path / "suspicious.db")
    repo.ensure_schema(store_raw=False)
    target = date(2024, 1, 5)

    clicks = []
    # High volume: 60 clicks for same IP/UA
    for i in range(60):
        clicks.append(
            _click(
                idx=100 + i,
                click_date=target,
                seconds=i * 10,
                media="ma",
                program="pa",
                ip="9.9.9.9",
                ua="UA-busy",
            )
        )

    # Cross media: 1 click per media across 3 media IDs
    for j, media in enumerate(["ma", "mb", "mc"]):
        clicks.append(
            _click(
                idx=200 + j,
                click_date=target,
                seconds=400 + j,
                media=media,
                program="pb",
                ip="2.2.2.2",
                ua="UA-wide",
            )
        )

    # Burst in short window: 20 clicks within 5 minutes
    for k in range(20):
        clicks.append(
            _click(
                idx=300 + k,
                click_date=target,
                seconds=k * 15,
                media="mc",
                program="pc",
                ip="3.3.3.3",
                ua="UA-burst",
            )
        )

    # Benign: should not be flagged
    clicks.append(
        _click(
            idx=400,
            click_date=target,
            seconds=100,
            media="md",
            program="pd",
            ip="4.4.4.4",
            ua="UA-normal",
        )
    )

    repo.ingest_clicks(clicks, target_date=target, store_raw=False)

    detector = SuspiciousDetector(repo, rules=SuspiciousRuleSet())
    findings = detector.find_for_date(target)

    keys = {(f.ipaddress, f.useragent) for f in findings}
    assert ("9.9.9.9", "UA-busy") in keys  # high volume
    assert ("2.2.2.2", "UA-wide") in keys  # cross media
    assert ("3.3.3.3", "UA-burst") in keys  # burst window
    assert ("4.4.4.4", "UA-normal") not in keys


def test_browser_only_filter(tmp_path):
    """browser_only=True の場合、ブラウザ由来UAのみが検知対象になる"""
    repo = SQLiteRepository(tmp_path / "browser.db")
    repo.ensure_schema(store_raw=False)
    target = date(2024, 1, 10)

    clicks = []
    # ブラウザ由来のUA: Chrome（検知対象）
    for i in range(60):
        clicks.append(
            _click(
                idx=100 + i,
                click_date=target,
                seconds=i * 10,
                media="ma",
                program="pa",
                ip="10.0.0.1",
                ua="Mozilla/5.0 (Windows NT 10.0) Chrome/120.0.0.0 Safari/537.36",
            )
        )

    # サーバー由来のUA: python-requests（除外対象）
    for i in range(60):
        clicks.append(
            _click(
                idx=200 + i,
                click_date=target,
                seconds=i * 10,
                media="mb",
                program="pb",
                ip="10.0.0.2",
                ua="python-requests/2.28.0",
            )
        )

    # サーバー由来のUA: curl（除外対象）
    for i in range(60):
        clicks.append(
            _click(
                idx=300 + i,
                click_date=target,
                seconds=i * 10,
                media="mc",
                program="pc",
                ip="10.0.0.3",
                ua="curl/7.88.1",
            )
        )

    # ボットUA（除外対象）
    for i in range(60):
        clicks.append(
            _click(
                idx=400 + i,
                click_date=target,
                seconds=i * 10,
                media="md",
                program="pd",
                ip="10.0.0.4",
                ua="Mozilla/5.0 (compatible; Googlebot/2.1)",
            )
        )

    # ブラウザ由来のUA: Firefox（検知対象）
    for i in range(60):
        clicks.append(
            _click(
                idx=500 + i,
                click_date=target,
                seconds=i * 10,
                media="me",
                program="pe",
                ip="10.0.0.5",
                ua="Mozilla/5.0 (Windows NT 10.0; rv:121.0) Gecko/20100101 Firefox/121.0",
            )
        )

    repo.ingest_clicks(clicks, target_date=target, store_raw=False)

    # browser_only=False の場合（デフォルト）: すべて検知
    detector_all = SuspiciousDetector(repo, rules=SuspiciousRuleSet(browser_only=False))
    findings_all = detector_all.find_for_date(target)
    keys_all = {f.ipaddress for f in findings_all}
    assert "10.0.0.1" in keys_all
    assert "10.0.0.2" in keys_all
    assert "10.0.0.3" in keys_all
    assert "10.0.0.4" in keys_all
    assert "10.0.0.5" in keys_all

    # browser_only=True の場合: ブラウザUAのみ検知
    detector_browser = SuspiciousDetector(repo, rules=SuspiciousRuleSet(browser_only=True))
    findings_browser = detector_browser.find_for_date(target)
    keys_browser = {f.ipaddress for f in findings_browser}
    assert "10.0.0.1" in keys_browser  # Chrome: 検知される
    assert "10.0.0.2" not in keys_browser  # python-requests: 除外
    assert "10.0.0.3" not in keys_browser  # curl: 除外
    assert "10.0.0.4" not in keys_browser  # Googlebot: 除外
    assert "10.0.0.5" in keys_browser  # Firefox: 検知される


def test_exclude_datacenter_ip_filter(tmp_path):
    """exclude_datacenter_ip=True の場合、データセンターIPが除外される"""
    repo = SQLiteRepository(tmp_path / "datacenter.db")
    repo.ensure_schema(store_raw=False)
    target = date(2024, 1, 15)

    clicks = []
    # 一般ユーザーのIP（検知対象）
    for i in range(60):
        clicks.append(
            _click(
                idx=100 + i,
                click_date=target,
                seconds=i * 10,
                media="ma",
                program="pa",
                ip="192.168.1.100",
                ua="Mozilla/5.0 Chrome/120.0.0.0",
            )
        )

    # GoogleのIP（除外対象）
    for i in range(60):
        clicks.append(
            _click(
                idx=200 + i,
                click_date=target,
                seconds=i * 10,
                media="mb",
                program="pb",
                ip="74.125.113.26",
                ua="Mozilla/5.0 Chrome/120.0.0.0",
            )
        )

    # AWSのIP（除外対象: 52.x.x.x）
    for i in range(60):
        clicks.append(
            _click(
                idx=300 + i,
                click_date=target,
                seconds=i * 10,
                media="mc",
                program="pc",
                ip="52.199.47.143",
                ua="Mozilla/5.0 Chrome/120.0.0.0",
            )
        )

    # GoogleのIP（除外対象: 172.253.x.x）
    for i in range(60):
        clicks.append(
            _click(
                idx=400 + i,
                click_date=target,
                seconds=i * 10,
                media="md",
                program="pd",
                ip="172.253.218.61",
                ua="Mozilla/5.0 Chrome/120.0.0.0",
            )
        )

    # 別の一般ユーザーIP（検知対象）
    for i in range(60):
        clicks.append(
            _click(
                idx=500 + i,
                click_date=target,
                seconds=i * 10,
                media="me",
                program="pe",
                ip="203.0.113.50",
                ua="Mozilla/5.0 Firefox/121.0",
            )
        )

    repo.ingest_clicks(clicks, target_date=target, store_raw=False)

    # exclude_datacenter_ip=False の場合（デフォルト）: すべて検知
    detector_all = SuspiciousDetector(repo, rules=SuspiciousRuleSet(exclude_datacenter_ip=False))
    findings_all = detector_all.find_for_date(target)
    keys_all = {f.ipaddress for f in findings_all}
    assert "192.168.1.100" in keys_all
    assert "74.125.113.26" in keys_all
    assert "52.199.47.143" in keys_all
    assert "172.253.218.61" in keys_all
    assert "203.0.113.50" in keys_all

    # exclude_datacenter_ip=True の場合: データセンターIP除外
    detector_no_dc = SuspiciousDetector(repo, rules=SuspiciousRuleSet(exclude_datacenter_ip=True))
    findings_no_dc = detector_no_dc.find_for_date(target)
    keys_no_dc = {f.ipaddress for f in findings_no_dc}
    assert "192.168.1.100" in keys_no_dc  # 一般IP: 検知される
    assert "74.125.113.26" not in keys_no_dc  # Google IP: 除外
    assert "52.199.47.143" not in keys_no_dc  # AWS IP: 除外
    assert "172.253.218.61" not in keys_no_dc  # Google IP: 除外
    assert "203.0.113.50" in keys_no_dc  # 一般IP: 検知される
