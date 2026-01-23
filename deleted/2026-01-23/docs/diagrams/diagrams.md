# Fraud Checker v2 - Diagrams (Mermaid)

このファイルは、Fraud Checker v2（FastAPI + Next.js + SQLite + 外部ACS）の設計を理解・共有するための図表を Mermaid でまとめたものです。

## Index
- 01. システムコンテキスト図（System Context / C4-L1）
- 02. C4 コンテナ図（Container / C4-L2）
- 03. Backend コンポーネント図（Component / C4-L3）
- 04. Frontend コンポーネント図（Component / App Router）
- 05. 物理/デプロイ構成図 + トラフィックフロー
- 06. ジョブ基盤/バッチ基盤の構成図 + 状態遷移
- 07. シーケンス図（主要フロー：正常系/競合/失敗）
- 08. データモデル（ER）+ データフロー
- 09. API・インタフェース俯瞰（一覧/エラー）
- 10. フロントエンド（サイトマップ/画面状態）
- 11. セキュリティ（DFD + Trust Boundary / 最小）
- 12. 運用（最小：バックアップ/日次運用）

---

## 01. システムコンテキスト図（System Context / C4-L1）

```mermaid
flowchart LR
  %% People
  op[運用者 / 分析者<br/>（ダッシュボード利用）]
  admin[運用者<br/>（取り込み/設定変更/マスタ同期）]

  %% External system
  acs[ACS API（外部）<br/>click/action logs / masters]

  %% Our system
  fc[Fraud Checker v2<br/>不正検知（UI + API + CLI）]

  op -->|閲覧/検索/エクスポート| fc
  admin -->|取り込み実行/設定変更/マスタ同期| fc
  fc -->|ログ取得/マスタ取得| acs
```

### 目的
- 外部境界（誰が/何が関わるか）を最短で共有する。
- 「本システムが何を責務として持つか」を合意する。

### 説明（一般）
- 人・外部サービス・自分たちのシステムの関係を、1枚でざっくり把握する図。
- 詳細設計より前に「誰が何に触れるか」を揃える目的で使う。

### このプロジェクトならでは
- Fraud Checker v2 は ACS API からログ/マスタを取得し、運用者はダッシュボードで閲覧する構成。
- 取り込みや設定変更は運用者（管理）側の操作として整理されている。

---

## 02. C4 コンテナ図（Container / C4-L2）

```mermaid
flowchart TB
  %% ===== Users =====
  user[運用者/分析者]
  devops[運用者（CLI実行）]

  %% ===== Containers =====
  subgraph FC[Fraud Checker v2]
    next[Frontend: Next.js Dashboard<br/>:3000]
    api[Backend: FastAPI API<br/>:8001]
    cli[CLI: python -m fraud_checker.cli]
    db[(SQLite DB file<br/>fraud_checker.db)]
  end

  acs[ACS API（外部）]

  %% ===== Flows =====
  user -->|HTTP/HTTPS: UI表示| next
  user -->|HTTP: API呼び出し（fetch）| api

  api -->|read/write| db
  api -->|HTTPS + X-Auth-Token| acs

  devops -->|ローカル実行| cli
  cli -->|read/write| db
  cli -->|HTTPS + X-Auth-Token| acs
```

### 備考
- UI からの API 呼び出しはブラウザから `NEXT_PUBLIC_API_URL`（例: `http://localhost:8001`）へ直接行われる想定。
- CLI は FastAPI を経由せず、同じロジック（ACS クライアント + SQLiteRepository）を直接利用する。

### 説明（一般）
- システムを「動く単位（プロセス/サービス）」に分けて、通信の流れを示す図。
- どこで動いて、どこと通信するかがわかる。

### このプロジェクトならでは
- UI は Next.js、API は FastAPI、DB はローカルの SQLite ファイルという最小構成。
- CLI も同じ DB/ACS を触るため、UI と並ぶ運用経路として明示している。

---

## 03. Backend コンポーネント図（Component / C4-L3）

