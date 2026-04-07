# Business Test Scenarios

この文書は current console UI と backend の主要 business scenario をまとめた正本です。  
存在しない E2E や削除済み画面は参照せず、現在 repo にあるテストだけを対応表へ載せます。

## Backend

### SC-01 短時間に集中したコンバージョンを不正候補として検知する

- 業務上の意味: 同一 IP / UA に集中する不自然な CV を検知し、調査対象へ回す。
- 入力条件: 同一 IP / UA で conversion threshold や burst 条件を超える。
- 期待結果: suspicious conversion finding が作られ、理由とリスクが付く。
- 主な保証レイヤー: backend unit
- 対応テスト: `backend/tests/test_suspicious_behavior.py`

### SC-02 findings 再計算時に lineage と damage snapshot を保存する

- 業務上の意味: 後から見ても「どの条件で検知され、どの程度の被害見積もりだったか」を説明できる。
- 入力条件: recompute が対象日の findings を再生成する。
- 期待結果: `computed_by_job_id`, `generation_id`, `estimated_damage_yen`, `damage_evidence_json` が保存される。
- 主な保証レイヤー: backend unit
- 対応テスト: `backend/tests/test_findings_lineage_behavior.py`

### SC-03 ダッシュボードで最新日の KPI を返す

- 業務上の意味: 運用担当者が開いた瞬間に今日のフラウド状況を把握できる。
- 入力条件: summary と current alert rows が存在する。
- 期待結果: fraud rate、未対応件数、被害推定額、trend、ranking を返す。
- 主な保証レイヤー: backend API, backend service
- 対応テスト: `backend/tests/test_console_api_behavior.py`, `backend/tests/test_reporting_behavior.py`

### SC-04 alerts 一覧は filter / pagination / review status を扱える

- 業務上の意味: triage 対象を絞り込み、必要な単位でレビューを進められる。
- 入力条件: status、date range、page、page_size を指定して一覧を引く。
- 期待結果: filter が適用され、`total`, `page`, `page_size`, `has_next`, `status_counts` が返る。
- 主な保証レイヤー: backend API
- 対応テスト: `backend/tests/test_console_api_behavior.py`

### SC-05 review 操作は admin 権限でだけ更新できる

- 業務上の意味: triage 判定を権限境界の内側に閉じる。
- 入力条件: finding keys と review status を送る。
- 期待結果: admin 以外は拒否され、admin は bulk update 結果を受け取る。
- 主な保証レイヤー: backend API
- 対応テスト: `backend/tests/test_console_api_behavior.py`

### SC-06 refresh は queue へ積み、競合時は競合として扱う

- 業務上の意味: 重い再取得処理を request 内で実行せず、安全に再計算を始める。
- 入力条件: refresh を起動する。
- 期待結果: queued job id を返し、競合時は `409` を返す。
- 主な保証レイヤー: backend API, backend service
- 対応テスト: `backend/tests/test_api_behavior.py`, `backend/tests/test_jobs_behavior.py`

### SC-07 read posture は analyst/admin/public の設定に従う

- 業務上の意味: read API の露出範囲を環境ごとに制御する。
- 入力条件: `FC_REQUIRE_READ_AUTH` などの posture を設定する。
- 期待結果: read token なしの呼び出しは拒否され、権限別の endpoint matrix が保たれる。
- 主な保証レイヤー: backend API, backend unit
- 対応テスト: `backend/tests/test_api_behavior.py`, `backend/tests/test_runtime_guards_behavior.py`

## Frontend

### FC-01 ダッシュボードで KPI とランキングを表示する

- 業務上の意味: 現在のフラウド状況を一画面で把握できる。
- 入力条件: console dashboard API が payload を返す。
- 期待結果: KPI card、trend、ranking が表示される。
- 主な保証レイヤー: frontend component
- 対応テスト: `frontend/src/features/console/dashboard-screen.test.tsx`

### FC-02 ダッシュボードから更新を開始できる

