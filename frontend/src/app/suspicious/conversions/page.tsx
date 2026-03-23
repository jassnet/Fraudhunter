"use client";

import SuspiciousListPage from "@/components/suspicious-list-page";
import {
  fetchSuspiciousConversionDetail,
  fetchSuspiciousConversions,
} from "@/lib/api";

export default function SuspiciousConversionsPage() {
  return (
    <SuspiciousListPage
      title="不審コンバージョン"
      countLabel="CV数"
      fetcher={fetchSuspiciousConversions}
      fetchDetail={fetchSuspiciousConversionDetail}
      metricKey="total_conversions"
    />
  );
}
