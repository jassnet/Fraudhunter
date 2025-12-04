# fraud_checker

ACS click logs & conversion logs → SQLite aggregation → suspicious IP/UA detection.

成果ログには `entry_ipaddress` / `entry_useragent`（実ユーザーのIP/UA）が含まれており、これを直接使用してフラウド検知を行います。ポストバック経由の成果でも、実ユーザーのIP/UAで検知が可能です。

The codebase is structured as a src layout package (`src/fraud_checker`). Install in editable mode and run everything as a module (`python -m fraud_checker.cli ...`).

## Setup

```
python -m pip install -e ".[dev]"
```

Place a `.env` file in the project root (same level as `pyproject.toml`). Required variables:

- `ACS_BASE_URL` (full URL such as `https://acs.example.com/api`)
- `ACS_ACCESS_KEY`
- `ACS_SECRET_KEY`
- or `ACS_TOKEN` (`access_key:secret_key` combined)
- `FRAUD_DB_PATH` (SQLite path, absolute path recommended)

Optional overrides:

### クリックログ用
- `FRAUD_PAGE_SIZE` (default 500; ACS limit)
- `FRAUD_STORE_RAW` (`true`/`false`) - クリックログの生データ保存（将来のクリックベース拡張用）
- `FRAUD_CLICK_THRESHOLD` (default 50)
- `FRAUD_MEDIA_THRESHOLD` (default 3)
- `FRAUD_PROGRAM_THRESHOLD` (default 3)
- `FRAUD_BURST_CLICK_THRESHOLD` (default 20)
- `FRAUD_BURST_WINDOW_SECONDS` (default 600)
- `ACS_LOG_ENDPOINT` (default `track_log/search`)

### 成果ログ用
- `FRAUD_CONVERSION_THRESHOLD` (default 5) - 同一IP/UAからの成果数閾値
- `FRAUD_CONV_MEDIA_THRESHOLD` (default 2) - 複数媒体閾値
- `FRAUD_CONV_PROGRAM_THRESHOLD` (default 2) - 複数案件閾値
- `FRAUD_BURST_CONVERSION_THRESHOLD` (default 3) - バースト成果数
- `FRAUD_BURST_CONVERSION_WINDOW_SECONDS` (default 1800) - バースト時間窓（30分）

### 共通
- `FRAUD_BROWSER_ONLY` (`true`/`false`) - ブラウザ由来のUA/IPのみ
- `FRAUD_EXCLUDE_DATACENTER_IP` (`true`/`false`) - データセンターIP除外

The CLI loads `.env` automatically on startup.

---

## CLI commands

Always run as a module:

### クリックログ取り込み

```bash
python -m fraud_checker.cli ingest --date 2024-01-01 \
  --base-url https://acs.example.com/api \
  --access-key YOUR_KEY --secret-key YOUR_SECRET \
  --endpoint track_log/search \
  --db /var/lib/fraud/fraud_checker.db \
  --page-size 500
```

### クリックベースの不正検知

```bash
python -m fraud_checker.cli suspicious --date 2024-01-01 \
  --db /var/lib/fraud/fraud_checker.db \
  --click-threshold 50 \
  --media-threshold 3 \
  --program-threshold 3 \
  --burst-click-threshold 20 \
  --burst-window-seconds 600
```

### 成果ログ取り込み

```bash
python -m fraud_checker.cli ingest-conversions --date 2024-01-01 \
  --db /var/lib/fraud/fraud_checker.db \
  --base-url https://acs.example.com/api \
  --access-key YOUR_KEY --secret-key YOUR_SECRET
```

成果ログには `entry_ipaddress` / `entry_useragent`（実ユーザーのIP/UA）が含まれており、これを直接使用して集計します。クリックログとの突合は不要です。

### 成果ベースの不正検知

```bash
python -m fraud_checker.cli suspicious-conversions --date 2024-01-01 \
  --db /var/lib/fraud/fraud_checker.db \
  --conversion-threshold 5 \
  --media-threshold 2 \
  --program-threshold 2
```

### デイリーバッチ（クリックのみ）

```bash
python -m fraud_checker.cli daily \
  --days-ago 1 \
  --db /var/lib/fraud/fraud_checker.db \
  --base-url https://acs.example.com/api \
  --access-key YOUR_KEY --secret-key YOUR_SECRET
```

### デイリーバッチ（クリック＋成果の統合検知）

```bash
python -m fraud_checker.cli daily-full \
  --days-ago 1 \
  --db /var/lib/fraud/fraud_checker.db \
  --base-url https://acs.example.com/api \
  --access-key YOUR_KEY --secret-key YOUR_SECRET
```

