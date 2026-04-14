# FraudChecker ビジネス/要件/ユーザビリティ レビュー 2026-04-13

> **レビュー対象**: yuma2004 ブランチ HEAD
> **レビュー観点**: ビジネス要件の充足度、実際の運用フローにおける使い勝手、要件の矛盾や漏れ
> **調査方法**: ローカル起動した画面（dashboard / alerts / alert detail / review dialog / algorithm）の実地確認、frontend/backend/render.yaml/tests のコードレビュー、2026-04-08 総合レビューとの差分確認
> **前提**: 2026-04-13 時点の実装を基準とし、すでに修正済みの項目は末尾で整理する

---

## A. エグゼクティブサマリー

FraudChecker は、`不正検知 -> トリアージ -> レビュー記録` まではかなり形になっている。特にアラート一覧の case-centric な構造、詳細画面での証拠表示、レビュー理由の必須化、アルゴリズム説明画面は、日常の目視レビューを回すための土台として十分に機能している。

一方で、**business 運用として「誰が、何を、どこまで処理したか」を安定して回すにはまだ足りない**。現状は「単独オペレーターの調査補助ツール」としては使えるが、「複数人で backlog を追い、支払停止や報告までつなぐ運用基盤」としては未完成。

優先度が高い論点は次の3点。

1. **`critical` フィルターがデッド UI**。画面では「重大」を選べるが、バックエンドは `critical` を生成しないため常に 0 件になる。
2. **ダッシュボード/一覧のデフォルトが最新 finding 日だけ**。過去日の `unhandled` が自然に隠れ、朝の巡回で backlog を見落としやすい。
3. **`confirmed_fraud` が後続業務に接続されていない**。レビュー状態と監査履歴は残るが、支払保留・Slack 通知・担当アサインなどの運用アクションにつながらない。

### 改善提案の全体像

| カテゴリ | P0 (即時修正) | P1 (早期改善) | P2 (中期改善) | P3 (将来検討) |
|----------|:---:|:---:|:---:|:---:|
| データ整合性 / 要件整合 | 2 | 2 | 1 | - |
| トリアージ効率 | 1 | 5 | 4 | 1 |
| レビュー運用 | - | 2 | 4 | 2 |
| UI/表示 | - | 3 | 3 | 2 |
| 運用可視性 / 連携 | - | 1 | 3 | 2 |

---

## B. 実際の運用フローに沿った問題点

### B-1. フロー1: 朝の巡回チェック（ダッシュボード確認）

**想定シナリオ**: 運用担当者が朝にダッシュボードを開き、未対応 backlog と昨夜の新着を確認する。

#### B-1-1. [P1] ダッシュボードと一覧のデフォルトが最新 finding 日だけ

- **問題**: ダッシュボードは `get_dashboard()` で `resolved_date` 1 日分のみを集計し、アラート一覧も `_resolve_alert_window()` により日付未指定時は最新 finding 日 1 日分に固定される。
- **該当箇所**: `backend/src/fraud_checker/services/console.py:51-71`, `console.py:120-155`, `console.py:428-456`
- **実地確認**: `GET /api/console/alerts?status=unhandled&sort=risk_desc&page=1&page_size=5` の `applied_filters` が `start_date=end_date=2026-04-09` になり、未対応 backlog が 1 日に閉じていた。
- **ビジネスインパクト**: 過去日に検出された `unhandled` が朝の巡回で見えない。backfill で過去日が再検出されたケースも自然に埋もれる。
- **推奨**: 既定表示を「全期間の未対応」または「直近7日 + 未対応優先」に変更。日付フィルターは任意指定にする。

#### B-1-2. [P1] 日付セレクターが UI に存在しない

