"use client";

import SuspiciousListPage from "@/components/suspicious-list-page";
import { fetchSuspiciousConversions } from "@/lib/api";

export default function SuspiciousConversionsPage() {
  return (
    <SuspiciousListPage
      title="Suspicious Conversions"
      description="Conversion-based suspicious IP/UA patterns."
      countLabel="Conversions"
      fetcher={fetchSuspiciousConversions}
      metricKey="total_conversions"
    />
  );
}
