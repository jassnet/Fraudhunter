from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Optional

from .api_models import JobStatusResponse
from .services import lifecycle


IDLE_JOB_MESSAGE = "まだジョブは実行されていません"
QUEUED_JOB_MESSAGE = "ジョブを実行待ちキューに登録しました"
FAILED_JOB_MESSAGE = "ジョブが失敗しました"
RISK_LABELS = {
    "high": "高リスク",
    "medium": "中リスク",
    "low": "低リスク",
}

_REASON_PRIORITY = {
    "spread_both": 0,
    "spread_media": 0,
    "spread_program": 0,
    "click_padding": 1,
    "burst": 2,
    "timing_fast": 3,
    "timing_slow": 3,
    "volume": 4,
}


def format_reasons(reasons: list[str]) -> list[str]:
    formatted: list[str] = []
    for reason in reasons:
        if reason.startswith("total_clicks >="):
            threshold = reason.split(">=")[1].strip()
            formatted.append(f"クリック数が閾値以上です（{threshold}件以上）")
        elif reason.startswith("media_count >="):
            threshold = reason.split(">=")[1].strip()
            formatted.append(f"同一 IP/UA で複数媒体にまたがるクリックがあります（{threshold}媒体以上）")
        elif reason.startswith("program_count >="):
            threshold = reason.split(">=")[1].strip()
            formatted.append(f"同一 IP/UA で複数案件にまたがるクリックがあります（{threshold}案件以上）")
        elif reason.startswith("burst:") and "clicks" in reason:
            formatted.append("短時間にクリックが集中しています（バースト検知）")
        elif reason.startswith("conversion_count >="):
            threshold = reason.split(">=")[1].strip()
            formatted.append(f"成果数が閾値以上です（{threshold}件以上）")
        elif reason.startswith("burst:") and "conversions" in reason:
            formatted.append("短時間に成果が集中しています（バースト検知）")
        elif reason.startswith("click_to_conversion_seconds <="):
            threshold = reason.split("<=")[1].split("s")[0].strip()
            formatted.append(f"クリックから成果までの時間が短すぎます（{threshold}秒以下）")
        elif reason.startswith("click_to_conversion_seconds >="):
            threshold = reason.split(">=")[1].split("s")[0].strip()
            formatted.append(f"クリックから成果までの時間が長すぎます（{threshold}秒以上）")
        elif reason.startswith("click_padding_linked_ratio >="):
            threshold = reason.split(">=")[1].split("(")[0].strip()
            formatted.append(
                f"不審CVに紐づくクリック数が多すぎます（CVあたり{threshold}件以上）"
            )
        elif reason.startswith("click_padding_extra_window >="):
            threshold = reason.split(">=")[1].split("in")[0].strip()
            formatted.append(
                f"不審CVの前後30分に追加クリックが集中しています（{threshold}件以上）"
            )
        elif reason.startswith("click_padding_non_browser_ratio >="):
            threshold = reason.split(">=")[1].split("(")[0].strip()
            formatted.append(
                f"追加クリックの非ブラウザ比率が高すぎます（{threshold}以上）"
            )
        else:
            formatted.append(reason)
    return formatted


