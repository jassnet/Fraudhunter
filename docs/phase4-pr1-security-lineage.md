# Phase 4 PR1: Security + Findings Lineage

## 目的

- read-oriented monitoring API の最小許容セキュリティポスチャを明確化する
- findings の生成系譜を残し、監査性と stale 判定を強化する
- raw ingest freshness と findings freshness を分けて可視化する
- production では migration-only 原則を維持し、test だけ self-contained に動かす

## 本 PR の変更

### 1. Read access posture を明示必須化

production では、以下のどれか 1 つを明示しない限りアプリは起動しない。

- `FC_REQUIRE_READ_AUTH=true`
  - backend 自身が read auth を要求する
  - `X-Read-API-Key`, `X-API-Key`, `Authorization: Bearer ...` を受け付ける
  - 許可されるキーは `FC_READ_API_KEY` または `FC_ADMIN_API_KEY`
- `FC_EXTERNAL_READ_PROTECTION=true`
  - Cloudflare Access, VPN, private network, Render private service など外側保護前提
  - backend 内では追加 read auth を要求しない
- `FC_ALLOW_PUBLIC_READ=true`
  - public read を明示的に許可する
  - production では例外運用扱い

複数を同時に有効化した場合は起動時に hard-fail する。

### 2. Findings lineage を永続化

両 findings table に以下を追加した。

- `computed_by_job_id`
- `settings_updated_at_snapshot`
- `source_click_watermark`
- `source_conversion_watermark`
- `generation_id`

これにより各 finding 行について以下が追跡できる。

- どの durable job で計算されたか
- どの settings 状態を前提にしたか
- どの raw source watermark を見ていたか
- 同一再計算バッチに属するか

### 3. Sensitive 値の list/detail 分離

- suspicious list API は `mask_sensitive=true` を既定値にした
- list payload の `ipaddress` / `useragent` は masked 値を返す
- detail API は full 値を返す
- payload には以下を追加した
  - `ipaddress_masked`
  - `useragent_masked`
  - `sensitive_values_masked`

この設計により、一覧 UI の視認性と秘匿性を両立しつつ、詳細調査時には完全な evidence にアクセスできる。

### 4. Findings freshness の分離可視化

`GET /api/summary` と `GET /api/health` で以下を返す。

- `quality.findings.findings_last_computed_at`
- `quality.findings.click_findings_last_computed_at`
- `quality.findings.conversion_findings_last_computed_at`
- `quality.findings.stale`
- `quality.findings.stale_reasons`

stale 判定は以下を基準にする。

- raw source watermark が findings watermark より進んでいる
- settings 更新時刻が findings snapshot より新しい
- click/conversion findings が存在しない

## 環境変数

### production で必須のどれか 1 つ

- `FC_REQUIRE_READ_AUTH=true`
- `FC_EXTERNAL_READ_PROTECTION=true`
- `FC_ALLOW_PUBLIC_READ=true`

### `FC_REQUIRE_READ_AUTH=true` の場合に必要

- `FC_READ_API_KEY`
  - read-only 用
- `FC_ADMIN_API_KEY`
  - 管理系兼用でもよい

少なくともどちらか 1 つは必要。

## Migration

本 PR で追加される migration:

- `backend/alembic/versions/0005_add_findings_lineage.py`

production では deploy 前に Alembic upgrade を実行する。

```bash
cd backend
python -m alembic -c alembic.ini upgrade head
```

## Test / E2E 方針

production では runtime schema ensure を行わない。

ただし `FC_ENV=test` の Playwright backend は self-contained を優先し、web server 起動前に `python -m fraud_checker.migrations` を実行する。
この helper は以下を行う。

- `alembic_version` がある場合は通常の `upgrade head`
- 旧 test DB のように table だけ存在する場合は schema を推定して `stamp`
- その後に `upgrade head`

これにより test DB は最新 schema に自動追従する。

## Rollback

### アプリ rollback

- 先にアプリを前バージョンへ戻す
- `0005` で増えた列は残したままで問題ない
- 旧コードは追加列を無視できる

### DB rollback

本当に downgrade が必要な場合のみ実施する。

```bash
cd backend
python -m alembic -c alembic.ini downgrade -1
```

ただし lineage 情報を失うため、通常は column を残したままアプリだけ rollback するほうが安全。

## 推奨運用

- production では `FC_REQUIRE_READ_AUTH=true` または `FC_EXTERNAL_READ_PROTECTION=true` を使う
- `FC_ALLOW_PUBLIC_READ=true` は demo / temporary review 環境に限定する
- stale 判定が `true` のまま継続する場合は以下を確認する
  - 該当日の raw ingest が完了しているか
  - refresh/recompute job が成功しているか
  - settings 更新後の再計算が走っているか
