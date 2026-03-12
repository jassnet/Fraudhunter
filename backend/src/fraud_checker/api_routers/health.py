from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends, HTTPException

from ..api_dependencies import require_admin
from ..services.jobs import get_repository

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/")
def root():
    return {"message": "Fraud Checker API v2.0", "status": "running"}


@router.get("/api/health", dependencies=[Depends(require_admin)])
def health_check():
    issues: list[dict] = []
    warnings: list[dict] = []

    db_path = os.getenv("FRAUD_DB_PATH")
    database_url = os.getenv("DATABASE_URL")
    if not db_path and not database_url:
        issues.append(
            {
                "type": "error",
                "field": "FRAUD_DB_PATH",
                "message": "データベースパスが設定されていません",
                "hint": ".envファイルにFRAUD_DB_PATHを設定してください",
            }
        )

    acs_base_url = os.getenv("ACS_BASE_URL")
    if not acs_base_url:
        issues.append(
            {
                "type": "error",
                "field": "ACS_BASE_URL",
                "message": "ACS APIのURLが設定されていません",
                "hint": ".envファイルにACS_BASE_URLを設定してください",
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
                "message": "ACS API認証情報が設定されていません",
                "hint": ".envファイルにACS_TOKEN、またはACS_ACCESS_KEYとACS_SECRET_KEYを設定してください",
            }
        )

    try:
        repo = get_repository()
        click_count = repo.fetch_one("SELECT COUNT(*) as cnt FROM click_ipua_daily")
        if not click_count or click_count["cnt"] == 0:
            warnings.append(
                {
                    "type": "warning",
                    "field": "click_data",
                    "message": "クリックログデータがありません",
                    "hint": "「データ取り込み」からクリックログを取り込んでください",
                }
            )

        media_count = repo.fetch_one("SELECT COUNT(*) as cnt FROM master_media")
        if not media_count or media_count["cnt"] == 0:
            warnings.append(
                {
                    "type": "warning",
                    "field": "master_data",
                    "message": "マスタデータが未同期です",
                    "hint": "「設定」→「マスタデータ」→「ACSから同期」を実行してください",
                }
            )
    except Exception as exc:
        logger.exception("Error checking health status")
        issues.append(
            {
                "type": "error",
                "field": "database",
                "message": f"データベースに接続できません: {exc}",
                "hint": "FRAUD_DB_PATHが正しいか確認してください",
            }
        )

    has_errors = any(item["type"] == "error" for item in issues)
    has_warnings = bool(warnings)
    return {
        "status": "error" if has_errors else ("warning" if has_warnings else "ok"),
        "issues": issues + warnings,
        "config": {
            "db_path_configured": bool(db_path or database_url),
            "acs_base_url_configured": bool(acs_base_url),
            "acs_auth_configured": bool(acs_token or (acs_access_key and acs_secret_key)),
        },
    }