```mermaid
flowchart TB
  %% ===== Presentation =====
  subgraph API["FastAPI (backend/src/fraud_checker)"]
    routes[api.py<br/>HTTP endpoints]
  end

  %% ===== Services =====
  subgraph Services[Services]
    jobs[services/jobs.py<br/>enqueue_job + run_*]
    reporting[services/reporting.py<br/>summary/daily/dates queries]
    settings[services/settings.py<br/>settings cache + persistence]
  end

  %% ===== Domain =====
  subgraph Domain[Domain / Usecases]
    ingestion[ingestion.py<br/>ClickLogIngestor / ConversionIngestor]
    suspicious[suspicious.py<br/>Detectors + Rules]
  end

  %% ===== Infrastructure =====
  subgraph Infra[Infrastructure]
    repo[repository.py<br/>SQLiteRepository]
    jobstore[job_status.py<br/>JobStatusStore]
    acsclient[acs_client.py<br/>AcsHttpClient]
    sqlite[(SQLite DB file)]
    acs[(ACS API)]
  end

  %% ===== Dependencies =====
  routes --> reporting
  routes --> settings
  routes --> jobs
  routes --> suspicious

  jobs --> ingestion
  jobs --> repo
  jobs --> jobstore
  jobs --> acsclient

  reporting --> repo
  settings --> repo
  suspicious --> repo

  repo --> sqlite
  jobstore --> sqlite
  acsclient --> acs
```

### 補足（境界/責務）
- `api.py`：HTTP 入出力、バリデーション、例外→HTTP 変換。
- `services/*`：ユースケースの組み立て（レポート、設定、ジョブ実行）。
- `ingestion.py`：ACS からの取得・ページング、DB への投入ポリシー（例外時は中断）。
- `repository.py`：SQLite スキーマ管理、CRUD/集計、マスタ参照、詳細取得。

### 説明（一般）
- バックエンド内部の「層（レイヤ）」と依存関係を示す図。
- 入口（API）→処理（Services/Domain）→保存/外部連携（Infra）の流れがわかる。

### このプロジェクトならでは
- ジョブ実行・集計・設定が `services/*` に集約され、DB アクセスは `repository.py` に一本化。
- 外部 ACS 連携は `acs_client.py` で分離されているため、交換やモック化がしやすい。

---

## 04. Frontend コンポーネント図（Component / App Router）

```mermaid
flowchart TB
  subgraph Next["Next.js (frontend/src)"]
    subgraph Routes["Routes (app/)"]
      root["/ (app/page.tsx)<br/>Summary/Daily/操作"]
      clicks["/suspicious/clicks (app/suspicious/clicks/page.tsx)"]
      convs["/suspicious/conversions (app/suspicious/conversions/page.tsx)"]
      settingsPage["/settings (app/settings/page.tsx)"]
    end

    subgraph Components[Components]
      list[suspicious-list-page.tsx<br/>一覧/検索/ページング]
      job[job-status-indicator.tsx<br/>ジョブ状態表示]
      updated[last-updated.tsx<br/>更新時刻表示]
    end

    subgraph Hooks[Hooks]
      jobHook[use-job-status.ts<br/>polling store]
      healthHook[use-health-status.ts<br/>polling store]
    end

    apiLib[lib/api.ts<br/>fetch + retry + typed API]
  end

  backend[FastAPI Backend<br/>:8001]

  %% Route → Component wiring
  clicks --> list
  convs --> list
  root --> job
  root --> updated
  settingsPage --> apiLib
  list --> apiLib
  job --> jobHook --> apiLib
  updated --> apiLib
  healthHook --> apiLib

  %% API calls
  apiLib --> backend
```

### 備考
- `use-job-status.ts` は `status=running` の間は 2 秒、そうでなければ 10 秒で `/api/job/status` をポーリング。
- `lib/api.ts` は GET 系に簡易リトライ（デフォルト 2 回）を持つ（POST 系は retries=0）。

### 説明（一般）
- 画面（Routes）と部品（Components/ Hooks）がどうつながるかを示す図。
- どのページがどのデータ取得/状態管理に依存するかがわかる。

### このプロジェクトならでは
- 不正一覧ページは `suspicious-list-page.tsx` を共通化して、クリック/成果で使い回す設計。
- ジョブ状態やヘルスはポーリングで扱うため、専用 Hook を中心に構成している。

---

## 05. 物理/デプロイ構成図 + トラフィックフロー

### 05-1. ローカル開発（AS-IS）

```mermaid
flowchart LR
  subgraph Host[User Host / VM]
    browser[Browser]
    next[Next.js Dev/Node Server<br/>:3000]
    api["FastAPI (uvicorn)<br/>:8001"]
    db[(SQLite DB file)]
  end

  acs[(ACS API / Internet)]

  browser -->|HTTP:3000<br/>HTML/JS/CSS| next
  browser -->|HTTP:8001<br/>JSON API| api
  api -->|read/write| db
  api -->|HTTPS + X-Auth-Token| acs
```

