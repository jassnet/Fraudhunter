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
            return 2, 0, 2, 1

    monkeypatch.setattr(jobs, "resolve_acs_settings", lambda: DummySettings())
    monkeypatch.setattr(jobs, "get_repository", lambda: object())
    monkeypatch.setattr(jobs, "get_acs_client", lambda: object())
    monkeypatch.setattr(jobs, "ClickLogIngestor", DummyClickIngestor)
    monkeypatch.setattr(jobs, "ConversionIngestor", DummyConversionIngestor)
    monkeypatch.setattr(
        jobs,
        "enqueue_findings_recompute_jobs",
        lambda dates, **kwargs: [type("QueuedJob", (), {"id": f"job-{index + 1}"})() for index, _ in enumerate(dates)],
    )

    result, message = jobs.run_refresh(1, clicks=True, conversions=True, detect=True)

    assert result["clicks"]["new"] == 1
    assert result["conversions"]["new"] == 2
    assert result["conversions"]["click_enriched"] == 1
    assert result["findings_recompute"]["mode"] == "queued"
    assert result["findings_recompute"]["detect_requested"] is True
