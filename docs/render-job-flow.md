# Render Job Flow

## 方針

本番の Render 環境では、同期や再取得の**要求**と**実行**を分離する。

- Web API は durable job を `job_runs` に登録するだけ
- 実処理は `run-worker` が queue から取得して実行する
- 定期実行も手動実行も同じ queue 経路を使う

これにより、request timeout、多重実行、再起動時の中断に強い運用に揃える。

## Render 上の役割

- `fraudchecker-backend`
  - 管理 API を受け付ける
  - `POST /api/refresh`
  - `POST /api/sync/masters`
  - `POST /api/ingest/*`
  - production では `FC_ENABLE_IN_PROCESS_JOB_KICK=false`

- `fraudchecker-refresh-hourly`
  - `python -m fraud_checker.cli enqueue-refresh --hours 1 --detect`
  - 再取得 job を queue に登録する

- `fraudchecker-sync-masters-daily`
  - `python -m fraud_checker.cli enqueue-sync-masters`
  - マスタ同期 job を queue に登録する

- `fraudchecker-queue-runner-minute`
  - `python -m fraud_checker.cli run-worker --max-jobs 5`
  - 毎分 queue を処理する

## 手動同期

通常の手動同期は管理 API から行う。

- `POST /api/sync/masters`
- `POST /api/refresh`

API は即時実行しない。`job_id` を返すだけで、実行開始 SLA は最長 1 分程度とする。

## CLI の使い分け

- 通常運用
  - `enqueue-refresh`
  - `enqueue-sync-masters`
  - `run-worker`

- break-glass 用
  - `refresh`
  - `sync-masters`

`refresh` と `sync-masters` は inline 実行なので、Render 本番の通常経路では使わない。

## 運用ルール

- 同一内容の `refresh` / `master_sync` は dedupe される
- 既に同じ job が queued/running なら既存 `job_id` を返す
- 別種 job は queue に積める。global lock はかけない
- 監視対象:
  - `oldest_queued_age_seconds`
  - `queued_jobs_count`
  - `running_jobs_count`
  - `failed_jobs_count`
  - `last_successful_ingest_at`
  - `findings_last_computed_at`
  - `master_sync` freshness