def _collect_reason_group_entries(reasons: list[str], *, is_conversion: bool) -> list[tuple[str, str]]:
    grouped: list[tuple[str, str]] = []

    has_media_spread = any(reason.startswith("media_count >=") for reason in reasons)
    has_program_spread = any(reason.startswith("program_count >=") for reason in reasons)
    if has_media_spread or has_program_spread:
        if has_media_spread and has_program_spread:
            grouped.append(("spread_both", "\u540c\u4e00 IP/UA \u3067\u8907\u6570\u5a92\u4f53\u30fb\u8907\u6570\u6848\u4ef6\u306b\u307e\u305f\u304c\u308b\u6210\u679c\u304c\u3042\u308a\u307e\u3059"))
        elif has_media_spread:
            grouped.append(("spread_media", "\u540c\u4e00 IP/UA \u3067\u8907\u6570\u5a92\u4f53\u306b\u307e\u305f\u304c\u308b\u6210\u679c\u304c\u3042\u308a\u307e\u3059"))
        else:
            grouped.append(("spread_program", "\u540c\u4e00 IP/UA \u3067\u8907\u6570\u6848\u4ef6\u306b\u307e\u305f\u304c\u308b\u6210\u679c\u304c\u3042\u308a\u307e\u3059"))

    if any(reason.startswith("click_padding_") for reason in reasons):
        grouped.append(("click_padding", "\u4e0d\u5be9CV\u3092\u96a0\u3059\u305f\u3081\u306e\u30af\u30ea\u30c3\u30af\u4e0a\u4e57\u305b\u304c\u7591\u308f\u308c\u307e\u3059"))

    if any(reason.startswith("burst:") for reason in reasons):
        grouped.append(
            (
                "burst",
                "\u77ed\u6642\u9593\u306b\u6210\u679c\u304c\u96c6\u4e2d\u3057\u3066\u3044\u307e\u3059"
                if is_conversion
                else "\u77ed\u6642\u9593\u306b\u30af\u30ea\u30c3\u30af\u304c\u96c6\u4e2d\u3057\u3066\u3044\u307e\u3059",
            )
        )

    if any(reason.startswith("click_to_conversion_seconds <=") for reason in reasons):
        grouped.append(("timing_fast", "\u30af\u30ea\u30c3\u30af\u304b\u3089\u6210\u679c\u307e\u3067\u306e\u6642\u9593\u304c\u77ed\u3059\u304e\u307e\u3059"))
    if any(reason.startswith("click_to_conversion_seconds >=") for reason in reasons):
        grouped.append(("timing_slow", "\u30af\u30ea\u30c3\u30af\u304b\u3089\u6210\u679c\u307e\u3067\u306e\u6642\u9593\u304c\u9577\u3059\u304e\u307e\u3059"))

    has_volume_reason = any(
        reason.startswith("total_clicks >=") or reason.startswith("conversion_count >=")
        for reason in reasons
    )
    if has_volume_reason:
        grouped.append(
            (
                "volume",
                "\u540c\u4e00 IP/UA \u304b\u3089\u6210\u679c\u304c\u96c6\u4e2d\u3057\u3066\u3044\u307e\u3059"
                if is_conversion
                else "\u540c\u4e00 IP/UA \u304b\u3089\u30af\u30ea\u30c3\u30af\u304c\u96c6\u4e2d\u3057\u3066\u3044\u307e\u3059",
            )
        )

    grouped.sort(key=lambda item: _REASON_PRIORITY.get(item[0], 99))
    return grouped


def _reason_cluster_key_from_entries(grouped: list[tuple[str, str]], raw_reasons: list[str]) -> str:
    if grouped:
        ids = sorted({gid for gid, _ in grouped})
        return "|".join(ids)
    raw = "\n".join(sorted(raw_reasons))
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"raw:{digest}"


def build_reason_display(reasons: list[str], *, is_conversion: bool) -> dict:
    grouped = _collect_reason_group_entries(reasons, is_conversion=is_conversion)
    reason_groups = [label for _, label in grouped]
    return {
        "reason_summary": reason_groups[0] if reason_groups else None,
        "reason_group_count": len(reason_groups),
        "reason_groups": reason_groups,
        "reason_cluster_key": _reason_cluster_key_from_entries(grouped, reasons),
    }


def calculate_risk_level(reasons: list[str], count: int, is_conversion: bool = False) -> dict:
    score = len(reasons) * 20
    has_click_padding_reason = any(reason.startswith("click_padding_") for reason in reasons)

    for reason in reasons:
        if "burst" in reason.lower():
            score += 30
        if "click_to_conversion_seconds <=" in reason:
            score += 25
        if "media_count" in reason or "program_count" in reason:
            score += 15
    if has_click_padding_reason:
        score += 25

    if is_conversion:
        if count >= 10:
            score += 40
        elif count >= 5:
            score += 20
    else:
        if count >= 200:
            score += 40
        elif count >= 100:
            score += 25
        elif count >= 50:
            score += 10

    if score >= 80:
        return {"level": "high", "score": score, "label": RISK_LABELS["high"]}
    if score >= 40:
        return {"level": "medium", "score": score, "label": RISK_LABELS["medium"]}
    return {"level": "low", "score": score, "label": RISK_LABELS["low"]}


def format_datetime_value(value: object) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return None


