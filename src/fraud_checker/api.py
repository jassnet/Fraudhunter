"""
FastAPI backend for Fraud Checker v2
"""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .acs_client import AcsHttpClient
from .config import (
    resolve_acs_settings,
    resolve_conversion_rules,
    resolve_db_path,
    resolve_rules,
    resolve_store_raw,
)
from .ingestion import ClickLogIngestor, ConversionIngestor
from .repository import SQLiteRepository
from .suspicious import (
    CombinedSuspiciousDetector,
    ConversionSuspiciousDetector,
    SuspiciousDetector,
)

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fraud Checker API",
    description="不正検知システム API",
    version="2.0.0",
)

# CORS設定（フロントエンドからのアクセス許可）
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


# ========== Global State ==========

# バックグラウンドジョブの状態管理
job_status: dict = {
    "running": False,
    "last_job": None,
    "last_result": None,
}


# ========== Helper Functions ==========

def get_repository() -> SQLiteRepository:
    """Get SQLite repository instance"""
    db_path = resolve_db_path(None)
    repo = SQLiteRepository(db_path)
    repo.ensure_schema(store_raw=True)
    repo.ensure_conversion_schema()
    return repo


def get_acs_client():
    """Get ACS HTTP client"""
    settings = resolve_acs_settings()
    return AcsHttpClient(
        base_url=settings.base_url,
        access_key=settings.access_key,
        secret_key=settings.secret_key,
        endpoint_path=settings.log_endpoint,
    )


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


# ========== API Endpoints ==========

@app.get("/")
def root():
    return {"message": "Fraud Checker API v2.0", "status": "running"}


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
        
        # マージ
        merged = {}
        for row in click_rows:
            merged[row["date"]] = {"date": row["date"], "clicks": row["clicks"], "conversions": 0}
        for row in conv_rows:
            if row["date"] in merged:
                merged[row["date"]]["conversions"] = row["conversions"]
            else:
                merged[row["date"]] = {"date": row["date"], "clicks": 0, "conversions": row["conversions"]}
        
        data = sorted(merged.values(), key=lambda x: x["date"])
        return DailyStatsResponse(data=data)
    except Exception as e:
        logger.exception("Error getting daily stats")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/suspicious/clicks", response_model=SuspiciousResponse)
def get_suspicious_clicks(
    target_date: Optional[str] = Query(None, alias="date"),
    limit: int = 100
):
    """Get suspicious click patterns"""
    try:
        repo = get_repository()
        
        if not target_date:
            row = execute_query_one(repo, "SELECT MAX(date) as last_date FROM click_ipua_daily")
            target_date = row["last_date"] if row and row["last_date"] else None
        
        if not target_date:
            return SuspiciousResponse(date="", data=[])
        
        rows = execute_query(repo, """
            SELECT
                date,
                ipaddress,
                useragent,
                SUM(click_count) AS total_clicks,
                COUNT(DISTINCT media_id) AS media_count,
                COUNT(DISTINCT program_id) AS program_count,
                MIN(first_time) AS first_time,
                MAX(last_time) AS last_time
            FROM click_ipua_daily
            WHERE date = ?
            GROUP BY date, ipaddress, useragent
            HAVING
                SUM(click_count) >= 50
                OR COUNT(DISTINCT media_id) >= 3
                OR COUNT(DISTINCT program_id) >= 3
            ORDER BY total_clicks DESC
            LIMIT ?
        """, (target_date, limit))
        
        return SuspiciousResponse(date=target_date, data=rows)
    except Exception as e:
        logger.exception("Error getting suspicious clicks")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/suspicious/conversions", response_model=SuspiciousResponse)
def get_suspicious_conversions(
    target_date: Optional[str] = Query(None, alias="date"),
    limit: int = 100
):
    """Get suspicious conversion patterns"""
    try:
        repo = get_repository()
        
        if not target_date:
            row = execute_query_one(repo, "SELECT MAX(date) as last_date FROM conversion_ipua_daily")
            target_date = row["last_date"] if row and row["last_date"] else None
        
        if not target_date:
            return SuspiciousResponse(date="", data=[])
        
        rows = execute_query(repo, """
            SELECT
                date,
                ipaddress,
                useragent,
                SUM(conversion_count) AS total_conversions,
                COUNT(DISTINCT media_id) AS media_count,
                COUNT(DISTINCT program_id) AS program_count,
                MIN(first_time) AS first_time,
                MAX(last_time) AS last_time
            FROM conversion_ipua_daily
            WHERE date = ?
            GROUP BY date, ipaddress, useragent
            HAVING
                SUM(conversion_count) >= 5
                OR COUNT(DISTINCT media_id) >= 2
                OR COUNT(DISTINCT program_id) >= 2
            ORDER BY total_conversions DESC
            LIMIT ?
        """, (target_date, limit))
        
        return SuspiciousResponse(date=target_date, data=rows)
    except Exception as e:
        logger.exception("Error getting suspicious conversions")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest/clicks", response_model=IngestResponse)
