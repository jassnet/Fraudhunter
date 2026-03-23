# Phase 3 Repository Split

## Goal
- `PostgresRepository` の単一肥大化を止める
- 既存 API / service / CLI の呼び出し契約は維持する
- small PR で段階的に責務分離できる土台を作る

## Implemented Slice
- `RepositoryBase`
  - 接続管理
  - 汎用 SQL helper
  - filter helper
- `IngestionRepository`
  - click / conversion ingest
  - merge / dedupe
  - conversion click enrich
- `ReportingReadRepository`
  - dashboard / daily stats / quality read
- `SuspiciousReadRepository`
  - persisted findings read / replace / detail
- `MasterRepository`
  - master upsert / stats
- `SettingsRepository`
  - settings read / write / freshness

## Backward Compatibility
- `PostgresRepository` は残す
- 実装は split repository を多重継承する薄い facade へ変更
- 既存 service, router, CLI, tests は破壊せずに継続利用できる

## Why This Shape
- まず read/write/settings/master を分離すると、Phase 2 までで増えた query 群の責務境界が明確になる
- ここで interface を完全に差し替えるより、facade を残した方が安全
- 次段階では service 単位で型ヒントを `PostgresRepository` から各 repository へ絞れる

## Next Step Candidates
- `services/reporting.py` を `ReportingReadRepository` ベースへ寄せる
- `ingestion.py` を `IngestionRepository` ベースへ寄せる
- `suspicious.py` / `services/findings.py` を `SuspiciousReadRepository` ベースへ寄せる
- `JobRepository` を追加して durable job query を独立させる
- `ai-architecture-review-pack.md` の source inventory を split 構成へ更新する
