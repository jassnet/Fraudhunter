export const dashboardCopy = {
  title: "Dashboard",
  loadingMeta: "Loading current snapshot",
  targetDateLabel: (date: string) => `Target date: ${date}`,
  labels: {
    clicks: "Tracked Clicks",
    conversions: "Conversions",
    suspiciousConversions: "Suspicious Conversions",
    chart: "Daily Trend",
  },
  states: {
    loadError: "Could not load the dashboard data.",
    noDataTitle: "No dashboard data available",
    noDataMessage: "Select another date or retry after the backend finishes loading data.",
    refresh: "Refresh",
    retry: "Retry",
    refreshing: "Refreshing...",
    transientTitle: "Temporary backend issue",
    staleTitle: "Suspicious findings are older than the latest ingest.",
    unauthorizedTitle: "Login required",
    forbiddenTitle: "You do not have access to this view.",
    genericErrorTitle: "Dashboard could not be rendered",
  },
  chart: {
    empty: "No daily data available.",
    title: "Rolling click and conversion trend",
    legends: {
      clicks: "Clicks",
      conversions: "Conversions",
      suspiciousConversions: "Suspicious",
    },
    subtitle: (days: number) => `Showing the last ${days} available days.`,
    maxLabel: (value: number) => `Max ${value.toLocaleString("en-US")}`,
  },
  admin: {
    unavailableShortHint: "Admin actions are hidden because the Admin API is not available.",
    title: "Admin actions",
    description: "Run a refresh or master sync without leaving the dashboard.",
    actions: {
      refresh: "Refresh ingest",
      masterSync: "Run master sync",
    },
    feedback: {
      refresh: {
        queued: "Refresh job queued",
        running: "Refresh job running",
        succeeded: "Refresh job completed",
        failed: "Refresh job failed",
      },
      masterSync: {
        queued: "Master sync queued",
        running: "Master sync running",
        succeeded: "Master sync completed",
        failed: "Master sync failed",
      },
    },
  },
} as const;
