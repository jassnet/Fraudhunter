"use client";

import SuspiciousListPage from "@/components/suspicious-list-page";
import { suspiciousCopy } from "@/copy/suspicious";
import { fetchSuspiciousConversionDetail, fetchSuspiciousConversions } from "@/lib/api";

export default function SuspiciousConversionsPage() {
  return (
    <SuspiciousListPage
      title={suspiciousCopy.conversionsTitle}
      countLabel={suspiciousCopy.countLabelConversions}
      fetcher={fetchSuspiciousConversions}
      fetchDetail={fetchSuspiciousConversionDetail}
      metricKey="total_conversions"
    />
  );
}
