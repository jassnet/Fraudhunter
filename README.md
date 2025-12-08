# Fraud Checker v2

FastAPI + Next.js stack for click/conversion ingestion and fraud detection.

## Project Structure
- `backend/` – Python package (`fraud_checker`), CLI, tests, examples, docs.
- `frontend/` – Next.js dashboard UI.
- `dev.py` / `start.sh` / `start.bat` – one-command dev runner.
- `.env` – shared environment (read from repo root or `backend/.env`).

## Quick Start

### 1. Backend Setup
```bash
cd backend
python -m pip install -e ".[dev]"
```

### 2. Frontend Setup
```bash
cd frontend
npm install
```

### 3. Environment Configuration

Create `.env` file at the repo root:

```env
# === 必須設定 ===
# SQLiteデータベースのパス（絶対パス推奨）
FRAUD_DB_PATH=C:/path/to/fraud_checker.db

# ACS API設定
ACS_BASE_URL=https://your-acs-domain.com/api
ACS_ACCESS_KEY=your_access_key
ACS_SECRET_KEY=your_secret_key
# または ACS_TOKEN=access_key:secret_key 形式でも可

# === オプション設定 ===
# ページサイズ（デフォルト: 500, ACS APIの上限）
# FRAUD_PAGE_SIZE=500

# 生データ保存（デフォルト: false）
# FRAUD_STORE_RAW=true

# クリック検知閾値
# FRAUD_CLICK_THRESHOLD=50        # 1日のクリック数上限
# FRAUD_MEDIA_THRESHOLD=3         # 重複媒体数上限
# FRAUD_PROGRAM_THRESHOLD=3       # 重複案件数上限
# FRAUD_BURST_CLICK_THRESHOLD=20  # バースト検知クリック数
# FRAUD_BURST_WINDOW_SECONDS=600  # バースト検知時間窓（秒）

# 成果検知閾値
# FRAUD_CONVERSION_THRESHOLD=5            # 1日の成果数上限
# FRAUD_CONV_MEDIA_THRESHOLD=2            # 重複媒体数上限
# FRAUD_CONV_PROGRAM_THRESHOLD=2          # 重複案件数上限
# FRAUD_BURST_CONVERSION_THRESHOLD=3      # バースト検知成果数
# FRAUD_BURST_CONVERSION_WINDOW_SECONDS=1800  # バースト検知時間窓（秒）

# フィルタ設定
# FRAUD_BROWSER_ONLY=false           # ブラウザのみ検知
# FRAUD_EXCLUDE_DATACENTER_IP=false  # データセンターIP除外

# ACS APIエンドポイント（通常変更不要）
# ACS_LOG_ENDPOINT=track_log/search
```

### 4. Run (backend + frontend)
```bash
python dev.py
```

- Backend: http://localhost:8000 (API docs at /docs)
- Frontend: http://localhost:3000

## Operation Guide

### 日次運用フロー

1. **データ取り込み**
   - ダッシュボードの「データ取込」ボタンをクリック
   - 「リフレッシュ」タブで過去N時間分を取り込み（推奨: 24時間）
   - または「日付指定」タブで特定日を指定して取り込み

2. **マスタ同期**（初回または定期的に）
   - 設定ページ > マスタデータ > 「ACSから同期」ボタン
   - 媒体名・案件名・アフィリエイター名の表示に必要

3. **不正検知確認**
   - サイドメニュー > 不正クリック検知 / 不正成果検知
   - 日付を選択して検知結果を確認
   - 詳細ボタンで関連媒体・案件を確認
   - 必要に応じてCSV出力

4. **閾値調整**
   - 設定ページで検知閾値を調整
   - 変更は「変更を保存」で即時反映

### CLI操作（バッチ処理向け）

```bash
cd backend

# クリックログ取り込み
python -m fraud_checker.cli ingest --date 2024-01-01

# 成果ログ取り込み
python -m fraud_checker.cli ingest-conversions --date 2024-01-01

# 不正クリック検知
python -m fraud_checker.cli suspicious --date 2024-01-01

# 不正成果検知
python -m fraud_checker.cli suspicious-conversions --date 2024-01-01

# 日次バッチ（昨日のデータ取り込み＋検知）
python -m fraud_checker.cli daily --days-ago 1

# フルバッチ（クリック＋成果の取り込みと検知）
python -m fraud_checker.cli daily-full --days-ago 1

# リフレッシュ（過去N時間の差分取り込み）
python -m fraud_checker.cli refresh --hours 12 --detect
```

## Troubleshooting

### 接続エラー

**症状**: ダッシュボードに「接続エラー」が表示される

**解決方法**:
1. バックエンドが起動しているか確認
   ```bash
   python dev.py
   ```
2. `.env` ファイルが正しく設定されているか確認
3. ポート 8000 が使用可能か確認

### ジョブ競合エラー（409）

**症状**: 「Another job is already running」エラー

**解決方法**:
1. 現在実行中のジョブが完了するまで待機（通常数分）
2. バックエンドを再起動してジョブ状態をリセット
3. 大量データの場合は日付を分割して取り込み

### データが表示されない

**症状**: 不正検知一覧にデータが表示されない

**解決方法**:
1. データ取り込みが完了しているか確認
2. 日付選択で正しい日付が選ばれているか確認
3. 閾値設定が厳しすぎないか確認（設定ページで調整）

### マスタ名が表示されない

**症状**: 媒体名・案件名がIDのまま表示される

**解決方法**:
1. 設定ページ > マスタデータ > 「ACSから同期」を実行
2. 同期完了後、ページを再読み込み

## API Reference

主要エンドポイント:

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/api/summary` | GET | ダッシュボードサマリー |
| `/api/suspicious/clicks` | GET | 不正クリック一覧 |
| `/api/suspicious/conversions` | GET | 不正成果一覧 |
| `/api/ingest/clicks` | POST | クリックログ取り込み |
| `/api/ingest/conversions` | POST | 成果ログ取り込み |
| `/api/refresh` | POST | リフレッシュ取り込み |
| `/api/sync/masters` | POST | マスタ同期 |
| `/api/settings` | GET/POST | 設定取得/保存 |
| `/api/job/status` | GET | ジョブ状態確認 |

詳細は http://localhost:8000/docs を参照。

## Tests
```bash
cd backend
python -m pytest
```

## License

Proprietary - Internal Use Only

---

More backend details live in `backend/README.md`.