### 説明（一般）
- どのプロセスがどのポートで動くかを示す「配置図」。
- 開発環境での動作イメージを共有するために使う。

### このプロジェクトならでは
- UI（3000）と API（8001）が同一ホストで動き、DB は SQLite ファイル。
- 外部 ACS に HTTPS でアクセスするため、ローカルでも外部通信が発生する。

### 05-2. トラフィックフロー（入口→内部）

```mermaid
flowchart TB
  user[運用者]
  browser[Browser]
  next[Next.js UI :3000]
  api[FastAPI :8001]
  db[(SQLite)]
  acs[(ACS API)]

  user --> browser
  browser --> next
  browser --> api
  api --> db
  api --> acs
```

### 説明（一般）
- ユーザー操作がどの順にシステム内を流れるかを示す図。
- 入口から内部処理までの道筋をざっくり掴む。

### このプロジェクトならでは
- ブラウザが UI と API の両方に直接アクセスするため、CORS/環境変数の設定が重要。
- 外部 ACS への通信は API 側でまとめて行う。

### 前提
- ここでは「単一ホスト/単一プロセス群」を前提として図示（LB/VPC 等は未記載）。

---

## 06. ジョブ基盤/バッチ基盤の構成図 + 状態遷移

### 06-1. ジョブ実行フロー（FastAPI BackgroundTasks）

```mermaid
flowchart TB
  %% Entry points
  subgraph HTTP[FastAPI Request]
    endpoints[POST /api/ingest/*<br/>POST /api/refresh<br/>POST /api/sync/masters]
    enqueue["services/jobs.enqueue_job()"]
    check["JobStatusStore.get()"]
    start["JobStatusStore.start(job_id)"]
  end

  subgraph BG[BackgroundTasks]
    runner["_runner()"]
    runfn["run_*()<br/>ingestion/refresh/sync"]
    done["JobStatusStore.complete()"]
    fail["JobStatusStore.fail()"]
  end

  db[(SQLite: job_status + tables)]
  acs[(ACS API)]
  repo[SQLiteRepository]

  endpoints --> enqueue --> check
  check -->|status=running| conflict[409 Conflict<br/>Another job is already running]
  check -->|それ以外| start
  start --> db
  start --> runner --> runfn
  runfn --> acs
  runfn --> repo --> db
  runner --> done --> db
  runner --> fail --> db
```

### 説明（一般）
- バッチ/ジョブの流れ（受付→実行→完了/失敗）を示す図。
- UI/API とは別に動く処理があることを明確にする。

### このプロジェクトならでは
- `JobStatusStore` で排他を行い、同時実行時は 409 を返す設計。
- 取得→変換→保存は `acs` と `repo` を経由し、SQLite に集約される。

### 06-2. JobStatus 状態遷移（State Machine）

```mermaid
stateDiagram-v2
  [*] --> idle
  idle --> running: start(job_id)
  running --> completed: complete(job_id)
  running --> failed: fail(job_id)
  completed --> running: start(next_job)
  failed --> running: start(next_job)
```

### 説明（一般）
- ジョブが取り得る状態と、その遷移ルールを示す図。
- 「今どの状態か」「どう切り替わるか」を理解しやすくする。

### このプロジェクトならでは
- `failed` になっても再実行で `running` に戻す前提の運用。
- 完了/失敗どちらも同じ経路で次のジョブに進められる。

### ポイント
- 同時実行は `job_status.status == running` で排他（409 を返す）。
- 例外はジョブ失敗として `failed` に保存し、運用者が原因解消後に再実行する前提。

---

## 07. シーケンス図（主要フロー：正常系/競合/失敗）

### 07-1. クリック取り込み（/api/ingest/clicks）

