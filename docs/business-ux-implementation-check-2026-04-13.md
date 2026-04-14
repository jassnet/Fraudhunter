# FraudChecker ビジネスUX 実装・検証チェック 2026-04-13

> **対象**: `docs/business-ux-review-2026-04-13.md` で改善対象として整理した項目
> **実装対象範囲**: レビューのアクションプラン項目一式 + 検証中に残件として見えた follow-up 期限/SLA 可視化
> **検証方法**: frontend/backend のコード確認、対象テスト実行、ローカル起動した画面の実操作、API 応答確認、DB 直接確認
> **判定日**: 2026-04-13

---

## A. エグゼクティブサマリー

2026-04-13 時点の business UX レビューで改善対象として挙げた実装項目は、ローカル環境では一通り実装され、実画面・API・DB まで含めて確認できた。

特に大きいのは次の3点。

1. **ダッシュボード/一覧が backlog 前提で使える形になった**。日付セレクター、全期間 backlog 基準、優先ケース、人間向けラベル、レビュー結果、失敗ジョブ/次回実行が揃った。
2. **ケース運用が単発レビューで終わらなくなった**。担当アサイン、`confirmed_fraud` 後の follow-up task 生成、期限表示、完了/未完了切替まで動作を確認した。
3. **設定・検証系の裏取りが揃った**。設定画面、API route、backend route、DB migration、frontend/backend test がつながっている。

今回の検証で唯一引っかかったのは、**ローカル DB に Alembic の新規 migration が未適用だったこと**。`0015_add_case_assignments_and_followups.py` と `0016_add_followup_due_at.py` を適用後、assignment / follow-up / due date の挙動を再確認し、期待どおりに動くことを確認した。

---

## B. 実装完了チェック

