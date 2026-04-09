from fraud_checker.services import jobs


def test_run_refresh_includes_detect(monkeypatch):
    class DummySettings:
        page_size = 10

    class DummyClickIngestor:
        def __init__(self, *args, **kwargs):
            self.last_affected_dates = []

        def run_for_time_range(self, start_time, end_time):
            self.last_affected_dates = [start_time.date()]
            return 1, 0

    class DummyConversionIngestor:
        def __init__(self, *args, **kwargs):
            self.last_affected_dates = []

        def run_for_time_range(self, start_time, end_time):
            self.last_affected_dates = [start_time.date()]
            return 2, 0, 2, 1

    class DummyRepo:
        def ensure_fraud_schema(self):
            return None

        def replace_check_logs(self, target_date, checks):
            return 0

        def replace_track_logs(self, target_date, tracks):
            return 0

        def replace_entity_daily_metrics(self, target_date, metrics, *, table_name, value_column):
            return 0

    class DummyClient:
        def fetch_check_logs(self, target_date, page, page_size):
            return []

        def fetch_track_logs(self, target_date, page, page_size):
            return []

        def fetch_click_metrics(self, target_date, page, page_size):
            return []

        def fetch_access_metrics(self, target_date, page, page_size):
            return []

        def fetch_imp_metrics(self, target_date, page, page_size):
            return []

    monkeypatch.setattr(jobs, "resolve_acs_settings", lambda: DummySettings())
    monkeypatch.setattr(jobs, "get_repository", lambda: DummyRepo())
    monkeypatch.setattr(jobs, "get_acs_client", lambda: DummyClient())
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
    assert len(result["findings_recompute"]["target_dates"]) == 1


def test_run_refresh_skips_recompute_when_detect_is_false(monkeypatch):
    class DummySettings:
        page_size = 10

    class DummyClickIngestor:
        def __init__(self, *args, **kwargs):
            self.last_affected_dates = []

        def run_for_time_range(self, start_time, end_time):
            self.last_affected_dates = [start_time.date()]
            return 1, 0

    class DummyConversionIngestor:
        def __init__(self, *args, **kwargs):
            self.last_affected_dates = []

        def run_for_time_range(self, start_time, end_time):
            self.last_affected_dates = [start_time.date()]
            return 2, 0, 2, 1

    class DummyRepo:
        pass

    captured: list[list] = []
    monkeypatch.setattr(jobs, "resolve_acs_settings", lambda: DummySettings())
    monkeypatch.setattr(jobs, "get_repository", lambda: DummyRepo())
    monkeypatch.setattr(jobs, "get_acs_client", lambda: object())
    monkeypatch.setattr(jobs, "ClickLogIngestor", DummyClickIngestor)
    monkeypatch.setattr(jobs, "ConversionIngestor", DummyConversionIngestor)
    monkeypatch.setattr(
        jobs,
        "enqueue_findings_recompute_jobs",
        lambda dates, **kwargs: captured.append(dates) or [],
    )

    result, _message = jobs.run_refresh(1, clicks=True, conversions=True, detect=False)

    assert "findings_recompute" not in result
    assert captured == []


def test_run_master_sync_ensures_master_schema_before_upserts(monkeypatch):
    class DummyRepo:
        def __init__(self):
            self.master_schema_ensured = False

        def ensure_master_schema(self):
            self.master_schema_ensured = True

        def bulk_upsert_media(self, media_list):
            assert self.master_schema_ensured is True
            return len(media_list)

        def bulk_upsert_promotions(self, promo_list):
            assert self.master_schema_ensured is True
            return len(promo_list)

        def bulk_upsert_users(self, user_list):
            assert self.master_schema_ensured is True
            return len(user_list)

    class DummyClient:
        def fetch_all_media_master(self):
            return [{"id": "m1", "name": "Media 1"}]

        def fetch_all_promotion_master(self):
            return [{"id": "p1", "name": "Promo 1"}]

        def fetch_all_user_master(self):
            return [{"id": "u1", "name": "User 1"}]

    repo = DummyRepo()

    monkeypatch.setattr(jobs, "get_repository", lambda: repo)
    monkeypatch.setattr(jobs, "get_acs_client", lambda: DummyClient())
    monkeypatch.setattr("fraud_checker.services.reporting.get_available_dates", lambda repo: [])

    result, message = jobs.run_master_sync()

    assert repo.master_schema_ensured is True
    assert result["media_count"] == 1
    assert result["promotion_count"] == 1
    assert result["user_count"] == 1
    assert message == "Master sync completed"