def normalize_job_status_message(status: str, message: str | None) -> str | None:
    if message == "No job has been run yet":
        return IDLE_JOB_MESSAGE
    if message == "Job failed":
        return FAILED_JOB_MESSAGE
    if message is not None:
        return message
    if status == "idle":
        return IDLE_JOB_MESSAGE
    if status == "failed":
        return FAILED_JOB_MESSAGE
    return None


def mask_ipaddress(value: str | None) -> str:
    if not value:
        return "-"
    if ":" in value:
        segments = value.split(":")
        if len(segments) <= 2:
            return value
        return ":".join(segments[:2] + ["*"] * max(1, len(segments) - 2))
    parts = value.split(".")
    if len(parts) == 4:
        return ".".join(parts[:2] + ["x", "x"])
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:3]}***"


def mask_useragent(value: str | None) -> str:
    if not value:
        return "-"
    compact = " ".join(value.split())
    if len(compact) <= 24:
        return compact[:12] + "..." if len(compact) > 12 else compact
    return f"{compact[:18]}...{compact[-6:]}"


def build_job_status_response(status) -> JobStatusResponse:
    message = normalize_job_status_message(status.status, status.message)
    return JobStatusResponse(
        status=status.status,
        job_id=status.job_id if status.status != "idle" else None,
        message=message,
        started_at=format_datetime_value(status.started_at),
        completed_at=format_datetime_value(status.completed_at),
        result=status.result,
        queue=status.queue,
    )


def build_job_status_summary_response(status) -> JobStatusResponse:
    message = normalize_job_status_message(status.status, status.message)
    return JobStatusResponse(
        status=status.status,
        job_id=status.job_id if status.status != "idle" else None,
        message=message,
        started_at=format_datetime_value(status.started_at),
        completed_at=format_datetime_value(status.completed_at),
        result=None,
        queue=status.queue,
    )


def filter_findings_by_search(findings, details_cache, search: Optional[str], include_names: bool):
    if not search:
        return findings

    search_lower = search.lower()
    filtered = []
    for finding in findings:
        if search_lower in finding.ipaddress.lower() or search_lower in finding.useragent.lower():
            filtered.append(finding)
            continue
        if include_names:
            details = details_cache.get((finding.ipaddress, finding.useragent), [])
            media_names = [detail["media_name"].lower() for detail in details]
            program_names = [detail["program_name"].lower() for detail in details]
            if any(search_lower in name for name in media_names + program_names):
                filtered.append(finding)
    return filtered


def _detail_fields(details: list[dict]) -> dict:
    return {
        "details": details,
        "media_names": list({detail["media_name"] for detail in details}),
        "program_names": list({detail["program_name"] for detail in details}),
        "affiliate_names": list(
            {
                detail.get("affiliate_name", "")
                for detail in details
                if detail.get("affiliate_name")
            }
        ),
    }


def _evidence_fields(value: object) -> dict:
    if hasattr(value, "isoformat"):
        return lifecycle.describe_evidence_availability(value)
    return {
        "evidence_status": "unknown",
        "evidence_available": False,
        "evidence_expired": False,
        "evidence_retention_days": lifecycle.get_evidence_contract_days(),
        "evidence_expires_on": None,
        "evidence_checked_on": None,
    }


def present_click_finding(finding, include_names: bool, details: list[dict] | None = None) -> dict:
    risk = calculate_risk_level(finding.reasons, finding.total_clicks, is_conversion=False)
    reason_display = build_reason_display(finding.reasons, is_conversion=False)
    item = {
        "date": finding.date.isoformat(),
        "ipaddress": finding.ipaddress,
        "useragent": finding.useragent,
        "total_clicks": finding.total_clicks,
        "media_count": finding.media_count,
        "program_count": finding.program_count,
        "first_time": finding.first_time.isoformat(),
        "last_time": finding.last_time.isoformat(),
        "reasons": finding.reasons,
        "reasons_formatted": format_reasons(finding.reasons),
        "risk_level": risk["level"],
        "risk_score": risk["score"],
        "risk_label": risk["label"],
        **reason_display,
        **_evidence_fields(finding.date),
    }
    if include_names:
        item.update(_detail_fields(details or []))
    return item


