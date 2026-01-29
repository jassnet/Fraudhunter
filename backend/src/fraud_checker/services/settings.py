from __future__ import annotations

import logging

from ..config import (
    DEFAULT_BROWSER_ONLY,
    DEFAULT_BURST_CLICK_THRESHOLD,
    DEFAULT_BURST_CONVERSION_THRESHOLD,
    DEFAULT_BURST_CONVERSION_WINDOW_SECONDS,
    DEFAULT_BURST_WINDOW_SECONDS,
    DEFAULT_CLICK_THRESHOLD,
    DEFAULT_CONVERSION_THRESHOLD,
    DEFAULT_CONV_MEDIA_THRESHOLD,
    DEFAULT_CONV_PROGRAM_THRESHOLD,
    DEFAULT_EXCLUDE_DATACENTER_IP,
    DEFAULT_MAX_CLICK_TO_CONV_SECONDS,
    DEFAULT_MEDIA_THRESHOLD,
    DEFAULT_MIN_CLICK_TO_CONV_SECONDS,
    DEFAULT_PROGRAM_THRESHOLD,
    _env_bool,
    _env_int,
)
from ..suspicious import ConversionSuspiciousRuleSet, SuspiciousRuleSet
from ..repository_pg import PostgresRepository

logger = logging.getLogger(__name__)

_settings_cache: dict | None = None


def _load_settings_from_env() -> dict:
    return {
        "click_threshold": _env_int("FRAUD_CLICK_THRESHOLD", DEFAULT_CLICK_THRESHOLD),
        "media_threshold": _env_int("FRAUD_MEDIA_THRESHOLD", DEFAULT_MEDIA_THRESHOLD),
        "program_threshold": _env_int("FRAUD_PROGRAM_THRESHOLD", DEFAULT_PROGRAM_THRESHOLD),
        "burst_click_threshold": _env_int("FRAUD_BURST_CLICK_THRESHOLD", DEFAULT_BURST_CLICK_THRESHOLD),
        "burst_window_seconds": _env_int("FRAUD_BURST_WINDOW_SECONDS", DEFAULT_BURST_WINDOW_SECONDS),
        "conversion_threshold": _env_int("FRAUD_CONVERSION_THRESHOLD", DEFAULT_CONVERSION_THRESHOLD),
        "conv_media_threshold": _env_int("FRAUD_CONV_MEDIA_THRESHOLD", DEFAULT_CONV_MEDIA_THRESHOLD),
        "conv_program_threshold": _env_int("FRAUD_CONV_PROGRAM_THRESHOLD", DEFAULT_CONV_PROGRAM_THRESHOLD),
        "burst_conversion_threshold": _env_int(
            "FRAUD_BURST_CONVERSION_THRESHOLD", DEFAULT_BURST_CONVERSION_THRESHOLD
        ),
        "burst_conversion_window_seconds": _env_int(
            "FRAUD_BURST_CONVERSION_WINDOW_SECONDS", DEFAULT_BURST_CONVERSION_WINDOW_SECONDS
        ),
        "min_click_to_conv_seconds": _env_int(
            "FRAUD_MIN_CLICK_TO_CONV_SECONDS", DEFAULT_MIN_CLICK_TO_CONV_SECONDS
        ),
        "max_click_to_conv_seconds": _env_int(
            "FRAUD_MAX_CLICK_TO_CONV_SECONDS", DEFAULT_MAX_CLICK_TO_CONV_SECONDS
        ),
        "browser_only": _env_bool("FRAUD_BROWSER_ONLY", DEFAULT_BROWSER_ONLY),
        "exclude_datacenter_ip": _env_bool(
            "FRAUD_EXCLUDE_DATACENTER_IP", DEFAULT_EXCLUDE_DATACENTER_IP
        ),
    }


def _load_settings(repo: PostgresRepository) -> dict:
    try:
        db_settings = repo.load_settings()
        if db_settings:
            env_defaults = _load_settings_from_env()
            return {**env_defaults, **db_settings}
    except Exception as exc:
        logger.warning("Failed to load settings from DB: %s", exc)
    return _load_settings_from_env()


def get_settings(repo: PostgresRepository) -> dict:
    global _settings_cache
    if not _settings_cache:
        _settings_cache = _load_settings(repo)
    return _settings_cache


def update_settings(repo: PostgresRepository, settings: dict) -> dict:
    global _settings_cache
    try:
        repo.save_settings(settings)
        _settings_cache = settings
        logger.info("Settings saved to DB: %s", _settings_cache)
        return {"success": True, "settings": _settings_cache, "persisted": True}
    except Exception as exc:
        logger.exception("Failed to save settings to DB")
        _settings_cache = settings
        return {
            "success": True,
            "settings": _settings_cache,
            "persisted": False,
            "warning": str(exc),
        }


def build_rule_sets(
    repo: PostgresRepository,
) -> tuple[SuspiciousRuleSet, ConversionSuspiciousRuleSet]:
    settings = get_settings(repo)
    click_rules = SuspiciousRuleSet(
        click_threshold=settings["click_threshold"],
        media_threshold=settings["media_threshold"],
        program_threshold=settings["program_threshold"],
        burst_click_threshold=settings["burst_click_threshold"],
        burst_window_seconds=settings["burst_window_seconds"],
        browser_only=settings["browser_only"],
        exclude_datacenter_ip=settings["exclude_datacenter_ip"],
    )
    conversion_rules = ConversionSuspiciousRuleSet(
        conversion_threshold=settings["conversion_threshold"],
        media_threshold=settings["conv_media_threshold"],
        program_threshold=settings["conv_program_threshold"],
        burst_conversion_threshold=settings["burst_conversion_threshold"],
        burst_window_seconds=settings["burst_conversion_window_seconds"],
        min_click_to_conv_seconds=settings["min_click_to_conv_seconds"],
        max_click_to_conv_seconds=settings["max_click_to_conv_seconds"],
        browser_only=settings["browser_only"],
        exclude_datacenter_ip=settings["exclude_datacenter_ip"],
    )
    return click_rules, conversion_rules
