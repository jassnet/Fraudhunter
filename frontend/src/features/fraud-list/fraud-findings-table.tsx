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
import { getFraudReasonSummary } from "@/features/fraud-list/fraud-finding-metrics";
import type { FraudFindingItem } from "@/lib/api";

const riskToneMap: Record<string, "high" | "medium" | "low" | "neutral"> = {
  high: "high",
  medium: "medium",
  low: "low",
};

interface FraudFindingsTableProps {
  data: FraudFindingItem[];
  onOpenDetail: (item: FraudFindingItem) => void | Promise<void>;
}

export function FraudFindingsTable({
  data,
  onOpenDetail,
}: FraudFindingsTableProps) {
  return (
    <div className="min-h-0 min-w-0 overflow-x-auto">
      <Table className="min-w-[58rem] table-fixed">
        <TableHeader className="bg-muted/35 text-left text-xs text-muted-foreground">
          <TableRow className="hover:bg-transparent">
            <TableHead className="w-[6.5rem] px-4 py-3 font-semibold">{fraudCopy.columns.metric}</TableHead>
            <TableHead className="w-[10rem] px-4 py-3 font-semibold">{fraudCopy.columns.user}</TableHead>
            <TableHead className="w-[9rem] px-4 py-3 font-semibold">{fraudCopy.columns.media}</TableHead>
            <TableHead className="w-[18rem] px-4 py-3 font-semibold">{fraudCopy.columns.promotion}</TableHead>
            <TableHead className="w-[8rem] px-4 py-3 font-semibold">{fraudCopy.columns.risk}</TableHead>
            <TableHead className="min-w-[14rem] px-4 py-3 font-semibold">{fraudCopy.columns.reasons}</TableHead>
            <TableHead className="w-[7rem] px-4 py-3 text-right font-semibold">
              {fraudCopy.columns.detail}
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((item) => (
            <TableRow key={item.finding_key} className="text-sm hover:bg-muted/20">
              <TableCell className="px-4 py-3 align-top tabular-nums font-semibold text-foreground">
                {item.primary_metric.toLocaleString("ja-JP")}
              </TableCell>
              <TableCell className="px-4 py-3 align-top font-medium text-foreground">
                {item.user_name}
              </TableCell>
              <TableCell className="px-4 py-3 align-top text-foreground/92">{item.media_name}</TableCell>
              <TableCell className="px-4 py-3 align-top">
                <div className="line-clamp-3 leading-relaxed text-foreground/92">{item.promotion_name}</div>
              </TableCell>
              <TableCell className="px-4 py-3 align-top">
                <StatusBadge tone={riskToneMap[item.risk_level || ""] || "neutral"}>
                  {item.risk_label || item.risk_level || "-"}
                </StatusBadge>
              </TableCell>
              <TableCell className="px-4 py-3 align-top">
                <div className="line-clamp-3 leading-relaxed text-foreground/92">
                  {getFraudReasonSummary(item)}
                </div>
              </TableCell>
              <TableCell className="px-4 py-3 text-right align-top">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => void onOpenDetail(item)}
                  className="min-w-[4.5rem]"
                >
                  {fraudCopy.labels.detail}
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
