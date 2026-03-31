"use client";

import { Fragment, useEffect, useMemo, useState, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { suspiciousCopy } from "@/copy/suspicious";
import {
  clusterSuspiciousItems,
  getReasonClusterKey,
  sumMetric,
  worstRiskLabel,
  worstRiskLevel,
} from "@/features/suspicious-list/reason-cluster";
import {
  COLUMN_ORDER,
  type MetricKey,
  type SuspiciousTableColumnId,
  type SuspiciousTableLayout,
  layoutFromMetricKey,
} from "@/features/suspicious-list/suspicious-list-table-config";
import { SuspiciousTableHeadRow } from "@/features/suspicious-list/suspicious-list-table-head";
import { cn } from "@/lib/utils";
import type { SuspiciousItem } from "@/lib/api";

const riskToneMap: Record<string, "high" | "medium" | "low" | "neutral"> = {
  high: "high",
  medium: "medium",
  low: "low",
};

const cellClass = "!px-2 !py-2 align-middle min-w-0";

/** CV 一覧: 数値をやや強調（列幅はヘッダー側の % に任せる） */
const cvMetricCellClass =
  "text-right align-middle tabular-nums text-base font-semibold leading-none tracking-tight text-foreground sm:text-lg sm:pr-1";

function maskedValue(value?: string, masked?: string, isMasked?: boolean) {
  if (!isMasked) return value || "-";
  return masked?.trim() ? masked : "—";
}

function getReasonSummary(item: SuspiciousItem) {
  return item.reason_summary?.trim() || item.reasons_formatted?.[0] || item.reasons?.[0] || "-";
}

function getExtraReasonCount(item: SuspiciousItem) {
  if (typeof item.reason_group_count !== "number" || item.reason_group_count <= 1) {
    return 0;
  }
  return item.reason_group_count - 1;
}

function rowKey(item: SuspiciousItem) {
  return item.finding_key || `${item.ipaddress}-${item.useragent}`;
}

function metricCellClass(layout: SuspiciousTableLayout): string {
  return layout === "cv_conversions"
    ? cvMetricCellClass
    : "text-right tabular-nums text-[13px] text-foreground";
}

interface SuspiciousListTableProps {
  title: string;
  metricKey: MetricKey;
  data: SuspiciousItem[];
  onOpenDetail: (item: SuspiciousItem) => void | Promise<void>;
  groupByReason?: boolean;
}

export function SuspiciousListTable({
  title,
  metricKey,
  data,
  onOpenDetail,
  groupByReason = false,
}: SuspiciousListTableProps) {
  const [expandedClusters, setExpandedClusters] = useState<Set<string>>(() => new Set());

  useEffect(() => {
    if (!groupByReason) {
      setExpandedClusters(new Set());
    }
  }, [groupByReason]);

  const groups = useMemo(() => clusterSuspiciousItems(data), [data]);
  const layout = layoutFromMetricKey(metricKey);
  const columnOrder = COLUMN_ORDER[layout];

  const toggleCluster = (clusterKey: string) => {
    setExpandedClusters((prev) => {
      const next = new Set(prev);
      if (next.has(clusterKey)) next.delete(clusterKey);
      else next.add(clusterKey);
      return next;
    });
  };

  const captionText =
    layout === "cv_conversions"
      ? `${title}の検知一覧。列は${title}・IP・ユーザーエージェント・リスク・理由・詳細の順です。`
      : `${title}の検知一覧。列はIP・ユーザーエージェント・${title}・リスク・理由・詳細の順です。`;

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
      <div className="min-h-0 min-w-0 flex-1 overflow-x-auto overflow-y-auto overscroll-contain [scrollbar-gutter:stable] px-2 pb-3 pt-2 sm:px-3">
        <Table className="!table-auto w-full min-w-0 max-w-full">
          <caption className="sr-only">{captionText}</caption>
          <TableHeader>
            <SuspiciousTableHeadRow layout={layout} order={columnOrder} sectionTitle={title} />
          </TableHeader>
          <TableBody>
            {groups.flatMap((group) => {
              const { clusterKey, members } = group;
              const multi = groupByReason && members.length > 1;
              if (!multi) {
                const item = members[0]!;
                return [
                  <DataRow
                    key={rowKey(item)}
                    item={item}
                    metricKey={metricKey}
                    layout={layout}
                    columnOrder={columnOrder}
                    onOpenDetail={onOpenDetail}
                  />,
                ];
              }

              const expanded = expandedClusters.has(clusterKey);
              const representative = members[0]!;
              const reasonSummary = getReasonSummary(representative);
              const extraReasonCount = getExtraReasonCount(representative);
              const totalMetric = sumMetric(members, metricKey);
              const riskLvl = worstRiskLevel(members);
              const riskLbl = worstRiskLabel(members);

              const cells: Record<SuspiciousTableColumnId, ReactNode> = {
                metric: (
                  <TableCell className={cn(cellClass, metricCellClass(layout))}>
                    {totalMetric.toLocaleString()}
                  </TableCell>
                ),
                ip: (
                  <TableCell className={`${cellClass} font-mono text-[12px] text-foreground/92`}>
                    <div className="flex min-w-0 items-start gap-1.5">
                      <button
                        type="button"
                        className="mt-0.5 shrink-0 rounded-sm text-[14px] leading-none text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60"
                        aria-expanded={expanded}
                        aria-label={
                          expanded ? suspiciousCopy.labels.groupCollapse : suspiciousCopy.labels.groupExpand
                        }
                        onClick={() => toggleCluster(clusterKey)}
                      >
                        {expanded ? "▾" : "▸"}
                      </button>
                      <div className="min-w-0 break-words">
                        <span className="font-sans text-[12px] font-medium text-foreground">
                          {suspiciousCopy.labels.groupPatternSummary(members.length)}
                        </span>
                      </div>
                    </div>
                  </TableCell>
                ),
                ua: (
                  <TableCell className={`${cellClass} hidden text-[12px] text-muted-foreground lg:table-cell`}>
                    —
                  </TableCell>
                ),
                risk: (
                  <TableCell className={`${cellClass} hidden md:table-cell`}>
                    <StatusBadge tone={riskToneMap[riskLvl || ""] || "neutral"}>
                      {riskLbl || riskLvl || "-"}
                    </StatusBadge>
                  </TableCell>
                ),
                reason: (
                  <TableCell className={`${cellClass} hidden text-[12px] text-foreground/78 xl:table-cell`}>
                    <div className="line-clamp-2 break-words" title={reasonSummary}>
                      {reasonSummary}
                      {extraReasonCount > 0 ? (
                        <span className="ml-1 text-[11px] text-muted-foreground">{`\u4ed6${extraReasonCount}\u4ef6`}</span>
                      ) : null}
                    </div>
                  </TableCell>
                ),
                action: (
                  <TableCell className={cn(cellClass, "text-right align-middle")}>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => toggleCluster(clusterKey)}
                      className="h-8 max-w-full whitespace-nowrap px-2.5 text-[12px] font-medium"
                    >
                      {expanded ? suspiciousCopy.labels.groupCollapse : suspiciousCopy.labels.groupExpand}
                    </Button>
                  </TableCell>
                ),
              };

              const rows: ReactNode[] = [
                <TableRow
                  key={`g:${clusterKey}`}
                  className={cn(
                    "bg-muted/25 outline-none transition-colors duration-150",
                    "hover:bg-muted/35 focus-within:bg-muted/35"
                  )}
                >
                  {columnOrder.map((col) => (
                    <Fragment key={col}>{cells[col]}</Fragment>
                  ))}
                </TableRow>,
              ];

              if (expanded) {
                for (const item of members) {
                  rows.push(
                    <DataRow
                      key={rowKey(item)}
                      item={item}
                      metricKey={metricKey}
                      layout={layout}
                      columnOrder={columnOrder}
                      onOpenDetail={onOpenDetail}
                      indent
                    />
                  );
                }
              }

              return rows;
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function DataRow({
  item,
  metricKey,
  layout,
  columnOrder,
  onOpenDetail,
  indent = false,
}: {
  item: SuspiciousItem;
  metricKey: MetricKey;
  layout: SuspiciousTableLayout;
  columnOrder: readonly SuspiciousTableColumnId[];
  onOpenDetail: (item: SuspiciousItem) => void | Promise<void>;
  indent?: boolean;
}) {
  const reasonSummary = getReasonSummary(item);
  const extraReasonCount = getExtraReasonCount(item);
  const metricDisplay =
    metricKey === "total_clicks"
      ? item.total_clicks?.toLocaleString()
      : item.total_conversions?.toLocaleString();

  const cells: Record<SuspiciousTableColumnId, ReactNode> = {
    metric: (
      <TableCell className={cn(cellClass, metricCellClass(layout))}>
        {metricDisplay}
      </TableCell>
    ),
    ip: (
      <TableCell className={`${cellClass} font-mono text-[12px] text-foreground/92`}>
        <div className={cn("break-all", indent ? "pl-3" : undefined)}>
          {maskedValue(item.ipaddress, item.ipaddress_masked, item.sensitive_values_masked)}
        </div>
      </TableCell>
    ),
    ua: (
      <TableCell className={`${cellClass} hidden text-[12px] text-foreground/82 lg:table-cell`}>
        <div className="line-clamp-2 break-all lg:line-clamp-3">
          {maskedValue(item.useragent, item.useragent_masked, item.sensitive_values_masked)}
        </div>
      </TableCell>
    ),
    risk: (
      <TableCell className={`${cellClass} hidden md:table-cell`}>
        <StatusBadge tone={riskToneMap[item.risk_level || ""] || "neutral"}>
          {item.risk_label || item.risk_level || "-"}
        </StatusBadge>
      </TableCell>
    ),
    reason: (
      <TableCell className={`${cellClass} hidden text-[12px] text-foreground/78 xl:table-cell`}>
        <div className="line-clamp-2 break-words" title={reasonSummary}>
          {reasonSummary}
          {extraReasonCount > 0 ? (
            <span className="ml-1 text-[11px] text-muted-foreground">{`\u4ed6${extraReasonCount}\u4ef6`}</span>
          ) : null}
        </div>
      </TableCell>
    ),
    action: (
      <TableCell className={cn(cellClass, "text-right align-middle")}>
        <Button
          variant="outline"
          size="sm"
          onClick={(event) => {
            event.stopPropagation();
            void onOpenDetail(item);
          }}
          className="h-8 max-w-full whitespace-nowrap px-2.5 text-[12px] font-medium"
        >
          {suspiciousCopy.labels.detail}
        </Button>
      </TableCell>
    ),
  };

  return (
    <TableRow
      tabIndex={0}
      data-cluster-member={indent ? getReasonClusterKey(item) : undefined}
      onClick={() => void onOpenDetail(item)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          void onOpenDetail(item);
        }
      }}
      aria-label={`${suspiciousCopy.labels.detail}を開く`}
      className={cn(
        "cursor-pointer outline-none transition-colors duration-150",
        "hover:bg-muted/30 focus-visible:bg-muted/35 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring/60",
        item.risk_level === "high" ? "bg-destructive/[0.04]" : undefined,
        indent ? "border-l-2 border-l-primary/25 bg-card/80" : undefined
      )}
    >
      {columnOrder.map((col) => (
        <Fragment key={col}>{cells[col]}</Fragment>
      ))}
    </TableRow>
  );
}
