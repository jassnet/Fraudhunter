from __future__ import annotations

import os


PRODUCTION_ENVS = {"prod", "production"}
LOCAL_ENVS = {"dev", "development", "local", "test"}


def current_env() -> str:
    return os.getenv("FC_ENV", "production").strip().lower()


def is_production_env() -> bool:
    return current_env() in PRODUCTION_ENVS


def should_enable_docs() -> bool:
    explicit = os.getenv("FC_ENABLE_API_DOCS")
    if explicit is not None:
        return explicit.strip().lower() in {"1", "true", "yes", "on"}
    return not is_production_env()


def validate_runtime_guards() -> None:
    env = current_env()
    allow_insecure_admin = os.getenv("FC_ALLOW_INSECURE_ADMIN", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    allow_insecure_acs = os.getenv("ACS_ALLOW_INSECURE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if env in PRODUCTION_ENVS and allow_insecure_admin:
        raise RuntimeError("FC_ALLOW_INSECURE_ADMIN must not be enabled in production.")
    if env in PRODUCTION_ENVS and allow_insecure_acs:
        raise RuntimeError("ACS_ALLOW_INSECURE must not be enabled in production.")
