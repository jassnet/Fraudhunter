from .suspicious_findings_read import SuspiciousFindingsReadRepository
from .suspicious_findings_write import SuspiciousFindingsWriteRepository


class SuspiciousReadRepository(
    SuspiciousFindingsWriteRepository,
    SuspiciousFindingsReadRepository,
):
    """Backward-compatible facade over suspicious findings read/write responsibilities."""
