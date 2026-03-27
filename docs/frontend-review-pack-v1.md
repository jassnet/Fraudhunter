# Fraud Checker v2 Frontend Review Pack v1

このファイルは、外部の高度な AI reviewer に `frontend` を集中的にレビューしてもらうためのハンドオフ資料です。

目的は、単なる UI 感想ではなく、以下を前提にした具体的な改善提案を得ることです。

- read-oriented monitoring UI の価値を落とさない
- Render + PostgreSQL の monolith 前提を崩さない
- 既存 API を大きく壊さない
- 日本語 UI を維持する
- デザイン・視認性・保守性・状態管理・運用導線を同時に改善する

---

## 1. Executive Summary

`Fraud Checker v2` の frontend は、affiliate fraud monitoring 用の read-oriented web UI です。

現時点の frontend は、プロトタイプ段階は超えています。

すでにある強み:

- Next.js App Router ベースで小さくまとまっている
- ダッシュボードと不審一覧の責務が明確
- suspicious list は server-side pagination/search/filter/sort 対応済み
- detail は lazy fetch
- masked list / unmasked detail の privacy 境界がある
- URL state sync が入っていて deep link が可能
- design system のたたき台があり、ダーク/ライト切替もある
- unit/component/E2E テストがある

ただし、frontend はまだ「監視 UI として使える」状態であって、「長時間運用に耐える polished monitoring product」とまでは言えません。

特に残課題:

- 一部ファイルで日本語文言の文字化けが残っている
- ダッシュボードと一覧の情報階層がまだ揺れている
- UI state と async state が component/hook に分散していて、今後の拡張境界が少し曖昧
- design system はあるが、コンポーネント実装への浸透がまだ不完全
- analyst / admin / public minimal の access posture 強化に対して frontend 側の振る舞い整理がこれから必要

Current HEAD:

- `c8000a00b641a0f13baa373c922d1052e5a099c0`

---

## 2. Product Role Of The Frontend

この frontend は以下のための画面です。

1. 日次 KPI を見る
2. suspicious findings を一覧で見る
3. finding detail を drill-down する
4. freshness / quality / master sync 状態を見る
5. 一部の admin action の状態を追う

これは BI ツールでも CMS でもなく、監視オペレーション画面です。

そのため、review では次の観点を重視してください。

- 一目で異常が見えるか
- 操作の学習コストが低いか
- analyst が迷わず一覧から detail に降りられるか
- stale / expired / unavailable の状態が誤読されないか
- deep link を共有しても意図どおりに再現できるか

---

## 3. Stack Snapshot

### Runtime

- Next.js `16.1.4`
- React `19.2.0`
- TypeScript
- Tailwind `4`

### Test Stack

- Vitest
- Testing Library
- MSW
- Playwright

### Scripts

from [package.json](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/package.json)

- `npm run dev`
- `npm run build`
- `npm run start`
- `npm run test`
- `npm run test:e2e`

---

## 4. Route / Screen Inventory

### Dashboard

- [page.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/app/page.tsx)

責務:

- selected date の summary を表示
- KPI strip を表示
- 直近推移 chart を表示
- refresh / date change を受ける

依存:

- [use-dashboard-data.ts](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/hooks/use-dashboard-data.ts)
- [overview-chart.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/overview-chart.tsx)
- [metric-strip.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/ui/metric-strip.tsx)
- [page-header.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/ui/page-header.tsx)

### Suspicious Clicks

- [page.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/app/suspicious/clicks/page.tsx)

### Suspicious Conversions

- [page.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/app/suspicious/conversions/page.tsx)

両ページとも共通本体:

- [suspicious-list-page.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/suspicious-list-page.tsx)
- [use-suspicious-list.ts](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/hooks/use-suspicious-list.ts)
- [suspicious-row-details.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/suspicious-row-details.tsx)

責務:

