"use client";

import SuspiciousListPage from "@/components/suspicious-list-page";
import { fetchSuspiciousConversions } from "@/lib/api";

export default function SuspiciousConversionsPage() {
  return (
    <SuspiciousListPage
      title="不審コンバージョン"
      countLabel="CV数"
      fetcher={fetchSuspiciousConversions}
      metricKey="total_conversions"
    />
  );
}
