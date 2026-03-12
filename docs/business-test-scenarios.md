# Business Test Scenarios

この文書は、fraud checker の検証済み business 要件を backend と frontend をまたいで読みやすく整理した正本である。各シナリオには、業務上の意味、入力条件、期待結果、主な保証レイヤー、対応テストを記載する。詳細なテスト方針は `docs/test-strategy.md` を参照する。

## Backend

### SC-01 短時間に集中したクリックを不正候補として検知する

- 業務上の意味: 通常運用では起こりにくい短時間の大量クリックを検知し、調査対象へ回す。
- 入力条件: 同一 IP と同一 UA に対して、しきい値を超えるクリックが短時間に集中している。
- 期待結果: 該当 IP / UA が不正クリックとして返り、burst 理由が付与される。
- 主な保証レイヤー: backend unit
- 対応テスト: `backend/tests/test_suspicious_behavior.py`

### SC-02 短時間に集中したコンバージョンを不正候補として検知する

- 業務上の意味: 不自然な CV 集中を検知し、成果の信頼性を確認できるようにする。
- 入力条件: 同一 IP と同一 UA に対して CV 数が短時間に集中している。
- 期待結果: 該当 IP / UA が不正 CV として返る。
- 主な保証レイヤー: backend unit
- 対応テスト: `backend/tests/test_suspicious_behavior.py`

### SC-03 クリックから CV までの異常に短い時間差を不正 CV として扱う

- 業務上の意味: 人の操作として不自然な時間差を検知し、機械的な成果発生を見逃さない。
- 入力条件: click-to-conversion の時間差が許容下限より短い。
- 期待結果: time gap 理由が追加され、不正 CV として返る。
- 主な保証レイヤー: backend unit
- 対応テスト: `backend/tests/test_suspicious_behavior.py`

### SC-04 クリックと CV の両面で不自然な IP / UA は高リスクとして扱う

- 業務上の意味: 調査優先度を高くすべき対象を明確にする。
- 入力条件: クリック側と CV 側の両方で不正理由が成立している。
- 期待結果: risk label が高リスク相当で返る。
- 主な保証レイヤー: backend unit, backend API
- 対応テスト: `backend/tests/test_suspicious_behavior.py`, `backend/tests/test_api_behavior.py`

### SC-05 ダッシュボードで最新日の主要指標を確認できる

- 業務上の意味: 運用担当者がその日のクリック数、CV 数、不正件数を一目で把握できる。
- 入力条件: 対象日の click / conversion 集計と不正判定件数が存在する。
- 期待結果: summary payload に主要指標が入り、画面カードに表示される。
- 主な保証レイヤー: backend unit, frontend page
- 対応テスト: `backend/tests/test_reporting_behavior.py`, `frontend/src/app/page.test.tsx`, `frontend/e2e/tests/dashboard.spec.ts`

### SC-06 日次推移を表示して前日との差分を確認できる

- 業務上の意味: 異常値や急増減を日次で追跡できる。
- 入力条件: 複数日の click / conversion 実績がある。
- 期待結果: 日別推移が返り、前日差分を表示できるデータがそろう。
- 主な保証レイヤー: backend unit
- 対応テスト: `backend/tests/test_reporting_behavior.py`

### SC-07 利用可能な日付一覧を返し、画面側が選択できる

- 業務上の意味: 画面から分析対象日を迷わず切り替えられる。
- 入力条件: click / conversion に複数日のデータが存在する。
- 期待結果: 降順の日付一覧が返る。
- 主な保証レイヤー: backend unit, frontend component
- 対応テスト: `backend/tests/test_reporting_behavior.py`, `frontend/src/components/date-quick-select.test.tsx`

### SC-08 認証されていない API 呼び出しは拒否する

- 業務上の意味: 認可されていない利用者から運用 API を守る。
- 入力条件: API キー未設定、または不正なヘッダーでアクセスする。
- 期待結果: `401 Unauthorized` を返す。
- 主な保証レイヤー: backend API
- 対応テスト: `backend/tests/test_api_behavior.py`

### SC-09 不正な日付や入力値は業務エラーとして説明付きで返す

- 業務上の意味: 利用者が入力ミスを即座に修正できる。
- 入力条件: `YYYY-MM-DD` ではない日付、または許容外のパラメータを送る。
- 期待結果: `400` と説明メッセージを返す。
- 主な保証レイヤー: backend API
- 対応テスト: `backend/tests/test_api_behavior.py`

### SC-10 同時実行できないジョブは競合として扱う

- 業務上の意味: refresh や sync の二重実行でデータ不整合を起こさない。
- 入力条件: すでに実行中のジョブがある状態で refresh / sync を起動する。
- 期待結果: `409 Conflict` を返し、実行中ジョブを案内する。
- 主な保証レイヤー: backend API, backend service
- 対応テスト: `backend/tests/test_api_behavior.py`, `backend/tests/test_jobs_behavior.py`

