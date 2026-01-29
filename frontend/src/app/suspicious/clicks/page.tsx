"use client";

import SuspiciousListPage from "@/components/suspicious-list-page";
import { fetchSuspiciousClicks } from "@/lib/api";

export default function SuspiciousClicksPage() {
  return (
    <SuspiciousListPage
      title="Suspicious Clicks"
      description="IPs and user agents flagged by click-based rules."
      countLabel="Clicks"
      fetcher={fetchSuspiciousClicks}
      metricKey="total_clicks"
    />
  );
}
