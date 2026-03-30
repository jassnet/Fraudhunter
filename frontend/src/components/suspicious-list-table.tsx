"use client";

import { Fragment } from "react";
import { SuspiciousRowDetails } from "@/components/suspicious-row-details";
import { Button } from "@/components/ui/button";
import { SectionFrame } from "@/components/ui/section-frame";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { suspiciousCopy } from "@/copy/suspicious";
import type { SuspiciousItem } from "@/lib/api";

const riskToneMap: Record<string, "high" | "medium" | "low" | "neutral"> = {
  high: "high",
  medium: "medium",
  low: "low",
};

function maskedValue(value?: string, masked?: string, isMasked?: boolean) {
  if (!isMasked) return value || "-";
  return masked || suspiciousCopy.labels.masked;
}

interface SuspiciousListTableProps {
  title: string;
  metricKey: "total_clicks" | "total_conversions";
  data: SuspiciousItem[];
  expandedRow: string | null;
  getDetailState: (
    item: SuspiciousItem
  ) => {
    item: SuspiciousItem;
    status: "idle" | "loading" | "ready" | "expired" | "unauthorized" | "forbidden" | "error";
    message: string | null;
  };
  onToggleRow: (item: SuspiciousItem, rowKey: string, isExpanded: boolean) => Promise<void>;
}

export function SuspiciousListTable({
  title,
  metricKey,
  data,
  expandedRow,
  getDetailState,
  onToggleRow,
}: SuspiciousListTableProps) {
  return (
    <SectionFrame title={title}>
      <div className="space-y-3">
        <div className="text-[12px] text-foreground/68">{suspiciousCopy.states.maskedHint}</div>
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="w-[10rem]">IP</TableHead>
              <TableHead className="hidden w-[18rem] lg:table-cell">User-Agent</TableHead>
              <TableHead className="w-[10rem]">{title}</TableHead>
              <TableHead className="hidden w-[7rem] md:table-cell">{suspiciousCopy.labels.risk}</TableHead>
              <TableHead className="hidden w-[9rem] xl:table-cell">{suspiciousCopy.labels.reasons}</TableHead>
              <TableHead className="w-28 text-right">{suspiciousCopy.labels.detail}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((item) => {
              const rowKey = item.finding_key || `${item.ipaddress}-${item.useragent}`;
              const detailState = getDetailState(item);
              const isExpanded = expandedRow === rowKey;

              return (
                <Fragment key={rowKey}>
                  <TableRow className={item.risk_level === "high" ? "bg-destructive/[0.04]" : ""}>
                    <TableCell className="font-mono text-[12px] text-foreground/92">
                      <div>{maskedValue(item.ipaddress, item.ipaddress_masked, item.sensitive_values_masked)}</div>
                      {item.sensitive_values_masked ? (
                        <div className="mt-1 text-[11px] text-foreground/58">{suspiciousCopy.labels.masked}</div>
                      ) : null}
                    </TableCell>
                    <TableCell className="hidden text-[12px] text-foreground/82 lg:table-cell">
                      {maskedValue(item.useragent, item.useragent_masked, item.sensitive_values_masked)}
                    </TableCell>
                    <TableCell className="tabular-nums text-[13px] text-foreground">
                      {metricKey === "total_clicks"
                        ? item.total_clicks?.toLocaleString()
                        : item.total_conversions?.toLocaleString()}
                    </TableCell>
                    <TableCell className="hidden md:table-cell">
                      <StatusBadge tone={riskToneMap[item.risk_level || ""] || "neutral"}>
                        {item.risk_label || item.risk_level || "-"}
                      </StatusBadge>
                    </TableCell>
                    <TableCell className="hidden text-[12px] text-foreground/78 xl:table-cell">
                      {item.reasons_formatted?.[0] || item.reasons?.[0] || "-"}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => void onToggleRow(item, rowKey, isExpanded)}
                        className="min-w-[4.75rem] whitespace-nowrap"
                      >
                        {isExpanded ? suspiciousCopy.labels.close : suspiciousCopy.labels.detail}
                      </Button>
                    </TableCell>
                  </TableRow>
                  {isExpanded ? (
                    <TableRow className="hover:bg-transparent">
                      <TableCell colSpan={6} className="p-0">
                        <SuspiciousRowDetails
                          item={detailState.item}
                          status={detailState.status}
                          detailError={detailState.message}
                        />
                      </TableCell>
                    </TableRow>
                  ) : null}
                </Fragment>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </SectionFrame>
  );
}
