"""
FastAPI backend for Fraud Checker v2
"""
from __future__ import annotations

import logging
import os
from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from .api_models import (
    DailyStatsResponse,
    IngestRequest,
    IngestResponse,
    JobStatusResponse,
    RefreshRequest,
    SettingsModel,
    SummaryResponse,
    SuspiciousResponse,
)

from .env import load_env
from .config import (
    resolve_conversion_rules,
    resolve_rules,
)
from .suspicious import ConversionSuspiciousDetector, SuspiciousDetector
from .services import reporting, settings as settings_service
from .services.jobs import (
    JobConflictError,
    enqueue_job,
    get_job_store,
    get_repository,
    run_click_ingestion,
    run_conversion_ingestion,
    run_master_sync,
    run_refresh,
)

# Load environment variables (supports repo root and backend/.env)
load_env()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fraud Checker API",
    description="Fraud detection API",
    version="2.0.0",
)

# CORS settings for the local Next.js frontend
_cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "FC_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Helper Functions ==========

def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip() or None
    return None


def require_admin(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None),
) -> None:
    expected = os.getenv("FC_ADMIN_API_KEY")
    if not expected:
        # Allow in dev when no key is configured.
        return
    token = x_api_key or _extract_bearer(authorization)
    if token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def format_reasons(reasons: list[str]) -> list[str]:
    """
    判定理由を人が読みやすい日本語に変換する
    """
    formatted = []
    for reason in reasons:
        if reason.startswith("total_clicks >="):
            threshold = reason.split(">=")[1].strip()
            formatted.append(f"クリック数過多（{threshold}回以上）")
        elif reason.startswith("media_count >="):
            threshold = reason.split(">=")[1].strip()
            formatted.append(
                f"同じ端末・ブラウザから別のサイト/ページを短時間に行き来しています（{threshold}件以上）"
            )
        elif reason.startswith("program_count >="):
            threshold = reason.split(">=")[1].strip()
            formatted.append(
                f"同じ端末・ブラウザから別の商品/申込ページを次々に見ています（{threshold}件以上）"
            )
        elif reason.startswith("burst:") and "clicks" in reason:
            # "burst: 25 clicks in 300s (<= 600s)"
            formatted.append(f"短時間クリック集中（バースト検知）")
        elif reason.startswith("conversion_count >="):
            threshold = reason.split(">=")[1].strip()
            formatted.append(f"成果数過多（{threshold}件以上）")
        elif reason.startswith("burst:") and "conversions" in reason:
            formatted.append(f"短時間成果集中（バースト検知）")
        elif reason.startswith("click_to_conversion_seconds <="):
            threshold = reason.split("<=")[1].split("s")[0].strip()
            formatted.append(f"クリック→成果までが短すぎ（閾値{threshold}秒）")
        elif reason.startswith("click_to_conversion_seconds >="):
            threshold = reason.split(">=")[1].split("s")[0].strip()
            formatted.append(f"クリック→成果までが長すぎ（閾値{threshold}秒）")
        else:
            formatted.append(reason)
    return formatted


def calculate_risk_level(reasons: list[str], count: int, is_conversion: bool = False) -> dict:
    """
    リスクレベルを計算する
    返り値: {"level": "high"|"medium"|"low", "score": int, "label": str}
    """
    score = 0
    
    # 理由の数に基づくスコア
    reason_count = len(reasons)
    score += reason_count * 20
    
    # 特定の理由に基づく追加スコア
    for reason in reasons:
        if "burst" in reason.lower():
            score += 30  # バースト検知は重要
        if "click_to_conversion_seconds <=" in reason:
            score += 25  # クリック→成果が短すぎは重要
        if "media_count" in reason or "program_count" in reason:
            score += 15  # 複数媒体/案件
    
    # 件数に基づくスコア
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
    
    # レベル判定
    if score >= 80:
        return {"level": "high", "score": score, "label": "高リスク"}
    elif score >= 40:
        return {"level": "medium", "score": score, "label": "中リスク"}
    else:
        return {"level": "low", "score": score, "label": "低リスク"}


