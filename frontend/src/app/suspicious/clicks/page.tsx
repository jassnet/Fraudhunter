"use client";

import SuspiciousListPage from "@/components/suspicious-list-page";
import { suspiciousCopy } from "@/copy/suspicious";
import { fetchSuspiciousClickDetail, fetchSuspiciousClicks } from "@/lib/api";

export default function SuspiciousClicksPage() {
  return (
    <SuspiciousListPage
      title={suspiciousCopy.clicksTitle}
      countLabel={suspiciousCopy.countLabelClicks}
      fetcher={fetchSuspiciousClicks}
      fetchDetail={fetchSuspiciousClickDetail}
      metricKey="total_clicks"
    />
  );
}