- **問題**: バックエンドは `target_date` と `available_dates` に対応しているが、フロントエンドは `getDashboard()` を固定 URL で呼ぶだけで日付切替 UI を持たない。
- **該当箇所**: `backend/src/fraud_checker/api_routers/console.py:24-27`, `backend/src/fraud_checker/services/console.py:92-105`, `frontend/src/lib/console-api.ts:53-55`, `frontend/src/features/console/dashboard-screen.tsx:160-163`
- **ビジネスインパクト**: API はあるのに過去日の確認ができず、オペレーターは「今日の一枚絵」しか見られない。
- **推奨**: `available_dates` を使った日付ドロップダウンを追加し、URL パラメータで共有可能にする。

#### B-1-3. [P1] 優先ケースが人間向けではなく、しかも説明どおりの並びになっていない

- **問題**: 優先ケースパネルは `case_key` をそのままリンク表示している。`case_key` は `date + ip + ua` の SHA-256 ハッシュで、人間には意味がない。さらにパネル説明は「リスクと想定被害額から優先度」とあるが、実際の並びは `risk_desc` のみで damage は使っていない。
- **該当箇所**: `frontend/src/features/console/dashboard-screen.tsx:254-277`, `backend/src/fraud_checker/services/findings.py:21-31`, `backend/src/fraud_checker/services/console.py:54-60`, `console.py:73-85`
- **実地確認**: ローカル画面では `6c1f0505...` のような 64 文字ハッシュが優先ケースの主見出しとして並んでいた。
- **ビジネスインパクト**: 優先順位づけの初速が落ちる。`誰のどの案件か` が一目で分からず、また description と実装が食い違うため信頼感も下がる。
- **推奨**: リンク主見出しを `affiliate + program + primary_reason` または `IP + date` に変更し、case_key は補助情報に落とす。ランキング順は `risk_score` と `estimated_damage` の複合スコアに変更する。

#### B-1-4. [P2] 想定被害額 KPI が全ステータス合算

- **問題**: `estimated_damage` は `items` 全件の `reward_amount` を合算しており、`white` や `confirmed_fraud` を除外していない。
- **該当箇所**: `backend/src/fraud_checker/services/console.py:67-71`
- **ビジネスインパクト**: 経営報告や日次共有で「まだリスクが残っている金額」と誤読されやすい。
- **推奨**: `unhandled + investigating`、または `confirmed_fraud` のように用途別 KPI を分ける。

#### B-1-5. [P2] 「更新」ボタンの影響範囲が UI から読めない

- **問題**: ボタンラベルは単に「更新」だが、実際には `hours=1` の refresh + detect を起動する。
- **該当箇所**: `frontend/src/features/console/dashboard-screen.tsx:170-176`, `frontend/src/lib/console-api.ts:57-67`, `backend/src/fraud_checker/api_routers/console.py:147-168`
- **ビジネスインパクト**: 管理者が「再読込」のつもりで押し、意図せず検知再計算を走らせるリスクがある。
- **推奨**: 「データ再取得」にラベル変更し、対象範囲をツールチップまたは補助文で明示する。

#### B-1-6. [P2] キュー表示はあるが、失敗の drill-down と次回自動実行が見えない

- **問題**: ダッシュボードはキュー件数と最新ジョブ ID しか出さず、失敗理由や cron の次回実行時刻は表示しない。
- **該当箇所**: `frontend/src/features/console/dashboard-screen.tsx:225-250`, `render.yaml:55-161`
- **ビジネスインパクト**: 管理者は「失敗したこと」は分かっても、何を見れば直るのかが分からない。定常運用の監視としては弱い。
- **推奨**: 失敗ジョブ詳細の panel、次回 cron 実行時刻、直近失敗メッセージを表示する。

---

### B-2. フロー2: アラートトリアージ（一覧画面での仕分け作業）

**想定シナリオ**: 運用担当者が未対応ケースを上から確認し、優先順位を付けながら処理を進める。

#### B-2-1. [P0] 「重大(critical)」フィルターがデッド UI

- **問題**: UI には `critical` があるが、バックエンドのリスク計算は `high` / `medium` / `low` の 3 段階しか生成しない。
- **該当箇所**:
  - `frontend/src/features/console/alerts-screen.tsx:273-286`
  - `frontend/src/components/console-ui.tsx:214-225`
  - `backend/src/fraud_checker/api_presenters.py:197-230`