| ID | 項目 | 実装内容 | 主な実装箇所 | 判定 |
|---|---|---|---|---|
| C-1 | デフォルト報酬の統一 | fallback default を `3,000円` に統一し、説明画面も一致させた | `backend/src/fraud_checker/constants.py:1`, `frontend/src/features/console/algorithm-screen.tsx:253-267` | 完了 |
| C-2 | `critical` dead UI 解消 | frontend の risk filter を `high/medium/low` に統一し、backend の risk level と揃えた | `frontend/src/features/console/alerts-screen.tsx:359-371`, `backend/src/fraud_checker/api_presenters.py:197-230` | 完了 |
| B-1-1 / B-1-2 | backlog 既定表示 + 日付セレクター | dashboard は「日次」と「全期間 backlog」を分離し、一覧は start/end 未指定で全期間表示、dashboard は `available_dates` で日付切替可能にした | `backend/src/fraud_checker/services/console.py:58-142`, `frontend/src/features/console/dashboard-screen.tsx:191-235` | 完了 |
| B-1-3 | 優先ケースの人間向け表示 | ranking を `display_label / secondary_label / damage / assignee / follow-up open count` で表示し、並びも `status + priority_score + risk + damage` に変更した | `backend/src/fraud_checker/services/console.py:90-117`, `frontend/src/features/console/dashboard-screen.tsx:365-395` | 完了 |
| E-2 | レビュー結果の可視化 | `confirmed_fraud / white / investigating / confirmed_ratio` を dashboard で表示した | `backend/src/fraud_checker/services/console.py:123-139,964-978`, `frontend/src/features/console/dashboard-screen.tsx:342-363` | 完了 |
| B-5-1 | 失敗ジョブ / 次回自動実行 | failed jobs と schedules を operations に載せ、dashboard で表示した | `backend/src/fraud_checker/services/console.py`, `frontend/src/features/console/dashboard-screen.tsx:309-339` | 完了 |
| B-2-2 | bulk review の運用改善 | page size 選択、filtered bulk review、URL 状態保持、日本語 pagination を実装した | `frontend/src/features/console/alerts-screen.tsx:221-264,391-403,458-480,599-620`, `backend/src/fraud_checker/services/console.py:145-216,739-759` | 完了 |
| B-2-3 | 被害額ソート | `damage_desc / damage_asc` を backend/frontend 両方で実装した | `backend/src/fraud_checker/services/console.py:602-609`, `frontend/src/features/console/alerts-screen.tsx:374-389` | 完了 |
| B-2-4 | 検索 UI の強化 | affiliate / program / IP / UA / 理由を想定した placeholder と search_text 検索を揃えた | `backend/src/fraud_checker/services/console.py:565-573`, `frontend/src/features/console/alerts-screen.tsx:427-437` | 完了 |
| B-3-1 | transaction state の人間向け表示 | raw code を `承認 (1)` などのラベルへ変換した | `backend/src/fraud_checker/services/console.py:_format_transaction_state`, `_present_transaction`, `frontend/src/features/console/alert-detail-screen.tsx:72-119` | 完了 |
| B-4-1 | `confirmed_fraud` 後の運用接続 | review 後に follow-up tasks を自動生成し、detail 画面で checklist として運用できるようにした | `backend/src/fraud_checker/repositories/suspicious_findings_write.py:13-23`, `backend/src/fraud_checker/services/console.py:433-450,903-948`, `frontend/src/features/console/alert-detail-screen.tsx:378-405` | 完了 |
| B-4-2 | assignee / ownership | claim / release API と UI を実装し、一覧・詳細・ranking に担当表示を入れた | `backend/src/fraud_checker/services/console.py:410-430,951-961`, `backend/src/fraud_checker/api_routers/console.py:157-199`, `frontend/src/features/console/alert-detail-screen.tsx:220-233,439-487`, `frontend/src/features/console/alerts-screen.tsx:565-569` | 完了 |
| B-4-5 | SLA / 期限可視化 | follow-up task に `due_at` を追加し、detail で期限と overdue 判定を表示できるようにした | `backend/src/fraud_checker/db/models.py`, `backend/alembic/versions/0016_add_followup_due_at.py`, `backend/src/fraud_checker/repositories/suspicious_findings_write.py`, `backend/src/fraud_checker/services/console.py:934-947`, `frontend/src/features/console/alert-detail-screen.tsx:385-391` | 完了 |
| D-2 / E-3 | settings UI / route | admin 向け settings 画面、frontend proxy route、backend console route を実装した | `frontend/src/features/console/settings-screen.tsx:69-200`, `frontend/src/app/settings/page.tsx`, `frontend/src/app/api/console/settings/route.ts`, `backend/src/fraud_checker/api_routers/console.py:201-209` | 完了 |

---

## C. 検証方法

### C-1. 自動テスト

- backend:
  - `python -m pytest tests/test_console_api_behavior.py tests/test_job_status_pg_behavior.py tests/test_api_behavior.py`
- frontend:
  - `npm run lint`
  - `npm run typecheck`
  - `npm run test -- --run src/features/console/dashboard-screen.test.tsx src/features/console/alerts-screen.test.tsx src/features/console/alert-detail-screen.test.tsx src/components/app-frame.test.tsx src/app/api/console/dashboard/route.test.ts src/app/api/console/refresh/route.test.ts`

### C-2. 実画面確認

- `python dev.py` で frontend / backend / worker を起動
- `http://127.0.0.1:3000/dashboard`
- `http://127.0.0.1:3000/alerts`
- `http://127.0.0.1:3000/alerts/{caseKey}`
- `http://127.0.0.1:3000/settings`

### C-3. API / DB 確認

- `GET /api/console/dashboard`
- `GET /api/console/alerts?status=unhandled&sort=risk_desc&page=1&page_size=50`
- `GET /api/console/alerts/{caseKey}`
- `GET /api/console/settings`
- PostgreSQL 上の `fraud_alert_followup_tasks` を直接参照

---

## D. 自動テスト結果

