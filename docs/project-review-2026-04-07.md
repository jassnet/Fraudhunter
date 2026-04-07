# Fraud Checker 総合レビュー

レビュー日: 2026-04-07  
対象: `C:\Users\user\Documents\working\Dev\fraudchecker` のリポジトリ一式  
前提: 実運用トラフィック、実DBサイズ、Render 上の実際の監視設定、Secrets 管理ポリシー、SLO、監査要件は未確認です。未確認事項は `不明` または `要確認` と明記します。負荷や将来破綻リスクは一部 `推測` を含みます。

## A. エグゼクティブサマリー

- 全体評価  
  このプロジェクトは「Render + PostgreSQL + durable job + read-heavy console」という方針がかなり明確で、特に backend のジョブ制御、runtime guard、health 情報、テストの厚みは強いです。一方で、console の read path が徐々に重くなっており、UI と API が現行運用規模には十分でも、データ量増加・チーム拡大・継続運用の観点では詰めが甘い箇所があります。最大の論点は、`alert 一覧/ダッシュボードの計算を request time に寄せすぎていること`、`read access posture が設定依存で fail-open 寄りに見えること`、`CI/CD とドキュメントが現実のコードに追いついていないこと` です。
- 最も重要な懸念トップ5
  1. アラート一覧がページングなしで全件取得・全件描画されており、backend は `status_counts` を全件で返すために `status=None` で一覧を読んだうえで Python 側で status を再フィルタしています。設計意図は理解できるものの、スケール耐性は低いです。根拠: `backend/src/fraud_checker/services/console.py:80-119`, `backend/src/fraud_checker/services/console.py:242-250`, `backend/src/fraud_checker/services/console.py:259-287`, `frontend/src/features/console/alerts-screen.tsx:126-153`, `frontend/src/features/console/alerts-screen.tsx:301-415`
  2. 被害推定額や impacted conversions の算出が read path で raw データ再突合・価格推定をしており、履歴の再現性と性能の両方で不安がある。根拠: `backend/src/fraud_checker/services/console.py:35-65`, `backend/src/fraud_checker/services/console.py:324-442`, `README.md:51-57`, `README.md:129-133`, `README.md:490-505`
  3. production では startup 時に read posture の未宣言は弾かれますが、`FC_EXTERNAL_READ_PROTECTION=true` の場合は保護をインフラ側に委ねており、アプリ内部では追加検証をしていません。さらに frontend proxy は read token 不在時に admin token へフォールバックします。根拠: `backend/src/fraud_checker/api_dependencies.py:81-109`, `backend/src/fraud_checker/runtime_guards.py:22-68`, `frontend/src/lib/server/backend-proxy.ts:10-29`
  4. CI が実質未整備で、テスト資産があっても継続的に自動検証されていない。根拠: `.github/workflows` 配下に workflow ファイルが見当たらないこと、`frontend/package.json:8-16`
  5. console read path に migration 相当の処理と防御的な存在確認が残っており、リクエストごとの DDL チェックと schema 存在確認が発生します。根拠: `backend/src/fraud_checker/services/console.py:88`, `backend/src/fraud_checker/services/console.py:123`, `backend/src/fraud_checker/services/console.py:169`, `backend/src/fraud_checker/services/console.py:208`, `backend/src/fraud_checker/services/console.py:235`, `backend/src/fraud_checker/services/console.py:291`, `backend/src/fraud_checker/services/console.py:326`, `backend/src/fraud_checker/services/console.py:517`, `backend/src/fraud_checker/services/console.py:538`, `backend/src/fraud_checker/services/console.py:572`, `backend/src/fraud_checker/services/console.py:790-794`
