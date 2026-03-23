"use client";

import SuspiciousListPage from "@/components/suspicious-list-page";
import { fetchSuspiciousConversions } from "@/lib/api";

export default function SuspiciousConversionsPage() {
  return (
    <SuspiciousListPage
      title="不審コンバージョン"
      description="コンバージョン起点の検知ルールに該当した IP アドレスと User-Agent を確認します。"
      countLabel="CV 数"
      fetcher={fetchSuspiciousConversions}
      metricKey="total_conversions"
    />
  );
}
