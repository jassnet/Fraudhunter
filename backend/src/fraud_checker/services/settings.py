from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import date

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
from ..service_protocols import SettingsRepository
from ..suspicious import ConversionSuspiciousRuleSet, SuspiciousRuleSet

logger = logging.getLogger(__name__)

_settings_cache: dict | None = None
_settings_cache_updated_at = None


def settings_fingerprint(settings: dict) -> str:
    canonical = json.dumps(settings, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _repo_settings_updated_at(repo: SettingsRepository):
    getter = getattr(repo, "get_settings_updated_at", None)
    if getter is None:
        return None
    return getter()


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


def _load_settings(repo: SettingsRepository) -> dict:
    try:
        db_settings = repo.load_settings()
        if db_settings:
            env_defaults = _load_settings_from_env()
            return {**env_defaults, **db_settings}
    except Exception as exc:
        logger.warning("Failed to load settings from DB: %s", exc)
    return _load_settings_from_env()


def get_settings(repo: SettingsRepository) -> dict:
    global _settings_cache, _settings_cache_updated_at
    db_updated_at = _repo_settings_updated_at(repo)
    if not _settings_cache or db_updated_at != _settings_cache_updated_at:
        _settings_cache = _load_settings(repo)
        _settings_cache_updated_at = db_updated_at
    return _settings_cache


def update_settings(repo: SettingsRepository, settings: dict) -> dict:
    global _settings_cache, _settings_cache_updated_at
    fingerprint = settings_fingerprint(settings)
    try:
        settings_version_id = repo.save_settings(settings, fingerprint=fingerprint)
        _settings_cache = settings
        _settings_cache_updated_at = _repo_settings_updated_at(repo)
        logger.info("Settings saved to DB: %s", _settings_cache)
    except Exception as exc:
        logger.exception("Failed to save settings to DB")
        _settings_cache = settings
        return {
            "success": True,
            "settings": _settings_cache,
            "persisted": False,
            "warning": str(exc),
        }

    try:
        from . import findings as findings_service
        from . import reporting as reporting_service

        dates = [
            date.fromisoformat(value)
            for value in reporting_service.get_available_dates(repo)
            if value
        ]
        recompute_generation_id = f"settings-{uuid.uuid4().hex[:12]}"
        recomputed = findings_service.recompute_findings_for_dates(
            repo,
            dates,
            generation_id=recompute_generation_id,
        )
        return {
            "success": True,
            "settings": _settings_cache,
            "persisted": True,
            "settings_version_id": settings_version_id,
            "settings_fingerprint": fingerprint,
            "findings_recomputed": True,
            "recomputed_dates": recomputed,
            "generation_id": recompute_generation_id,
        }
    except Exception as exc:
        logger.exception("Settings persisted but finding recomputation failed")
        return {
            "success": True,
            "settings": _settings_cache,
            "persisted": True,
            "settings_version_id": settings_version_id,
            "settings_fingerprint": fingerprint,
            "findings_recomputed": False,
            "warning": str(exc),
        }


def build_rule_sets(
    repo: SettingsRepository,
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
