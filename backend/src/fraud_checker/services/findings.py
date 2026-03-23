from __future__ import annotations

import hashlib
import json
import logging
from datetime import date

from ..api_presenters import calculate_risk_level, format_reasons
from ..logging_utils import log_event, log_timed
from ..repository_pg import PostgresRepository
from ..suspicious import ConversionSuspiciousDetector, SuspiciousDetector
from ..time_utils import now_local
from . import settings as settings_service

logger = logging.getLogger(__name__)


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _rule_version(settings: dict) -> str:
    canonical = json.dumps(settings, sort_keys=True, ensure_ascii=False)
    return _hash_text(canonical)[:16]


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


def recompute_findings_for_dates(repo: PostgresRepository, target_dates: list[date]) -> dict[str, dict[str, int]]:
    if not target_dates:
        return {}

    settings = settings_service.get_settings(repo)
    click_rules, conversion_rules = settings_service.build_rule_sets(repo)
    rule_version = _rule_version(settings)
    computed_at = now_local()
    results: dict[str, dict[str, int]] = {}

    click_detector = SuspiciousDetector(repo, click_rules)
    conversion_detector = ConversionSuspiciousDetector(repo, conversion_rules)

    for target_date in sorted(set(target_dates)):
        with log_timed(logger, "recompute_findings", target_date=target_date):
            click_findings = click_detector.find_for_date(target_date)
            click_details = repo.get_suspicious_click_details_bulk(
                target_date,
                [(finding.ipaddress, finding.useragent) for finding in click_findings],
            )
            click_rows = []
            for finding in click_findings:
                details = click_details.get((finding.ipaddress, finding.useragent), [])
                media_ids = _unique([detail["media_id"] for detail in details])
                program_ids = _unique([detail["program_id"] for detail in details])
                media_names = _unique([detail["media_name"] for detail in details])
                program_names = _unique([detail["program_name"] for detail in details])
                affiliate_names = _unique([detail.get("affiliate_name") for detail in details if detail.get("affiliate_name")])
                reasons_formatted = format_reasons(finding.reasons)
                risk = calculate_risk_level(finding.reasons, finding.total_clicks, is_conversion=False)
                metrics = {
                    "total_clicks": finding.total_clicks,
                    "media_count": finding.media_count,
                    "program_count": finding.program_count,
                    "first_time": finding.first_time.isoformat(),
                    "last_time": finding.last_time.isoformat(),
                }
                click_rows.append(
                    {
                        "finding_key": _hash_text(
                            f"click|{target_date.isoformat()}|{finding.ipaddress}|{finding.useragent}|{rule_version}"
                        ),
                        "date": target_date,
                        "ipaddress": finding.ipaddress,
                        "useragent": finding.useragent,
                        "ua_hash": _hash_text(finding.useragent),
                        "media_ids_json": json.dumps(media_ids, ensure_ascii=False),
                        "program_ids_json": json.dumps(program_ids, ensure_ascii=False),
                        "media_names_json": json.dumps(media_names, ensure_ascii=False),
                        "program_names_json": json.dumps(program_names, ensure_ascii=False),
                        "affiliate_names_json": json.dumps(affiliate_names, ensure_ascii=False),
                        "risk_level": risk["level"],
                        "risk_score": risk["score"],
                        "reasons_json": json.dumps(finding.reasons, ensure_ascii=False),
                        "reasons_formatted_json": json.dumps(reasons_formatted, ensure_ascii=False),
                        "metrics_json": json.dumps(metrics, ensure_ascii=False),
                        "total_clicks": finding.total_clicks,
                        "media_count": finding.media_count,
                        "program_count": finding.program_count,
                        "first_time": finding.first_time,
                        "last_time": finding.last_time,
                        "rule_version": rule_version,
                        "computed_at": computed_at,
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
            repo.replace_click_findings(target_date, click_rows)

            conversion_findings = conversion_detector.find_for_date(target_date)
            conversion_details = repo.get_suspicious_conversion_details_bulk(
                target_date,
                [(finding.ipaddress, finding.useragent) for finding in conversion_findings],
            )
            conversion_rows = []
            for finding in conversion_findings:
                details = conversion_details.get((finding.ipaddress, finding.useragent), [])
                media_ids = _unique([detail["media_id"] for detail in details])
                program_ids = _unique([detail["program_id"] for detail in details])
                media_names = _unique([detail["media_name"] for detail in details])
                program_names = _unique([detail["program_name"] for detail in details])
                affiliate_names = _unique([detail.get("affiliate_name") for detail in details if detail.get("affiliate_name")])
                reasons_formatted = format_reasons(finding.reasons)
                risk = calculate_risk_level(finding.reasons, finding.conversion_count, is_conversion=True)
                metrics = {
                    "total_conversions": finding.conversion_count,
                    "media_count": finding.media_count,
                    "program_count": finding.program_count,
                    "min_click_to_conv_seconds": finding.min_click_to_conv_seconds,
                    "max_click_to_conv_seconds": finding.max_click_to_conv_seconds,
                    "first_time": finding.first_conversion_time.isoformat(),
                    "last_time": finding.last_conversion_time.isoformat(),
                }
                conversion_rows.append(
                    {
                        "finding_key": _hash_text(
                            f"conversion|{target_date.isoformat()}|{finding.ipaddress}|{finding.useragent}|{rule_version}"
                        ),
                        "date": target_date,
                        "ipaddress": finding.ipaddress,
                        "useragent": finding.useragent,
                        "ua_hash": _hash_text(finding.useragent),
                        "media_ids_json": json.dumps(media_ids, ensure_ascii=False),
                        "program_ids_json": json.dumps(program_ids, ensure_ascii=False),
                        "media_names_json": json.dumps(media_names, ensure_ascii=False),
                        "program_names_json": json.dumps(program_names, ensure_ascii=False),
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
            repo.replace_conversion_findings(target_date, conversion_rows)

            results[target_date.isoformat()] = {
                "suspicious_clicks": len(click_rows),
                "suspicious_conversions": len(conversion_rows),
            }
            log_event(
                logger,
                "findings_recomputed",
                target_date=target_date,
                suspicious_clicks=len(click_rows),
                suspicious_conversions=len(conversion_rows),
                rule_version=rule_version,
            )

    return results