- 良い点トップ5
  1. 「enqueue-only + queue runner + Postgres queue」という運用制約に即したアーキテクチャ判断が一貫している。根拠: `README.md:6-7`, `render.yaml:47-153`, `backend/src/fraud_checker/services/jobs.py:157-218`, `backend/src/fraud_checker/services/jobs.py:346-420`
  2. runtime guard があり、production で危険な設定を禁止しているのは良い。根拠: `backend/src/fraud_checker/runtime_guards.py:54-68`
  3. health API が freshness、master sync、queue metrics まで返しており、運用で必要な一次情報が揃っている。根拠: `backend/src/fraud_checker/api_routers/health.py:25-70`, `backend/src/fraud_checker/api_routers/health.py:88-176`
  4. backend テストの厚みが高く、job/repository/runtime guard/settings/reporting まで広くカバーしている。根拠: `backend/tests/` 配下のテスト群、特に `test_jobs_behavior.py`, `test_reporting_behavior.py`, `test_runtime_guards_behavior.py`, `test_repository_behavior.py`, `test_console_api_behavior.py`
  5. ログが JSON に正規化され、少なくとも request timing と job lifecycle は追いやすい。根拠: `backend/src/fraud_checker/api.py:64-77`, `backend/src/fraud_checker/logging_utils.py:22-34`
- 今すぐ直すべき点
  1. alerts API にページング・件数制限・server-side grouping/filtering を入れる
  2. read access posture を fail-closed に寄せ、frontend proxy の admin fallback を廃止または明示 opt-in にする
  3. CI で backend/frontend の test・lint・typecheck を必須化する
  4. 被害推定額を findings 生成時に snapshot して、read path で再構成しない方向へ寄せる
  5. `fraud_alert_reviews` の schema 作成を migration 管理へ移し、console の request path から `create_all` と過剰な `_table_exists()` を外す
- 今は見送ってよい点
  1. マイクロサービス分割
  2. 過度な DI フレームワーク導入
  3. リアルタイム push 更新
  4. 高度な A/B テスト基盤
  5. 分散キューへの移行

## B. スコアカード

| 項目 | 点数 | 一言理由 |
| --- | --- | --- |
| コード品質 | 4/5 | backend は整理されているが、console service に read-time 複雑性が寄っている。 |
| 設計 | 3/5 | durable job と監視設計は良い一方、console read path と frontend data flow は設計不足。 |
| セキュリティ | 3/5 | guard は良いが、read 認可の fail-open 寄り挙動と proxy の admin fallback が気になる。 |
| パフォーマンス | 2/5 | 現状規模なら動くが、alerts 一覧と damage 再計算はスケールで詰まりやすい。 |
| UI/UX | 3/5 | 最低限の監視 UI は成立しているが、初回表示・URL 共有性・a11y は改善余地が大きい。 |
| ビジネス適合性 | 4/5 | fraud monitoring の実務フローに近いが、歴史的な金額信頼性と triage 指標が不足。 |
| 運用保守性 | 3/5 | health と queue は良いが、CI/alerting/runbook 不足で継続運用が属人化しやすい。 |
| テスト | 4/5 | backend は強い。ただし E2E と CI 接続、ドキュメント同期が弱い。 |
| 開発体験 | 3/5 | ローカル実行性は悪くないが、typecheck/CI/workflow が不足し、ドキュメントも古い。 |
| 総合評価 | 3/5 | 良い基盤はあるが、「このまま増築すると壊れる箇所」がはっきり見え始めている。 |

## C. 詳細レビュー

### 1. alerts 一覧が全件取得・全件描画になっている

- 観点: パフォーマンス / API / UI / 運用保守
- 重要度: High
- 問題: alerts API がページングなしで全件返し、backend 側は `status_counts` を全件で返すために `status=None` で一覧を引いてから Python 側で status を再フィルタしています。`_fetch_alert_rows()` 自体は SQL レベルで status を絞れるので、現状は「できない」のではなく「counts のために意図的にそうしている」実装です。frontend も受け取った全件を group 化してテーブル描画しています。
- 根拠: `backend/src/fraud_checker/services/console.py:80-119`, `backend/src/fraud_checker/services/console.py:242-250`, `backend/src/fraud_checker/services/console.py:259-287`, `frontend/src/features/console/alerts-screen.tsx:63-114`, `frontend/src/features/console/alerts-screen.tsx:126-153`, `frontend/src/features/console/alerts-screen.tsx:301-415`
- 影響: データ量増加時に API レイテンシ、DB 負荷、ネットワーク転送量、ブラウザ描画負荷が同時に悪化します。レビュー担当者が「最近 7 日」などで絞った瞬間に UX が重くなる構造です。
- 推奨アクション: `status_counts` は別の集計クエリに分離し、本体一覧クエリには `status` を SQL レベルで適用してください。そのうえで `limit/offset` か cursor pagination を追加し、grouping も server-side に寄せるべきです。少なくとも初期表示は `latest 100` など上限を持つべきです。
- トレードオフ: server-side grouping は API 形状を変えるため frontend 修正が要ります。ただし今のうちに直した方が変更コストは低いです。
- 実装コスト感: M
- 優先度: P0

