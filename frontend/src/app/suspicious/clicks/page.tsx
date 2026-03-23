"use client";

import SuspiciousListPage from "@/components/suspicious-list-page";
import { fetchSuspiciousClicks } from "@/lib/api";

export default function SuspiciousClicksPage() {
  return (
    <SuspiciousListPage
      title="不審クリック"
      description="クリック起点の検知ルールに該当した IP アドレスと User-Agent を確認します。"
      countLabel="クリック数"
      fetcher={fetchSuspiciousClicks}
      metricKey="total_clicks"
    />
  );
}
