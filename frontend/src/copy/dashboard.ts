export const dashboardCopy = {
  title: "ダッシュボード",
  loadingMeta: "読み込み中です",
  targetDateLabel: (date: string) => `対象日: ${date}`,
  labels: {
    clicks: "計測クリック数",
    conversions: "CV数",
    suspiciousClicks: "不審クリック",
    suspiciousConversions: "不審コンバージョン",
    chart: "日次推移",
    diagnostics: "データ品質",
    findingsFreshness: "不審判定の更新",
    coverage: "IP・UA の補完",
    enrichment: "CV 紐付け",
    masterSync: "マスタ同期",
  },
  states: {
    loadError: "ダッシュボードのデータを取得できませんでした。",
    noDataTitle: "表示できるデータがありません",
    noDataMessage: "選択した日付に、表示できるデータがありません。",
    refresh: "更新",
    retry: "再試行",
    refreshing: "更新中",
    transientTitle: "一時的に取得できませんでした",
    staleTitle: "不審判定の集計が最新でない可能性があります",
    unauthorizedTitle: "ログインが必要です",
    forbiddenTitle: "この画面を表示する権限がありません",
    genericErrorTitle: "表示できませんでした",
  },
  diagnosticsText: {
    stale: "元データの取り込みに比べ、不審判定の集計が遅れています。",
    healthy: "不審判定は最新の集計を表示しています。",
    noSignal: "データなし",
    masterSyncMissing: "同期履歴がありません",
  },
  chart: {
    empty: "グラフ用のデータがありません",
    title: "クリック・CV・不審件数の日次推移",
    legends: {
      clicks: "クリック",
      conversions: "CV",
      suspiciousClicks: "不審クリック",
      suspiciousConversions: "不審CV",
    },
  },
  admin: {
    unavailableShortHint: "管理者操作を使うには Admin API の設定が必要です。",
    unavailableHint:
      "管理者向けの「直近の再取得」「マスタ同期」は、Next.js に FC_ADMIN_API_KEY を設定しバックエンドへ接続できるときのみ使えます。`python dev.py` ではリポジトリ直下の .env が読み込まれます。",
    actions: {
      refresh: "直近データを再取得",
      masterSync: "マスタ同期",
    },
    feedback: {
      refresh: {
        queued: "再取得を受け付けました",
        running: "再取得を実行中です",
        succeeded: "再取得が完了しました",
        failed: "再取得に失敗しました",
      },
      masterSync: {
        queued: "マスタ同期を受け付けました",
        running: "マスタ同期を実行中です",
        succeeded: "マスタ同期が完了しました",
        failed: "マスタ同期に失敗しました",
      },
    },
  },
} as const;