### 2. 被害推定額の算出が read path に寄りすぎている

- 観点: 設計 / データ整合性 / ビジネス適合性 / パフォーマンス
- 重要度: High
- 問題: dashboard と alerts が raw transaction を request time に再突合し、足りない分は同日同案件の観測単価や固定 fallback で補っています。これは表示時点の DB 状態に依存し、履歴の再現性が弱いです。
- 根拠: `backend/src/fraud_checker/services/console.py:35-65`, `backend/src/fraud_checker/services/console.py:324-442`, `backend/src/fraud_checker/services/console.py:445-481`, `README.md:51-57`, `README.md:129-133`, `README.md:490-505`
- 影響: 「なぜ昨日見た金額と今日見た金額が違うのか」を説明しづらくなります。raw retention 切れや join 不一致時の補完ロジックで、監査性とユーザー信頼を損ないやすいです。
- 推奨アクション: findings 生成時に `transaction_count`, `estimated_damage`, `unit_price_source`, `evidence_snapshot` を保存し、console read path は snapshot を読むだけに寄せるのが本筋です。
- トレードオフ: findings schema 拡張と backfill が必要です。ただし long-term では性能・説明責任・保守性が大幅に改善します。
- 実装コスト感: M
- 優先度: P0

### 3. read access posture が fail-open に見えやすい

- 観点: セキュリティ / 認可 / 運用
- 重要度: High
- 問題: production では `validate_runtime_guards()` により read posture の未宣言は startup で弾かれるため、そこ自体は fail-open ではありません。実際の問題は、`FC_EXTERNAL_READ_PROTECTION=true` の場合に保護をアプリ外へ委譲しており、アプリ内部では追加の read 認可検証をしていないことです。さらに frontend proxy は read token が無い場合 admin token にフォールバックします。
- 根拠: `backend/src/fraud_checker/api_dependencies.py:81-109`, `backend/src/fraud_checker/runtime_guards.py:22-68`, `frontend/src/lib/server/backend-proxy.ts:10-29`
- 影響: インフラ側の保護が外れた場合に read API が意図せず露出するリスクがあります。frontend 側の read 経路に admin token が混ざるのも least privilege に反します。
- 推奨アクション: `FC_EXTERNAL_READ_PROTECTION=true` のときは app 側でも専用ヘッダや internal secret を検証する、または frontend から必ず `FC_READ_API_KEY` を使わせ、read 経路で admin token を使わないようにするべきです。
- トレードオフ: ローカル開発は少し面倒になります。ただし本番安全性と設定ミス耐性は上がります。
- 実装コスト感: S
- 優先度: P0

### 4. CI が実質未整備

- 観点: CI/CD / テスト / チーム開発 / セキュリティ
- 重要度: High
- 問題: backend/frontend にテスト資産はあるのに、GitHub Actions などの workflow が確認できませんでした。
- 根拠: `.github/workflows` 配下に workflow ファイルが見当たらないこと、`frontend/package.json:8-16`
- 影響: テストの価値がローカル依存になり、回帰が mainline に入りやすくなります。dependency scan、SAST、migration safety check も回りません。
- 推奨アクション: 最低限 `backend pytest`, `frontend vitest`, `eslint`, `tsc --noEmit`, `alembic upgrade --sql` または migration smoke を PR 必須にするべきです。
- トレードオフ: CI 実行時間と整備コストは増えますが、今の段階では ROI が非常に高いです。
- 実装コスト感: M
- 優先度: P0

### 5. request path に `create_all()` が残っている

