from __future__ import annotations

import logging
import os


PRODUCTION_ENVS = {"prod", "production"}
LOCAL_ENVS = {"dev", "development", "local", "test"}
logger = logging.getLogger(__name__)


def current_env() -> str:
    return os.getenv("FC_ENV", "production").strip().lower()


def is_production_env() -> bool:
    return current_env() in PRODUCTION_ENVS


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def read_access_mode() -> str:
    require_read_auth = _env_truthy("FC_REQUIRE_READ_AUTH")
    external_protection = _env_truthy("FC_EXTERNAL_READ_PROTECTION")
    allow_public_read = _env_truthy("FC_ALLOW_PUBLIC_READ")
    selected = [
        mode
        for mode, enabled in (
            ("read_auth", require_read_auth),
            ("external_protection", external_protection),
            ("public", allow_public_read),
        )
        if enabled
    ]
    if len(selected) > 1:
        raise RuntimeError(
            "Choose only one read-access mode: FC_REQUIRE_READ_AUTH, "
            "FC_EXTERNAL_READ_PROTECTION, or FC_ALLOW_PUBLIC_READ."
        )
    if selected:
        return selected[0]
    if current_env() in LOCAL_ENVS:
        return "local"
    return "unset"


def should_enable_docs() -> bool:
    explicit = os.getenv("FC_ENABLE_API_DOCS")
    if explicit is not None:
        return explicit.strip().lower() in {"1", "true", "yes", "on"}
    return not is_production_env()


def validate_runtime_guards() -> None:
    env = current_env()
    allow_insecure_admin = _env_truthy("FC_ALLOW_INSECURE_ADMIN")
    allow_insecure_acs = _env_truthy("ACS_ALLOW_INSECURE")

    if env in PRODUCTION_ENVS and allow_insecure_admin:
        raise RuntimeError("FC_ALLOW_INSECURE_ADMIN must not be enabled in production.")
    if env in PRODUCTION_ENVS and allow_insecure_acs:
        raise RuntimeError("ACS_ALLOW_INSECURE must not be enabled in production.")
    if env not in LOCAL_ENVS and allow_insecure_admin:
        logger.warning("FC_ALLOW_INSECURE_ADMIN is enabled outside local/test environments.")
    if env in PRODUCTION_ENVS and read_access_mode() == "unset":
        raise RuntimeError(
            "Production must declare a read-access posture. Set exactly one of "
            "FC_REQUIRE_READ_AUTH=true, FC_EXTERNAL_READ_PROTECTION=true, "
            "or FC_ALLOW_PUBLIC_READ=true."
        )