- **ビジネスインパクト**: オペレーターが「重大」を選ぶと常に 0 件になり、重大案件がないと誤認する。
- **推奨**: バックエンドに `critical` を追加するか、フロントエンドから削除して 3 段階に統一する。

#### B-2-2. [P1] 一括レビューがページ内だけで、ページサイズも固定的

- **問題**: 一括レビュー対象は現在ページの `items.map((item) => item.case_key)` のみ。表示件数は 50 固定で、UI から変更できない。
- **該当箇所**: `frontend/src/features/console/alerts-screen.tsx:40-48`, `alerts-screen.tsx:226-228`, `alerts-screen.tsx:390-419`
- **ビジネスインパクト**: 低リスク案件をまとめて処理したいときに、ページ送りと同じ操作を繰り返す必要がある。
- **推奨**: 「現在のフィルター条件に一致する全件を対象」の bulk action を追加するか、100 / 200 件表示を選べるようにする。

#### B-2-3. [P1] 被害額順ソートがない

- **問題**: ソート条件は `risk_desc`, `risk_asc`, `detected_desc`, `detected_asc` の 4 種のみ。
- **該当箇所**: `backend/src/fraud_checker/services/console.py:518-523`
- **ビジネスインパクト**: 高額ケースから先に処理したい運用に対応できない。
- **推奨**: `damage_desc`, `damage_asc` を追加する。

#### B-2-4. [P2] 検索対象が UI から分からない

- **問題**: プレースホルダーは「アフィリエイト、IP、UA」だが、実装上は `search_text` に program 名、media 名、formatted reasons まで入っている。
- **該当箇所**: `frontend/src/features/console/alerts-screen.tsx:311-320`, `backend/src/fraud_checker/services/console.py:481-489`, `backend/src/fraud_checker/services/findings.py:39-40`, `findings.py:230-237`
- **ビジネスインパクト**: 実際には便利な検索ができるのに、ユーザーが使いこなせない。逆に「何がヒットしたのか」が分かりづらい。
- **推奨**: プレースホルダーを「アフィリエイト名、案件名、IP、UA、検知理由」で明示する。

#### B-2-5. [P2] ページネーション文言が英語混在

- **問題**: 一覧下部の件数表示が `total, showing X-Y` のまま。
- **該当箇所**: `frontend/src/features/console/alerts-screen.tsx:458-463`
- **実地確認**: ローカル画面でも `8 total, showing 1-8` が表示された。
- **ビジネスインパクト**: 完成度の低さを感じさせ、運用ツールへの信頼を落とす。
- **推奨**: `全 {total} 件中 {start}-{end} 件を表示` に統一する。

---

### B-3. フロー3: ケース調査（詳細画面での証拠確認）

**想定シナリオ**: 担当者が高リスクケースを開き、証拠と周辺情報を見て判定する。

#### B-3-1. [P1] 証拠トランザクションのステータスが raw code

- **問題**: 詳細画面は `transaction.state` をそのまま表示する。実データでは `"1"` が返っており、画面にもそのまま出る。
- **該当箇所**: `frontend/src/features/console/alert-detail-screen.tsx:81-89`, `backend/src/fraud_checker/services/console.py:1133-1140`
- **実地確認**: `GET /api/console/alerts/{case_key}` の `evidence_transactions[].state` が `"1"` で返っていた。
- **ビジネスインパクト**: 証拠の意味が一目で分からず、判定コストが上がる。
- **推奨**: ACS の state コードを `承認`, `保留`, `却下` などのラベルに変換する。

#### B-3-2. [P1] レビュー履歴のステータスだけ英語生値