`daily-full` は以下を一括実行します：
1. クリックログ取り込み
2. 成果ログ取り込み（entry IP/UAを使用）
3. クリックベースの不正検知
4. 成果ベースの不正検知
5. 両方で検出された高リスクIP/UAの特定

---

## 成果ログのIP/UA取得方式

```
[成果ログ（action_log_raw）]
         |
         | entry_ipaddress / entry_useragent
         | （実ユーザーのIP/UA）
         ↓
    成果ベースのフラウド検知
```

成果ログには以下の2種類のIP/UAが含まれています：

| フィールド | 説明 | 用途 |
|-----------|------|------|
| `ipaddress` / `useragent` | ポストバックサーバーのIP/UA | 参考情報 |
| `entry_ipaddress` / `entry_useragent` | **実ユーザーのIP/UA** | **フラウド検知に使用** |

ポストバック経由の成果でも、`entry_ipaddress` / `entry_useragent` には実ユーザー（成果発生時のブラウザ）のIP/UAが記録されているため、正確なフラウド検知が可能です。

---

## Examples & Tests

### Local example (no network)

Run an end-to-end dry run with stubbed data and in-memory SQLite:

```bash
python -m fraud_checker.examples.local_example
```

Set `FRAUD_DB_PATH` to a file path beforehand if you want to inspect the resulting DB.

### API接続テスト

クリックログ取得の接続確認:
```bash
python examples/fetch_access_log_sample.py --date 2024-01-01
```

成果ログ取得の接続確認:
```bash
python examples/fetch_conversion_sample.py --date 2024-01-01
```

### 統合テスト（実際のAPI使用）

全機能の統合テスト:
```bash
python examples/test_real_api.py --date 2024-01-01 -v
```

オプション:
- `--date`: 対象日付（省略時は昨日）
- `--db`: テスト用DBパス（省略時は一時ファイル）
- `--keep-db`: テスト後もDBを保持
- `-v, --verbose`: 詳細表示
- `--test`: 実行するテスト（all/click/conversion/ingestion/detection/full）

### E2Eフルフローテスト

クリック→成果→検知の完全フローテスト:
```bash
python examples/e2e_full_flow.py --date 2024-01-01 --db ./test_e2e.db
```

オプション:
- `--date`: 対象日付（省略時は昨日）
- `--db`: DBパス（必須）
- `--page-size`: APIページサイズ
- `--click-threshold`: クリック検知閾値
- `--conversion-threshold`: 成果検知閾値

---

## ACS API assumptions

### クリックログ
- Endpoint: `/track_log/search` by default (joined with `ACS_BASE_URL`)
- Auth header: `X-Auth-Token: {access_key}:{secret_key}`
- Query params: `limit` (<=500), `offset` (0-based), `regist_unix=between_date` と `regist_unix_A_Y/M/D` / `regist_unix_B_Y/M/D` で日付絞り込み
- Track Log は `ipaddress` / `useragent` / `referrer` を含む

### 成果ログ
- Endpoint: `/action_log_raw/search`
- Query params: 同様に `regist_unix=between_date` で日付絞り込み
- 重要フィールド：
  - `id`: 成果ID
  - `check_log_raw`: cid（クリックIDへの参照、将来の拡張用）
  - `entry_ipaddress`: **実ユーザーのIP**（フラウド検知に使用）
  - `entry_useragent`: **実ユーザーのUA**（フラウド検知に使用）
  - `ipaddress` / `useragent`: ポストバックサーバーのIP/UA（参考情報）

---

## Data model

### クリックログ関連
- `click_raw` (オプション): クリックログ生データ。将来のクリックベース拡張用。
- `click_ipua_daily`: IP/UA×媒体×案件×日付の集計テーブル
  - Primary key: (`date`, `media_id`, `program_id`, `ipaddress`, `useragent`)

### 成果ログ関連
- `conversion_raw`: 成果ログ生データ
  - `cid`: クリックIDへの参照（将来の拡張用）
  - `entry_ipaddress`, `entry_useragent`: 実ユーザーのIP/UA（フラウド検知に使用）
  - `postback_ipaddress`, `postback_useragent`: ポストバックサーバーのIP/UA（参考情報）
- `conversion_ipua_daily`: 成果のIP/UA×媒体×案件×日付の集計（実ユーザーのIP/UAベース）
  - Primary key: (`date`, `media_id`, `program_id`, `ipaddress`, `useragent`)

---

## Tests

```bash
python -m pytest
```