- server-side paginated list を表示
- search / risk / sort / page / date を URL state と同期
- finding key ベースで detail を lazy fetch
- list は masked, detail は unmasked
- evidence expired を UI 上で表現

### Shell / Navigation

- [layout.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/app/layout.tsx)
- [app-shell.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/app-shell.tsx)
- [main-nav.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/main-nav.tsx)
- [mobile-nav.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/mobile-nav.tsx)

責務:

- sidebar open/compact
- dark/light theme toggle
- mobile navigation
- page shell and scroll containment

---

## 5. Current Frontend Architecture

### 5.1 Data Layer

API client は [api.ts](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/lib/api.ts) に集約されています。

特徴:

- `fetchJson()` に retry がある
- summary / daily stats / suspicious list / suspicious detail / dates などが typed wrapper 化されている
- backend の `masked list / unmasked detail` 契約を型として持っている
- `ApiError` と `getErrorMessage()` で表示用エラーを吸収している

現在の課題:

- frontend error semantics が API contract にかなり密結合
- stale / evidence expired / unauthorized / forbidden をより明確な UI 状態へ分ける余地がある
- read auth tier が backend 側で分化したので、それに対応する frontend の表示方針は今後整理が必要

### 5.2 Hook Layer

主要 hook:

- [use-dashboard-data.ts](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/hooks/use-dashboard-data.ts)
- [use-suspicious-list.ts](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/hooks/use-suspicious-list.ts)
- [use-job-runner.ts](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/lib/use-job-runner.ts)

現状の設計:

- dashboard は `dates -> summary/stats` の初期ロードを hook に閉じ込めている
- suspicious list は page, search debounce, selected date, expansion state, result range を hook に持つ
- URL state sync は page component 内で行っている

課題:

- URL state sync が hook 外にあるため、page + hook の責務境界がやや曖昧
- hook が loading/error/refreshing/expandedRow など複数責務を抱え始めている
- list/detail の query lifecycle は良いが、今後 filter 増加時に肥大化しやすい

### 5.3 Component Layer

現在の UI プリミティブ:

- [button.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/ui/button.tsx)
- [input.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/ui/input.tsx)
- [table.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/ui/table.tsx)
- [status-badge.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/ui/status-badge.tsx)
- [section-frame.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/ui/section-frame.tsx)
- [control-bar.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/ui/control-bar.tsx)
- [metric-strip.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/ui/metric-strip.tsx)
- [page-header.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/ui/page-header.tsx)
- [empty-state.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/ui/empty-state.tsx)

意図している方向:

- card 多用を避ける
- 黒ベースの監視画面
- 線と余白で整理
- 数値・状態・表を主役にする

実態としての課題:

- design system のルールはあるが、細部の class 設計は page local に残っている
- Japanese copy と tracking/uppercase の相性が悪い箇所がある
- `section-frame` / `control-bar` / `metric-strip` の一貫性は改善途上
- chart が視覚言語としてやや簡素で、監視画面としての signal strength が弱い

---

## 6. Current API Contracts Used By Frontend

### Summary

- `GET /api/summary`

主に使用している payload:

- `date`
- `stats.clicks.total`
- `stats.clicks.unique_ips`
- `stats.conversions.total`
- `stats.suspicious.click_based`
- `stats.suspicious.conversion_based`
- `quality.last_successful_ingest_at`
- `quality.click_ip_ua_coverage`
- `quality.conversion_click_enrichment`
- `quality.findings.findings_last_computed_at`
- `quality.findings.stale`
- `quality.master_sync.last_synced_at`

### Daily Stats

- `GET /api/stats/daily`

用途:

- dashboard chart

### Dates

- `GET /api/dates`

用途:

- dashboard/suspicious list 共通の日付選択

### Suspicious List

- `GET /api/suspicious/clicks`
- `GET /api/suspicious/conversions`

query:

- `date`
- `limit`
- `offset`
- `search`
- `risk_level`
- `sort_by`
- `sort_order`
- `include_details`
- `mask_sensitive`