- **問題**: 画面全体は `StatusBadge` で日本語化しているのに、レビュー履歴表だけ `confirmed_fraud`, `investigating` を raw で表示する。
- **該当箇所**: `frontend/src/features/console/alert-detail-screen.tsx:258-264`, `frontend/src/components/console-ui.tsx:9-14`
- **ビジネスインパクト**: 監査用の履歴ほど読みづらいという逆転が起きている。
- **推奨**: 履歴表でも `StatusBadge` か同じラベルマッピングを使う。

#### B-3-3. [P1] 内部キーが強すぎて、判断材料より目立つ

- **問題**: `ケース識別子` と `検知キー` が summary card と sidebar の両方で強く表示される。一方で、判断に使う理由や関連対象は相対的に弱い。
- **該当箇所**: `frontend/src/features/console/alert-detail-screen.tsx:204-208`, `alert-detail-screen.tsx:326-343`
- **ビジネスインパクト**: オペレーターの視線が内部 ID に奪われ、判断材料への到達が遅れる。
- **推奨**: case key / finding key は「メタ情報」セクションに寄せ、上部は `理由 / 被害額 / 対象` を優先表示する。

#### B-3-4. [P2] アフィリエイト横断の調査導線がない

- **問題**: 影響アフィリエイトは見えるが、そのアフィリエイトが関わる別ケースへ遷移する導線がない。
- **該当箇所**: `frontend/src/features/console/alert-detail-screen.tsx:41-54`, `alert-detail-screen.tsx:223-233`
- **ビジネスインパクト**: 日をまたぐ少量不正や横断的な不正パターンを追いにくい。
- **推奨**: affiliate ID / name から一覧へフィルター遷移できるようにする。

#### B-3-5. [P2] `affiliate_recent_transactions` が単一 affiliate ケースにしか出ない

- **問題**: `affected_affiliates` が 1 件のときだけ補足テーブルを返す。
- **該当箇所**: `backend/src/fraud_checker/services/console.py:242-247`
- **ビジネスインパクト**: 複数 affiliate 関与ケースほど補足情報が減る。
- **推奨**: 主 affiliate を 1 つ選んで出すか、affiliate ごとにタブ切替で表示する。

#### B-3-6. [P2] 証拠テーブルにページネーションがない

- **問題**: 証拠トランザクションも affiliate recent も全件 DOM 展開。
- **該当箇所**: `frontend/src/features/console/alert-detail-screen.tsx:57-95`, `alert-detail-screen.tsx:236-281`
- **ビジネスインパクト**: 取引が多いケースほど画面が重くなり、スクロール負荷が増える。
- **推奨**: 初回 20 件 + `さらに表示` にする。

---

### B-4. フロー4: レビュー判定（ステータス変更）

**想定シナリオ**: 担当者がケースを `不正確定` / `ホワイト` / `調査中` に更新し、その後続を回す。

#### B-4-1. [P1] `confirmed_fraud` が review state 更新で止まる

- **問題**: `apply_review_action()` は review state / review event を書き込むだけで、支払保留・報告・通知などの downstream action を起こさない。
- **該当箇所**: `backend/src/fraud_checker/services/console.py:294-349`, `backend/src/fraud_checker/repositories/suspicious_findings_write.py:83-168`
- **ビジネスインパクト**: 「見つけたが止めていない」状態になりやすい。運用基盤としてはここが最重要。
- **推奨**: `confirmed_fraud` 時に Slack/Webhook、支払保留キュー、または「次のアクション」チェックリストを必ず出す。

#### B-4-2. [P1] 担当者アサイン / ownership がない

- **問題**: 履歴には `reviewed_by` が残るが、`誰が今持っているか` は持たない。
- **該当箇所**: `backend/src/fraud_checker/services/console.py:27`, `console.py:328-331`, `frontend/src/lib/console-types.ts:130-161`
- **ビジネスインパクト**: 複数人運用で重複対応と取りこぼしが起きやすい。
- **推奨**: `assignee` を追加する。短期的には一覧に「最終操作者」を出すだけでもよい。

#### B-4-3. [P2] レビュー理由に定型語彙がない