```mermaid
sequenceDiagram
  autonumber
  actor User as 運用者
  participant UI as Browser(UI)
  participant API as FastAPI
  participant Store as JobStatusStore(SQLite)
  participant BG as BackgroundTasks
  participant ACS as ACS API
  participant DB as SQLiteRepository/DB

  User->>UI: 取り込み実行（date）
  UI->>API: POST /api/ingest/clicks {date}
  API->>Store: get()
  alt status == running
    API-->>UI: 409 Another job is already running
  else status != running
    API->>Store: start(job_id)
    API->>BG: add_task(run_click_ingestion)
    API-->>UI: 200 {success:true, job_id}

    par UI polls job status
      loop status=running (2s)
        UI->>API: GET /api/job/status
        API->>Store: get()
        API-->>UI: {status:"running", job_id, ...}
      end
    and Background job
      BG->>ACS: GET access_log/search (page=1..N)
      ACS-->>BG: records[]
      BG->>DB: ingest_clicks(clear date, upsert aggregates, raw optional)
      DB-->>BG: count
      BG->>Store: complete(job_id, result)
    end
  end
```

### 説明（一般）
- 1つの操作が UI→API→外部→DB と流れる様子を時系列で追う図。
- 画面操作とバックグラウンド処理の関係がわかる。

### このプロジェクトならでは
- 競合時は 409 を返し、UI はジョブ状態を 2 秒間隔でポーリング。
- クリックログは ACS からページング取得して DB へ投入する。

### 07-2. 不正クリック一覧取得（/api/suspicious/clicks）

```mermaid
sequenceDiagram
  autonumber
  participant UI as Browser(UI)
  participant API as FastAPI
  participant Repo as SQLiteRepository
  participant DB as SQLite(click_ipua_daily/master_*)

  UI->>API: GET /api/suspicious/clicks?date&limit&offset&search
  API->>Repo: _resolve_target_date(click_ipua_daily)
  API->>Repo: Detector.find_for_date(date)
  API->>Repo: get_suspicious_click_details_bulk(...) (optional)
  Repo->>DB: SELECT/GROUP BY/JOIN(master_*)
  DB-->>Repo: rows
  Repo-->>API: suspicious findings + details/names
  API-->>UI: SuspiciousResponse
```

### 説明（一般）
- 読み取り系 API の処理手順を示す図。
- どの層で検索や集計が行われるかが見える。

### このプロジェクトならでは
- `click_ipua_daily` と `master_*` を JOIN して画面表示に必要な情報を補完。
- 追加詳細は optional で取得するため、レスポンス設計に柔軟性がある。

### 07-3. 設定更新（/api/settings）

```mermaid
sequenceDiagram
  autonumber
  participant UI as Browser(UI)
  participant API as FastAPI
  participant Svc as services/settings.py
  participant Repo as SQLiteRepository
  participant DB as SQLite(app_settings)

  UI->>API: POST /api/settings {settings}
  API->>Repo: get_repository()
  API->>Svc: update_settings(repo, settings)
  Svc->>DB: UPSERT app_settings (key,value)
  DB-->>Svc: ok / error
  Svc-->>API: {success, persisted, settings}
  API-->>UI: response
```

### 説明（一般）
- 設定変更がどこに保存されるかを示す CRUD フロー。
- UI→API→DB の基本パターンを理解できる。

### このプロジェクトならでは
- 設定値は `app_settings` に UPSERT で保存し、読み書きの単純化を優先。

### 07-4. マスタ同期（/api/sync/masters）

```mermaid
sequenceDiagram
  autonumber
  participant UI as Browser(UI)
  participant API as FastAPI
  participant Store as JobStatusStore(SQLite)
  participant BG as BackgroundTasks
  participant ACS as ACS API
  participant Repo as SQLiteRepository
  participant DB as SQLite(master_*)

  UI->>API: POST /api/sync/masters
  API->>Store: get()
  alt status == running
    API-->>UI: 409 Another job is already running
  else status != running
    API->>Store: start(job_id="sync_masters")
    API->>BG: add_task(run_master_sync)
    API-->>UI: 200 {success:true, job_id:"sync_masters"}

    BG->>ACS: fetch_all_media_master()
    BG->>ACS: fetch_all_promotion_master()
    BG->>ACS: fetch_all_user_master()
    ACS-->>BG: lists
    BG->>Repo: bulk_upsert_*()
    Repo->>DB: INSERT/UPDATE master_*
    BG->>Store: complete(job_id, result)
  end
```

### 説明（一般）
- 外部の基礎データ（マスタ）を取り込む手順を示す図。
- データ量が多い想定でも流れを追える。

### このプロジェクトならでは
- メディア/プロモーション/ユーザーの 3 種マスタを ACS から取得。
- `bulk_upsert_*` により差分更新でDBを保つ。

---

## 08. データモデル（ER）+ データフロー

