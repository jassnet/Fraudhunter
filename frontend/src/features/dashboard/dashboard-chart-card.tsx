import type { ReactNode } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { dashboardCopy } from "@/features/dashboard/copy";

interface DashboardChartCardProps {
  children: ReactNode;
}

export function DashboardChartCard({ children }: DashboardChartCardProps) {
  return (
    <section className="flex min-h-0 flex-1 flex-col overflow-hidden border border-border bg-card">
      <div className="flex min-h-12 items-center border-b border-border bg-muted/35 px-4 py-3">
        <h2 className="text-sm font-semibold tracking-[0.02em] text-foreground">
          {dashboardCopy.labels.chart}
        </h2>
      </div>
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden p-3 sm:p-4">{children}</div>
    </section>
  );
}

export function DashboardChartSkeleton() {
  return (
    <DashboardChartCard>
      <Skeleton className="min-h-[12rem] flex-1 rounded-none" />
    </DashboardChartCard>
  );
}