list semantics:

- masked IP / UA
- paginated
- server-side filtered
- evidence availability fields included

### Suspicious Detail

- `GET /api/suspicious/clicks/{finding_key}`
- `GET /api/suspicious/conversions/{finding_key}`

detail semantics:

- unmasked values
- joined detail rows
- expired evidence では full evidence を返さない contract に移行済み

### Job Status

- analyst 向け sanitized endpoint
- admin 向け full endpoint が backend にはある

frontend 側の導線は今後の整理対象

---

## 7. Current UX / Visual Direction

Current design direction is documented in [design-system.md](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/docs/design-system.md).

意図:

- Sharp Operations
- dark-first monitoring UI
- light mode も token 共有で対応
- 線中心
- operational copy を短く保つ
- status color は risk/state のみに強く使う

frontend reviewer に見てほしい論点:

- いまの design system が実装と一致しているか
- KPI / chart / table / detail / nav が一貫した hierarchy を持てているか
- light mode が dark-first の副産物で破綻していないか
- monitoring UI として視線誘導が十分か

---

## 8. Known Frontend Problems

### 8.1 Mojibake / UTF-8 Regression

これは重要です。

現在の frontend 実ファイルには、日本語文言が正常な箇所と文字化けしている箇所が混在しています。

確認できる例:

- [page.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/app/page.tsx)
- [suspicious-list-page.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/suspicious-list-page.tsx)
- [use-dashboard-data.ts](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/hooks/use-dashboard-data.ts)
- [app-shell.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/app-shell.tsx)
- [overview-chart.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/overview-chart.tsx)

この問題は cosmetic ではなく、以下に影響します。

- UX trust
- accessibility labels
- tests readability
- design review の精度
- copy consistency

reviewer には、まずこの encoding/copy regression をどう安全に直すべきかを見てほしいです。

### 8.2 Page-Level State Boundaries

suspicious list の状態は概ね良いですが、責務境界はやや曖昧です。

例:

- hook が query state と fetch lifecycle を持つ
- page が URL state sync を持つ
- detail cache は page local

このままでも動きますが、以下が起きやすいです。

- filter/sort の増加で hook が膨らむ
- route shareability 追加時に page と hook の責務がずれる
- future admin actions を list page に足すと複雑化する

### 8.3 Visual Hierarchy Is Better Than Before But Still Uneven

現状は以前よりかなり改善されていますが、まだ uneven です。

特に:

- dashboard KPI の signal strength
- chart の存在感
- table header / row / expanded detail の hierarchy
- dark mode での secondary/faint text の使い分け

### 8.4 Frontend Access-State UX Is Not Fully Modeled Yet

backend は `public minimal / analyst / admin` に分かれ始めています。

frontend ではまだ十分にモデル化されていません。

今後の論点:

- unauthorized / forbidden の扱い
- admin-only action/status の出し分け
- analyst UI の最小 exposure

### 8.5 Job-Oriented UX Is Still Thin

production model は enqueue-only durable jobs です。

しかし frontend はまだ fully job-aware ではありません。

潜在論点:

- manual sync の enqueue 後 UX
- polling / progress / success / failure visibility
- analyst 向けに queue state をどう見せるか

---

## 9. Current Testing Posture

### Unit / Component

examples:

- [page.test.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/app/page.test.tsx)
- [suspicious-list-page.test.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/suspicious-list-page.test.tsx)
- [suspicious-row-details.test.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/suspicious-row-details.test.tsx)
- [api.test.ts](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/lib/api.test.ts)

Recent passing state:

- `npm test`: 24 passed

### E2E

files:

- [dashboard.spec.ts](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/e2e/tests/dashboard.spec.ts)
- [suspicious-clicks.spec.ts](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/e2e/tests/suspicious-clicks.spec.ts)
- [suspicious-conversions.spec.ts](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/e2e/tests/suspicious-conversions.spec.ts)

