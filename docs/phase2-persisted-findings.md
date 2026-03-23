# Phase 2 Persisted Findings

## 目的
- `suspicious findings` を request-time compute から切り離す
- dashboard / daily stats / suspicious list を persisted findings 読みへ寄せる
- suspicious list を server-side pagination / search / risk filter / sort に切り替える
- detail payload を list から切り離し、必要時だけ lazy fetch できるようにする

## 追加テーブル
- `suspicious_click_findings`
- `suspicious_conversion_findings`

主なカラム:
- `finding_key`
- `date`
- `ipaddress`
- `useragent`
- `ua_hash`
- `media_ids_json`
- `program_ids_json`
- `media_names_json`
- `program_names_json`
- `affiliate_names_json`
- `risk_level`
- `risk_score`
- `reasons_json`
- `reasons_formatted_json`
- `metrics_json`
- `rule_version`
- `computed_at`
- `is_current`
- `search_text`

## 再計算トリガ
- click ingest 完了後
- conversion ingest 完了後
- refresh 完了後
- settings 更新後
- E2E baseline seed 後

実装:
- [findings.py](C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/backend/src/fraud_checker/services/findings.py)
- [jobs.py](C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/backend/src/fraud_checker/services/jobs.py)
- [settings.py](C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/backend/src/fraud_checker/services/settings.py)
- [e2e_seed.py](C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/backend/src/fraud_checker/services/e2e_seed.py)

## API
既存互換を維持しつつ、suspicious list は persisted findings を返す。

一覧:
- `GET /api/suspicious/clicks`
- `GET /api/suspicious/conversions`

追加 query:
- `risk_level=high|medium|low`
- `sort_by=count|risk|latest`
- `sort_order=asc|desc`
- `include_details=true|false`

detail:
- `GET /api/suspicious/clicks/{finding_key}`
- `GET /api/suspicious/conversions/{finding_key}`

推奨:
- 一覧は `include_details=false`
- row expand 時だけ detail endpoint を叩く

## frontend
一覧は server-side query を使用し、details は lazy fetch する。

主要ファイル:
- [api.ts](C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/lib/api.ts)
- [use-suspicious-list.ts](C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/hooks/use-suspicious-list.ts)
- [suspicious-list-page.tsx](C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/suspicious-list-page.tsx)
- [suspicious-row-details.tsx](C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/suspicious-row-details.tsx)

## migration
- [0004_add_persisted_findings.py](C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/backend/alembic/versions/0004_add_persisted_findings.py)

適用:
```bash
cd backend
alembic upgrade head
```

## テスト
- backend: `pytest backend/tests -q`
- frontend unit: `cd frontend && npm test`
- frontend e2e:
```powershell
$env:FRAUD_TEST_DATABASE_URL='postgresql+psycopg://postgres@localhost:5432/fraudchecker'
cd frontend
npm run test:e2e
```

## 残課題
- repository 分割は Phase 3
- `inet` / `ua_hash` 正規化は Phase 3
- triage / annotation model は Phase 3
