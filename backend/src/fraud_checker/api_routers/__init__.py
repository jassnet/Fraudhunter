from .console import router as console_router
from .fraud import router as fraud_router
from .health import router as health_router
from .jobs import router as jobs_router
from .masters import router as masters_router
from .reporting import router as reporting_router
from .settings import router as settings_router
from .suspicious import router as suspicious_router
from .testdata import router as testdata_router

__all__ = [
    "health_router",
    "console_router",
    "fraud_router",
    "jobs_router",
    "masters_router",
    "reporting_router",
    "settings_router",
    "suspicious_router",
    "testdata_router",
]