def present_conversion_finding(finding, include_names: bool, details: list[dict] | None = None) -> dict:
    risk = calculate_risk_level(finding.reasons, finding.conversion_count, is_conversion=True)
    reason_display = build_reason_display(finding.reasons, is_conversion=True)
    item = {
        "date": finding.date.isoformat(),
        "ipaddress": finding.ipaddress,
        "useragent": finding.useragent,
        "total_conversions": finding.conversion_count,
        "media_count": finding.media_count,
        "program_count": finding.program_count,
        "first_time": finding.first_conversion_time.isoformat(),
        "last_time": finding.last_conversion_time.isoformat(),
        "reasons": finding.reasons,
        "reasons_formatted": format_reasons(finding.reasons),
        "min_click_to_conv_seconds": finding.min_click_to_conv_seconds,
        "max_click_to_conv_seconds": finding.max_click_to_conv_seconds,
        "linked_click_count": finding.linked_click_count,
        "linked_clicks_per_conversion": finding.linked_clicks_per_conversion,
        "extra_window_click_count": finding.extra_window_click_count,
        "extra_window_non_browser_ratio": finding.extra_window_non_browser_ratio,
        "risk_level": risk["level"],
        "risk_score": risk["score"],
        "risk_label": risk["label"],
        **reason_display,
        **_evidence_fields(finding.date),
    }
    if include_names:
        item.update(_detail_fields(details or []))
    return item


def present_click_finding_record(
    row: dict,
    details: list[dict] | None = None,
    *,
    mask_sensitive: bool = False,
) -> dict:
    ipaddress = row["ipaddress"]
    useragent = row["useragent"]
    masked_ip = mask_ipaddress(ipaddress)
    masked_ua = mask_useragent(useragent)
    reason_display = build_reason_display(row["reasons_json"], is_conversion=False)
    item = {
        "finding_key": row["finding_key"],
        "date": row["date"].isoformat() if hasattr(row["date"], "isoformat") else row["date"],
        "ipaddress": masked_ip if mask_sensitive else ipaddress,
        "useragent": masked_ua if mask_sensitive else useragent,
        "ipaddress_masked": masked_ip,
        "useragent_masked": masked_ua,
        "sensitive_values_masked": mask_sensitive,
        "total_clicks": row["total_clicks"],
        "media_count": row["media_count"],
        "program_count": row["program_count"],
        "first_time": row["first_time"].isoformat() if hasattr(row["first_time"], "isoformat") else row["first_time"],
        "last_time": row["last_time"].isoformat() if hasattr(row["last_time"], "isoformat") else row["last_time"],
        "reasons": row["reasons_json"],
        "reasons_formatted": row["reasons_formatted_json"],
        "risk_level": row["risk_level"],
        "risk_score": row["risk_score"],
        "risk_label": RISK_LABELS.get(row["risk_level"], row["risk_level"]),
        **reason_display,
        "media_names": row.get("media_names_json") or [],
        "program_names": row.get("program_names_json") or [],
        "affiliate_names": row.get("affiliate_names_json") or [],
        **_evidence_fields(row["date"]),
    }
    if details is not None:
        item["details"] = details
    return item


def present_conversion_finding_record(
    row: dict,
    details: list[dict] | None = None,
    *,
    mask_sensitive: bool = False,
) -> dict:
    ipaddress = row["ipaddress"]
    useragent = row["useragent"]
    masked_ip = mask_ipaddress(ipaddress)
    masked_ua = mask_useragent(useragent)
    reason_display = build_reason_display(row["reasons_json"], is_conversion=True)
    metrics = row.get("metrics_json") or {}
    item = {
        "finding_key": row["finding_key"],
        "date": row["date"].isoformat() if hasattr(row["date"], "isoformat") else row["date"],
        "ipaddress": masked_ip if mask_sensitive else ipaddress,
        "useragent": masked_ua if mask_sensitive else useragent,
        "ipaddress_masked": masked_ip,
        "useragent_masked": masked_ua,
        "sensitive_values_masked": mask_sensitive,
        "total_conversions": row["total_conversions"],
        "media_count": row["media_count"],
        "program_count": row["program_count"],
        "first_time": row["first_time"].isoformat() if hasattr(row["first_time"], "isoformat") else row["first_time"],
        "last_time": row["last_time"].isoformat() if hasattr(row["last_time"], "isoformat") else row["last_time"],
        "reasons": row["reasons_json"],
        "reasons_formatted": row["reasons_formatted_json"],
        "min_click_to_conv_seconds": row.get("min_click_to_conv_seconds"),
        "max_click_to_conv_seconds": row.get("max_click_to_conv_seconds"),
        "linked_click_count": metrics.get("linked_click_count"),
        "linked_clicks_per_conversion": metrics.get("linked_clicks_per_conversion"),
        "extra_window_click_count": metrics.get("extra_window_click_count"),
        "extra_window_non_browser_ratio": metrics.get("extra_window_non_browser_ratio"),
        "risk_level": row["risk_level"],
        "risk_score": row["risk_score"],
        "risk_label": RISK_LABELS.get(row["risk_level"], row["risk_level"]),
        **reason_display,
        "media_names": row.get("media_names_json") or [],
        "program_names": row.get("program_names_json") or [],
        "affiliate_names": row.get("affiliate_names_json") or [],
        **_evidence_fields(row["date"]),
    }
    if details is not None:
        item["details"] = details
    return item