def _resolve_target_date(repo, table: str, target_date: Optional[str]) -> Optional[str]:
    if target_date:
        return target_date
    return reporting.get_latest_date(repo, table)


def _filter_findings(findings, details_cache, search: Optional[str], include_names: bool):
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
            media_names = [d["media_name"].lower() for d in details]
            program_names = [d["program_name"].lower() for d in details]
            if any(search_lower in name for name in media_names + program_names):
                filtered.append(finding)
    return filtered


# ========== API Endpoints ==========

@app.get("/")
def root():
    return {"message": "Fraud Checker API v2.0", "status": "running"}


@app.get("/api/health")
def health_check():
    """システムの状態と環境変数の設定状況をチェック"""
    import os
    
    issues = []
    warnings = []
    
    # 必須環境変数のチェック
    db_path = os.getenv("FRAUD_DB_PATH")
    database_url = os.getenv("DATABASE_URL")
    if not db_path and not database_url:
        issues.append({
            "type": "error",
            "field": "FRAUD_DB_PATH",
            "message": "データベースパスが設定されていません",
            "hint": ".envファイルにFRAUD_DB_PATHを設定してください"
        })
    
    acs_base_url = os.getenv("ACS_BASE_URL")
    if not acs_base_url:
        issues.append({
            "type": "error",
            "field": "ACS_BASE_URL",
            "message": "ACS APIのURLが設定されていません",
            "hint": ".envファイルにACS_BASE_URLを設定してください"
        })
    
    acs_token = os.getenv("ACS_TOKEN")
    acs_access_key = os.getenv("ACS_ACCESS_KEY")
    acs_secret_key = os.getenv("ACS_SECRET_KEY")
    if not acs_token and not (acs_access_key and acs_secret_key):
        issues.append({
            "type": "error",
            "field": "ACS_TOKEN / ACS_ACCESS_KEY / ACS_SECRET_KEY",
            "message": "ACS API認証情報が設定されていません",
            "hint": ".envファイルにACS_TOKEN、またはACS_ACCESS_KEYとACS_SECRET_KEYを設定してください"
        })
    
    # DBの状態チェック
    try:
        repo = get_repository()
        
        # クリックデータの有無
        click_count = repo.fetch_one("SELECT COUNT(*) as cnt FROM click_ipua_daily")
        if not click_count or click_count["cnt"] == 0:
            warnings.append({
                "type": "warning",
                "field": "click_data",
                "message": "クリックログデータがありません",
                "hint": "「データ取り込み」からクリックログを取り込んでください"
            })
        
        # マスタデータの有無
        media_count = repo.fetch_one("SELECT COUNT(*) as cnt FROM master_media")
        if not media_count or media_count["cnt"] == 0:
            warnings.append({
                "type": "warning",
                "field": "master_data",
                "message": "マスタデータが未同期です",
                "hint": "「設定」→「マスタデータ」→「ACSから同期」を実行してください"
            })
    except Exception as e:
        issues.append({
            "type": "error",
            "field": "database",
            "message": f"データベースに接続できません: {str(e)}",
            "hint": "FRAUD_DB_PATHが正しいか確認してください"
        })
    
    has_errors = len([i for i in issues if i["type"] == "error"]) > 0
    has_warnings = len(warnings) > 0
    
    return {
        "status": "error" if has_errors else ("warning" if has_warnings else "ok"),
        "issues": issues + warnings,
        "config": {
            "db_path_configured": bool(db_path or database_url),
            "acs_base_url_configured": bool(acs_base_url),
            "acs_auth_configured": bool(acs_token or (acs_access_key and acs_secret_key)),
        }
    }


@app.get("/api/summary", response_model=SummaryResponse)
def get_summary(target_date: Optional[str] = None):
    """Get summary statistics for a specific date."""
    try:
        repo = get_repository()
        payload = reporting.get_summary(repo, target_date)
        return SummaryResponse(**payload)
    except Exception as e:
        logger.exception("Error getting summary")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/stats/daily", response_model=DailyStatsResponse)
