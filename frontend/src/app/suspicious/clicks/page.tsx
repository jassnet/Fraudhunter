"use client";

import SuspiciousListPage from "@/components/suspicious-list-page";
import { fetchSuspiciousClicks } from "@/lib/api";

export default function SuspiciousClicksPage() {
  return (
    <SuspiciousListPage
      title="Suspicious Clicks"
      description="Click-based suspicious IP/UA patterns."
      countLabel="Clicks"
      fetcher={fetchSuspiciousClicks}
      metricKey="total_clicks"
    />
  );
}
