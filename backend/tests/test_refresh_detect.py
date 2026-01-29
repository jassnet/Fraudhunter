from fraud_checker.services import jobs


def test_run_refresh_includes_detect(monkeypatch):
    class DummySettings:
        page_size = 10

    class DummyClickIngestor:
        def __init__(self, *args, **kwargs):
            pass

        def run_for_time_range(self, start_time, end_time):
            return 1, 0

    class DummyConversionIngestor:
        def __init__(self, *args, **kwargs):
            pass

        def run_for_time_range(self, start_time, end_time):
            return 2, 0, 2

    class DummyDetector:
        def __init__(self, *args, **kwargs):
            pass

        def find_for_date(self, target_date):
            return [], [], []

    monkeypatch.setattr(jobs, "resolve_acs_settings", lambda: DummySettings())
    monkeypatch.setattr(jobs, "get_repository", lambda: object())
    monkeypatch.setattr(jobs, "get_acs_client", lambda: object())
    monkeypatch.setattr(jobs, "ClickLogIngestor", DummyClickIngestor)
    monkeypatch.setattr(jobs, "ConversionIngestor", DummyConversionIngestor)
    monkeypatch.setattr(jobs, "CombinedSuspiciousDetector", DummyDetector)
    monkeypatch.setattr(jobs.settings_service, "build_rule_sets", lambda repo: (None, None))

    result, message = jobs.run_refresh(1, clicks=True, conversions=True, detect=True)

    assert result["clicks"]["new"] == 1
    assert result["conversions"]["new"] == 2
    assert "detect" in result
    assert isinstance(result["detect"], dict)