- **問題**: 理由は常に自由記述で、よくある判定理由のプリセットや taxonomy がない。
- **該当箇所**: `frontend/src/features/console/review-reason-dialog.ts:80-87`, `frontend/src/components/console-ui.tsx:183-204`
- **ビジネスインパクト**: 入力負荷が高く、理由の表記ゆれで後分析しにくい。
- **推奨**: プリセット + 自由記述の併用にする。

#### B-4-4. [P2] Analyst には「なぜ操作できないか」が表示されない

- **問題**: 詳細画面のレビュー操作は `viewerRole === "admin"` のときだけ出る。Analyst 側には説明メッセージがない。
- **該当箇所**: `frontend/src/features/console/alert-detail-screen.tsx:285-316`
- **ビジネスインパクト**: 権限制御が UI 不具合に見える。
- **推奨**: 「レビュー操作には Admin 権限が必要です」を sidebar に表示する。

#### B-4-5. [P3] SLA / 対応期限の概念がない

- **問題**: `何日放置された未対応か` を UI 上で追えない。
- **推奨**: ダッシュボードに `3日以上未対応件数` と oldest unhandled age を出す。

---

### B-5. フロー5: データ更新と運用管理

**想定シナリオ**: 管理者がジョブを起動し、成功/失敗と次回実行を把握する。

#### B-5-1. [P2] 失敗ジョブの詳細を UI で辿れない

- **問題**: ダッシュボードは `failed` 件数しか出さず、どの job が何故失敗したかを表示しない。
- **該当箇所**: `frontend/src/features/console/dashboard-screen.tsx:239-249`
- **ビジネスインパクト**: 障害時に運用者が自己解決できず、結局ログ調査に戻る。
- **推奨**: 失敗ジョブ一覧と message の drill-down を追加する。

#### B-5-2. [P2] 自動実行スケジュールがコンソールから見えない

- **問題**: 毎時 refresh、6 時間ごと backfill、毎日 master sync があるが、次回実行時刻は UI で見えない。
- **該当箇所**: `render.yaml:55-161`
- **ビジネスインパクト**: 「待てば次で入るのか」「手動実行すべきか」の判断がしづらい。
- **推奨**: データ鮮度 panel に次回予定時刻を出す。

#### B-5-3. [P3] 毎分 worker 起動の運用コスト

- **問題**: `fraudchecker-queue-runner-minute` は毎分 `pip install .` を伴って起動する。
- **該当箇所**: `render.yaml:136-161`
- **ビジネスインパクト**: ジョブがなくてもコストが乗る。障害切り分けも複雑になる。
- **推奨**: 常駐 worker、または軽量チェック方式へ寄せる。

---

## C. データ整合性 / 要件整合の問題

### C-1. [P0] アルゴリズム説明画面のデフォルト単価がコードと不一致

| 項目 | 画面表示 | コード実装 | 一致 |
|------|----------|-----------|:---:|
| デフォルト単価 | ¥5,000 | `DEFAULT_REWARD_YEN = 3000` | **不一致** |
| 高リスク閾値 | 65点以上 | `score >= 65` | 一致 |
| 中リスク閾値 | 30-64点 | `score >= 30` | 一致 |
| 低リスク閾値 | 30点未満 | else | 一致 |

- **該当箇所**: `frontend/src/features/console/algorithm-screen.tsx:258-274`, `backend/src/fraud_checker/constants.py:1-3`
- **ビジネスインパクト**: 被害額の説明責任が崩れる。監査・営業報告・ASP 連携で矛盾が出る。
- **推奨**: 画面か定数のどちらかを即時修正し、説明と実装を一致させる。

### C-2. [P0] フロントエンドの `critical` とバックエンドの 3 段階リスクの不整合

フロントエンドでは `critical` が以下で存在している。

- `frontend/src/lib/console-types.ts` で型として許容
- `frontend/src/features/console/alerts-screen.tsx:282` でフィルター表示
- `frontend/src/components/console-ui.tsx:214-225` で `score >= 90` を critical tone として描画

