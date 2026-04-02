"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { suspiciousCopy } from "@/features/suspicious-list/copy";
import {
  clusterSuspiciousItems,
  getReasonClusterKey,
  sumConversions,
  worstRiskLabel,
  worstRiskLevel,
} from "@/features/suspicious-list/reason-cluster";
import type { SuspiciousItem } from "@/lib/api";
import { cn } from "@/lib/utils";

const riskToneMap: Record<string, "high" | "medium" | "low" | "neutral"> = {
  high: "high",
  medium: "medium",
  low: "low",
};

const cellClass = "!px-2 !py-2 align-middle min-w-0";
const headBase =
  "sticky top-0 z-[1] h-10 !px-2 !py-2 align-middle bg-card text-[11px] font-semibold leading-tight tracking-tight text-muted-foreground shadow-[inset_0_-1px_0_0_hsl(var(--border))]";
const emptyExpandedClusters = new Set<string>();

function maskedValue(value?: string, masked?: string, isMasked?: boolean) {
  if (!isMasked) return value || "-";
  return masked?.trim() ? masked : suspiciousCopy.labels.hiddenValue;
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

interface SuspiciousListTableProps {
  data: SuspiciousItem[];
  onOpenDetail: (item: SuspiciousItem) => void | Promise<void>;
  groupByReason?: boolean;
}

interface DataRowProps {
  item: SuspiciousItem;
  onOpenDetail: (item: SuspiciousItem) => void | Promise<void>;
  indent?: boolean;
}

export function SuspiciousListTable({
  data,
  onOpenDetail,
  groupByReason = false,
}: SuspiciousListTableProps) {
  const [expandedClusters, setExpandedClusters] = useState<Set<string>>(() => new Set());
  const groups = useMemo(() => clusterSuspiciousItems(data), [data]);
  const visibleExpandedClusters = groupByReason ? expandedClusters : emptyExpandedClusters;

  const toggleCluster = (clusterKey: string) => {
    setExpandedClusters((previous) => {
      const next = new Set(previous);
      if (next.has(clusterKey)) {
        next.delete(clusterKey);
      } else {
        next.add(clusterKey);
      }
      return next;
    });
  };

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
      <div className="min-h-0 min-w-0 flex-1 overflow-x-auto overflow-y-auto overscroll-contain [scrollbar-gutter:stable] px-2 pb-3 pt-2 sm:px-3">
        <Table className="!table-auto w-full min-w-0 max-w-full">
          <caption className="sr-only">
            リスク、理由の概要、詳細操作を含む不審コンバージョン一覧
          </caption>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead
                scope="col"
                aria-label={suspiciousCopy.countLabelConversions}
                title={suspiciousCopy.countLabelConversions}
                className={cn(
                  headBase,
                  "h-11 w-[22%] min-w-[4.5rem] text-right text-[12px] font-bold tracking-tight text-foreground sm:min-w-[5rem] md:w-[18%] lg:w-[15%] xl:w-[13%]"
                )}
              >
                {suspiciousCopy.countLabelConversions}
              </TableHead>
              <TableHead
                scope="col"
                aria-label={suspiciousCopy.labels.columnIp}
                title={suspiciousCopy.labels.columnIp}
                className={cn(headBase, "w-[36%] min-w-0 text-left md:w-[28%] lg:w-[22%] xl:w-[18%]")}
              >
                {suspiciousCopy.labels.columnIp}
              </TableHead>
              <TableHead
                scope="col"
                aria-label={suspiciousCopy.labels.columnUserAgent}
                title={suspiciousCopy.labels.columnUserAgent}
                className={cn(headBase, "hidden min-w-0 text-left lg:table-cell lg:w-[24%] xl:w-[20%]")}
              >
                {suspiciousCopy.labels.columnUserAgentShort}
              </TableHead>
              <TableHead
                scope="col"
                aria-label={suspiciousCopy.labels.risk}
                title={suspiciousCopy.labels.risk}
                className={cn(headBase, "hidden text-left md:table-cell md:w-[14%] lg:w-[11%] xl:w-[9%]")}
              >
                {suspiciousCopy.labels.risk}
              </TableHead>
              <TableHead
                scope="col"
                aria-label={suspiciousCopy.labels.reasons}
                title={suspiciousCopy.labels.reasons}
                className={cn(headBase, "hidden min-w-0 text-left xl:table-cell xl:w-[22%]")}
              >
                {suspiciousCopy.labels.columnReasonsShort}
              </TableHead>
              <TableHead
                scope="col"
                aria-label={suspiciousCopy.labels.detail}
                title={suspiciousCopy.labels.detail}
                className={cn(headBase, "w-[34%] min-w-[4.5rem] text-right md:w-[38%] lg:w-[26%] xl:w-[12%]")}
              >
                {suspiciousCopy.labels.detail}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {groups.flatMap((group) => {
              const { clusterKey, members } = group;
              const multi = groupByReason && members.length > 1;

              if (!multi) {
                return [
                  <DataRow
                    key={rowKey(members[0]!)}
                    item={members[0]!}
                    onOpenDetail={onOpenDetail}
                  />,
                ];
              }

              const expanded = visibleExpandedClusters.has(clusterKey);
              const representative = members[0]!;
              const reasonSummary = getReasonSummary(representative);
              const extraReasonCount = getExtraReasonCount(representative);
              const totalConversions = sumConversions(members);
              const riskLevel = worstRiskLevel(members);
              const riskLabel = worstRiskLabel(members);

              return [
                <TableRow
                  key={`g:${clusterKey}`}
                  className={cn(
                    "bg-muted/25 outline-none transition-colors duration-150",
                    "hover:bg-muted/35 focus-within:bg-muted/35"
                  )}
                >
                  <TableCell
                    className={cn(
                      cellClass,
                      "text-right align-middle text-base font-semibold leading-none tracking-tight text-foreground tabular-nums sm:pr-1 sm:text-lg"
                    )}
                  >
                    {totalConversions.toLocaleString("ja-JP")}
                  </TableCell>
                  <TableCell className={`${cellClass} font-mono text-[12px] text-foreground/92`}>
                    <div className="flex min-w-0 items-start gap-1.5">
                      <button
                        type="button"
                        className="mt-0.5 shrink-0 rounded-sm text-[14px] leading-none text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60"
                        aria-expanded={expanded}
                        aria-label={
                          expanded
                            ? suspiciousCopy.labels.groupCollapse
                            : suspiciousCopy.labels.groupExpand
                        }
                        onClick={() => toggleCluster(clusterKey)}
                      >
                        {expanded ? "-" : "+"}
                      </button>
                      <div className="min-w-0 break-words">
                        <span className="font-sans text-[12px] font-medium text-foreground">
                          {suspiciousCopy.labels.groupPatternSummary(members.length)}
                        </span>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className={`${cellClass} hidden text-[12px] text-muted-foreground lg:table-cell`}>
                    -
                  </TableCell>
                  <TableCell className={`${cellClass} hidden md:table-cell`}>
                    <StatusBadge tone={riskToneMap[riskLevel || ""] || "neutral"}>
                      {riskLabel || riskLevel || "-"}
                    </StatusBadge>
                  </TableCell>
                  <TableCell className={`${cellClass} hidden text-[12px] text-foreground/78 xl:table-cell`}>
                    <div className="line-clamp-2 break-words" title={reasonSummary}>
                      {reasonSummary}
                      {extraReasonCount > 0 ? (
                        <span className="ml-1 text-[11px] text-muted-foreground">
                          {suspiciousCopy.labels.extraCount(extraReasonCount)}
                        </span>
                      ) : null}
                    </div>
                  </TableCell>
                  <TableCell className={cn(cellClass, "text-right align-middle")}>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => toggleCluster(clusterKey)}
                      className="h-8 max-w-full whitespace-nowrap px-2.5 text-[12px] font-medium"
                    >
                      {expanded
                        ? suspiciousCopy.labels.groupCollapse
                        : suspiciousCopy.labels.groupExpand}
                    </Button>
                  </TableCell>
                </TableRow>,
                ...(expanded
                  ? members.map((item) => (
                      <DataRow
                        key={rowKey(item)}
                        item={item}
                        onOpenDetail={onOpenDetail}
                        indent
                      />
                    ))
                  : []),
              ];
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function DataRow({ item, onOpenDetail, indent = false }: DataRowProps) {
  const reasonSummary = getReasonSummary(item);
  const extraReasonCount = getExtraReasonCount(item);
  const metricDisplay =
    typeof item.total_conversions === "number"
      ? item.total_conversions.toLocaleString("ja-JP")
      : "-";

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
      aria-label={suspiciousCopy.labels.rowActionLabel(item.ipaddress_masked || item.ipaddress)}
      className={cn(
        "cursor-pointer outline-none transition-colors duration-150",
        "hover:bg-muted/30 focus-visible:bg-muted/35 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring/60",
        item.risk_level === "high" ? "bg-destructive/[0.04]" : undefined,
        indent ? "border-l-2 border-l-primary/25 bg-card/80" : undefined
      )}
    >
      <TableCell
        className={cn(
          cellClass,
          "text-right align-middle text-base font-semibold leading-none tracking-tight text-foreground tabular-nums sm:pr-1 sm:text-lg"
        )}
      >
        {metricDisplay}
      </TableCell>
      <TableCell className={`${cellClass} font-mono text-[12px] text-foreground/92`}>
        <div className={cn("break-all", indent ? "pl-3" : undefined)}>
          {maskedValue(item.ipaddress, item.ipaddress_masked, item.sensitive_values_masked)}
        </div>
      </TableCell>
      <TableCell className={`${cellClass} hidden text-[12px] text-foreground/82 lg:table-cell`}>
        <div className="line-clamp-2 break-all lg:line-clamp-3">
          {maskedValue(item.useragent, item.useragent_masked, item.sensitive_values_masked)}
        </div>
      </TableCell>
      <TableCell className={`${cellClass} hidden md:table-cell`}>
        <StatusBadge tone={riskToneMap[item.risk_level || ""] || "neutral"}>
          {item.risk_label || item.risk_level || "-"}
        </StatusBadge>
      </TableCell>
      <TableCell className={`${cellClass} hidden text-[12px] text-foreground/78 xl:table-cell`}>
        <div className="line-clamp-2 break-words" title={reasonSummary}>
          {reasonSummary}
          {extraReasonCount > 0 ? (
            <span className="ml-1 text-[11px] text-muted-foreground">
              {suspiciousCopy.labels.extraCount(extraReasonCount)}
            </span>
          ) : null}
        </div>
      </TableCell>
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
    </TableRow>
  );
}
