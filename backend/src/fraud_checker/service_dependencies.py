from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from .acs_client import AcsHttpClient
from .config import resolve_acs_settings
from .db.session import get_database_url
from .job_status_pg import JobStatusStorePG
from .repository_pg import PostgresRepository
from .time_utils import now_local


def get_repository() -> PostgresRepository:
    return PostgresRepository(get_database_url())


def get_job_store() -> JobStatusStorePG:
    return JobStatusStorePG(get_database_url())


def get_acs_client() -> AcsHttpClient:
    settings = resolve_acs_settings()
    return AcsHttpClient(
        base_url=settings.base_url,
        access_key=settings.access_key,
        secret_key=settings.secret_key,
        endpoint_path=settings.log_endpoint,
    )


@dataclass(frozen=True)
class RuntimeDependencies:
    repository_factory: Callable[[], PostgresRepository]
    job_store_factory: Callable[[], JobStatusStorePG]
    acs_client_factory: Callable[[], AcsHttpClient]
    now_provider: Callable[[], datetime]

    def repository(self) -> PostgresRepository:
        return self.repository_factory()

    def job_store(self) -> JobStatusStorePG:
        return self.job_store_factory()

    def acs_client(self) -> AcsHttpClient:
        return self.acs_client_factory()

    def now(self) -> datetime:
        return self.now_provider()


def get_runtime_dependencies() -> RuntimeDependencies:
    return RuntimeDependencies(
        repository_factory=get_repository,
        job_store_factory=get_job_store,
        acs_client_factory=get_acs_client,
        now_provider=now_local,
    )
