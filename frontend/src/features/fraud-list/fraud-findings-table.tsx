"use client";

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
import { fraudCopy } from "@/features/fraud-list/copy";
import type { FraudFindingItem } from "@/lib/api";

const riskToneMap: Record<string, "high" | "medium" | "low" | "neutral"> = {
  high: "high",
  medium: "medium",
  low: "low",
};

function getReasonSummary(item: FraudFindingItem) {
  return item.reason_summary?.trim() || item.reasons_formatted?.[0] || item.reasons?.[0] || "-";
}

interface FraudFindingsTableProps {
  data: FraudFindingItem[];
  onOpenDetail: (item: FraudFindingItem) => void | Promise<void>;
}

export function FraudFindingsTable({
  data,
  onOpenDetail,
}: FraudFindingsTableProps) {
  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <div className="min-h-0 min-w-0 overflow-x-auto">
        <Table className="w-full table-fixed">
          <TableHeader className="bg-muted/40 text-left text-xs text-muted-foreground">
            <TableRow className="hover:bg-transparent">
              <TableHead className="px-3 py-2">{fraudCopy.columns.metric}</TableHead>
              <TableHead className="px-3 py-2">{fraudCopy.columns.user}</TableHead>
              <TableHead className="px-3 py-2">{fraudCopy.columns.media}</TableHead>
              <TableHead className="px-3 py-2">{fraudCopy.columns.promotion}</TableHead>
              <TableHead className="px-3 py-2">{fraudCopy.columns.risk}</TableHead>
              <TableHead className="px-3 py-2">{fraudCopy.columns.reasons}</TableHead>
              <TableHead className="px-3 py-2 text-right">{fraudCopy.columns.detail}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((item) => (
              <TableRow key={item.finding_key} className="text-sm">
                <TableCell className="px-3 py-2 tabular-nums">
                  {item.primary_metric.toLocaleString("ja-JP")}
                </TableCell>
                <TableCell className="px-3 py-2">{item.user_name}</TableCell>
                <TableCell className="px-3 py-2">{item.media_name}</TableCell>
                <TableCell className="px-3 py-2">{item.promotion_name}</TableCell>
                <TableCell className="px-3 py-2">
                  <StatusBadge tone={riskToneMap[item.risk_level || ""] || "neutral"}>
                    {item.risk_label || item.risk_level || "-"}
                  </StatusBadge>
                </TableCell>
                <TableCell className="px-3 py-2">{getReasonSummary(item)}</TableCell>
                <TableCell className="px-3 py-2 text-right">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => void onOpenDetail(item)}
                  >
                    {fraudCopy.labels.detail}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

