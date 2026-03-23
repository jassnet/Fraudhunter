from __future__ import annotations

import fraud_checker.db.models  # noqa: F401

from .repositories import (
    IngestionRepository,
    MasterRepository,
    ReportingReadRepository,
    SettingsRepository,
    SuspiciousReadRepository,
)


class PostgresRepository(
    IngestionRepository,
    ReportingReadRepository,
    SuspiciousReadRepository,
    MasterRepository,
    SettingsRepository,
):
    """Backward-compatible facade over split repository responsibilities."""

