# Backfill Operations

## 背景
- `track_log` は日中も継続して増える
- 通常の hourly refresh を `--hours 1` だけにすると、worker 停止や API 一時障害で欠損時間帯が残る
- 重複は raw ID で吸収できるため、欠損補完は「広めに再取得して重複を捨てる」方針が安全

## 運用方針
- 通常 freshness:
  - `enqueue-refresh --hours 1 --detect`
- 欠損補完 / 初回同期:
  - `enqueue-backfill --hours 24 --detect`
- Render 本番では 6 時間ごとに 24 時間 backfill を走らせる
- 手動 UI の再取得ボタンも 24 時間 backfill を投げる

## 期待する効果
- 直近 1 時間の新着は hourly refresh で追う
- 欠損や遅延到着は 24 時間 backfill で自己修復する
- request-time の重い再集計は増やさず、既存 `refresh` job をそのまま使う

## CLI
```bash
cd backend
python -m fraud_checker.cli enqueue-backfill --hours 24 --detect
```

より広い期間を取り直したい場合:
```bash
cd backend
python -m fraud_checker.cli enqueue-backfill --hours 72 --detect
```

## 注意点
- backfill は `track_log/search` / `action_log_raw/search` を広めに再取得する
- findings は影響日のみ再計算される
- 取得元 API の rate limit や応答時間次第で、`--hours` を広げすぎると worker 1 回あたりの負荷が増える
- 初回一括投入は 24 時間を何度も回すより、必要に応じて 72 時間・168 時間などを明示して走らせる
