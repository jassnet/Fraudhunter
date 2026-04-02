from __future__ import annotations

import fraud_checker.db.models  # noqa: F401

from .repositories import (
    FraudFindingsReadRepository,
    FraudFindingsWriteRepository,
    IngestionRepository,
    MasterRepository,
    ReportingReadRepository,
    SettingsRepository,
    SuspiciousReadRepository,
)


class PostgresRepository(
    IngestionRepository,
    ReportingReadRepository,
    FraudFindingsReadRepository,
    FraudFindingsWriteRepository,
    SuspiciousReadRepository,
    MasterRepository,
    SettingsRepository,
):
    """Backward-compatible facade over split repository responsibilities."""
