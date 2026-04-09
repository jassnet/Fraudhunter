from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import date
from pathlib import Path

from ..api_presenters import calculate_risk_level, format_reasons
from ..constants import DEFAULT_REWARD_YEN
from ..logging_utils import log_event, log_timed
from ..service_protocols import FindingsRepository
from ..suspicious import ConversionSuspiciousDetector
from ..time_utils import now_local
from . import settings as settings_service

logger = logging.getLogger(__name__)


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _rule_version(settings: dict) -> str:
    canonical = json.dumps(settings, sort_keys=True, ensure_ascii=False)
    return _hash_text(canonical)[:16]


def _case_key(target_date: date, ipaddress: str, useragent: str) -> str:
    return _hash_text(f"conversion_case|{target_date.isoformat()}|{ipaddress}|{useragent}")


def _detector_code_version() -> str:
    suspicious_path = Path(__file__).resolve().parent.parent / "suspicious.py"
    return _hash_text(suspicious_path.read_text(encoding="utf-8", errors="ignore"))[:16]


def _search_text(*parts: str) -> str:
    return " ".join(part.lower() for part in parts if part)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _estimate_damage_snapshot(
    *,
    total_conversions: int,
    details: list[dict],
    program_unit_prices: dict[str, int],
) -> tuple[int, str, list[dict[str, object]]]:
    evidence_rows: list[dict[str, object]] = []
    estimated_damage = 0
    detail_total = 0

    for detail in details:
        conversion_count = int(detail.get("conversion_count") or 0)
        if conversion_count <= 0:
            continue
        detail_total += conversion_count
        program_id = str(detail.get("program_id") or "")
        if program_id and program_id in program_unit_prices:
            unit_price = program_unit_prices[program_id]
            source = "program_observed"
        else:
            unit_price = DEFAULT_REWARD_YEN
            source = "fallback_default"
        estimated_damage += conversion_count * unit_price
        evidence_rows.append(
            {
                "program_id": program_id or None,
                "program_name": detail.get("program_name") or None,
                "conversion_count": conversion_count,
                "unit_price_yen": unit_price,
                "unit_price_source": source,
            }
        )

    missing_count = max(total_conversions - detail_total, 0)
    if missing_count > 0:
        estimated_damage += missing_count * DEFAULT_REWARD_YEN
        evidence_rows.append(
            {
                "program_id": None,
                "program_name": "unknown",
                "conversion_count": missing_count,
                "unit_price_yen": DEFAULT_REWARD_YEN,
                "unit_price_source": "fallback_default",
            }
        )

    sources = {str(row["unit_price_source"]) for row in evidence_rows}
    if not sources:
        evidence_rows.append(
            {
                "program_id": None,
                "program_name": "unknown",
                "conversion_count": total_conversions,
                "unit_price_yen": DEFAULT_REWARD_YEN,
                "unit_price_source": "fallback_default",
            }
        )
        estimated_damage = total_conversions * DEFAULT_REWARD_YEN
        unit_price_source = "fallback_default"
    elif len(sources) == 1:
        unit_price_source = next(iter(sources))
    else:
        unit_price_source = "mixed"

    return estimated_damage, unit_price_source, evidence_rows