### D-1. backend

- 実行結果: `64 passed, 19 warnings in 2.07s`
- 確認できたこと:
  - dashboard / alerts / detail の API 仕様
  - review state / review history
  - filtered bulk review
  - assignee API
  - follow-up update API
  - settings API
  - `confirmed_fraud -> follow-up task 作成 -> white -> open task cancel` の repository 振る舞い

主な根拠:

- `backend/tests/test_console_api_behavior.py:841-979`
- `backend/tests/test_job_status_pg_behavior.py`
- `backend/tests/test_api_behavior.py`

### D-2. frontend

- `npm run lint`: pass
- `npm run typecheck`: pass
- `npm run test ...`: `6 files / 15 tests passed`

主な根拠:

- `frontend/src/features/console/dashboard-screen.test.tsx`
- `frontend/src/features/console/alerts-screen.test.tsx`
- `frontend/src/features/console/alert-detail-screen.test.tsx:15-180`
- `frontend/src/components/app-frame.test.tsx`
- `frontend/src/app/api/console/dashboard/route.test.ts`
- `frontend/src/app/api/console/refresh/route.test.ts`

---

## E. 実画面確認結果

### E-1. dashboard

- 日付ドロップダウンが表示され、`最新 / 2026/04/09 / 2026/04/07` を切り替え可能
- ヘッダ説明に `2026/04/09 の日次サマリー / backlog は全期間表示` が出る
- KPI は `不正率 / 未対応アラート件数 / 想定被害額` を表示
- 右カラムで以下を確認
  - queue summary
  - 最新 job id
  - 最古の未対応
  - 3日超の未対応
  - 次回自動実行
  - 直近の失敗ジョブ
- `レビュー結果` パネルで `不正確定 / ホワイト / 調査中 / 判定精度` を表示
- `優先ケース` パネルで hash ではなく `affiliate / program` ベースの表示ラベルが出る

確認した実値:

- `oldest_unhandled_days = 4`
- `stale_unhandled_count = 6`
- `schedules = 4`
- `failed_jobs = 0`

### E-2. alerts

- デフォルト表示で `status=unhandled`、`start_date=null`、`end_date=null` を確認
- risk filter は `high / medium / low` の 3段階で、`critical` は消えている
- sort に `被害額高い順 / 被害額低い順` がある
- page size は `50 / 100 / 200`
- 検索 placeholder が `アフィリエイト名、案件名、IP、UA、検知理由` になっている
- pagination が `全 N 件中 X-Y 件を表示` の日本語表記になっている
- row summary に `担当` と `未完了タスク` が出る

実地確認では、`confirmed_fraud` にしたケースが一覧上で

- `担当: local-dev-admin`
- `未完了タスク 2件`

と表示された。

### E-3. alert detail

- 証拠 transaction の state は raw code ではなく `承認 (1)` と表示された
- `自分が担当` を押すと assignee が `local-dev-admin` に更新された
- `不正確定` の review dialog で preset 理由を選び、確定できた
- review 後に review history テーブルへ 1 行追加された
- `後続アクション` パネルが生成され、3 task が表示された
  - `関係者へ通知`
  - `支払保留を実施`
  - `証跡を保全`
- 各 task に期限が出た
  - `2026/04/14 03:52`
  - `2026/04/14 00:52`
  - `2026/04/14 23:52`
- `完了にする` を 1 件押すと、`完了: local-dev-admin / 2026/04/13 23:52` に切り替わった

### E-4. settings

- `設定` 画面が admin nav から開ける
- `クリック異常 / CV異常 / 不正兆候 / 補助フィルタ` の各セクションを表示
- `保存` ボタンが存在し、しきい値編集 UI として成立している

---

## F. API / DB 確認結果

### F-1. alerts API の backlog 既定挙動

`GET /api/console/alerts?status=unhandled&sort=risk_desc&page=1&page_size=50`