### SC-11 refresh は集計、検知、件数更新をまとめて完了させる

- 業務上の意味: 日次運用で必要な再計算が 1 回の refresh で終わる。
- 入力条件: refresh を開始できる状態で click / conversion データが存在する。
- 期待結果: 集計結果、検知件数、ジョブ状態が完了値になる。
- 主な保証レイヤー: backend service, CLI
- 対応テスト: `backend/tests/test_jobs_behavior.py`, `backend/tests/test_cli_behavior.py`

### SC-12 設定は保存結果と永続化成否を利用者へ返す

- 業務上の意味: しきい値変更後に、DB へ保存されたかどうかを運用者が判断できる。
- 入力条件: 設定更新 API または service に新しい値を渡す。
- 期待結果: 保存値が返り、永続化できない場合は warning と `persisted=false` が返る。
- 主な保証レイヤー: backend unit, backend API
- 対応テスト: `backend/tests/test_settings_behavior.py`, `backend/tests/test_api_behavior.py`

### SC-13 マスタ同期は件数付きで更新結果を返す

- 業務上の意味: media / promotion / user マスタの同期が正常に進んだか確認できる。
- 入力条件: sync-masters を実行する。
- 期待結果: 各マスタの upsert 件数と最終結果が返る。
- 主な保証レイヤー: backend service, CLI, backend API
- 対応テスト: `backend/tests/test_jobs_behavior.py`, `backend/tests/test_cli_behavior.py`, `backend/tests/test_api_behavior.py`

### SC-14 Postgres の schema と repository が本番構成で動く

- 業務上の意味: unit test だけでは見抜けない永続化不整合を防ぐ。
- 入力条件: schema 初期化後に repository / job status の読み書きを行う。
- 期待結果: 本物の DB に対して保存と取得が成功する。
- 主な保証レイヤー: backend integration
- 対応テスト: `backend/tests/test_postgres_smoke.py`, `backend/tests/test_repository_behavior.py`, `backend/tests/test_repository_behavior_extra.py`, `backend/tests/test_job_status_pg_behavior.py`

## Frontend

### FC-01 ダッシュボードで最新日の主要指標を表示する

- 業務上の意味: 利用者が画面を開くだけで最新の業務状況を把握できる。
- 入力条件: summary API が最新日の集計を返す。
- 期待結果: report date、主要カード、不正件数が表示される。
- 主な保証レイヤー: frontend page, E2E
- 対応テスト: `frontend/src/app/page.test.tsx`, `frontend/e2e/tests/dashboard.spec.ts`

### FC-02 日付切替でダッシュボード表示が更新される

- 業務上の意味: 調査対象日を変えたときに、画面がその日の集計へ切り替わる。
- 入力条件: 利用可能日付が複数あり、利用者が別日を選ぶ。
- 期待結果: report date が切り替わる。
- 主な保証レイヤー: frontend page, E2E
- 対応テスト: `frontend/src/app/page.test.tsx`, `frontend/e2e/tests/dashboard.spec.ts`

### FC-03 不正一覧は検索条件に合う行だけを表示する

- 業務上の意味: IP / UA を使った絞り込みで調査を早く進められる。
- 入力条件: 一覧表示後に検索キーワードを入力する。
- 期待結果: 件数表示と表示行が絞り込まれる。
- 主な保証レイヤー: frontend component, E2E
- 対応テスト: `frontend/src/components/suspicious-list-page.test.tsx`, `frontend/e2e/tests/suspicious-clicks.spec.ts`, `frontend/e2e/tests/suspicious-conversions.spec.ts`

### FC-04 不正一覧は詳細を開閉できる

- 業務上の意味: 一覧から詳細調査へ無駄なく進める。
- 入力条件: 一覧行の Details を押す。
- 期待結果: 詳細表示が開き、再度操作すると閉じる。
- 主な保証レイヤー: frontend component, E2E
- 対応テスト: `frontend/src/components/suspicious-list-page.test.tsx`, `frontend/e2e/tests/suspicious-clicks.spec.ts`, `frontend/e2e/tests/suspicious-conversions.spec.ts`

### FC-05 不正一覧の取得失敗は画面上で説明する

- 業務上の意味: API 異常時でも、利用者が障害を認識できる。
- 入力条件: 一覧取得が失敗し、error response が返る。
- 期待結果: エラーメッセージが画面に表示される。
- 主な保証レイヤー: frontend component, frontend API
- 対応テスト: `frontend/src/components/suspicious-list-page.test.tsx`, `frontend/src/lib/api.test.ts`

### FC-06 ダッシュボードは一時的なエラー後に Retry で回復できる