def get_daily_stats(limit: int = 30):
    """Get daily statistics for the last N days."""
    try:
        repo = get_repository()
        data = reporting.get_daily_stats(repo, limit)
        return DailyStatsResponse(data=data)
    except Exception as e:
        logger.exception("Error getting daily stats")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/suspicious/clicks", response_model=SuspiciousResponse)
def get_suspicious_clicks(
    target_date: Optional[str] = Query(None, alias="date"),
    limit: int = Query(500, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="IP/UA/媒体名/案件名で検索"),
    include_names: bool = Query(True, description="媒体/案件名を含める")
):
    """Get suspicious click patterns with pagination, search, and optional name resolution"""
    try:
        repo = get_repository()

        target_date = _resolve_target_date(repo, "click_ipua_daily", target_date)
        if not target_date:
            return SuspiciousResponse(date="", data=[], total=0, limit=limit, offset=offset)

        try:
            target_date_obj = date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        rules = resolve_rules(
            click_threshold=None,
            media_threshold=None,
            program_threshold=None,
            burst_click_threshold=None,
            burst_window_seconds=None,
            browser_only=None,
            exclude_datacenter_ip=None,
        )
        detector = SuspiciousDetector(repo, rules)
        findings = detector.find_for_date(target_date_obj)

        details_cache = {}
        if include_names and search:
            details_cache = repo.get_suspicious_click_details_bulk(
                target_date_obj,
                [(f.ipaddress, f.useragent) for f in findings],
            )

        findings = _filter_findings(findings, details_cache, search, include_names)

        total = len(findings)
        
        # ソートしてページネーション適用
        sorted_findings = sorted(findings, key=lambda f: f.total_clicks, reverse=True)
        paginated = sorted_findings[offset:offset + limit]

        if include_names and not details_cache:
            details_cache = repo.get_suspicious_click_details_bulk(
                target_date_obj,
                [(f.ipaddress, f.useragent) for f in paginated],
            )

        data = []
        for f in paginated:
            risk = calculate_risk_level(f.reasons, f.total_clicks, is_conversion=False)
            item = {
                "date": f.date.isoformat(),
                "ipaddress": f.ipaddress,
                "useragent": f.useragent,
                "total_clicks": f.total_clicks,
                "media_count": f.media_count,
                "program_count": f.program_count,
                "first_time": f.first_time.isoformat(),
                "last_time": f.last_time.isoformat(),
                "reasons": f.reasons,
                "reasons_formatted": format_reasons(f.reasons),
                "risk_level": risk["level"],
                "risk_score": risk["score"],
                "risk_label": risk["label"],
            }
            
            if include_names:
                details = details_cache.get((f.ipaddress, f.useragent), [])
                item["details"] = details
                # 主要な媒体・案件名をトップレベルに
                item["media_names"] = list(set(d["media_name"] for d in details))
                item["program_names"] = list(set(d["program_name"] for d in details))
                # アフィリエイター名も追加
                item["affiliate_names"] = list(set(d.get("affiliate_name", "") for d in details if d.get("affiliate_name")))
            
            data.append(item)

        return SuspiciousResponse(
            date=target_date_obj.isoformat(),
            data=data,
            total=total,
            limit=limit,
            offset=offset
        )
    except HTTPException:
        # Propagate explicit client errors (e.g., bad date format)
        raise
    except Exception as e:
        logger.exception("Error getting suspicious clicks")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/suspicious/conversions", response_model=SuspiciousResponse)