```json
{"status":"unhandled","start_date":null,"end_date":null,"total":6,"has_next":false}
```

判定:

- start/end が `null`
- 「最新日固定」ではなく全期間 backlog 前提で動いている

### F-2. dashboard API

`GET /api/console/dashboard`

```json
{"available_dates":2,"has_case_ranking":true,"oldest_unhandled_days":4,"stale_unhandled_count":6,"failed_jobs":0,"schedules":4}
```

判定:

- date selector 用データあり
- case ranking あり
- operations パネル用データあり

### F-3. detail API

`GET /api/console/alerts/bab19e68b80bfca8cc7b63debec5504d24a58b3a9785d0cd407bdbe5077f2b46`

```json
{"status":"confirmed_fraud","assignee_user":"local-dev-admin","follow_up_count":3,"open_followups":2,"first_due_at":"2026-04-14T03:52:00.141165"}
```

判定:

- review status は `confirmed_fraud`
- assignee は保存済み
- follow-up tasks は 3 件生成済み
- 1 件完了済みのため open は 2 件
- `due_at` が API に乗っている

### F-4. DB 直接確認

`fraud_alert_followup_tasks`

```json
[
  {"task_type":"evidence_preservation","task_status":"open","due_at":"2026-04-14T23:52:00.141165","completed_by":null},
  {"task_type":"partner_notice","task_status":"completed","due_at":"2026-04-14T03:52:00.141165","completed_by":"local-dev-admin"},
  {"task_type":"payout_hold","task_status":"open","due_at":"2026-04-14T00:52:00.141165","completed_by":null}
]
```

判定:

- task 生成は DB に persist されている
- `due_at` も persist されている
- 完了トグルは DB に反映されている

### F-5. settings API

`GET /api/console/settings`

```json
{"click_threshold":50,"browser_only":false,"dc_ip_exclusions":null,"version_id":null}
```

判定:

- settings route は応答している
- しきい値取得が frontend 画面と接続されている

---

## G. 検証中に見つかった問題と対処

### G-1. ローカル DB migration 未適用

- 症状:
  - 初回確認時、assignment / follow-up の UI は出るが DB 永続化が追えない
  - `fraud_alert_followup_tasks` テーブルの存在と列構成がローカル DB とコードでズレていた
- 原因:
  - Alembic `0015` と `0016` がローカル PostgreSQL に未適用
- 対応:
  - `python -m alembic upgrade head`
- 結果:
  - `0015_case_assignment_followups -> 0016_followup_due_at` まで適用
  - その後、assignment / follow-up / due date / completion を再確認して pass

### G-2. SQLite test の `datetime` 返却形式差

- 症状:
  - `test_apply_alert_reviews_creates_and_cancels_followup_tasks` が `datetime` と文字列の差で fail
- 原因:
  - SQLite 経由の `due_at` が文字列で返るケースがあった
- 対応:
  - test 側で `datetime.fromisoformat(str(row["due_at"]))` へ正規化
- 結果:
  - backend test は `64 passed`

---

## H. 最終判定

今回の対象としていた business UX 改善項目は、**ローカルでは実装済みかつ検証済み**と判断してよい。

判定理由:

1. コード上で dashboard / alerts / detail / settings / backend route / repository / migration が揃っている。
2. 自動テストで backend 64 件、frontend 15 件が通っている。
3. 実画面で `assign -> confirmed_fraud -> follow-up task 生成 -> due date 表示 -> 完了トグル` を通しで確認できた。
4. API と DB の両方で保存結果を裏取りできた。

現時点の注意点は 1 つだけ。

- 新しい環境で使う場合は、**アプリ起動前に Alembic migration を head まで適用すること**。これを外すと assignment / follow-up / due date 周りだけは「コードはあるのに動かない」状態になる。

それ以外については、今回の改善対象は「実装した」で止まらず、「本当に効いている」ことまで確認できた。
