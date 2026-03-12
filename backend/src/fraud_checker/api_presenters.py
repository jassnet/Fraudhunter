from __future__ import annotations

from datetime import datetime
from typing import Optional

from .api_models import JobStatusResponse


IDLE_JOB_MESSAGE = "まだジョブは実行されていません"
FAILED_JOB_MESSAGE = "ジョブが失敗しました"


def format_reasons(reasons: list[str]) -> list[str]:
    formatted: list[str] = []
    for reason in reasons:
        if reason.startswith("total_clicks >="):
            threshold = reason.split(">=")[1].strip()
            formatted.append(f"クリック数が閾値以上です（{threshold}件以上）")
        elif reason.startswith("media_count >="):
            threshold = reason.split(">=")[1].strip()
            formatted.append(
                f"同一IP/UAで複数メディアにまたがるクリックがあります（{threshold}媒体以上）"
            )
        elif reason.startswith("program_count >="):
            threshold = reason.split(">=")[1].strip()
            formatted.append(
                f"同一IP/UAで複数案件にまたがるクリックがあります（{threshold}案件以上）"
            )
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
        else:
            formatted.append(reason)
    return formatted


def calculate_risk_level(reasons: list[str], count: int, is_conversion: bool = False) -> dict:
    score = 0
    score += len(reasons) * 20

    for reason in reasons:
        if "burst" in reason.lower():
            score += 30
        if "click_to_conversion_seconds <=" in reason:
            score += 25
        if "media_count" in reason or "program_count" in reason:
            score += 15

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
        return {"level": "high", "score": score, "label": "高リスク"}
    if score >= 40:
        return {"level": "medium", "score": score, "label": "中リスク"}
    return {"level": "low", "score": score, "label": "低リスク"}


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


def build_job_status_response(status) -> JobStatusResponse:
    message = normalize_job_status_message(status.status, status.message)
    return JobStatusResponse(
        status=status.status,
        job_id=status.job_id if status.status != "idle" else None,
        message=message,
        started_at=format_datetime_value(status.started_at),
        completed_at=format_datetime_value(status.completed_at),
        result=status.result,
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


def present_click_finding(finding, include_names: bool, details: list[dict] | None = None) -> dict:
    risk = calculate_risk_level(finding.reasons, finding.total_clicks, is_conversion=False)
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
    }
    if include_names:
        item.update(_detail_fields(details or []))
    return item


def present_conversion_finding(finding, include_names: bool, details: list[dict] | None = None) -> dict:
    risk = calculate_risk_level(finding.reasons, finding.conversion_count, is_conversion=True)
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
        "risk_level": risk["level"],
        "risk_score": risk["score"],
        "risk_label": risk["label"],
    }
    if include_names:
        item.update(_detail_fields(details or []))
    return item