しかし、バックエンドの `calculate_risk_level()` は `high` / `medium` / `low` のみ返す。

- **該当箇所**: `backend/src/fraud_checker/api_presenters.py:197-230`
- **実際の影響**: `risk_level=critical` の検索は 0 件。`RiskBadge` だけが critical 見た目になり、データ値は `high` のまま。
- **推奨**: backend を 4 段階化するか、frontend を 3 段階へ戻す。どちらかを選んで統一する。

### C-3. [P1] 優先ケースの説明文と実装がずれている

- **問題**: パネル説明は「リスクと想定被害額から優先度」とあるが、backend は `risk_desc` 並びの上位 10 件をそのまま返している。
- **該当箇所**: `frontend/src/features/console/dashboard-screen.tsx:254-277`, `backend/src/fraud_checker/services/console.py:54-60`, `console.py:73-85`
- **ビジネスインパクト**: オペレーターは「被害額を考慮した優先順位」だと信じて使うが、実装はそうなっていない。
- **推奨**: 説明文を実装に合わせるか、実装を複合スコアに変える。

### C-4. [P1] 検索 UI の説明と実装がずれている

- **問題**: 画面は `アフィリエイト、IP、UA` だけが検索対象に見えるが、実際には program 名・media 名・理由文も検索可能。
- **該当箇所**: `frontend/src/features/console/alerts-screen.tsx:311-320`, `backend/src/fraud_checker/services/findings.py:230-237`
- **ビジネスインパクト**: せっかくの検索力が使われず、ユーザー教育コストが増える。
- **推奨**: プレースホルダーとヘルプを実装に合わせる。

---

## D. 権限 / ロールの使い勝手

### D-1. [P2] 現在のユーザー名とロールが画面に出ない

- **問題**: サイドバーはナビゲーションのみで、現在の role を表示しない。
- **該当箇所**: `frontend/src/components/app-frame.tsx:77-205`
- **ビジネスインパクト**: 権限差のある画面で「なぜできないか」が分かりにくい。
- **推奨**: footer にユーザー名 + ロールバッジを追加する。

### D-2. [P2] 設定 API はあるが、コンソールから辿れない

- **問題**: backend には admin-only の `/api/settings` があるが、frontend の nav には settings 導線がなく、`frontend/src/app/settings/` も空。
- **該当箇所**: `backend/src/fraud_checker/api_routers/settings.py:10-20`, `frontend/src/components/app-frame.tsx:77-80`
- **ビジネスインパクト**: しきい値管理の土台はあるのに、現場から触れず死蔵されている。
- **推奨**: 少なくとも admin 向けに settings 画面を接続する。

### D-3. [P3] ロールが実質 2 段階のみ

- **問題**: `analyst` と `admin` の二択で、中間権限がない。
- **ビジネスインパクト**: 「レビューだけできるが refresh は禁止」のような運用に対応しづらい。
- **推奨**: 将来的に RBAC 拡張を検討する。

---

## E. 検知ロジックのビジネス観点での課題

### E-1. [P1] 複数日にまたがる低頻度不正に弱い

- **問題**: case の単位が `date + ip + ua` でハッシュ化されるため、同一環境が毎日少量ずつ CV を発生させるパターンは日単位に分断される。
- **該当箇所**: `backend/src/fraud_checker/services/findings.py:30-31`
- **ビジネスインパクト**: 高度な不正ほど「毎日は小さく見える」ので取り逃しやすい。
- **推奨**: `過去 N 日の累積 CV` と `同一 affiliate の cross-day 集計` を補助指標で出す。

### E-2. [P2] 誤検知率のフィードバックループがない

- **問題**: `white` と `confirmed_fraud` の比率がダッシュボードで見えず、ルール改善の判断材料がない。
- **該当箇所**: `backend/src/fraud_checker/services/console.py:92-105`, `frontend/src/features/console/dashboard-screen.tsx:207-217`
- **ビジネスインパクト**: 運用していても精度が改善しない。
- **推奨**: `white / confirmed_fraud / investigating` を使った精度 KPI を追加する。

