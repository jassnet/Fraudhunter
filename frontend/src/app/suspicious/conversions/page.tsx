"use client";

import SuspiciousListPage from "@/components/suspicious-list-page";
import { fetchSuspiciousConversions } from "@/lib/api";

export default function SuspiciousConversionsPage() {
  return (
    <SuspiciousListPage
      title="不正成果検知"
      description="実ユーザーIPベースでの不正成果パターン検出（ポストバック経由含む）"
      ipLabel="実IPアドレス"
      countLabel="成果数"
      csvPrefix="suspicious_conversions"
      fetcher={fetchSuspiciousConversions}
      metricKey="total_conversions"
    />
  );
}
