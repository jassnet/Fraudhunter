from datetime import date, datetime, timedelta, timezone

from fraud_checker import cli
from fraud_checker.cli import main
from fraud_checker.models import ClickLog


class FakeCliClient:
    def __init__(self, clicks):
        self.clicks = clicks
        self.calls = []

    def fetch_click_logs(self, target_date: date, page: int, limit: int):
        self.calls.append((target_date, page, limit))
        # single page client; only page 1 returns data
        if page == 1:
            return self.clicks
        return []


def _click(idx: int, target: date, seconds: int, ip: str = "1.2.3.4"):
    base = datetime.combine(target, datetime.min.time(), tzinfo=timezone.utc)
    return ClickLog(
        click_id=f"cli-{idx}",
        click_time=base + timedelta(seconds=seconds),
        media_id="media-1",
        program_id="program-1",
        ipaddress=ip,
        useragent="UA-cli",
        referrer=None,
        raw_payload=None,
    )


def test_cli_ingest_and_list_suspicious(tmp_path, capfd):
    target = date(2024, 1, 7)
    clicks = [_click(1, target, 0), _click(2, target, 30)]
    fake_client = FakeCliClient(clicks)
    db_path = tmp_path / "cli.db"

    exit_code = main(
        [
            "ingest",
            "--date",
            target.isoformat(),
            "--db",
            str(db_path),
            "--store-raw",
            "--base-url",
            "https://example.invalid/api",
            "--access-key",
            "ak",
            "--secret-key",
            "sk",
        ],
        acs_client_factory=lambda settings: fake_client,
    )
    assert exit_code == 0
    out1 = capfd.readouterr().out
    assert "Ingested 2 click(s)" in out1
    assert (target, 1, 500) in fake_client.calls

    exit_code = main(
        [
            "suspicious",
            "--date",
            target.isoformat(),
            "--db",
            str(db_path),
            "--click-threshold",
            "1",
        ]
    )
    assert exit_code == 0
    out2 = capfd.readouterr().out
    assert "UA='UA-cli'" in out2


def test_cli_env_defaults(monkeypatch, tmp_path, capfd):
    target = date(2024, 1, 8)
    clicks = [_click(1, target, 0), _click(2, target, 10)]
    fake_client = FakeCliClient(clicks)
    db_path = tmp_path / "cli-env.db"

    monkeypatch.setenv("FRAUD_DB_PATH", str(db_path))
    monkeypatch.setenv("FRAUD_CLICK_THRESHOLD", "1")
    monkeypatch.setenv("ACS_BASE_URL", "https://example.invalid/api")
    monkeypatch.setenv("ACS_ACCESS_KEY", "ak")
    monkeypatch.setenv("ACS_SECRET_KEY", "sk")

    exit_code = main(
        [
            "ingest",
            "--date",
            target.isoformat(),
            "--store-raw",
        ],
        acs_client_factory=lambda settings: fake_client,
    )
    assert exit_code == 0

    exit_code = main(
        [
            "suspicious",
            "--date",
            target.isoformat(),
        ]
    )
    assert exit_code == 0
    out = capfd.readouterr().out
    assert "UA='UA-cli'" in out


def test_cli_daily_runs_yesterday(monkeypatch, tmp_path, capfd):
    class FakeToday(date):
        @classmethod
        def today(cls):
            return cls(2024, 1, 10)

    target = FakeToday(2024, 1, 9)
    clicks = [_click(1, target, 0)]
    fake_client = FakeCliClient(clicks)
    db_path = tmp_path / "cli-daily.db"

    monkeypatch.setattr(cli, "date", FakeToday)

    exit_code = main(
        [
            "daily",
            "--db",
            str(db_path),
            "--click-threshold",
            "1",
            "--base-url",
            "https://example.invalid/api",
            "--access-key",
            "ak",
            "--secret-key",
            "sk",
        ],
        acs_client_factory=lambda settings: fake_client,
    )

    assert exit_code == 0
    out = capfd.readouterr().out
    assert "Daily run for 2024-01-09" in out
