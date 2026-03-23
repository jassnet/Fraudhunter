"use client";

import SuspiciousListPage from "@/components/suspicious-list-page";
import { fetchSuspiciousClicks } from "@/lib/api";

export default function SuspiciousClicksPage() {
  return (
    <SuspiciousListPage
      title="不審クリック"
      countLabel="クリック数"
      fetcher={fetchSuspiciousClicks}
      metricKey="total_clicks"
    />
  );
}