- 業務上の意味: 一過性の API 障害で画面利用を中断させない。
- 入力条件: 初回取得が失敗し、再試行では成功する。
- 期待結果: エラー表示から通常のダッシュボード表示へ戻る。
- 主な保証レイヤー: frontend page
- 対応テスト: `frontend/src/app/page.test.tsx`

### FC-07 日付クイック選択は最新日や今日相当の日付を選べる

- 業務上の意味: よく使う日付への移動を素早く行える。
- 入力条件: quick button または select を操作する。
- 期待結果: 利用可能日付の中から適切な日付が `onChange` に渡る。
- 主な保証レイヤー: frontend component
- 対応テスト: `frontend/src/components/date-quick-select.test.tsx`

### FC-08 最終更新表示は refresh 操作の状態を示す

- 業務上の意味: 画面の鮮度と更新中状態を利用者が判断できる。
- 入力条件: 未更新状態、更新中状態、refresh 操作をそれぞれ発生させる。
- 期待結果: 時刻表示、loading 表示、Refresh ボタン状態が切り替わる。
- 主な保証レイヤー: frontend component
- 対応テスト: `frontend/src/components/last-updated.test.tsx`

### FC-09 不正 CV 画面は CV 件数列を起点に調査へ入れる

- 業務上の意味: click 起点ではなく CV 起点の調査画面へ正しく遷移できる。
- 入力条件: 不正 CV 画面を開く。
- 期待結果: 画面タイトルと CV 件数列が表示される。
- 主な保証レイヤー: frontend page, E2E
- 対応テスト: `frontend/src/app/suspicious/conversions/page.test.tsx`, `frontend/e2e/tests/suspicious-conversions.spec.ts`

## Scenario Mapping

| Scenario ID | 主な保証レイヤー | 対応テスト |
| --- | --- | --- |
| SC-01 | backend unit | `backend/tests/test_suspicious_behavior.py` |
| SC-02 | backend unit | `backend/tests/test_suspicious_behavior.py` |
| SC-03 | backend unit | `backend/tests/test_suspicious_behavior.py` |
| SC-04 | backend unit / API | `backend/tests/test_suspicious_behavior.py`, `backend/tests/test_api_behavior.py` |
| SC-05 | backend unit / frontend page / E2E | `backend/tests/test_reporting_behavior.py`, `frontend/src/app/page.test.tsx`, `frontend/e2e/tests/dashboard.spec.ts` |
| SC-06 | backend unit | `backend/tests/test_reporting_behavior.py` |
| SC-07 | backend unit / frontend component | `backend/tests/test_reporting_behavior.py`, `frontend/src/components/date-quick-select.test.tsx` |
| SC-08 | backend API | `backend/tests/test_api_behavior.py` |
| SC-09 | backend API | `backend/tests/test_api_behavior.py` |
| SC-10 | backend API / service | `backend/tests/test_api_behavior.py`, `backend/tests/test_jobs_behavior.py` |
| SC-11 | backend service / CLI | `backend/tests/test_jobs_behavior.py`, `backend/tests/test_cli_behavior.py` |
| SC-12 | backend unit / API | `backend/tests/test_settings_behavior.py`, `backend/tests/test_api_behavior.py` |
| SC-13 | backend service / CLI / API | `backend/tests/test_jobs_behavior.py`, `backend/tests/test_cli_behavior.py`, `backend/tests/test_api_behavior.py` |
| SC-14 | backend integration | `backend/tests/test_postgres_smoke.py`, `backend/tests/test_repository_behavior.py`, `backend/tests/test_repository_behavior_extra.py`, `backend/tests/test_job_status_pg_behavior.py` |
| FC-01 | frontend page / E2E | `frontend/src/app/page.test.tsx`, `frontend/e2e/tests/dashboard.spec.ts` |
| FC-02 | frontend page / E2E | `frontend/src/app/page.test.tsx`, `frontend/e2e/tests/dashboard.spec.ts` |
| FC-03 | frontend component / E2E | `frontend/src/components/suspicious-list-page.test.tsx`, `frontend/e2e/tests/suspicious-clicks.spec.ts`, `frontend/e2e/tests/suspicious-conversions.spec.ts` |
| FC-04 | frontend component / E2E | `frontend/src/components/suspicious-list-page.test.tsx`, `frontend/e2e/tests/suspicious-clicks.spec.ts`, `frontend/e2e/tests/suspicious-conversions.spec.ts` |
| FC-05 | frontend component / API | `frontend/src/components/suspicious-list-page.test.tsx`, `frontend/src/lib/api.test.ts` |
| FC-06 | frontend page | `frontend/src/app/page.test.tsx` |
| FC-07 | frontend component | `frontend/src/components/date-quick-select.test.tsx` |
| FC-08 | frontend component | `frontend/src/components/last-updated.test.tsx` |
| FC-09 | frontend page / E2E | `frontend/src/app/suspicious/conversions/page.test.tsx`, `frontend/e2e/tests/suspicious-conversions.spec.ts` |