def get_suspicious_conversions(
    target_date: Optional[str] = Query(None, alias="date"),
    limit: int = Query(500, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="IP/UA/媒体名/案件名で検索"),
    include_names: bool = Query(True, description="媒体/案件名を含める")
):
    """Get suspicious conversion patterns with pagination, search, and optional name resolution"""
    try:
        repo = get_repository()

        target_date = _resolve_target_date(repo, "conversion_ipua_daily", target_date)
        if not target_date:
            return SuspiciousResponse(date="", data=[], total=0, limit=limit, offset=offset)

        try:
            target_date_obj = date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        rules = resolve_conversion_rules(
            conversion_threshold=None,
            media_threshold=None,
            program_threshold=None,
            burst_conversion_threshold=None,
            burst_window_seconds=None,
            browser_only=None,
            exclude_datacenter_ip=None,
        )
        detector = ConversionSuspiciousDetector(repo, rules)
        findings = detector.find_for_date(target_date_obj)

        details_cache = {}
        if include_names and search:
            details_cache = repo.get_suspicious_conversion_details_bulk(
                target_date_obj,
                [(f.ipaddress, f.useragent) for f in findings],
            )

        findings = _filter_findings(findings, details_cache, search, include_names)

        total = len(findings)

        # ソートしてページネーション適用
        sorted_findings = sorted(
            findings, key=lambda f: f.conversion_count, reverse=True
        )
        paginated = sorted_findings[offset:offset + limit]

        if include_names and not details_cache:
            details_cache = repo.get_suspicious_conversion_details_bulk(
                target_date_obj,
                [(f.ipaddress, f.useragent) for f in paginated],
            )

        data = []
        for f in paginated:
            risk = calculate_risk_level(f.reasons, f.conversion_count, is_conversion=True)
            item = {
                "date": f.date.isoformat(),
                "ipaddress": f.ipaddress,
                "useragent": f.useragent,
                "total_conversions": f.conversion_count,
                "media_count": f.media_count,
                "program_count": f.program_count,
                "first_time": f.first_conversion_time.isoformat(),
                "last_time": f.last_conversion_time.isoformat(),
                "reasons": f.reasons,
                "reasons_formatted": format_reasons(f.reasons),
                "min_click_to_conv_seconds": f.min_click_to_conv_seconds,
                "max_click_to_conv_seconds": f.max_click_to_conv_seconds,
                "risk_level": risk["level"],
                "risk_score": risk["score"],
                "risk_label": risk["label"],
            }
            
            if include_names:
                details = details_cache.get((f.ipaddress, f.useragent), [])
                item["details"] = details
                # 主要な媒体・案件名をトップレベルに
                item["media_names"] = list(set(d["media_name"] for d in details))
                item["program_names"] = list(set(d["program_name"] for d in details))
                # アフィリエイター名も追加
                item["affiliate_names"] = list(set(d.get("affiliate_name", "") for d in details if d.get("affiliate_name")))
            
            data.append(item)

        return SuspiciousResponse(
            date=target_date_obj.isoformat(),
            data=data,
            total=total,
            limit=limit,
            offset=offset
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting suspicious conversions")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/ingest/clicks", response_model=IngestResponse, dependencies=[Depends(require_admin)])
def ingest_clicks(request: IngestRequest, background_tasks: BackgroundTasks):
    """Ingest click logs for a specific date"""
    try:
        target_date = date.fromisoformat(request.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    try:
        enqueue_job(
            background_tasks=background_tasks,
            job_id=f"ingest_clicks_{request.date}",
            start_message=f"Click ingestion started for {request.date}",
            run_fn=lambda: run_click_ingestion(target_date),
        )
    except JobConflictError:
        raise HTTPException(status_code=409, detail="Another job is already running")
    return IngestResponse(
        success=True,
        message=f"Click ingestion started for {request.date}",
        details={"job_id": f"ingest_clicks_{request.date}"}
    )


@app.post(
    "/api/ingest/conversions",
    response_model=IngestResponse,
    dependencies=[Depends(require_admin)],
)
def ingest_conversions(request: IngestRequest, background_tasks: BackgroundTasks):
    """Ingest conversion logs for a specific date"""
    try:
        target_date = date.fromisoformat(request.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    try:
        enqueue_job(
            background_tasks=background_tasks,
            job_id=f"ingest_conversions_{request.date}",
            start_message=f"Conversion ingestion started for {request.date}",
            run_fn=lambda: run_conversion_ingestion(target_date),
        )
    except JobConflictError:
        raise HTTPException(status_code=409, detail="Another job is already running")
    return IngestResponse(
        success=True,
        message=f"Conversion ingestion started for {request.date}",
        details={"job_id": f"ingest_conversions_{request.date}"}
    )


@app.post("/api/refresh", response_model=IngestResponse, dependencies=[Depends(require_admin)])
def refresh_data(request: RefreshRequest, background_tasks: BackgroundTasks):
    """Refresh data for the last N hours"""
    try:
        enqueue_job(
            background_tasks=background_tasks,
            job_id=f"refresh_{request.hours}h",
            start_message=f"Refresh started for last {request.hours} hours",
            run_fn=lambda: run_refresh(request.hours, request.clicks, request.conversions),
        )
    except JobConflictError:
        raise HTTPException(status_code=409, detail="Another job is already running")
    return IngestResponse(
        success=True,
        message=f"Refresh started for last {request.hours} hours",
        details={"hours": request.hours, "clicks": request.clicks, "conversions": request.conversions}
    )


@app.get("/api/job/status", response_model=JobStatusResponse)
def get_job_status():
    """Get the status of the background job"""
    status = get_job_store().get()
    if status.status == "running":
        return JobStatusResponse(
            status="running",
            job_id=status.job_id,
            message=status.message,
            started_at=status.started_at,
        )
    if status.status == "completed":
        return JobStatusResponse(
            status="completed",
            job_id=status.job_id,
            message=status.message,
            started_at=status.started_at,
            completed_at=status.completed_at,
            result=status.result,
        )
    if status.status == "failed":
        message = status.message or "Job failed"
        return JobStatusResponse(
            status="failed",
            job_id=status.job_id,
            message=message,
            started_at=status.started_at,
            completed_at=status.completed_at,
            result=status.result,
        )
    return JobStatusResponse(
        status="idle",
        job_id=None,
        message=status.message or "No job has been run yet",
        started_at=status.started_at,
        completed_at=status.completed_at,
        result=status.result,
    )


@app.get("/api/dates")
def get_available_dates():
    """Get list of available dates in the database."""
    try:
        repo = get_repository()
        return {"dates": reporting.get_available_dates(repo)}
    except Exception as e:
        logger.exception("Error getting dates")
        raise HTTPException(status_code=500, detail="Internal server error")


# ========== マスタ同期API ==========

@app.post("/api/sync/masters", dependencies=[Depends(require_admin)])
def sync_masters(background_tasks: BackgroundTasks):
    """ACSからマスタデータを同期"""
    try:
        enqueue_job(
            background_tasks=background_tasks,
            job_id="sync_masters",
            start_message="Master sync started",
            run_fn=run_master_sync,
        )
    except JobConflictError:
        raise HTTPException(status_code=409, detail="Another job is already running")
    return IngestResponse(
        success=True,
        message="Master sync started",
        details={"job_id": "sync_masters"}
    )


@app.get("/api/masters/status")
def get_masters_status():
    """マスタデータの状態を取得"""
    try:
        repo = get_repository()
        stats = repo.get_all_masters()
        return stats
    except Exception as e:
        logger.exception("Error getting master status")
        raise HTTPException(status_code=500, detail="Internal server error")


# ========== 設定API ==========

@app.get("/api/settings", dependencies=[Depends(require_admin)])
def get_settings():
    """Return current settings (DB overrides env defaults)."""
    repo = get_repository()
    return settings_service.get_settings(repo)


@app.post("/api/settings", dependencies=[Depends(require_admin)])
def update_settings(settings: SettingsModel):
    """Persist settings and update the in-memory cache."""
    settings_dict = settings.model_dump() if hasattr(settings, "model_dump") else settings.dict()
    repo = get_repository()
    return settings_service.update_settings(repo, settings_dict)


# ========== Main ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