### 08-1. ER 図（概念/論理）

> 実DBは SQLite で、FK 制約は明示していないが「論理的な関係」を図示しています。

```mermaid
erDiagram
  CLICK_IPUA_DAILY {
    TEXT date PK
    TEXT media_id PK
    TEXT program_id PK
    TEXT ipaddress PK
    TEXT useragent PK
    INT click_count
    TEXT first_time
    TEXT last_time
    TEXT created_at
    TEXT updated_at
  }

  CLICK_RAW {
    TEXT id PK
    TEXT click_time
    TEXT media_id
    TEXT program_id
    TEXT ipaddress
    TEXT useragent
    TEXT referrer
    TEXT raw_payload
    TEXT created_at
    TEXT updated_at
  }

  CONVERSION_RAW {
    TEXT id PK
    TEXT cid
    TEXT conversion_time
    TEXT click_time
    TEXT media_id
    TEXT program_id
    TEXT user_id
    TEXT postback_ipaddress
    TEXT postback_useragent
    TEXT entry_ipaddress
    TEXT entry_useragent
    TEXT state
    TEXT raw_payload
    TEXT created_at
    TEXT updated_at
  }

  CONVERSION_IPUA_DAILY {
    TEXT date PK
    TEXT media_id PK
    TEXT program_id PK
    TEXT ipaddress PK
    TEXT useragent PK
    INT conversion_count
    TEXT first_time
    TEXT last_time
    TEXT created_at
    TEXT updated_at
  }

  MASTER_MEDIA {
    TEXT id PK
    TEXT name
    TEXT user_id
    TEXT state
    TEXT updated_at
  }

  MASTER_PROMOTION {
    TEXT id PK
    TEXT name
    TEXT state
    TEXT updated_at
  }

  MASTER_USER {
    TEXT id PK
    TEXT name
    TEXT company
    TEXT state
    TEXT updated_at
  }

  APP_SETTINGS {
    TEXT key PK
    TEXT value
    TEXT updated_at
  }

  JOB_STATUS {
    INT id PK
    TEXT status
    TEXT job_id
    TEXT message
    TEXT started_at
    TEXT completed_at
    TEXT result_json
  }

  MASTER_USER ||--o{ MASTER_MEDIA : "user_id"
  MASTER_MEDIA ||--o{ CLICK_RAW : "media_id"
  MASTER_PROMOTION ||--o{ CLICK_RAW : "program_id"
  MASTER_MEDIA ||--o{ CLICK_IPUA_DAILY : "media_id"
  MASTER_PROMOTION ||--o{ CLICK_IPUA_DAILY : "program_id"

  MASTER_MEDIA ||--o{ CONVERSION_RAW : "media_id"
  MASTER_PROMOTION ||--o{ CONVERSION_RAW : "program_id"
  MASTER_USER ||--o{ CONVERSION_RAW : "user_id"
  MASTER_MEDIA ||--o{ CONVERSION_IPUA_DAILY : "media_id"
  MASTER_PROMOTION ||--o{ CONVERSION_IPUA_DAILY : "program_id"
```

### 説明（一般）
- テーブルとその関係（結びつき）を示す図。
- どのデータがどの軸で紐づくかがわかる。

### このプロジェクトならでは
- RAW と 日次集計（IP/UA 単位）が分離されており、分析と保存を両立。
- `master_*` を参照することで画面表示の名称解決を行う。

### 08-2. データフロー図（DFD：どこからどこへ）

```mermaid
flowchart LR
  acs[(ACS API)]

  subgraph Jobs[Background Jobs / CLI]
    ingestClicks["クリック取り込み<br/>ingest_clicks / refresh(clicks)"]
    ingestConvs["成果取り込み<br/>ingest_conversions / refresh(conversions)"]
    syncMasters[マスタ同期<br/>sync_masters]
  end

  db[(SQLite DB)]
  api[FastAPI API]
  ui[Next.js UI]

  acs --> ingestClicks --> db
  acs --> ingestConvs --> db
  acs --> syncMasters --> db

  db --> api --> ui
```

### 説明（一般）
- データがシステム内をどの経路で移動するかを示す図。
- 読み取り/書き込みの起点が理解しやすい。

### このプロジェクトならでは
- 外部 ACS からの取得はジョブ/CLI が担い、UI は API 経由で参照する。

---

## 09. API・インタフェース俯瞰（一覧/エラー）

