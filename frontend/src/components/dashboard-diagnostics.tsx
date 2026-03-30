import { MetricBlock } from "@/components/ui/metric-strip";
import { SectionFrame } from "@/components/ui/section-frame";
import { dashboardCopy } from "@/copy/dashboard";

interface DashboardDiagnosticsProps {
  diagnostics: {
    coverage?: {
      missing: number;
      missing_rate: number;
    } | null;
    enrichment?: {
      enriched: number;
      total: number;
      success_rate: number;
    } | null;
    findingsFreshness?: string | null;
    findingsStale: boolean;
    masterSyncAt?: string | null;
  };
}

const formatCoverage = (missingRate?: number | null) =>
  typeof missingRate === "number" ? `${Math.round((1 - missingRate) * 1000) / 10}%` : "-";

const formatRate = (value?: number | null) =>
  typeof value === "number" ? `${Math.round(value * 1000) / 10}%` : "-";

export function DashboardDiagnostics({ diagnostics }: DashboardDiagnosticsProps) {
  return (
    <SectionFrame title={dashboardCopy.labels.diagnostics}>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <MetricBlock
          label={dashboardCopy.labels.coverage}
          value={formatCoverage(diagnostics.coverage?.missing_rate)}
          meta={
            diagnostics.coverage
              ? `${diagnostics.coverage.missing.toLocaleString()}件が未補完`
              : dashboardCopy.diagnosticsText.noSignal
          }
          emphasis="diagnostic"
        />
        <MetricBlock
          label={dashboardCopy.labels.enrichment}
          value={formatRate(diagnostics.enrichment?.success_rate)}
          meta={
            diagnostics.enrichment
              ? `${diagnostics.enrichment.enriched.toLocaleString()} / ${diagnostics.enrichment.total.toLocaleString()}`
              : dashboardCopy.diagnosticsText.noSignal
          }
          emphasis="diagnostic"
        />
        <MetricBlock
          label={dashboardCopy.labels.findingsFreshness}
          value={diagnostics.findingsFreshness ? "最新" : "未計測"}
          meta={
            diagnostics.findingsStale
              ? dashboardCopy.diagnosticsText.stale
              : dashboardCopy.diagnosticsText.healthy
          }
          tone={diagnostics.findingsStale ? "warning" : "neutral"}
          emphasis="diagnostic"
        />
        <MetricBlock
          label={dashboardCopy.labels.masterSync}
          value={diagnostics.masterSyncAt ? "同期済み" : "未同期"}
          meta={diagnostics.masterSyncAt || dashboardCopy.diagnosticsText.masterSyncMissing}
          emphasis="diagnostic"
        />
      </div>
    </SectionFrame>
  );
}
