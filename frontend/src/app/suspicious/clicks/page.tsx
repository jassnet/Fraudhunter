"use client";

import SuspiciousListPage from "@/components/suspicious-list-page";
import { fetchSuspiciousClicks } from "@/lib/api";

export default function SuspiciousClicksPage() {
  return (
    <SuspiciousListPage
      title="不正クリック検知"
      description="閾値を超えた異常なクリックパターンを示すIPアドレス一覧"
      ipLabel="IPアドレス"
      countLabel="クリック数"
      csvPrefix="suspicious_clicks"
      fetcher={fetchSuspiciousClicks}
      metricKey="total_clicks"
    />
  );
}
