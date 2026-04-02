export const dashboardCopy = {
  title: "ダッシュボード",
  loadingMeta: "最新データを読み込み中",
  targetDateLabel: (date: string) => `対象日: ${date}`,
  labels: {
    clicks: "クリック",
    conversions: "コンバージョン",
    suspiciousConversions: "不正判定",
    chart: "日次推移",
  },
  states: {
    loadError: "ダッシュボードデータの読み込みに失敗しました",
    noDataTitle: "ダッシュボードデータがありません",
    noDataMessage: "対象日を選択するか、データ取込を実行してください。",
    refresh: "更新",
    retry: "再試行",
    refreshing: "更新中...",
    transientTitle: "一時的なエラー",
    staleTitle: "不正判定が最新データに追いついていません",
    unauthorizedTitle: "ログインが必要です",
    forbiddenTitle: "この画面へのアクセス権がありません",
    genericErrorTitle: "ダッシュボードを表示できませんでした",
  },
  chart: {
    empty: "日次データがありません。",
    title: "クリック・コンバージョン・不正判定",
    legends: {
      clicks: "クリック",
      conversions: "コンバージョン",
      suspiciousConversions: "不正判定",
    },
    subtitle: (days: number) => `直近 ${days} 日`,
    maxLabel: (value: number) => `最大 ${value.toLocaleString("ja-JP")}`,
  },
  admin: {
    unavailableShortHint: "管理系APIが無効なため、操作は表示のみです。",
    title: "管理操作",
    description: "取込やマスタ同期を実行します。",
    actions: {
      refresh: "データ再取得",
      masterSync: "マスタ同期",
    },
    feedback: {
      refresh: {
        queued: "再取得ジョブをキューに追加しました",
        running: "再取得ジョブ実行中",
        succeeded: "再取得ジョブが完了しました",
        failed: "再取得ジョブが失敗しました",
      },
      masterSync: {
        queued: "マスタ同期をキューに追加しました",
        running: "マスタ同期実行中",
        succeeded: "マスタ同期が完了しました",
        failed: "マスタ同期が失敗しました",
      },
    },
  },
} as const;