def ingest_clicks(request: IngestRequest, background_tasks: BackgroundTasks):
    """Ingest click logs for a specific date"""
    global job_status
    
    if job_status["running"]:
        raise HTTPException(status_code=409, detail="Another job is already running")
    
    try:
        target_date = date.fromisoformat(request.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    def run_ingest():
        global job_status
        job_status["running"] = True
        job_status["last_job"] = f"ingest_clicks_{request.date}"
        try:
            repo = get_repository()
            client = get_acs_client()
            settings = resolve_acs_settings()
            
            ingestor = ClickLogIngestor(
                client=client,
                repository=repo,
                page_size=settings.page_size,
                store_raw=True,
            )
            count = ingestor.run_for_date(target_date)
            job_status["last_result"] = {"success": True, "count": count}
            logger.info(f"Ingested {count} clicks for {target_date}")
        except Exception as e:
            logger.exception("Error during click ingestion")
            job_status["last_result"] = {"success": False, "error": str(e)}
        finally:
            job_status["running"] = False
    
    background_tasks.add_task(run_ingest)
    return IngestResponse(
        success=True,
        message=f"Click ingestion started for {request.date}",
        details={"job_id": f"ingest_clicks_{request.date}"}
    )


@app.post("/api/ingest/conversions", response_model=IngestResponse)
def ingest_conversions(request: IngestRequest, background_tasks: BackgroundTasks):
    """Ingest conversion logs for a specific date"""
    global job_status
    
    if job_status["running"]:
        raise HTTPException(status_code=409, detail="Another job is already running")
    
    try:
        target_date = date.fromisoformat(request.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    def run_ingest():
        global job_status
        job_status["running"] = True
        job_status["last_job"] = f"ingest_conversions_{request.date}"
        try:
            repo = get_repository()
            client = get_acs_client()
            settings = resolve_acs_settings()
            
            ingestor = ConversionIngestor(
                client=client,
                repository=repo,
                page_size=settings.page_size,
            )
            total, enriched = ingestor.run_for_date(target_date)
            job_status["last_result"] = {"success": True, "total": total, "enriched": enriched}
            logger.info(f"Ingested {total} conversions ({enriched} with entry IP/UA) for {target_date}")
        except Exception as e:
            logger.exception("Error during conversion ingestion")
            job_status["last_result"] = {"success": False, "error": str(e)}
        finally:
            job_status["running"] = False
    
    background_tasks.add_task(run_ingest)
    return IngestResponse(
        success=True,
        message=f"Conversion ingestion started for {request.date}",
        details={"job_id": f"ingest_conversions_{request.date}"}
    )


@app.post("/api/refresh", response_model=IngestResponse)
def refresh_data(request: RefreshRequest, background_tasks: BackgroundTasks):
    """Refresh data for the last N hours"""
    global job_status
    
    if job_status["running"]:
        raise HTTPException(status_code=409, detail="Another job is already running")
    
    def run_refresh():
        global job_status
        job_status["running"] = True
        job_status["last_job"] = f"refresh_{request.hours}h"
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=request.hours)
            
            repo = get_repository()
            client = get_acs_client()
            settings = resolve_acs_settings()
            
            result = {"clicks": None, "conversions": None}
            
            if request.clicks:
                click_ingestor = ClickLogIngestor(
                    client=client,
                    repository=repo,
                    page_size=settings.page_size,
                    store_raw=True,
                )
                click_new, click_skip = click_ingestor.run_for_time_range(start_time, end_time)
                result["clicks"] = {"new": click_new, "skipped": click_skip}
                logger.info(f"Refreshed clicks: {click_new} new, {click_skip} skipped")
            
            if request.conversions:
                conv_ingestor = ConversionIngestor(
                    client=client,
                    repository=repo,
                    page_size=settings.page_size,
                )
                conv_new, conv_skip, conv_valid = conv_ingestor.run_for_time_range(start_time, end_time)
                result["conversions"] = {"new": conv_new, "skipped": conv_skip, "valid_entry": conv_valid}
                logger.info(f"Refreshed conversions: {conv_new} new, {conv_skip} skipped")
            
            job_status["last_result"] = {"success": True, **result}
        except Exception as e:
            logger.exception("Error during refresh")
            job_status["last_result"] = {"success": False, "error": str(e)}
        finally:
            job_status["running"] = False
    
    background_tasks.add_task(run_refresh)
    return IngestResponse(
        success=True,
        message=f"Refresh started for last {request.hours} hours",
        details={"hours": request.hours, "clicks": request.clicks, "conversions": request.conversions}
    )


@app.get("/api/job/status", response_model=JobStatusResponse)
def get_job_status():
    """Get the status of the background job"""
    if job_status["running"]:
        return JobStatusResponse(
            status="running",
            job_id=job_status["last_job"],
            message="Job is currently running"
        )
    elif job_status["last_result"]:
        result = job_status["last_result"]
        if result.get("success"):
            return JobStatusResponse(
                status="completed",
                job_id=job_status["last_job"],
                message=f"Job completed successfully: {result}"
            )
        else:
            return JobStatusResponse(
                status="failed",
                job_id=job_status["last_job"],
                message=f"Job failed: {result.get('error', 'Unknown error')}"
            )
    else:
        return JobStatusResponse(
            status="idle",
            job_id=None,
            message="No job has been run yet"
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


# ========== Main ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