### E-3. [P2] しきい値の保存基盤はあるのに UI 未接続

- **問題**: backend には settings 保存・versioning・findings 再計算まであるが、frontend 側から触れない。
- **該当箇所**: `backend/src/fraud_checker/services/settings.py:157-209`, `backend/src/fraud_checker/repositories/settings.py:25-74`, `backend/src/fraud_checker/api_routers/settings.py:13-20`, `frontend/src/components/app-frame.tsx:77-80`
- **ビジネスインパクト**: 運用で閾値調整したい場面でも、結局コードや環境変数に戻る。
- **推奨**: admin 向け settings UI を優先度高めで接続する。

---

## F. UI/UX の細かい問題

### F-1. [P1] レビューダイアログの確定ボタン色が常に warning

- **問題**: `不正確定` でも confirm button は一律 `tone="warning"`。
- **該当箇所**: `frontend/src/components/console-ui.tsx:197-204`, `frontend/src/features/console/review-reason-dialog.ts:28-36`
- **ビジネスインパクト**: 危険度の高い操作の視覚差が弱い。
- **推奨**: `confirmed_fraud` は danger tone にする。

### F-2. [P2] 推定 / 実績の区別が小さなバッジだけ

- **問題**: 一覧では金額そのものは同じ見え方で、推定か実績かは小さな badge に依存する。
- **該当箇所**: `frontend/src/features/console/alerts-screen.tsx:442-447`
- **ビジネスインパクト**: 金額の確からしさを見落としやすい。
- **推奨**: 推定値は金額色・アイコン・脚注を強める。

### F-3. [P3] テーブル中心でモバイルの優先順位づけが弱い

- **問題**: 一覧も詳細も table 中心で、モバイル時の情報優先度再構成が弱い。
- **該当箇所**: `frontend/src/features/console/alerts-screen.tsx:380-481`, `frontend/src/features/console/alert-detail-screen.tsx:57-95`
- **推奨**: モバイルはカード化や重要列の折りたたみを検討する。

### F-4. [P3] キーボードショートカットがない

- **問題**: 反復レビュー向けの `j/k`、`f` などの移動・判定ショートカットがない。
- **推奨**: 中長期でショートカットを追加する。

---

## G. テスト / レビューの盲点

### G-1. [P1] `critical` 不整合がテスト fixture で温存されている

- **問題**: dashboard / alerts / alert detail の component test が `risk_level: "critical"` を普通に流している。
- **該当箇所**: `frontend/src/features/console/dashboard-screen.test.tsx:26-35`, `frontend/src/features/console/alerts-screen.test.tsx:92-99`, `frontend/src/features/console/alert-detail-screen.test.tsx:35-41`
- **ビジネスインパクト**: 実データでは起きない状態を前提に UI が育ち、dead UI が残りやすい。
- **推奨**: backend 実装に合わせて fixture を `high/medium/low` に揃える。`critical` を採用するなら backend 側も変える。

### G-2. [P2] 実データの transaction state 表示崩れをテストが拾えない

- **問題**: detail test は `approved` / `pending` を使っており、実 API の `"1"` のような値を想定していない。
- **該当箇所**: `frontend/src/features/console/alert-detail-screen.test.tsx:44-67`
- **ビジネスインパクト**: 画面上は読めない状態でもテストが通る。
- **推奨**: numeric code を含む fixture を追加し、ラベル変換をテストする。

### G-3. [P2] UX レベルの要件がテストで担保されていない

- **問題**: 日本語 pagination 文言、優先ケースの可読性、date selector の有無、failed job drill-down などはテスト観点に乗っていない。
- **該当箇所**: `docs/business-test-scenarios.md:39-77`, `frontend/src/features/console/dashboard-screen.test.tsx`, `alerts-screen.test.tsx`
- **ビジネスインパクト**: business UX の退行が検知しづらい。
- **推奨**: 文言・可読性・運用導線を含む scenario test を足す。