def recompute_findings_for_dates(
    repo: FindingsRepository,
    target_dates: list[date],
    *,
    computed_by_job_id: str | None = None,
    generation_id: str | None = None,
) -> dict[str, dict[str, int]]:
    if not target_dates:
        return {}

    settings = settings_service.get_settings(repo)
    _, conversion_rules = settings_service.build_rule_sets(repo)
    rule_version = _rule_version(settings)
    settings_fingerprint = settings_service.settings_fingerprint(settings)
    settings_version_id = repo.ensure_settings_version(settings, settings_fingerprint)
    detector_code_version = _detector_code_version()
    computed_at = now_local()
    generation_id = generation_id or f"recompute-{uuid.uuid4().hex[:12]}"
    settings_updated_at_snapshot = repo.get_settings_updated_at()
    results: dict[str, dict[str, int]] = {}

    conversion_detector = ConversionSuspiciousDetector(repo, conversion_rules)

    for target_date in sorted(set(target_dates)):
        with log_timed(logger, "recompute_findings", target_date=target_date):
            source_click_watermark = repo.get_click_data_watermark(target_date)
            source_conversion_watermark = repo.get_conversion_data_watermark(target_date)
            conversion_findings = conversion_detector.find_for_date(target_date)
            conversion_details = repo.get_suspicious_conversion_details_bulk(
                target_date,
                [(finding.ipaddress, finding.useragent) for finding in conversion_findings],
            )
            program_unit_prices = repo.get_program_unit_prices(
                target_date,
                [
                    str(detail["program_id"])
                    for details in conversion_details.values()
                    for detail in details
                    if detail.get("program_id")
                ],
            )
            conversion_rows = []
            for finding in conversion_findings:
                details = conversion_details.get((finding.ipaddress, finding.useragent), [])
                media_ids = _unique([detail["media_id"] for detail in details])
                program_ids = _unique([detail["program_id"] for detail in details])
                media_names = _unique([detail["media_name"] for detail in details])
                program_names = _unique([detail["program_name"] for detail in details])
                affiliate_ids = _unique([detail.get("affiliate_id") for detail in details if detail.get("affiliate_id")])
                affiliate_names = _unique([detail.get("affiliate_name") for detail in details if detail.get("affiliate_name")])
                estimated_damage_yen, damage_unit_price_source, damage_evidence = _estimate_damage_snapshot(
                    total_conversions=finding.conversion_count,
                    details=details,
                    program_unit_prices=program_unit_prices,
                )
                reasons_formatted = format_reasons(finding.reasons)
                risk = calculate_risk_level(finding.reasons, finding.conversion_count, is_conversion=True)
                metrics = {
                    "total_conversions": finding.conversion_count,
                    "media_count": finding.media_count,
                    "program_count": finding.program_count,
                    "min_click_to_conv_seconds": finding.min_click_to_conv_seconds,
                    "max_click_to_conv_seconds": finding.max_click_to_conv_seconds,
                    "linked_click_count": finding.linked_click_count,
                    "linked_clicks_per_conversion": finding.linked_clicks_per_conversion,
                    "extra_window_click_count": finding.extra_window_click_count,
                    "extra_window_non_browser_ratio": finding.extra_window_non_browser_ratio,
                    "first_time": finding.first_conversion_time.isoformat(),
                    "last_time": finding.last_conversion_time.isoformat(),
                }
                conversion_rows.append(
                    {
                        "finding_key": _hash_text(
                            f"conversion|{target_date.isoformat()}|{finding.ipaddress}|{finding.useragent}|{rule_version}"
                        ),
                        "case_key": _case_key(target_date, finding.ipaddress, finding.useragent),
                        "date": target_date,
                        "ipaddress": finding.ipaddress,
                        "useragent": finding.useragent,
                        "ua_hash": _hash_text(finding.useragent),
                        "media_ids_json": json.dumps(media_ids, ensure_ascii=False),
                        "program_ids_json": json.dumps(program_ids, ensure_ascii=False),
                        "media_names_json": json.dumps(media_names, ensure_ascii=False),
                        "program_names_json": json.dumps(program_names, ensure_ascii=False),
                        "affiliate_ids_json": json.dumps(affiliate_ids, ensure_ascii=False),
                        "affiliate_names_json": json.dumps(affiliate_names, ensure_ascii=False),
                        "risk_level": risk["level"],
                        "risk_score": risk["score"],
                        "reasons_json": json.dumps(finding.reasons, ensure_ascii=False),
                        "reasons_formatted_json": json.dumps(reasons_formatted, ensure_ascii=False),
                        "metrics_json": json.dumps(metrics, ensure_ascii=False),
                        "total_conversions": finding.conversion_count,
                        "media_count": finding.media_count,
                        "program_count": finding.program_count,
                        "min_click_to_conv_seconds": int(finding.min_click_to_conv_seconds) if finding.min_click_to_conv_seconds is not None else None,
                        "max_click_to_conv_seconds": int(finding.max_click_to_conv_seconds) if finding.max_click_to_conv_seconds is not None else None,
                        "first_time": finding.first_conversion_time,
                        "last_time": finding.last_conversion_time,
                        "rule_version": rule_version,
                        "computed_at": computed_at,
                        "computed_by_job_id": computed_by_job_id,
                        "settings_updated_at_snapshot": settings_updated_at_snapshot,
                        "source_click_watermark": source_click_watermark,
                        "source_conversion_watermark": source_conversion_watermark,
                        "estimated_damage_yen": estimated_damage_yen,
                        "damage_unit_price_source": damage_unit_price_source,
                        "damage_evidence_json": json.dumps(damage_evidence, ensure_ascii=False),
                        "generation_id": generation_id,
                        "is_current": True,
                        "search_text": _search_text(
                            finding.ipaddress,
                            finding.useragent,
                            *media_names,
                            *program_names,
                            *affiliate_names,
                            *reasons_formatted,
                        ),
                    }
                )
            repo.replace_conversion_findings(
                target_date,
                conversion_rows,
                generation_metadata={
                    "generation_id": generation_id,
                    "finding_type": "conversion",
                    "target_date": target_date,
                    "computed_by_job_id": computed_by_job_id,
                    "settings_version_id": settings_version_id,
                    "settings_fingerprint": settings_fingerprint,
                    "detector_code_version": detector_code_version,
                    "source_click_watermark": source_click_watermark,
                    "source_conversion_watermark": source_conversion_watermark,
                    "row_count": len(conversion_rows),
                    "created_at": computed_at,
                },
            )
            results[target_date.isoformat()] = {
                "suspicious_conversions": len(conversion_rows),
            }
            log_event(
                logger,
                "findings_recomputed",
                target_date=target_date,
                suspicious_conversions=len(conversion_rows),
                rule_version=rule_version,
                settings_version_id=settings_version_id,
                detector_code_version=detector_code_version,
                computed_by_job_id=computed_by_job_id,
                generation_id=generation_id,
            )

    return results