- 観点: 設計 / パフォーマンス / 運用保守 / データ
- 重要度: High
- 問題: `get_dashboard`, `list_alerts`, `get_alert_detail`, `apply_review_action` の入口で `_ensure_review_schema()` が呼ばれ、その中で `fraud_alert_reviews` に対して `Base.metadata.create_all()` を実行しています。これは migration で管理すべき関心であり、request path に置くべきではありません。
- 根拠: `backend/src/fraud_checker/services/console.py:36`, `backend/src/fraud_checker/services/console.py:88`, `backend/src/fraud_checker/services/console.py:123`, `backend/src/fraud_checker/services/console.py:169`, `backend/src/fraud_checker/services/console.py:790-794`
- 影響: リクエストごとに DDL チェックが走る構造になり、レイテンシ悪化と運用責務の混濁を招きます。migration 不整合を request path で隠す設計にもなります。
- 推奨アクション: `fraud_alert_reviews` を Alembic migration へ移し、`_ensure_review_schema()` は削除してください。起動時検証が欲しいなら migration version check を health または startup で行う方が安全です。
- トレードオフ: 初回導入時に migration 配布が必要になりますが、責務分離と安全性の改善効果が大きいです。
- 実装コスト感: S
- 優先度: P0

### 6. `_table_exists()` の防御的チェックが多すぎる

- 観点: 設計 / パフォーマンス / 技術的負債
- 重要度: Medium
- 問題: console read path の複数箇所で `repo._table_exists()` を都度呼んでいます。migration が正常である前提なら、request ごとの存在確認は防御的すぎます。
- 根拠: `backend/src/fraud_checker/services/console.py:208`, `backend/src/fraud_checker/services/console.py:235`, `backend/src/fraud_checker/services/console.py:291`, `backend/src/fraud_checker/services/console.py:326`, `backend/src/fraud_checker/services/console.py:517`, `backend/src/fraud_checker/services/console.py:538`, `backend/src/fraud_checker/services/console.py:572`
- 影響: code path が増えて複雑になり、schema 不整合の本質的な問題を見えにくくします。パフォーマンスコストは小さくても、設計上のノイズが継続的に効きます。
- 推奨アクション: migration 前提に寄せて `_table_exists()` を整理し、必要なら startup/health で schema 完備をまとめて検証してください。
- トレードオフ: 互換モードや部分導入時の柔軟性は落ちますが、本番運用と保守性は改善します。
- 実装コスト感: S
- 優先度: P1

### 7. review のバッチ更新が 1 件ずつ実行されている

- 観点: パフォーマンス / API / 保守性
- 重要度: Medium
- 問題: `apply_review_action()` が transaction 内で finding ごとに `conn.execute()` を繰り返しています。件数が増えると N 件分の round-trip 相当になります。
- 根拠: `backend/src/fraud_checker/services/console.py:161-193`
- 影響: 一括 review 件数が増えたときに無駄な DB overhead が出ます。将来的に bulk triage を強めるとボトルネックになりやすいです。
- 推奨アクション: SQLAlchemy の executemany 相当、または複数 VALUES の一括 upsert に変更してください。
- トレードオフ: SQL の見通しは少し複雑になりますが、処理効率と将来余力は改善します。
- 実装コスト感: S
- 優先度: P1

### 8. ドキュメントと実装のズレが大きい

- 観点: ドキュメント / Team Scalability / プロダクト整合性
- 重要度: Medium
- 問題: README は suspicious clicks / suspicious conversions 一覧の存在を前提に書かれていますが、現行ナビは dashboard と alerts の 2 画面です。business test scenarios も古いテストパスを多数参照しています。
- 根拠: `README.md:27-35`, `README.md:38-45`, `frontend/src/components/app-frame.tsx:66-69`, `docs/business-test-scenarios.md:24-27`, `docs/business-test-scenarios.md:73-114`
- 影響: 新規メンバーやレビュー担当者が誤った mental model を持ちやすく、保守判断を誤ります。監査や顧客説明でも不信につながります。
- 推奨アクション: README の画面説明、テスト戦略、business scenario を現行 UI とテスト資産に同期させてください。古い画面は削除済みか planned かを明記するべきです。
- トレードオフ: 直接売上にはつながりませんが、将来の認知コストを大きく下げます。
- 実装コスト感: S
- 優先度: P1

### 9. frontend が全面的に client fetch 依存で初回体験が弱い