---

## H. 今回確認できた良い点

- **一覧は case-centric で、URL 同期もできている**。`status / risk / date / search / page` が URL に反映され、共有可能な triage link として機能する。`frontend/src/features/console/alerts-screen.tsx:78-109`, `alerts-screen.tsx:185-189`
- **レビュー理由は frontend/backend の両方で必須化されている**。誤操作防止と監査性の観点では良い。`frontend/src/features/console/review-reason-dialog.ts:80-87`, `backend/src/fraud_checker/services/console.py:305-309`
- **詳細画面の証拠・関連対象・履歴は揃っている**。FC-05 の土台は満たしている。`frontend/src/features/console/alert-detail-screen.tsx:211-281`
- **アルゴリズム説明画面は非エンジニアにも説明しやすい**。ルールベースであること、スコア、被害額の考え方が見える。`frontend/src/features/console/algorithm-screen.tsx:75-289`

---

## I. 優先アクションプラン

### 即時修正 (P0)

| # | 問題 | 修正方針 |
|---|------|----------|
| C-1 | デフォルト単価 5,000 円 / 3,000 円の不一致 | 画面か定数を即時統一 |
| C-2 | `critical` dead UI | backend を 4 段階化するか frontend を 3 段階へ統一 |

### 早期改善 (P1)

| # | 問題 | 修正方針 |
|---|------|----------|
| B-1-1 | 最新 finding 日しか見えない | 既定表示を backlog 対応に変える |
| B-1-2 | ダッシュボード日付切替なし | `available_dates` を UI 接続 |
| B-1-3 | 優先ケースが hash 表示かつ damage 未反映 | 人間向けラベル + 複合優先度へ変更 |
| B-3-1 | transaction state が raw code | 状態ラベル変換を追加 |
| B-4-1 | `confirmed_fraud` が後続業務につながらない | 通知 / 保留 / checklist のいずれかを接続 |
| B-4-2 | assignee がない | ownership を導入 |

### 中期改善 (P2)

| # | 問題 | 修正方針 |
|---|------|----------|
| B-2-2 | bulk review がページ内だけ | 全件対象 bulk action または page size 選択 |
| B-2-3 | damage sort なし | `damage_desc/asc` 追加 |
| B-2-4 | 検索対象が不明 | プレースホルダーとヘルプを明確化 |
| B-5-1 | failed job 詳細なし | 失敗一覧 / エラー詳細 panel |
| D-2 / E-3 | settings backend 未接続 | admin 向け settings 画面接続 |
| E-2 | 誤検知率の可視化なし | review 結果 KPI 追加 |

---

## J. 2026-04-08 総合レビューからの変化

前回レビューで指摘していた項目のうち、今回の確認で解消済み / 依然残存を整理する。

| 前回の論点 | 現在の状態 | 補足 |
|-----------|:---:|------|
| ダッシュボードに case ranking が出ていない | **解消** | `frontend/src/features/console/dashboard-screen.tsx:254-285` |
| console query failure が空配列 / 0 件に潰れる | **解消** | `backend/src/fraud_checker/services/console.py:531-547`, `backend/src/fraud_checker/api_routers/console.py:30-32` |
| queue payload 名称不整合 | **概ね解消** | UI と API で `queued/running/failed` は揃った |
| デフォルト単価の不一致 | **未解消** | `algorithm-screen.tsx:272`, `constants.py:3` |
| `critical` dead UI | **未解消** | frontend は存在、backend は未生成 |
| 最新 finding 日だけが既定表示 | **未解消** | dashboard / alerts の両方で残存 |
| レビュー後の業務接続不足 | **未解消** | 今回の business 観点で重要度が上がった |

---

> レビュー実施日: 2026-04-13
> レビュー対象: yuma2004 ブランチ HEAD
> レビュー観点: ビジネス要件の充足度、実際の運用フローにおける使い勝手、要件の矛盾や漏れ
