# Phase 4 PR2: Job Hardening

## 目的

- durable job queue の運用品質を上げる
- duplicate enqueue を抑止し、retry/backoff を明示する
- production での in-process background kick を既定で無効化する
- queue health を API/health から観測できるようにする

## 本 PR の変更

### `job_runs` の追加列

- `attempt_count`
- `max_attempts`
- `next_retry_at`
- `dedupe_key`
- `priority`

### Duplicate enqueue 戦略

- `job_type + params` の canonical JSON から `dedupe_key` を作る
- 同じ `dedupe_key` の job が `queued` / `running` なら新規 row は作らない
- API は既存 `job_id` をそのまま返す
- 異なる job が既に active の場合は従来どおり conflict 扱い

### Retry / Backoff

- 既定 `max_attempts`
  - `refresh`: 4
  - `ingest_clicks`: 3
  - `ingest_conversions`: 3
  - `master_sync`: 2
- `ValueError` は non-retryable として即 `failed`
- それ以外の例外は retryable とみなし、attempt 残数があれば `queued` に戻す
- backoff は `30s, 60s, 120s, ...` の exponential で、上限 `900s`

### Queue scan

- worker は `status='queued'` かつ `next_retry_at <= now` の job だけ取得する
- order は `priority ASC, queued_at ASC`
- stale running job は lease recovery 後に `queued` へ戻す

### Production posture

- production の in-process background kick は既定で無効
- 明示的に使う場合だけ `FC_ENABLE_IN_PROCESS_JOB_KICK=true`
- local / dev / test では既定で有効

### Queue health 可視化

`GET /api/health`

- `metrics.jobs.queued_jobs_count`
- `metrics.jobs.retry_scheduled_jobs_count`
- `metrics.jobs.running_jobs_count`
- `metrics.jobs.failed_jobs_count`
- `metrics.jobs.oldest_queued_at`
- `metrics.jobs.oldest_queued_age_seconds`

`GET /api/job/status`

- 既存 payload に `queue` を追加

## Migration

```bash
cd backend
python -m alembic -c alembic.ini upgrade head
```

追加 migration:

- `backend/alembic/versions/0006_add_job_run_controls.py`

## 運用ルール

- queue が詰まっているかは `oldest_queued_age_seconds` をまず見る
- `retry_scheduled_jobs_count` が増えている場合は downstream 障害の可能性が高い
- `failed_jobs_count` が継続的に増える場合は retry では解消しない failure を疑う
- production は worker/cron を主経路にし、in-process kick は補助にしない

## Rollback

- アプリ rollback を優先する
- `0006` の列と index は残置 rollback で問題ない
- 完全 downgrade が必要な場合のみ Alembic downgrade を使う
