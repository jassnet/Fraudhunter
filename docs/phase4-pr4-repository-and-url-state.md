# Phase 4 PR4: Repository Split Finish + URL State Sync

## Scope
- service layer の型依存を `PostgresRepository` facade から狭い protocol へ寄せる
- 不審一覧の `date/search/page/risk/sort` を URL state に同期する
- 一覧まわりの日本語文言を正常化する

## Backend

### Narrow service dependencies
- `backend/src/fraud_checker/service_protocols.py`
  - `ReportingRepository`
  - `FindingsRepository`
  - `SettingsRepository`
  - `LifecycleRepository`
- `backend/src/fraud_checker/services/reporting.py`
- `backend/src/fraud_checker/services/findings.py`
- `backend/src/fraud_checker/services/settings.py`
- `backend/src/fraud_checker/services/lifecycle.py`

方針:
- runtime の実装はそのまま維持する
- service の関心ごとごとに必要最小限の method set だけを protocol として宣言する
- `PostgresRepository` facade は後方互換のため残すが、新規 service は facade 全体に依存しない

### Regression test
- `backend/tests/test_service_protocol_behavior.py`

狙い:
- facade 固有の実装詳細に service が依存していないことを stub repository で確認する

## Frontend

### URL state sync
- `frontend/src/components/suspicious-list-page.tsx`
- `frontend/src/hooks/use-suspicious-list.ts`

同期する state:
- `date`
- `search`
- `page`
- `risk`
- `sort`

ルール:
- `page=1`, `risk=all`, `sort=count`, 空検索は URL から落とす
- `router.replace(..., { scroll: false })` を使い、一覧操作でページ先頭へ不要に戻さない
- deep link で一覧状態を復元できる

### Copy cleanup
- `frontend/src/components/suspicious-row-details.tsx`
- `frontend/src/components/date-quick-select.tsx`
- `frontend/src/components/last-updated.tsx`
- `frontend/src/app/suspicious/clicks/page.tsx`
- `frontend/src/app/suspicious/conversions/page.tsx`

方針:
- list は `mask_sensitive=true` のまま維持する
- detail fetch でのみ full value を取得する
- 日本語 UI は monitoring 向けに短く揃える

## Tests
- `frontend/src/components/suspicious-list-page.test.tsx`
  - search/risk の server-side delegation
  - lazy detail fetch
  - query string 初期値復元
  - URL 更新
- `frontend/src/components/date-quick-select.test.tsx`
- `frontend/src/components/last-updated.test.tsx`
- `frontend/src/app/suspicious/conversions/page.test.tsx`
- `frontend/e2e/tests/suspicious-clicks.spec.ts`
- `frontend/e2e/tests/suspicious-conversions.spec.ts`

## Rollback
- backend は protocol type hint のみなので、rollback はコード差し戻しだけでよい
- frontend URL state sync も DB 変更なし
- 一覧 deep link を無効化したい場合は `suspicious-list-page.tsx` の query sync を戻せばよい
