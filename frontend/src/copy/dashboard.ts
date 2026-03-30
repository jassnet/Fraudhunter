export const dashboardCopy = {
  title: "ダッシュボード",
  loadingMeta: "読み込み中",
  targetDateLabel: (date: string) => `対象日 ${date}`,
  labels: {
    clicks: "総クリック",
    conversions: "総CV",
    suspiciousClicks: "不審クリック",
    suspiciousConversions: "不審コンバージョン",
    chart: "直近14日推移",
    diagnostics: "診断指標",
    findingsFreshness: "Findings鮮度",
    coverage: "IP/UAカバレッジ",
    enrichment: "CV紐付け率",
    masterSync: "マスタ同期",
  },
  states: {
    loadError: "ダッシュボードの取得に失敗しました。",
    noDataTitle: "表示できるデータがありません",
    noDataMessage: "対象日に利用できるデータがありません。",
    retry: "再読込",
    transientTitle: "一時的な取得エラー",
    staleTitle: "Findings の更新が遅れています",
    unauthorizedTitle: "認証が必要です",
    forbiddenTitle: "表示権限がありません",
    genericErrorTitle: "表示エラー",
  },
  diagnosticsText: {
    stale: "raw ingest より findings が古い状態です。",
    healthy: "最新の findings を参照しています。",
    noSignal: "診断データなし",
    masterSyncMissing: "同期履歴なし",
  },
  chart: {
    empty: "表示できる推移データがありません",
    title: "クリック、CV、不審件数の比較",
    legends: {
      clicks: "クリック",
      conversions: "CV",
      suspiciousClicks: "不審クリック",
      suspiciousConversions: "不審CV",
    },
  },
  admin: {
    actions: {
      refresh: "最新1時間を再取得",
      masterSync: "マスタ同期",
    },
    feedback: {
      refresh: {
        queued: "再取得 / キュー登録済み",
        running: "再取得 / 実行中",
        succeeded: "再取得 / 完了",
        failed: "再取得 / 失敗",
      },
      masterSync: {
        queued: "マスタ同期 / キュー登録済み",
        running: "マスタ同期 / 実行中",
        succeeded: "マスタ同期 / 完了",
        failed: "マスタ同期 / 失敗",
      },
    },
  },
} as const;
