"""
FastAPI backend for Fraud Checker v2
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .env import load_env
from .config import (
    resolve_conversion_rules,
    resolve_rules,
)
from .suspicious import (
    CombinedSuspiciousDetector,
    ConversionSuspiciousDetector,
    SuspiciousDetector,
)
from .repository import SQLiteRepository
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Pydantic Models ==========

class SummaryResponse(BaseModel):
    date: str
    stats: dict


class DailyStatsItem(BaseModel):
    date: str
    clicks: int
    conversions: int
    suspicious_clicks: int = 0
    suspicious_conversions: int = 0


class DailyStatsResponse(BaseModel):
    data: list[DailyStatsItem]


class SuspiciousItem(BaseModel):
    date: str
    ipaddress: str
    useragent: str
    total_clicks: Optional[int] = None
    total_conversions: Optional[int] = None
    media_count: int
    program_count: int
    first_time: str
    last_time: str


class SuspiciousResponse(BaseModel):
    date: str
    data: list[dict]
    total: int = 0
    limit: int = 500
    offset: int = 0


class IngestRequest(BaseModel):
    date: str  # YYYY-MM-DD format


class RefreshRequest(BaseModel):
    hours: int = 24
    clicks: bool = True
    conversions: bool = True
    detect: bool = False


class IngestResponse(BaseModel):
    success: bool
    message: str
    details: Optional[dict] = None


class JobStatusResponse(BaseModel):
    status: str
    job_id: Optional[str] = None
    message: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[dict] = None


# ========== Helper Functions ==========


def execute_query(repo: SQLiteRepository, query: str, params: tuple = ()):
    """Execute a query and return results as list of dicts"""
    import sqlite3
    conn = sqlite3.connect(repo.db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(query, params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def execute_query_one(repo: SQLiteRepository, query: str, params: tuple = ()):
    """Execute a query and return single result as dict"""
    import sqlite3
    conn = sqlite3.connect(repo.db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


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
            formatted.append(f"複数媒体アクセス（{threshold}媒体以上）")
        elif reason.startswith("program_count >="):
            threshold = reason.split(">=")[1].strip()
            formatted.append(f"複数案件アクセス（{threshold}案件以上）")
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
    if not db_path:
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
        click_count = execute_query_one(repo, "SELECT COUNT(*) as cnt FROM click_ipua_daily")
        if not click_count or click_count["cnt"] == 0:
            warnings.append({
                "type": "warning",
                "field": "click_data",
                "message": "クリックログデータがありません",
                "hint": "「データ取り込み」からクリックログを取り込んでください"
            })
        
        # マスタデータの有無
        media_count = execute_query_one(repo, "SELECT COUNT(*) as cnt FROM master_media")
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
            "db_path": db_path or "(未設定)",
            "acs_base_url": acs_base_url or "(未設定)",
            "acs_auth": "設定済み" if (acs_token or (acs_access_key and acs_secret_key)) else "(未設定)"
        }
    }


@app.get("/api/summary", response_model=SummaryResponse)
def get_summary(target_date: Optional[str] = None):
    """Get summary statistics for a specific date"""
    try:
        repo = get_repository()

        # 最新の日付を取得
        if not target_date:
            row = execute_query_one(repo, "SELECT MAX(date) as last_date FROM click_ipua_daily")
            target_date = row["last_date"] if row and row["last_date"] else None
            
            conv_row = execute_query_one(repo, "SELECT MAX(date) as last_date FROM conversion_ipua_daily")
            if conv_row and conv_row["last_date"]:
                if not target_date or conv_row["last_date"] > target_date:
                    target_date = conv_row["last_date"]
        
        if not target_date:
            target_date = (date.today() - timedelta(days=1)).isoformat()
        
        # クリック統計
        click_row = execute_query_one(repo, """
            SELECT 
                COALESCE(SUM(click_count), 0) as total_clicks,
                COUNT(DISTINCT ipaddress) as unique_ips,
                COUNT(DISTINCT media_id) as active_media
            FROM click_ipua_daily 
            WHERE date = ?
        """, (target_date,))
        
        # 成果統計
        conv_row = execute_query_one(repo, """
            SELECT 
                COALESCE(SUM(conversion_count), 0) as total_conversions,
                COUNT(DISTINCT ipaddress) as conversion_ips
            FROM conversion_ipua_daily 
            WHERE date = ?
        """, (target_date,))
        
        # 前日のデータ
        prev_date = (datetime.fromisoformat(target_date) - timedelta(days=1)).strftime("%Y-%m-%d")
        
        prev_click = execute_query_one(repo,
            "SELECT COALESCE(SUM(click_count), 0) as total FROM click_ipua_daily WHERE date = ?",
            (prev_date,)
        )
        
        prev_conv = execute_query_one(repo,
            "SELECT COALESCE(SUM(conversion_count), 0) as total FROM conversion_ipua_daily WHERE date = ?",
            (prev_date,)
        )
        
        # 不正疑惑カウント（閾値: click >= 50, conversion >= 5）
        susp_clicks = execute_query_one(repo, """
            SELECT COUNT(*) as count FROM (
                SELECT ipaddress, useragent
                FROM click_ipua_daily
                WHERE date = ?
                GROUP BY ipaddress, useragent
                HAVING SUM(click_count) >= 50
            )
        """, (target_date,))
        
        susp_convs = execute_query_one(repo, """
            SELECT COUNT(*) as count FROM (
                SELECT ipaddress, useragent
                FROM conversion_ipua_daily
                WHERE date = ?
                GROUP BY ipaddress, useragent
                HAVING SUM(conversion_count) >= 5
            )
        """, (target_date,))
        
        return SummaryResponse(
            date=target_date,
            stats={
                "clicks": {
                    "total": click_row["total_clicks"] if click_row else 0,
                    "unique_ips": click_row["unique_ips"] if click_row else 0,
                    "media_count": click_row["active_media"] if click_row else 0,
                    "prev_total": prev_click["total"] if prev_click else 0,
                },
                "conversions": {
                    "total": conv_row["total_conversions"] if conv_row else 0,
                    "unique_ips": conv_row["conversion_ips"] if conv_row else 0,
                    "prev_total": prev_conv["total"] if prev_conv else 0,
                },
                "suspicious": {
                    "click_based": susp_clicks["count"] if susp_clicks else 0,
                    "conversion_based": susp_convs["count"] if susp_convs else 0,
                }
            }
        )
    except Exception as e:
        logger.exception("Error getting summary")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats/daily", response_model=DailyStatsResponse)
def get_daily_stats(limit: int = 30):
    """Get daily statistics for the last N days"""
    try:
        repo = get_repository()
        
        click_rows = execute_query(repo, """
            SELECT date, SUM(click_count) as clicks
            FROM click_ipua_daily
            GROUP BY date
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))
        
        conv_rows = execute_query(repo, """
            SELECT date, SUM(conversion_count) as conversions
            FROM conversion_ipua_daily
            GROUP BY date
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))
        
        # 不正疑惑クリック（閾値: >= 50）
        susp_click_rows = execute_query(repo, """
            SELECT date, COUNT(*) as suspicious_count
            FROM (
                SELECT date, ipaddress, useragent
                FROM click_ipua_daily
                GROUP BY date, ipaddress, useragent
                HAVING SUM(click_count) >= 50
            )
            GROUP BY date
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))
        
        # 不正疑惑成果（閾値: >= 5）
        susp_conv_rows = execute_query(repo, """
            SELECT date, COUNT(*) as suspicious_count
            FROM (
                SELECT date, ipaddress, useragent
                FROM conversion_ipua_daily
                GROUP BY date, ipaddress, useragent
                HAVING SUM(conversion_count) >= 5
            )
            GROUP BY date
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))
        
        # マージ
        merged = {}
        for row in click_rows:
            merged[row["date"]] = {
                "date": row["date"], 
                "clicks": row["clicks"], 
                "conversions": 0,
                "suspicious_clicks": 0,
                "suspicious_conversions": 0
            }
        for row in conv_rows:
            if row["date"] in merged:
                merged[row["date"]]["conversions"] = row["conversions"]
            else:
                merged[row["date"]] = {
                    "date": row["date"], 
                    "clicks": 0, 
                    "conversions": row["conversions"],
                    "suspicious_clicks": 0,
                    "suspicious_conversions": 0
                }
        for row in susp_click_rows:
            if row["date"] in merged:
                merged[row["date"]]["suspicious_clicks"] = row["suspicious_count"]
        for row in susp_conv_rows:
            if row["date"] in merged:
                merged[row["date"]]["suspicious_conversions"] = row["suspicious_count"]
        
        data = sorted(merged.values(), key=lambda x: x["date"])
        return DailyStatsResponse(data=data)
    except Exception as e:
        logger.exception("Error getting daily stats")
        raise HTTPException(status_code=500, detail=str(e))


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

        if not target_date:
            row = execute_query_one(repo, "SELECT MAX(date) as last_date FROM click_ipua_daily")
            target_date = row["last_date"] if row and row["last_date"] else None

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

        # 名前解決用のデータを取得（検索前に全件取得）
        details_cache = {}
        if include_names:
            for f in findings:
                key = (f.ipaddress, f.useragent)
                if key not in details_cache:
                    details_cache[key] = repo.get_suspicious_click_details(
                        target_date_obj, f.ipaddress, f.useragent
                    )

        # 検索フィルタ適用
        if search:
            search_lower = search.lower()
            filtered_findings = []
            for f in findings:
                # IP/UAで検索
                if search_lower in f.ipaddress.lower() or search_lower in f.useragent.lower():
                    filtered_findings.append(f)
                    continue
                # 媒体名/案件名で検索
                if include_names:
                    details = details_cache.get((f.ipaddress, f.useragent), [])
                    media_names = [d["media_name"].lower() for d in details]
                    program_names = [d["program_name"].lower() for d in details]
                    if any(search_lower in name for name in media_names + program_names):
                        filtered_findings.append(f)
            findings = filtered_findings

        # 総件数（検索後）
        total = len(findings)
        
        # ソートしてページネーション適用
        sorted_findings = sorted(findings, key=lambda f: f.total_clicks, reverse=True)
        paginated = sorted_findings[offset:offset + limit]

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
        raise HTTPException(status_code=500, detail=str(e))


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

        if not target_date:
            row = execute_query_one(repo, "SELECT MAX(date) as last_date FROM conversion_ipua_daily")
            target_date = row["last_date"] if row and row["last_date"] else None

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

        # 名前解決用のデータを取得（検索前に全件取得）
        details_cache = {}
        if include_names:
            for f in findings:
                key = (f.ipaddress, f.useragent)
                if key not in details_cache:
                    details_cache[key] = repo.get_suspicious_conversion_details(
                        target_date_obj, f.ipaddress, f.useragent
                    )

        # 検索フィルタ適用
        if search:
            search_lower = search.lower()
            filtered_findings = []
            for f in findings:
                # IP/UAで検索
                if search_lower in f.ipaddress.lower() or search_lower in f.useragent.lower():
                    filtered_findings.append(f)
                    continue
                # 媒体名/案件名で検索
                if include_names:
                    details = details_cache.get((f.ipaddress, f.useragent), [])
                    media_names = [d["media_name"].lower() for d in details]
                    program_names = [d["program_name"].lower() for d in details]
                    if any(search_lower in name for name in media_names + program_names):
                        filtered_findings.append(f)
            findings = filtered_findings

        # 総件数（検索後）
        total = len(findings)

        # ソートしてページネーション適用
        sorted_findings = sorted(
            findings, key=lambda f: f.conversion_count, reverse=True
        )
        paginated = sorted_findings[offset:offset + limit]

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
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest/clicks", response_model=IngestResponse)
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


@app.post("/api/ingest/conversions", response_model=IngestResponse)
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


@app.post("/api/refresh", response_model=IngestResponse)
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
    """Get list of available dates in the database"""
    try:
        repo = get_repository()
        
        click_dates = execute_query(repo,
            "SELECT DISTINCT date FROM click_ipua_daily ORDER BY date DESC"
        )
        
        conv_dates = execute_query(repo,
            "SELECT DISTINCT date FROM conversion_ipua_daily ORDER BY date DESC"
        )
        
        all_dates = set(row["date"] for row in click_dates) | set(row["date"] for row in conv_dates)
        
        return {"dates": sorted(all_dates, reverse=True)}
    except Exception as e:
        logger.exception("Error getting dates")
        raise HTTPException(status_code=500, detail=str(e))


# ========== マスタ同期API ==========

@app.post("/api/sync/masters")
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
        raise HTTPException(status_code=500, detail=str(e))


# ========== 設定API ==========

class SettingsModel(BaseModel):
    click_threshold: int = 50
    media_threshold: int = 3
    program_threshold: int = 3
    burst_click_threshold: int = 20
    burst_window_seconds: int = 600
    conversion_threshold: int = 5
    conv_media_threshold: int = 2
    conv_program_threshold: int = 2
    burst_conversion_threshold: int = 3
    burst_conversion_window_seconds: int = 1800
    min_click_to_conv_seconds: int = 5
    max_click_to_conv_seconds: int = 2592000
    browser_only: bool = False
    exclude_datacenter_ip: bool = False


# 設定をメモリにキャッシュ（DBからの読み込み結果を保持）
_settings_cache: dict = {}


def _load_settings_from_env() -> dict:
    """環境変数からデフォルト設定を読み込む"""
    from .config import (
        DEFAULT_CLICK_THRESHOLD,
        DEFAULT_MEDIA_THRESHOLD,
        DEFAULT_PROGRAM_THRESHOLD,
        DEFAULT_BURST_CLICK_THRESHOLD,
        DEFAULT_BURST_WINDOW_SECONDS,
        DEFAULT_CONVERSION_THRESHOLD,
        DEFAULT_CONV_MEDIA_THRESHOLD,
        DEFAULT_CONV_PROGRAM_THRESHOLD,
        DEFAULT_BURST_CONVERSION_THRESHOLD,
        DEFAULT_BURST_CONVERSION_WINDOW_SECONDS,
        DEFAULT_MIN_CLICK_TO_CONV_SECONDS,
        DEFAULT_MAX_CLICK_TO_CONV_SECONDS,
        DEFAULT_BROWSER_ONLY,
        DEFAULT_EXCLUDE_DATACENTER_IP,
        _env_int,
        _env_bool,
    )
    return {
        "click_threshold": _env_int("FRAUD_CLICK_THRESHOLD", DEFAULT_CLICK_THRESHOLD),
        "media_threshold": _env_int("FRAUD_MEDIA_THRESHOLD", DEFAULT_MEDIA_THRESHOLD),
        "program_threshold": _env_int("FRAUD_PROGRAM_THRESHOLD", DEFAULT_PROGRAM_THRESHOLD),
        "burst_click_threshold": _env_int("FRAUD_BURST_CLICK_THRESHOLD", DEFAULT_BURST_CLICK_THRESHOLD),
        "burst_window_seconds": _env_int("FRAUD_BURST_WINDOW_SECONDS", DEFAULT_BURST_WINDOW_SECONDS),
        "conversion_threshold": _env_int("FRAUD_CONVERSION_THRESHOLD", DEFAULT_CONVERSION_THRESHOLD),
        "conv_media_threshold": _env_int("FRAUD_CONV_MEDIA_THRESHOLD", DEFAULT_CONV_MEDIA_THRESHOLD),
        "conv_program_threshold": _env_int("FRAUD_CONV_PROGRAM_THRESHOLD", DEFAULT_CONV_PROGRAM_THRESHOLD),
        "burst_conversion_threshold": _env_int("FRAUD_BURST_CONVERSION_THRESHOLD", DEFAULT_BURST_CONVERSION_THRESHOLD),
        "burst_conversion_window_seconds": _env_int("FRAUD_BURST_CONVERSION_WINDOW_SECONDS", DEFAULT_BURST_CONVERSION_WINDOW_SECONDS),
        "min_click_to_conv_seconds": _env_int("FRAUD_MIN_CLICK_TO_CONV_SECONDS", DEFAULT_MIN_CLICK_TO_CONV_SECONDS),
        "max_click_to_conv_seconds": _env_int("FRAUD_MAX_CLICK_TO_CONV_SECONDS", DEFAULT_MAX_CLICK_TO_CONV_SECONDS),
        "browser_only": _env_bool("FRAUD_BROWSER_ONLY", DEFAULT_BROWSER_ONLY),
        "exclude_datacenter_ip": _env_bool("FRAUD_EXCLUDE_DATACENTER_IP", DEFAULT_EXCLUDE_DATACENTER_IP),
    }


def _load_settings() -> dict:
    """DBから設定を読み込み、なければ環境変数のデフォルトを使用"""
    try:
        repo = get_repository()
        db_settings = repo.load_settings()
        if db_settings:
            # DBの設定を環境変数デフォルトとマージ（新しいキーがあれば追加）
            env_defaults = _load_settings_from_env()
            merged = {**env_defaults, **db_settings}
            return merged
    except Exception as e:
        logger.warning(f"Failed to load settings from DB: {e}")
    return _load_settings_from_env()


@app.get("/api/settings")
def get_settings():
    """現在の設定を取得（DB優先、なければ環境変数デフォルト）"""
    global _settings_cache
    if not _settings_cache:
        _settings_cache = _load_settings()
    return _settings_cache


@app.post("/api/settings")
def update_settings(settings: SettingsModel):
    """設定を更新（DBに永続化）"""
    global _settings_cache
    # Pydantic v2ではmodel_dump、v1互換環境ではdictを使う
    settings_dict = settings.model_dump() if hasattr(settings, "model_dump") else settings.dict()
    
    try:
        repo = get_repository()
        repo.save_settings(settings_dict)
        _settings_cache = settings_dict
        logger.info(f"Settings saved to DB: {_settings_cache}")
        return {"success": True, "settings": _settings_cache, "persisted": True}
    except Exception as e:
        logger.exception("Failed to save settings to DB")
        # DBに保存できなくてもメモリには反映
        _settings_cache = settings_dict
        return {"success": True, "settings": _settings_cache, "persisted": False, "warning": str(e)}


# ========== Main ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