- 観点: UI/UX / パフォーマンス / SEO不要でも体感品質
- 重要度: Medium
- 問題: dashboard、alerts、detail がいずれも mount 後 fetch で描画されます。server component や route-level data fetch を使っていないため、初回表示は空 + loading になりがちです。
- 根拠: `frontend/src/features/console/dashboard-screen.tsx:60-92`, `frontend/src/features/console/alerts-screen.tsx:126-153`, `frontend/src/features/console/alert-detail-screen.tsx:31-62`
- 影響: 監視ツールとして重要な「開いた瞬間に状況が見える」体験が弱くなります。ネットワークが悪いと操作感が落ち、ユーザーは更新失敗と誤解しやすいです。
- 推奨アクション: dashboard と alerts は server component で初期データを埋め、client side では再読込とレビュー操作だけに絞るのがよいです。
- トレードオフ: React/Next の責務分離が少し複雑になりますが、UX と体感性能は改善します。
- 実装コスト感: M
- 優先度: P1

### 10. filter 状態が URL と同期しておらず共有性が低い

- 観点: UI/UX / Product / 運用
- 重要度: Medium
- 問題: alerts の status/date/sort はコンポーネント state のみで保持され、URL query に反映されません。
- 根拠: `frontend/src/features/console/alerts-screen.tsx:117-159`, `frontend/src/features/console/alerts-screen.tsx:224-263`
- 影響: 「この条件で見て」と URL 共有できず、オペレーション連携や問い合わせ対応の効率が落ちます。
- 推奨アクション: Next router の search params に同期させ、初期値も URL から読むべきです。
- トレードオフ: 実装は少し増えますが、監視ツールでは非常にコスパの良い改善です。
- 実装コスト感: S
- 優先度: P1

### 11. a11y と操作性の詰めが甘い

- 観点: UI/UX / アクセシビリティ
- 重要度: Medium
- 問題: mobile overlay に focus trap や Escape close が見えず、グループ選択の checkbox も indeterminate 表現がありません。table 内 accordion もスクリーンリーダーにはやや厳しい構造です。
- 根拠: `frontend/src/components/app-frame.tsx:98-121`, `frontend/src/features/console/alerts-screen.tsx:170-194`, `frontend/src/features/console/alerts-screen.tsx:333-409`
- 影響: キーボード操作性と認知負荷が悪化し、業務利用時の操作ミスにつながります。
- 推奨アクション: dialog/drawer のキーボード制御、group checkbox の indeterminate、expand row の `aria-controls` 付与を入れてください。
- トレードオフ: デザイン変更は小さく、主に実装の詰め作業です。
- 実装コスト感: S
- 優先度: P2

### 12. health/queue の observability は良いが、アラート設計までは見えない

- 観点: 運用保守 / SRE / Observability
- 重要度: Medium
- 問題: health API で freshness、master sync age、queue metrics まで返せている一方、どの値に対して alert を飛ばすか、SLO/SLI をどう定義するかは repo 上で確認できませんでした。
- 根拠: `backend/src/fraud_checker/api_routers/health.py:25-70`, `backend/src/fraud_checker/api_routers/health.py:88-176`
- 影響: 監視ツール自体が stale になっても、人が見に行くまで気づけない運用になりやすいです。
- 推奨アクション: `latest_data_date lag`, `findings.stale`, `oldest_queued_age_seconds`, `failed_jobs_count`, `master_sync.age_hours` に閾値を定義し、監視連携するべきです。Runbook も必要です。
- トレードオフ: 監視ノイズの調整が必要です。
- 実装コスト感: M
- 優先度: P1

### 13. backend の layered abstraction はやや厚いが、現時点では概ね正当化できる

- 観点: オーバーエンジニアリング / 設計
- 重要度: Low
- 問題: `RuntimeDependencies`、Protocol 群、split repository、facade repository は小規模プロジェクトとしてはやや厚く見えます。
- 根拠: `backend/src/fraud_checker/service_dependencies.py:33-59`, `backend/src/fraud_checker/service_protocols.py:7-82`, `backend/src/fraud_checker/repository_pg.py:14-21`
- 影響: 学習コストは増えます。ただし job、ACS、DB、settings の差し替えテストが多い現状では、完全に無駄とは言えません。
- 推奨アクション: ここは大きく削るより、「console service の read-time 複雑性」と「frontend data layer」の方を優先して簡素化すべきです。Protocol を増やしすぎないガードレールだけ決めれば十分です。
- トレードオフ: simplification しすぎるとテスト差し替えのしやすさが落ちます。
- 実装コスト感: S
- 優先度: P3

