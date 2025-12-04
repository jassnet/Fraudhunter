# fraud_checker

ACS click logs → SQLite aggregation → suspicious IP/UA detection.

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

- `FRAUD_PAGE_SIZE` (default 500; ACS limit), `FRAUD_STORE_RAW` (`true`/`false`)
- `FRAUD_CLICK_THRESHOLD` (default 50), `FRAUD_MEDIA_THRESHOLD` (3), `FRAUD_PROGRAM_THRESHOLD` (3)
- `FRAUD_BURST_CLICK_THRESHOLD` (20), `FRAUD_BURST_WINDOW_SECONDS` (600)
- `ACS_LOG_ENDPOINT` (default `track_log/search`; set to `access_log/search` or `click_log/search` as needed)

The CLI loads `.env` automatically on startup.

## CLI commands

Always run as a module:

```
python -m fraud_checker.cli ingest --date 2024-01-01 \
  --base-url https://acs.example.com/api \
  --access-key YOUR_KEY --secret-key YOUR_SECRET \
  --endpoint track_log/search \  # default; use access_log/search or click_log/search if needed
  --db /var/lib/fraud/fraud_checker.db \
  --page-size 500 \
  --store-raw
```

```
python -m fraud_checker.cli suspicious --date 2024-01-01 \
  --db /var/lib/fraud/fraud_checker.db \
  --click-threshold 50 \
  --media-threshold 3 \
  --program-threshold 3 \
  --burst-click-threshold 20 \
  --burst-window-seconds 600
```

```
python -m fraud_checker.cli daily \
  --days-ago 1 \
  --db /var/lib/fraud/fraud_checker.db \
  --base-url https://acs.example.com/api \
  --access-key YOUR_KEY --secret-key YOUR_SECRET \
  --store-raw
```

`ingest` fetches ACS click logs for the given date, writes aggregates to `click_ipua_daily`, and optionally stores raw rows in `click_raw`. `suspicious` prints suspicious IP/UA pairs for the date using the rule set above. `daily` runs ingest for yesterday (or `--days-ago`) and then runs the suspicious report.

## Local example (no network)

Run an end-to-end dry run with stubbed data and in-memory SQLite:

```
python -m fraud_checker.examples.local_example
```

Set `FRAUD_DB_PATH` to a file path beforehand if you want to inspect the resulting DB.

## Access Log sample fetch

Fetch raw access logs without DB persistence (for connectivity/debug):

```
python examples/fetch_access_log_sample.py --date 2024-01-01
```

## ACS API assumptions

- Endpoint path: `/track_log/search` by default (joined with `ACS_BASE_URL`). Use `ACS_LOG_ENDPOINT=access_log/search` (IP/UAなし) or `click_log/search` (CPCログ) など用途に応じて切替。
- Auth header: `X-Auth-Token: {access_key}:{secret_key}`
- Query params (track_log): `limit` (<=500), `offset` (0-based), `regist_unix=between_date` と `regist_unix_A_Y/M/D` / `regist_unix_B_Y/M/D` で日付絞り込み。
- Track Log は `ipaddress` / `useragent` / `referrer` を含む。Access Log には IP/UA が含まれないため、フラウド用途では track_log を利用。
- Browser由来に限定したい場合は、取得後に UA ブラックリスト（bot/crawler など）・プライベートIP除外でフィルタしてから集計する。
- Non-200 responses raise with the response body logged; retries should be handled by the caller/scheduler if needed.

## Data model

- `click_ipua_daily` primary key: (`date`, `media_id`, `program_id`, `ipaddress`, `useragent`)
- Aggregation: `click_count` incremented by 1 per log, `first_time`/`last_time` track min/max click timestamp (date bucket derived from the click timestamp; ACS is assumed to return UTC times).
- Optional `click_raw` stores the raw ACS payload when `--store-raw` or `FRAUD_STORE_RAW=true`.
- Suspicious extraction uses SQL over `click_ipua_daily`, grouping by (`date`, `ipaddress`, `useragent`) with the thresholds above plus a burst rule applied in Python.

## Tests

```
python -m pytest
```
