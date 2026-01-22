# Backend (FastAPI + CLI)

Fraud Checker backend ingests ACS click/conversion logs, aggregates IP/UA stats, and exposes both a FastAPI service and a CLI.

## Layout
- `pyproject.toml` – package + dev dependencies.
- `src/fraud_checker/` – application code (API, CLI, ingestion, rules, repository).
- `tests/` – pytest suites.
- `examples/` – sample scripts and flows.
- `Docs/` – design notes.

## 環境変数

`.env` ファイルをリポジトリルートまたは `backend/.env` に作成してください。

### 必須設定

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `FRAUD_DB_PATH` | SQLiteデータベースのパス（絶対パス推奨） | `C:/path/to/fraud_checker.db` |
| `ACS_BASE_URL` | ACS APIのベースURL | `https://acs.example.com/api` |
| `ACS_ACCESS_KEY` | ACSアクセスキー | `your_access_key` |
| `ACS_SECRET_KEY` | ACSシークレットキー | `your_secret_key` |

※ `ACS_ACCESS_KEY`/`ACS_SECRET_KEY` の代わりに `ACS_TOKEN=access:secret` 形式も可

### クリック検知閾値

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `FRAUD_CLICK_THRESHOLD` | 50 | 1日あたりのクリック数上限 |
| `FRAUD_MEDIA_THRESHOLD` | 3 | 重複媒体数上限 |
| `FRAUD_PROGRAM_THRESHOLD` | 3 | 重複案件数上限 |
| `FRAUD_BURST_CLICK_THRESHOLD` | 20 | バースト検知クリック数 |
| `FRAUD_BURST_WINDOW_SECONDS` | 600 | バースト検知時間窓（秒） |

### 成果検知閾値

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `FRAUD_CONVERSION_THRESHOLD` | 5 | 1日あたりの成果数上限 |
| `FRAUD_CONV_MEDIA_THRESHOLD` | 2 | 重複媒体数上限 |
| `FRAUD_CONV_PROGRAM_THRESHOLD` | 2 | 重複案件数上限 |
| `FRAUD_BURST_CONVERSION_THRESHOLD` | 3 | バースト検知成果数 |
| `FRAUD_BURST_CONVERSION_WINDOW_SECONDS` | 1800 | バースト検知時間窓（秒） |
| `FRAUD_MIN_CLICK_TO_CONV_SECONDS` | 5 | クリック→成果の最短経過時間（秒） |
| `FRAUD_MAX_CLICK_TO_CONV_SECONDS` | 2592000 | クリック→成果の最長経過時間（秒、30日） |

### フィルタ設定

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `FRAUD_BROWSER_ONLY` | false | ブラウザ由来のUA/IPのみを検知対象に |
| `FRAUD_EXCLUDE_DATACENTER_IP` | false | データセンターIPを除外 |

### その他

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `FRAUD_PAGE_SIZE` | 500 | API取得時のページサイズ |
| `FRAUD_STORE_RAW` | false | 生データをDBに保存 |
| `ACS_LOG_ENDPOINT` | track_log/search | ACSログ取得エンドポイント |

## Install
```bash
cd backend
python -m pip install -e ".[dev]"
```

## Run API only
```bash
cd backend
python -m uvicorn fraud_checker.api:app --reload --app-dir ./src --port 8001
```
API Docs: http://localhost:8001/docs

### PostgreSQL runtime (optional)
Set `DATABASE_URL` to use PostgreSQL instead of SQLite. When set, the backend will use Postgres repositories automatically.

## CLI examples
```bash
# クリックログ取り込み
python -m fraud_checker.cli ingest --date 2024-01-01

# 不正クリック検知
python -m fraud_checker.cli suspicious --date 2024-01-01

# 成果ログ取り込み
python -m fraud_checker.cli ingest-conversions --date 2024-01-01

# 不正成果検知
python -m fraud_checker.cli suspicious-conversions --date 2024-01-01

# 日次バッチ（クリックのみ）
python -m fraud_checker.cli daily --days-ago 1

# 日次フルバッチ（クリック＋成果）
python -m fraud_checker.cli daily-full --days-ago 1

# リフレッシュ（過去N時間の差分取り込み）
python -m fraud_checker.cli refresh --hours 12 --detect
```

## Tests
```bash
python -m pytest
```

## PostgreSQL (Migration)

### 1) Initialize schema with Alembic
```bash
cd backend
set DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/fraudchecker
alembic upgrade head
```

### 2) Migrate SQLite data into PostgreSQL
```bash
cd backend
python -m fraud_checker.db.migrate_sqlite_to_postgres --sqlite C:/path/to/fraud_checker.db --database-url %DATABASE_URL% --batch-size 2000
```

Tips:
- Add `--skip-raw` to skip raw tables (faster).
- Add `--truncate` to clear destination tables before insert.

## API エンドポイント一覧

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/api/summary` | GET | ダッシュボードサマリー |
| `/api/stats/daily` | GET | 日別統計 |
| `/api/suspicious/clicks` | GET | 不正クリック一覧（検索・ページング対応） |
| `/api/suspicious/conversions` | GET | 不正成果一覧（検索・ページング対応） |
| `/api/dates` | GET | データが存在する日付一覧 |
| `/api/ingest/clicks` | POST | クリックログ取り込み開始 |
| `/api/ingest/conversions` | POST | 成果ログ取り込み開始 |
| `/api/refresh` | POST | リフレッシュ取り込み開始 |
| `/api/sync/masters` | POST | マスタデータ同期開始 |
| `/api/masters/status` | GET | マスタデータ件数 |
| `/api/settings` | GET/POST | 検知閾値の取得・保存 |
| `/api/job/status` | GET | バックグラウンドジョブの状態 |