### 14. 一方で console service は under-engineered

- 観点: 設計 / SRP / 複雑度 / 将来破綻リスク
- 重要度: High
- 問題: console service が dashboard KPI 計算、alert 一覧整形、transaction summary 復元、価格補完、review 更新を広く抱え、責務が肥大化しています。
- 根拠: `backend/src/fraud_checker/services/console.py:35-193`, `backend/src/fraud_checker/services/console.py:324-481`
- 影響: 仕様変更が入るたびに同ファイルへロジックが集まり、テストとレビューの認知負荷が上がります。
- 推奨アクション: `alert_read_model`, `damage_estimation`, `review_write_service` に分割し、read model を SQL view/materialization 方向へ寄せるのがよいです。
- トレードオフ: 分割だけ先にやると見た目のファイル数だけ増えるので、責務境界の再設計とセットでやるべきです。
- 実装コスト感: M
- 優先度: P1

### 15. API 契約として一覧系の拡張性が低い

- 観点: API / Integration / 将来拡張
- 重要度: Medium
- 問題: alerts API に pagination/filter/sort は一応ありますが、返却は単一 `items` 配列のみで cursor や page metadata がありません。dashboard/alerts/detail も versioning 戦略が repo 上では見えません。
- 根拠: `backend/src/fraud_checker/api_routers/console.py:17-64`, `backend/src/fraud_checker/services/console.py:103-119`
- 影響: consumer が増えると後方互換性を保ちにくくなります。UI の要求変化にも API が追随しづらいです。
- 推奨アクション: 少なくとも `page`, `page_size`, `total`, `has_next` を入れ、将来は `/api/console/v1/...` を検討してください。
- トレードオフ: URL 変更は consumer coordination が必要です。ただし今はまだ小さいので着手しやすいです。
- 実装コスト感: S
- 優先度: P2

### 16. rate limiting / abuse 対策が見えない

- 観点: セキュリティ / 運用
- 重要度: Medium
- 問題: repo 上では read API や review API に対する rate limiting、burst control、WAF 前提の記述が見当たりませんでした。
- 根拠: review 対象コード上で確認できず、不明。`backend/src/fraud_checker/api.py`, `backend/src/fraud_checker/api_routers/console.py` に該当実装は見当たらない。
- 影響: 公開範囲設定を誤った場合に scraping や brute-force 的アクセスに弱くなります。admin review API も token 漏えい時の blast radius が大きいです。
- 推奨アクション: Render 側の edge 制御があるなら明文化し、なければ app 側または proxy 側で rate limiting を入れてください。
- トレードオフ: 誤検知で正規オペレーションを止めない調整が必要です。
- 実装コスト感: M
- 優先度: P1

### 17. logging はよいが、structured trace / correlation は不足

- 観点: 運用保守 / 障害解析
- 重要度: Low
- 問題: JSON logging はありますが、request ID、job lineage ID、user action correlation が全経路で揃っているわけではありません。
- 根拠: `backend/src/fraud_checker/api.py:64-77`, `backend/src/fraud_checker/logging_utils.py:22-34`, `backend/src/fraud_checker/services/jobs.py:203-213`, `backend/src/fraud_checker/services/jobs.py:377-420`
- 影響: 「この refresh 操作がどの recompute に繋がり、どの findings 更新に反映されたか」を追いづらい場面が残ります。
- 推奨アクション: `request_id`, `job_run_id`, `generation_id`, `finding_key` を横断的に相関できる log fields を定義してください。
- トレードオフ: ログ項目が増えますが、MTTR 改善効果が高いです。
- 実装コスト感: S
- 優先度: P2

### 18. テスト方針は良いが、戦略と実体の同期が弱い