def format_fraud_reasons(reasons: list[str]) -> list[str]:
    mapping = {
        "check_invalid_rate": "無効チェック率が高いです",
        "check_duplicate_plid": "同一アドクリックIDの重複が多いです",
        "track_auth_error_rate": "認証エラーが多いです",
        "track_auth_ip_ua_rate": "IP/UA認証への依存が高いです",
        "action_short_gap": "クリックから成果までが短すぎます",
        "action_fixed_gap_pattern": "成果発生間隔が不自然に揃っています",
        "action_cancel_rate": "キャンセル率が高いです",
        "promotion_duplicate_guard_bypass_risk": "案件の重複防止設定との乖離があります",
        "click_spike": "クリック数が直近基準より急増しています",
        "access_spike": "アクセス数が直近基準より急増しています",
        "ctr_spike": "CTRが直近基準より急増しています",
    }
    return [mapping.get(reason, reason) for reason in reasons]


def calculate_fraud_risk_level(reasons: list[str], primary_metric: int) -> dict:
    score = 0
    hard_signals = {"check_invalid_rate", "check_duplicate_plid"}
    medium_signals = {
        "track_auth_error_rate",
        "track_auth_ip_ua_rate",
        "action_short_gap",
        "action_fixed_gap_pattern",
        "action_cancel_rate",
        "promotion_duplicate_guard_bypass_risk",
    }
    soft_signals = {"click_spike", "access_spike", "ctr_spike"}
    for reason in reasons:
        if reason in hard_signals:
            score += 35
        elif reason in medium_signals:
            score += 20
        elif reason in soft_signals:
            score += 10
        else:
            score += 8
    if primary_metric >= 20:
        score += 15
    elif primary_metric >= 10:
        score += 8
    if score >= 80:
        return {"level": "high", "score": score, "label": RISK_LABELS["high"]}
    if score >= 40:
        return {"level": "medium", "score": score, "label": RISK_LABELS["medium"]}
    return {"level": "low", "score": score, "label": RISK_LABELS["low"]}


def present_fraud_finding_record(row: dict) -> dict:
    reason_display = build_reason_display(row["reasons_json"], is_conversion=True)
    metrics = row.get("metrics_json") or {}
    return {
        "finding_key": row["finding_key"],
        "date": row["date"].isoformat() if hasattr(row["date"], "isoformat") else row["date"],
        "user_id": row["user_id"],
        "media_id": row["media_id"],
        "promotion_id": row["promotion_id"],
        "user_name": row.get("user_name") or row["user_id"],
        "media_name": row.get("media_name") or row["media_id"],
        "promotion_name": row.get("promotion_name") or row["promotion_id"],
        "primary_metric": row["primary_metric"],
        "reasons": row["reasons_json"],
        "reasons_formatted": row.get("reasons_formatted_json") or format_fraud_reasons(row["reasons_json"]),
        "risk_level": row["risk_level"],
        "risk_score": row["risk_score"],
        "risk_label": RISK_LABELS.get(row["risk_level"], row["risk_level"]),
        "first_time": format_datetime_value(row.get("first_time")),
        "last_time": format_datetime_value(row.get("last_time")),
        "details": metrics,
        **reason_display,
        **_evidence_fields(row["date"]),
    }
