# Frontend (Next.js)

Dashboard UI for the Fraud Checker API.

## Run
```bash
cd frontend
npm install
npm run dev
```

## 環境変数
フロントエンドの設定は以下の環境変数で制御できます。
`.env.local` ファイルを作成して設定してください。

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8001` | バックエンドAPIのURL |

例：
```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## 起動方法

### フロントエンドのみ起動
```bash
cd frontend
npm run dev
```
→ http://localhost:3000 でアクセス

### バックエンドと一緒に起動
プロジェクトルートから:
```bash
python dev.py
```

## 画面一覧
| パス | 説明 |
|------|------|
| `/` | ダッシュボード（サマリー表示） |
| `/suspicious/clicks` | 不正クリック疑惑一覧 |
| `/suspicious/conversions` | 不正成果疑惑一覧 |
| `/settings` | 検知閾値設定 |