- 観点: テスト品質 / ドキュメント / DevEx
- 重要度: Medium
- 問題: backend のテスト層は厚い一方、business scenarios と frontend E2E の記述が古いです。`frontend/package.json` にも `test:e2e` がありません。
- 根拠: `docs/business-test-scenarios.md:24-27`, `docs/business-test-scenarios.md:73-114`, `frontend/package.json:8-16`
- 影響: 「E2E がある想定」で安心してしまい、実際には守られていない振る舞いが出ます。
- 推奨アクション: 現状のテストマップを更新し、存在しないテスト参照は除去してください。必要なら最小 1 本の smoke E2E を復活させて CI に接続すべきです。
- トレードオフ: E2E は flaky になりやすいので、数を増やしすぎない方が良いです。
- 実装コスト感: S
- 優先度: P1

### 19. durable job 周りは、この規模では「残すべき複雑性」

- 観点: 設計 / 運用 / Over-engineering Check
- 重要度: Low
- 問題: 一見複雑に見えるが、ここは過剰設計とまでは言いにくいです。
- 根拠: `render.yaml:47-153`, `backend/src/fraud_checker/services/jobs.py:157-218`, `backend/src/fraud_checker/services/jobs.py:346-420`, `backend/src/fraud_checker/api_routers/health.py:46-70`
- 影響: Render の cron/timeout 前提では、in-request 処理より durable queue の方が安全です。
- 推奨アクション: queue 自体は維持し、むしろ metrics/alerting/runbook を強化してください。
- トレードオフ: 実装理解コストはありますが、障害時の blast radius を抑えやすいです。
- 実装コスト感: S
- 優先度: P3

## D. オーバーエンジニアリング診断

- 過剰設計と思われる箇所
  - `RuntimeDependencies` + Protocol + facade repository の三層は、現状の人数・規模だけ見ると少し厚いです。根拠: `backend/src/fraud_checker/service_dependencies.py:33-59`, `backend/src/fraud_checker/service_protocols.py:7-82`, `backend/src/fraud_checker/repository_pg.py:14-21`
  - ただしこれは「過剰だが有害」とまでは言いません。backend テストの差し替え容易性を実際に支えています。
- 逆に設計不足の箇所
  - console read model は不足です。alert 一覧と damage estimation を都度組み立てるのは under-engineering です。根拠: `backend/src/fraud_checker/services/console.py:35-119`, `backend/src/fraud_checker/services/console.py:324-481`
  - frontend data layer は不足です。URL state、pagination、SSR 初期データ、retry/cancel が無く、今後の機能追加に弱いです。根拠: `frontend/src/lib/console-api.ts:18-90`, `frontend/src/features/console/alerts-screen.tsx:117-153`
  - migration で担保すべき schema 存在を request path の `create_all()` と `_table_exists()` で吸収しているのも under-engineering です。根拠: `backend/src/fraud_checker/services/console.py:208`, `backend/src/fraud_checker/services/console.py:235`, `backend/src/fraud_checker/services/console.py:291`, `backend/src/fraud_checker/services/console.py:326`, `backend/src/fraud_checker/services/console.py:790-794`
- シンプル化案
  - alerts を server-side paginated/grouped read model にする
  - damage は findings snapshot に寄せる
  - frontend は server-rendered initial fetch + URL search params に寄せる
  - schema 存在確認は migration + startup/health へ寄せ、request path から除去する
  - backend dependency abstraction は現状維持しつつ、新規 Protocol 増殖を抑える
- 将来拡張を見据えて残すべき複雑性
  - Postgres queue の dedupe / concurrency key / stale recovery
  - runtime guards による本番設定チェック
  - health endpoint の freshness/queue/master sync 指標
  - findings lineage に基づく stale 判定

## E. セキュリティレビュー要約

- 想定される脅威
  - read API の意図しない露出
  - admin token の過剰利用
  - scraping / abuse / credential misuse
  - alert detail からの情報露出
  - 設定ミス起因の認可崩れ
- 攻撃面（attack surface）
  - backend public endpoints: `/api/console/*`, `/api/health/public`
  - frontend server proxy
  - admin review action
  - refresh / master sync 系の admin action