coverage focus:

- dashboard rendering
- suspicious list filtering/search
- detail expand
- URL state sync

reviewer に見てほしい点:

- 現状テストで何が十分か
- 何が弱いか
- visual regression を入れるべきか
- job-oriented UX を足すならどの層にテストを足すべきか

---

## 10. Concrete Review Questions For The External AI

以下に、generic advice ではなく、この frontend に対して具体的に答えてください。

1. 現在の frontend architecture を `Critical / High / Medium` で診断してください。
2. `今すぐ直すべき構造課題` と `まだ後回しでよい課題` を切り分けてください。
3. `small PR units` で 4〜6 本の改善計画を出してください。
4. `mojibake / UTF-8` をどう直すのが最も安全か、実ファイル単位で提案してください。
5. `dashboard` と `suspicious list` の state boundary をどう整理するのがよいか提案してください。
6. design system を今のまま育てるべきか、component contract を再定義すべきか提案してください。
7. `analyst / admin / public minimal` を frontend でどう扱うべきか提案してください。
8. `job-aware UX` を入れるなら、どの画面に何を最小で出すべきか提案してください。
9. `masked list / unmasked detail / evidence expired` の UX が適切かレビューしてください。
10. `URL state sync` の現実装が十分か、別の state model へ寄せるべきか提案してください。
11. 追加すべき tests を component / integration / E2E に分けて提案してください。
12. additive migration を前提に、backend の今後の contract changes に frontend が耐える形を提案してください。

---

## 11. Constraints For The Reviewer

必ず守ってほしい前提:

- monolith 維持
- backend API は可能な限り後方互換維持
- Japanese UI 維持
- Render 前提
- frontend は monitoring surface のまま進化
- generic な SPA 再設計案は不要
- micro-frontend, GraphQL, Redux 導入などの飛躍は不要

望ましい提案の性質:

- concrete file-level change proposals
- state boundary の具体整理
- design system の運用ルール
- small PR sequence
- rollback と test plan を含む

---

## 12. Suggested Reviewer Prompt

以下をそのまま外部 AI に渡せます。

```text
You are a principal/staff frontend engineer reviewing a production-oriented monitoring UI inside a Render + PostgreSQL monolith.

Read this frontend review pack and the repository if available.

Your job is to propose the next safe improvement phase for the frontend.

Important constraints:
- Keep the monolith.
- Keep Next.js + React + TypeScript.
- Keep the UI in Japanese.
- Keep the frontend as a read-oriented monitoring surface.
- Preserve existing API contracts where possible.
- Do not propose generic rewrites or unnecessary framework churn.

Focus on:
- correctness
- maintainability
- UX clarity
- accessibility
- observability of async/admin actions
- security/privacy boundaries in the UI
- design system consistency
- mojibake / UTF-8 correctness

Output format:
1. Critical / High / Medium diagnosis
2. What to do now vs later
3. 4-6 small PR plan
4. File-level changes
5. UI contract changes
6. Test plan
7. Rollback plan

Then propose PR1 in concrete detail.
```

---

## 13. Files The Reviewer Should Prioritize

Start here:

- [page.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/app/page.tsx)
- [suspicious-list-page.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/suspicious-list-page.tsx)
- [use-dashboard-data.ts](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/hooks/use-dashboard-data.ts)
- [use-suspicious-list.ts](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/hooks/use-suspicious-list.ts)
- [api.ts](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/lib/api.ts)
- [app-shell.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/app-shell.tsx)
- [overview-chart.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/overview-chart.tsx)
- [metric-strip.tsx](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/frontend/src/components/ui/metric-strip.tsx)
- [design-system.md](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/docs/design-system.md)

If the reviewer wants backend context, then read:

- [ai-architecture-review-pack-v3.md](/C:/Users/kayu0/OneDrive/ドキュメント/仕事用/Dev/fraud-checkerv2/docs/ai-architecture-review-pack-v3.md)

