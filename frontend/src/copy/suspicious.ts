export const suspiciousCopy = {
  clicksTitle: "不審クリック",
  conversionsTitle: "不審コンバージョン",
  countLabelClicks: "クリック数",
  countLabelConversions: "CV数",
  /** 一覧ヘッダー横の日付表示 */
  targetDateMeta: (date: string) => `対象日: ${date}`,
  targetDateMetaPending: "対象日を選択してください",
  labels: {
    targetDate: "対象日",
    search: "キーワード検索",
    searchPlaceholder: "IP・ユーザーエージェント・媒体・案件・アフィリエイター",
    searchOpenButton: "検索",
    sort: "並び順",
    riskFilter: "リスクで絞り込み",
    detail: "詳細",
    /** サイド／オーバーレイの詳細枠の見出し */
    detailPanelTitle: "詳細",
    /** × ボタン・キーボードで閉じる旨の補助用 */
    closeDetailPanel: "詳細パネルを閉じる",
    closeDetailPanelBackdrop: "詳細を閉じて一覧に戻る",
    /** 詳細パネルヘッダー下の補助（キー表示用ラベル） */
    detailPanelFindingLabel: "検知キー",
    /** 詳細パネル: 媒体・案件・アフィのまとめ見出し */
    detailPanelRelatedTitle: "紐づく媒体・案件・アフィリエイター",
    listFiltersLegend: "一覧の絞り込み",
    tableDisplayLegend: "表示切替",
    /** 検知理由の種類が同じ行を束ねる（当ページ内のみ） */
    groupByReasonPattern: "同じ検知理由の行をまとめる",
    groupByReasonHint:
      "同じ種類の検知理由が付いた行を、まとめて1行で表示します。現在のページに出ている行だけが対象です。",
    groupPatternSummary: (count: number) => `検知理由が同じ ${count}件`,
    groupExpand: "内訳を表示",
    groupCollapse: "内訳を閉じる",
    backToList: "一覧に戻る",
    detailBreadcrumb: "不審コンバージョン / 詳細",
    /** 詳細画面のキーボード案内 */
    detailEscapeHint: "Esc キーで詳細を閉じられます",
    close: "閉じる",
    all: "すべて",
    high: "高",
    medium: "中",
    low: "低",
    sortCount: "件数が多い順",
    sortRisk: "リスクが高い順",
    sortLatest: "検知が新しい順",
    reasons: "検知理由",
    relatedRows: "内訳（媒体・案件別）",
    summary: "概要",
    media: "媒体",
    program: "案件",
    affiliate: "アフィリエイター",
    risk: "リスク",
    firstSeen: "初回検知",
    lastSeen: "最終検知",
    clickToCvGap: "クリック〜CV の時間差",
    clickPadding: "クリック水増し指標",
    linkedClicks: "紐づきクリック数",
    clicksPerCv: "CVあたりクリック数",
    extraWindowClicks: "前後30分の追加クリック",
    extraWindowNonBrowserRatio: "追加クリックの非ブラウザ率",
    columnIp: "IP",
    /** 一覧ヘッダー用の短縮表示（完全名は aria-label / title） */
    columnUserAgent: "ユーザーエージェント",
    columnUserAgentShort: "UA",
    columnReasonsShort: "理由",
    tableColumnClicksShort: "クリック",
    tableColumnCvShort: "CV",
    detailTableClick: "クリック",
    detailTableCv: "CV",
  },
  pagination: {
    first: "先頭",
    prev: "前へ",
    next: "次へ",
    last: "末尾",
  },
  states: {
    loadingRange: "読み込み中…",
    emptyRange: "該当データなし",
    emptyTitle: "条件に一致する検知結果はありません",
    emptyMessage: "日付や絞り込みを変えて、再度お試しください。",
    loadErrorTitle: "一覧を取得できませんでした",
    unauthorizedTitle: "ログインが必要です",
    unauthorizedMessage: "一覧を表示するには、閲覧権限でのログインが必要です。",
    forbiddenTitle: "この一覧を表示する権限がありません",
    forbiddenMessage: "アカウントにこの一覧の閲覧権限がありません。",
    transientTitle: "一時的に取得できませんでした",
    transientMessage: "しばらくしてから再読み込みしてください。",
    detailLoading: "詳細を読み込み中です…",
    detailError: "詳細を取得できませんでした。",
    staleHint:
      "一覧は表示できますが、直近の再集計結果ではない可能性があります。",
    detailForbidden: "この詳細を表示する権限がありません。",
    detailUnauthorized: "詳細を表示するにはログインが必要です。",
  },
} as const;

/** 一覧の「n〜m件（全k件）」表示用 */
export function formatSuspiciousResultRange(start: number, end: number, total: number) {
  return `${start}〜${end}件（全${total.toLocaleString()}件）`;
}