- 重大なリスク
  - High: production では posture 宣言は強制されるが、`FC_EXTERNAL_READ_PROTECTION` 時の実防御が infra 依存で、アプリ内部には追加 read 認可が無い。根拠: `backend/src/fraud_checker/api_dependencies.py:81-109`, `backend/src/fraud_checker/runtime_guards.py:22-68`
  - High: read path で admin token fallback があり least privilege に反する。根拠: `frontend/src/lib/server/backend-proxy.ts:20-29`
  - Medium: request path に `create_all()` が残っており、migration の不整合を実行時に吸収しようとしている。根拠: `backend/src/fraud_checker/services/console.py:790-794`
  - Medium: rate limiting / abuse 対策が repo 上では不明
  - Medium: historical damage reconstruction により audit explanation が難しい
  - Low: CORS は allow origins 明示で wildcard ではないが、credentials 許可のため origin 管理は要継続確認。根拠: `backend/src/fraud_checker/api.py:40-55`
- すぐに入れるべき防御
  - read API は read token 必須に寄せる
  - frontend proxy で admin fallback をやめる
  - admin/review/refresh に rate limiting と audit log を追加する
  - auth posture の integration test を追加する
  - Render 側の WAF / private ingress / secret rotation 方針を README に明文化する
- 追加で必要なテストや監査
  - `FC_EXTERNAL_READ_PROTECTION=true` 時の期待挙動テスト
  - read token 不在時に frontend proxy が失敗することのテスト
  - 権限別 API contract test
  - dependency scan, secret scan, SAST
  - Render 側の ingress / environment / secret 管理の運用監査

## F. ビジネス優先度付き改善提案

### 高インパクト / 低工数

- alerts 一覧に pagination と server-side filtering を導入する  
  理由: 画面体感と DB 負荷に直結し、オペレーション効率をすぐ改善できる。
- read access posture を fail-closed に寄せる  
  理由: 事故コストが高く、修正規模は小さい。
- `fraud_alert_reviews` の migration を追加し、request path から `create_all()` を除去する  
  理由: 設計のねじれを小コストで解消できる。
- README / test scenario / package scripts を現実に合わせて更新する  
  理由: チームの誤解コストをすぐ減らせる。
- filters を URL と同期する  
  理由: オペレーション連携、問い合わせ再現、レビュー共有がしやすくなる。
- `tsc --noEmit` と CI workflow を追加する  
  理由: 回帰防止 ROI が高い。

### 高インパクト / 高工数

- findings 生成時に damage snapshot と evidence snapshot を保存する  
  理由: 金額の説明責任と履歴信頼性が大きく向上する。
- triage KPI を追加する  
  候補: confirmed fraud rate, median review latency, stale findings count, damage by affiliate  
  理由: 監視ツールとしての「意思決定価値」が上がる。
- minimum E2E + CI/CD + deploy guard を整える  
  理由: 継続運用の事故率を下げる。
- console read model を再設計する  
  理由: 今後の機能追加コストを下げる。

### 低インパクト / 低工数

- mobile drawer の a11y 改善
- group checkbox の indeterminate 対応
- review 一括更新を executemany 化する
- loading / refreshing 文言の見直し
- package scripts に `typecheck` と `test:e2e` の実態整備
- Python / Node バージョン記述の整合性調整  
  根拠: `backend/pyproject.toml:10`, `README.md:63-80`, `render.yaml:10-11`, `render.yaml:42-43`

## G. 出力フォーマット注記

- 元の依頼テンプレートでは `F` の次が `H` で、`G` 自体が定義されていませんでした。
- 初版レビューではそのテンプレートに従って `G` を省略しました。
- ただし番号が飛ぶ理由を明記しなかったのは不親切だったため、この注記を追加しています。

### 低インパクト / 高工数

- マイクロサービス分割
- リアルタイムストリーミング更新
- 汎用 plugin/extension 機構
- 複数 tenant を前提にした大規模権限モデル  
  これらは現時点では opportunity cost が高く、後回しでよいです。

## H. 追加で確認したい情報

- 本番の read access posture は実際にどのモードで運用しているか
- Render 側で private networking / IP allowlist / WAF / rate limit を使っているか
- 実際の `suspicious_conversion_findings` 件数と alerts 画面の典型検索期間
- 被害推定額を監査・請求・営業判断のどこまで正式に使うか
- false positive / false negative をどう測っているか
- review 操作の監査要件の有無
- on-call 体制、障害時エスカレーション、Runbook の有無
- E2E を落とした理由が「不要」なのか「壊れているから」なのか
- マスタ単価の信頼できるソースが別に存在するか
- 個人情報区分と retention 方針が法務・契約上どこまで定義されているか
