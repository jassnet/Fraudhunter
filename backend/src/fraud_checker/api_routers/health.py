from __future__ import annotations

import logging
import os
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException

from ..api_dependencies import require_protected_access
from ..runtime_guards import read_access_mode
from ..service_dependencies import get_acs_client, get_job_store, get_repository
from ..services import reporting
from ..services.jobs import (
    JOB_TYPE_CLICK_INGEST,
    JOB_TYPE_CONVERSION_INGEST,
    JOB_TYPE_REFRESH,
    _should_use_in_process_background_kick,
)
from ..time_utils import now_local

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


def _serialize_health_metrics(repo) -> dict:
    latest_click = repo.fetch_one("SELECT MAX(date) AS last_date FROM click_ipua_daily")
    latest_conv = repo.fetch_one("SELECT MAX(date) AS last_date FROM conversion_ipua_daily")
    latest_date = max(
        [item["last_date"] for item in (latest_click, latest_conv) if item and item.get("last_date")],
        default=None,
    )
    latest_date_obj = date.fromisoformat(latest_date) if isinstance(latest_date, str) else latest_date

    coverage = repo.get_click_ipua_coverage(latest_date_obj) if latest_date_obj else None
    conversion_enrichment = (
        repo.get_conversion_click_enrichment(latest_date_obj) if latest_date_obj else None
    )
    masters = repo.get_all_masters()
    last_master_sync = masters.get("last_synced_at")
    if isinstance(last_master_sync, datetime):
        master_sync_age_hours = round((now_local() - last_master_sync).total_seconds() / 3600, 2)
        last_master_sync = last_master_sync.isoformat()
    else:
        master_sync_age_hours = None

    job_store = get_job_store()
    last_ingest = job_store.get_latest_successful_finished_at(
        [JOB_TYPE_CLICK_INGEST, JOB_TYPE_CONVERSION_INGEST, JOB_TYPE_REFRESH]
    )
    findings = (
        reporting.get_summary(repo, latest_date_obj.isoformat())["quality"]["findings"]
        if latest_date_obj
        else {"findings_last_computed_at": None, "stale": False, "stale_reasons": []}
    )
    queue_metrics = job_store.get_queue_metrics()
    if isinstance(queue_metrics.get("oldest_queued_at"), datetime):
        queue_metrics["oldest_queued_at"] = queue_metrics["oldest_queued_at"].isoformat()
    try:
        acs_api = get_acs_client().ping()
    except Exception as exc:
        acs_api = {"ok": False, "error": str(exc)}

    return {
        "latest_data_date": latest_date_obj.isoformat() if latest_date_obj else None,
        "last_successful_ingest_at": last_ingest.isoformat() if last_ingest else None,
        "findings": findings,
        "click_ip_ua_coverage": coverage,
        "conversion_click_enrichment": conversion_enrichment,
        "master_sync": {
            "last_synced_at": last_master_sync,
            "age_hours": master_sync_age_hours,
        },
        "jobs": queue_metrics,
        "acs_api": acs_api,
    }


@router.get("/")
def root():
    return {"message": "Fraud Checker API", "status": "running", "storage": "postgresql"}


@router.get("/api/health/public")
def public_health_check():
    return {
        "status": "ok",
        "service": "fraud-checker-api",
        "storage": "postgresql",
        "read_access_mode": read_access_mode(),
    }


@router.get("/api/health", dependencies=[Depends(require_protected_access)])
def health_check():
    issues: list[dict] = []
    warnings: list[dict] = []

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        issues.append(
            {
                "type": "error",
                "field": "DATABASE_URL",
                "message": "PostgreSQL 接続文字列が設定されていません",
                "hint": ".env ファイルに DATABASE_URL を設定してください",
            }
        )

    acs_base_url = os.getenv("ACS_BASE_URL")
    if not acs_base_url:
        issues.append(
            {
                "type": "error",
                "field": "ACS_BASE_URL",
                "message": "ACS API の URL が設定されていません",
                "hint": ".env ファイルに ACS_BASE_URL を設定してください",
            }
        )

    acs_token = os.getenv("ACS_TOKEN")
    acs_access_key = os.getenv("ACS_ACCESS_KEY")
    acs_secret_key = os.getenv("ACS_SECRET_KEY")
    if not acs_token and not (acs_access_key and acs_secret_key):
        issues.append(
            {
                "type": "error",
                "field": "ACS_TOKEN / ACS_ACCESS_KEY / ACS_SECRET_KEY",
                "message": "ACS API 認証情報が設定されていません",
                "hint": ".env ファイルに ACS_TOKEN または ACS_ACCESS_KEY と ACS_SECRET_KEY を設定してください",
            }
        )

    try:
        repo = get_repository()
        click_count = repo.fetch_one("SELECT COUNT(*) AS cnt FROM click_ipua_daily")
        if not click_count or click_count["cnt"] == 0:
            warnings.append(
                {
                    "type": "warning",
                    "field": "click_data",
                    "message": "クリックログデータがありません",
                    "hint": "「データ再取得」またはクリックログ取り込みを実行してください",
                }
            )

        media_count = repo.fetch_one("SELECT COUNT(*) AS cnt FROM master_media")
        if not media_count or media_count["cnt"] == 0:
            warnings.append(
                {
                    "type": "warning",
                    "field": "master_data",
                    "message": "マスタデータが同期されていません",
                    "hint": "管理画面または「マスタ同期」API から同期を実行してください",
                }
            )

        metrics = _serialize_health_metrics(repo)
    except Exception as exc:
        logger.exception("Error checking health status")
        issues.append(
            {
                "type": "error",
                "field": "database",
                "message": f"データベースに接続できません: {exc}",
                "hint": "DATABASE_URL と migration の適用状況を確認してください",
            }
        )
        metrics = None

    return {
        "status": "error" if issues else ("warning" if warnings else "ok"),
        "issues": issues + warnings,
        "config": {
            "database_url_configured": bool(database_url),
            "acs_base_url_configured": bool(acs_base_url),
            "acs_auth_configured": bool(acs_token or (acs_access_key and acs_secret_key)),
            "read_access_mode": read_access_mode(),
            "in_process_job_kick_enabled": _should_use_in_process_background_kick(),
        },
        "metrics": metrics,
    }