### 09-1. API 俯瞰（グルーピング）

```mermaid
flowchart LR
  subgraph Reporting[Reporting / Read]
    summary[GET /api/summary]
    daily[GET /api/stats/daily]
    dates[GET /api/dates]
    mastersStatus[GET /api/masters/status]
    settingsGet[GET /api/settings]
    jobStatus[GET /api/job/status]
    health[GET /api/health]
  end

  subgraph Suspicious[Suspicious / Read]
    suspClicks[GET /api/suspicious/clicks]
    suspConvs[GET /api/suspicious/conversions]
  end

  subgraph Ops[Operations / Write]
    ingestClicks[POST /api/ingest/clicks]
    ingestConvs[POST /api/ingest/conversions]
    refresh[POST /api/refresh]
    syncMasters[POST /api/sync/masters]
    settingsPost[POST /api/settings]
  end
```

### 説明（一般）
- API を「読み取り」と「書き込み」に分類して俯瞰する図。
- 使い手がどの操作でどのAPIを叩くかを整理できる。

### このプロジェクトならでは
- `ingest/refresh/sync` はジョブ起動系、`summary/suspicious` は閲覧系に分けて設計。

### 09-2. API 一覧表（抜粋）

| Method | Path | 用途 | 主な副作用 |
|---|---|---|---|
| GET | `/api/health` | 稼働・設定ヘルス | なし |
| GET | `/api/summary` | サマリ | なし |
| GET | `/api/stats/daily` | 日次統計 | なし |
| GET | `/api/dates` | 利用可能日付 | なし |
| GET | `/api/suspicious/clicks` | 不正クリック一覧 | なし |
| GET | `/api/suspicious/conversions` | 不正成果一覧 | なし |
| POST | `/api/ingest/clicks` | クリック取り込み（指定日） | DB 更新 + ジョブ起動 |
| POST | `/api/ingest/conversions` | 成果取り込み（指定日） | DB 更新 + ジョブ起動 |
| POST | `/api/refresh` | 直近N時間の差分取り込み | DB 更新 + ジョブ起動 |
| POST | `/api/sync/masters` | マスタ同期 | DB 更新 + ジョブ起動 |
| GET | `/api/job/status` | ジョブ状態 | なし |
| GET/POST | `/api/settings` | 検知閾値の参照/更新 | app_settings 更新 |
| GET | `/api/masters/status` | マスタ件数など | なし |

### 09-3. ステータスコード/エラー（AS-IS）

| HTTP | 代表ケース | 例 |
|---|---|---|
| 200 | 正常 | `SuspiciousResponse` / `JobStatusResponse` |
| 400 | 入力不正 | `Invalid date format. Use YYYY-MM-DD` |
| 409 | ジョブ競合 | `Another job is already running` |
| 500 | 例外 | 依存先（ACS/DB）や実装例外 |

### 09-4. 認証/認可（AS-IS）
- 本 API 自体の認証は実装されていない前提（ローカル利用/内部利用を想定）。
- 外部 ACS への認証は `X-Auth-Token={accessKey}:{secretKey}`（環境変数）で実施。

---

## 10. フロントエンド（サイトマップ/画面状態）

### 10-1. サイトマップ（Routes）

```mermaid
flowchart TB
  home["/ (Dashboard)"]
  clicks["/suspicious/clicks"]
  convs["/suspicious/conversions"]
  settings["/settings"]

  home --> clicks
  home --> convs
  home --> settings
  clicks --> home
  convs --> home
  settings --> home
```

### 説明（一般）
- 画面同士の遷移関係をざっくり示す図。
- どこからどこへ移れるかを理解するための地図。

### このプロジェクトならでは
- ダッシュボードが入口で、不正一覧と設定に枝分かれする構造。

### 10-2. UI 状態遷移（不正一覧ページの典型）

```mermaid
stateDiagram-v2
  [*] --> Loading

  Loading --> Showing: fetch成功 & total>0
  Loading --> Empty: fetch成功 & total==0
  Loading --> Error: fetch失敗

  Showing --> Loading: date/search/page変更
  Empty --> Loading: date/search変更
  Error --> Loading: retry
```

### 説明（一般）
- 画面が「読み込み」「空」「エラー」などに切り替わる流れを示す図。
- ユーザー体験の分岐が明確になる。

### このプロジェクトならでは
- 不正一覧は日付/検索/ページ変更で再取得するため、戻り先は常に Loading。

