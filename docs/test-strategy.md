# 古典派テスト戦略

このリポジトリでは、テストを「実装の組み立て方を当てるもの」ではなく「利用者が観測できる結果と状態変化を保証するもの」として扱う。backend と frontend のどちらでも、business 要件を起点にテストを置き、内部 collaborator の呼び出し順や回数よりも、返却値、永続化結果、画面表示、HTTP レスポンスを優先して検証する。

## 基本原則

- business 要件からテストケースを作る。
- unit test は複雑な判定、集計、整形、境界条件に集中させる。
- 薄い CRUD や SQL の読み書き確認は integration test に集約する。
- HTTP、DB、外部 API、ブラウザ境界だけをテストダブル化する。
- 内部 collaborator の `spy`、呼び出し順、呼び出し回数は原則として検証しない。
- 同じ business 要件を unit、component、E2E で三重に保証しない。
- テスト名は日本語で「何を保証するか」が読める粒度にそろえる。
- 構成は `Given / When / Then` または `Arrange / Act / Assert` を守る。

## レイヤーごとの責務

### Unit Test

- 複雑な business rule を最短距離で確認する。
- 例: 不正クリック判定、不正 CV 判定、集計ロジック、設定の fallback。
- 外部依存は fake repository、fake store、fake client で隔離する。

### Integration Test

- Postgres schema、repository、job status 永続化を本物の DB で確認する。
- SQL の where 条件や upsert 結果は unit test ではなく integration test で保証する。
- 1 件の repository method を unit と integration の両方で重複確認しない。

### API Contract Test

- HTTP status、入力検証、認可、payload shape、整形済み表示値を確認する。
- service 内部の helper 呼び出し順ではなく、外から見えるレスポンスを検証する。
- 差し替えが必要な場合は service 戻り値を fake で与えて contract を固定する。

### Component / Page Test

- ユーザーが画面で観測する表示、入力、検索、ページング、詳細表示、エラー回復を確認する。
- hook や helper の内部状態は直接見ない。
- callback を検証する場合も、コンポーネントの公開契約として必要な最小限にとどめる。

### E2E Test

- 日次運用で重要な business flow を最終確認する。
- 画面単体テストと同じ枝葉の条件を重ねず、代表シナリオに絞る。

## テストダブルの方針

- fake repository / fake store / fake client を優先する。
- `monkeypatch` や `vi.fn()` は外部境界の置き換えに限定する。
- component test で API helper の内部実装は観測しない。
- MSW は frontend の HTTP 境界を表現する用途に限定する。

## 命名と配置

- backend は `*_behavior.py` を継続し、business wording を test 名に反映する。
- frontend は `describe` と `it` を日本語で書き、業務上の振る舞いが読めるようにする。
- business scenario を追加・変更したら `docs/business-test-scenarios.md` も更新する。
- `backend/tests/business-test-scenarios.md` は互換用入口として残し、正本への導線に使う。

## レビュー観点

- 公開結果または状態変化を検証しているか。
- 実装詳細や内部 collaborator の呼び出しに寄りすぎていないか。
- 同一 business 要件を複数レイヤーで無駄に重複保証していないか。
- business scenario 文書と対応テストが追跡できるか。
- 文字化けや英日混在で読み手の理解を妨げていないか。