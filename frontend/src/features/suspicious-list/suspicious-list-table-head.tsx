import { TableHead, TableRow } from "@/components/ui/table";
import { suspiciousCopy } from "@/copy/suspicious";
import { cn } from "@/lib/utils";
import type { SuspiciousTableColumnId, SuspiciousTableLayout } from "./suspicious-list-table-config";

const headBase =
  "sticky top-0 z-[1] h-10 !px-2 !py-2 align-middle text-[11px] font-semibold leading-tight tracking-tight text-muted-foreground bg-card shadow-[inset_0_-1px_0_0_hsl(var(--border))]";

/** 不審CV: 先頭にメトリック列。colgroup は使わず % は目安（ table-fixed との競合を避ける） */
const cvMetricHeadClass =
  "min-w-[4.5rem] w-[22%] text-right sm:min-w-[5rem] md:w-[18%] lg:w-[15%] xl:w-[13%] text-[12px] font-bold tracking-tight text-foreground";

function headClass(column: SuspiciousTableColumnId, layout: SuspiciousTableLayout): string {
  if (layout === "cv_conversions") {
    switch (column) {
      case "metric":
        return cn(headBase, "h-11", cvMetricHeadClass);
      case "ip":
        return cn(headBase, "min-w-0 w-[36%] text-left md:w-[28%] lg:w-[22%] xl:w-[18%]");
      case "ua":
        return cn(headBase, "hidden min-w-0 text-left lg:table-cell lg:w-[24%] xl:w-[20%]");
      case "risk":
        return cn(headBase, "hidden text-left md:table-cell md:w-[14%] lg:w-[11%] xl:w-[9%]");
      case "reason":
        return cn(headBase, "hidden min-w-0 text-left xl:table-cell xl:w-[22%]");
      case "action":
        return cn(headBase, "min-w-[4.5rem] w-[34%] text-right md:w-[38%] lg:w-[26%] xl:w-[12%]");
      default:
        return headBase;
    }
  }
  switch (column) {
    case "ip":
      return cn(headBase, "w-[42%] min-w-0 text-left md:w-[30%] lg:w-[22%] xl:w-[18%]");
    case "ua":
      return cn(headBase, "hidden min-w-0 text-left lg:table-cell lg:w-[28%] xl:w-[24%]");
    case "metric":
      return cn(headBase, "w-[24%] text-right tabular-nums md:w-[14%] lg:w-[10%] xl:w-[9%]");
    case "risk":
      return cn(headBase, "hidden text-left md:table-cell md:w-[16%] lg:w-[12%] xl:w-[10%]");
    case "reason":
      return cn(headBase, "hidden min-w-0 text-left xl:table-cell xl:w-[27%]");
    case "action":
      return cn(headBase, "w-[34%] text-right md:w-[40%] lg:w-[28%] xl:w-[12%]");
    default:
      return headBase;
  }
}

function headLabel(
  column: SuspiciousTableColumnId,
  sectionTitle: string
): { text: string; ariaLabel: string; title: string } {
  switch (column) {
    case "metric":
      return {
        text: sectionTitle,
        ariaLabel: sectionTitle,
        title: sectionTitle,
      };
    case "ip":
      return {
        text: suspiciousCopy.labels.columnIp,
        ariaLabel: suspiciousCopy.labels.columnIp,
        title: suspiciousCopy.labels.columnIp,
      };
    case "ua":
      return {
        text: suspiciousCopy.labels.columnUserAgentShort,
        ariaLabel: suspiciousCopy.labels.columnUserAgent,
        title: suspiciousCopy.labels.columnUserAgent,
      };
    case "risk":
      return {
        text: suspiciousCopy.labels.risk,
        ariaLabel: suspiciousCopy.labels.risk,
        title: suspiciousCopy.labels.risk,
      };
    case "reason":
      return {
        text: suspiciousCopy.labels.columnReasonsShort,
        ariaLabel: suspiciousCopy.labels.reasons,
        title: suspiciousCopy.labels.reasons,
      };
    case "action":
      return {
        text: suspiciousCopy.labels.detail,
        ariaLabel: suspiciousCopy.labels.detail,
        title: suspiciousCopy.labels.detail,
      };
    default:
      return { text: "", ariaLabel: "", title: "" };
  }
}

interface SuspiciousTableHeadRowProps {
  layout: SuspiciousTableLayout;
  order: readonly SuspiciousTableColumnId[];
  sectionTitle: string;
}

export function SuspiciousTableHeadRow({ layout, order, sectionTitle }: SuspiciousTableHeadRowProps) {
  return (
    <TableRow className="hover:bg-transparent">
      {order.map((column) => {
        const { text, ariaLabel, title } = headLabel(column, sectionTitle);
        return (
          <TableHead
            key={column}
            scope="col"
            aria-label={ariaLabel}
            title={title}
            className={headClass(column, layout)}
          >
            {text}
          </TableHead>
        );
      })}
    </TableRow>
  );
}