- 業務上の意味: 運用者が UI から最新データ取り込みを開始できる。
- 入力条件: admin action が有効で、利用者が更新ボタンを押す。
- 期待結果: refresh API を呼び、完了後に dashboard を再取得する。
- 主な保証レイヤー: frontend component
- 対応テスト: `frontend/src/features/console/dashboard-screen.test.tsx`

### FC-03 alerts 一覧は grouped row と bulk review を扱える

- 業務上の意味: 同一アフィリエイター・同一検知時刻のアラートをまとめて判断できる。
- 入力条件: alerts payload に grouped 対象の item が含まれる。
- 期待結果: まとめ行が表示され、展開・選択・一括 review ができる。
- 主な保証レイヤー: frontend component
- 対応テスト: `frontend/src/features/console/alerts-screen.test.tsx`

### FC-04 alerts 一覧は URL と同期した filter / pagination を扱える

- 業務上の意味: 「この条件で見て」と URL 共有できる。
- 入力条件: status/date/page を持つ search params で画面を開く、またはページ移動する。
- 期待結果: URL と画面状態が同期し、次ページ取得時も query が更新される。
- 主な保証レイヤー: frontend component
- 対応テスト: `frontend/src/features/console/alerts-screen.test.tsx`

### FC-05 alert detail は理由・被害推定額・transaction evidence を表示する

- 業務上の意味: 一覧から詳細調査へ無駄なく進める。
- 入力条件: finding key を指定して detail 画面を開く。
- 期待結果: affiliate 名、status、理由、被害推定額、transactions が表示される。
- 主な保証レイヤー: frontend component
- 対応テスト: `frontend/src/features/console/alert-detail-screen.test.tsx`

### FC-06 frontend proxy は read 用 key を必須とする

- 業務上の意味: read 経路で admin token を使い回さない。
- 入力条件: frontend server proxy が read API を呼ぶ。
- 期待結果: `FC_READ_API_KEY` が使われ、未設定時は 502 を返す。
- 主な保証レイヤー: frontend server unit
- 対応テスト: `frontend/src/lib/server/backend-proxy.test.ts`

### FC-07 mobile drawer は Escape で閉じられる

- 業務上の意味: モバイルでも迷わずナビゲーションを閉じられる。
- 入力条件: mobile menu を開いた状態で Escape を押す。
- 期待結果: drawer が閉じる。
- 主な保証レイヤー: frontend component
- 対応テスト: `frontend/src/components/app-frame.test.tsx`

## Scenario Mapping

| Scenario ID | 主な保証レイヤー | 対応テスト |
| --- | --- | --- |
| SC-01 | backend unit | `backend/tests/test_suspicious_behavior.py` |
| SC-02 | backend unit | `backend/tests/test_findings_lineage_behavior.py` |
| SC-03 | backend API / service | `backend/tests/test_console_api_behavior.py`, `backend/tests/test_reporting_behavior.py` |
| SC-04 | backend API | `backend/tests/test_console_api_behavior.py` |
| SC-05 | backend API | `backend/tests/test_console_api_behavior.py` |
| SC-06 | backend API / service | `backend/tests/test_api_behavior.py`, `backend/tests/test_jobs_behavior.py` |
| SC-07 | backend API / unit | `backend/tests/test_api_behavior.py`, `backend/tests/test_runtime_guards_behavior.py` |
| FC-01 | frontend component | `frontend/src/features/console/dashboard-screen.test.tsx` |
| FC-02 | frontend component | `frontend/src/features/console/dashboard-screen.test.tsx` |
| FC-03 | frontend component | `frontend/src/features/console/alerts-screen.test.tsx` |
| FC-04 | frontend component | `frontend/src/features/console/alerts-screen.test.tsx` |
| FC-05 | frontend component | `frontend/src/features/console/alert-detail-screen.test.tsx` |
| FC-06 | frontend server unit | `frontend/src/lib/server/backend-proxy.test.ts` |
| FC-07 | frontend component | `frontend/src/components/app-frame.test.tsx` |