### 10-3. UI ↔ API データ取得フロー（概略）

```mermaid
flowchart LR
  user[運用者] --> ui[UI操作]
  ui --> state[React state/store 更新]
  state --> api[lib/api.ts]
  api -->|fetch| backend[FastAPI]
  backend -->|JSON| api
  api --> state --> render[再描画]
```

### 説明（一般）
- UI が API からデータを取得し、画面を再描画する流れを示す図。
- React の基本的なデータフローを理解するための図。

### このプロジェクトならでは
- 取得は `lib/api.ts` に集約され、UI 側は state 更新に専念する設計。

---

## 11. セキュリティ（DFD + Trust Boundary / 最小）

### 11-1. DFD（Trust Boundary 付き）

```mermaid
flowchart LR
  %% Trust boundaries
  subgraph TB1[Trust Boundary: Browser]
    browser[Browser]
  end

  subgraph TB2[Trust Boundary: Host / Internal]
    next[Next.js UI :3000]
    api[FastAPI :8001]
    db[(SQLite DB)]
    envBackend[(.env / Env Vars<br/>ACS credentials)]
  end

  subgraph TB3[Trust Boundary: External]
    acs[(ACS API)]
  end

  browser -->|HTTP:3000| next
  browser -->|HTTP:8001| api
  envBackend --> api
  api -->|read/write| db
  api -->|HTTPS + X-Auth-Token| acs
```

### 説明（一般）
- どこが「信頼できる境界」かを示し、外部と内部の境目を明確にする図。
- どのデータがどこを通るかがわかる。

### このプロジェクトならでは
- ACS 認証情報は `.env` に置き、API のみが外部と通信する前提。
- UI と API は同一ホスト想定のため境界はシンプル。

### 11-2. 保護すべきデータ（抜粋）
- 秘密情報：`ACS_ACCESS_KEY` / `ACS_SECRET_KEY` / `ACS_TOKEN`
- 個人情報・準個人情報：IP address / User-Agent（ログ由来）
- DB ファイル（改ざん/持ち出し耐性、アクセス権）

### 11-3. 最小のリスク洗い出し（STRIDEの一部）

| 脅威 | 例 | 最小対策（要検討） |
|---|---|---|
| Spoofing | API を第三者が叩く | 内部ネットワーク限定/Basic認証/Reverse proxy で保護 |
| Tampering | SQLite を直接改ざん | ファイル権限・配置、バックアップ監査 |
| Info Disclosure | IP/UA が漏れる | UI/ログのマスキング、アクセス制御 |
| DoS | ingest/refresh の連打 | 認証 + レート制限、ジョブキュー化 |

---

## 12. 運用（最小：バックアップ/日次運用）

### 12-1. バックアップ/リストア（SQLite）

```mermaid
flowchart TB
  start([開始])
  stop["API/CLI の停止<br/>(またはメンテモード)"]
  copy["DBファイルをコピー<br/>fraud_checker.db(+wal/shm)"]
  store["安全な保管先へ保存<br/>(権限/暗号化)"]
  verify[必要なら復元テスト]
  finish([完了])

  start --> stop --> copy --> store --> verify --> finish
```

### 説明（一般）
- SQLite のバックアップ手順を順番で示す図。
- 「停止→コピー→保管→確認」という基本を押さえるためのもの。

### このプロジェクトならでは
- `fraud_checker.db` に加えて `wal/shm` を含めてコピーする点が重要。

### 12-2. 日次運用（例：前日分の取り込み→確認）

```mermaid
flowchart LR
  schedule[運用者/スケジュール] --> ingest[取り込み実行<br/>POST /api/ingest/* or CLI]
  ingest --> status[ジョブ状態確認<br/>GET /api/job/status]
  status -->|completed| review[不正一覧レビュー<br/>/suspicious/*]
  status -->|failed| fix[原因調査/復旧<br/>ヘルス/ログ/設定]
  fix --> ingest
```

### 説明（一般）
- 日々の運用がどの順で回るかを示す図。
- 失敗時にどこへ戻るかがわかる。

### このプロジェクトならでは
- ジョブ完了後に `/suspicious/*` で確認する運用が中心。
- 失敗時はヘルス/ログ/設定を見直して再実行する想定。

### 備考
- 現状はインプロセスの `BackgroundTasks` 実行のため、プロセス停止=ジョブ停止になる点に注意。
