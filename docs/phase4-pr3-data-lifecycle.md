# Phase 4 PR3: Data Lifecycle

## 目的

- raw / aggregates / findings / job_runs の retention を明文化する
- destructive operation を dry-run first にする
- dashboard / suspicious list の直近運用価値を落とさずに古いデータだけを整理する

## Retention Policy

- raw: `90` 日
- aggregates: `365` 日
- findings: `365` 日
- finished job runs: `30` 日

環境変数で上書き可能。

- `FC_RETENTION_RAW_DAYS`
- `FC_RETENTION_AGGREGATE_DAYS`
- `FC_RETENTION_FINDINGS_DAYS`
- `FC_RETENTION_JOB_RUN_DAYS`

`0` 以下を指定すると 해당 tier の purge は無効化する。

## 実装

### Service

- `backend/src/fraud_checker/services/lifecycle.py`
- cutoff 計算
- dry-run / execute 切替
- tier ごとの purge 集約

### Repository / Store

- raw purge
  - `click_raw.click_time < cutoff`
  - `conversion_raw.conversion_time < cutoff`
- aggregate purge
  - `click_ipua_daily.date < cutoff`
  - `conversion_ipua_daily.date < cutoff`
- findings purge
  - `suspicious_*_findings.date < cutoff`
- job run purge
  - terminal status かつ `finished_at < cutoff`

### CLI

```bash
cd backend
python -m fraud_checker.cli purge-data
python -m fraud_checker.cli purge-data --execute
```

override 例:

```bash
python -m fraud_checker.cli purge-data --execute --raw-days 30 --job-run-days 14
```

## Safety Rules

- 既定は dry-run
- `--execute` を付けたときだけ削除する
- recent data は cutoff にかからない限り残る
- `job_status` legacy table は今回 purge 対象にしない

## Partitioning 方針

今回の PR では partitioning は入れない。

導入条件:

- raw table が retention purge でも vacuum/latency を十分抑えられない
- findings list hot path の index size が明確に問題化する
- monthly partition の運用コストが retention purge より安いと判断できる

## 運用

1. まず dry-run で件数確認
2. 実行は off-hours 推奨
3. 実行後に dashboard / suspicious list / health を確認
4. `oldest_queued_age_seconds` と failed jobs が溜まっている場合は purge より先に queue 健全性を見る
