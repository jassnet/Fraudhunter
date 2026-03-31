"use client";

import type { ReactNode } from "react";
import { StatePanel } from "@/components/ui/state-panel";
import { StatusBadge } from "@/components/ui/status-badge";
import { suspiciousCopy } from "@/features/suspicious-list/copy";
import type { SuspiciousItem } from "@/lib/api";
import { cn } from "@/lib/utils";

const riskToneMap: Record<string, "high" | "medium" | "low" | "neutral"> = {
  high: "high",
  medium: "medium",
  low: "low",
};

const formatSeconds = (value?: number | null) => {
  if (typeof value !== "number" || !Number.isFinite(value)) return "-";
  const rounded = Math.round(value);
  if (rounded < 60) return `${rounded}s`;
  const minutes = Math.floor(rounded / 60);
  const seconds = rounded % 60;
  return seconds === 0 ? `${minutes}m` : `${minutes}m ${seconds}s`;
};

const formatCount = (value?: number | null) =>
  typeof value === "number" && Number.isFinite(value) ? value.toLocaleString("en-US") : "-";

const formatDecimal = (value?: number | null) =>
  typeof value === "number" && Number.isFinite(value)
    ? value.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 })
    : "-";

const formatPercent = (value?: number | null) =>
  typeof value === "number" && Number.isFinite(value)
    ? value.toLocaleString("en-US", {
        style: "percent",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      })
    : "-";

const renderTags = (items?: string[], pillClassName?: string) => {
  if (!items || items.length === 0) {
    return <span className="text-xs text-muted-foreground">-</span>;
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item, index) => (
        <span
          key={`${item}-${index}`}
          className={cn("border border-border px-2 py-0.5 text-xs text-foreground", pillClassName)}
        >
          {item}
        </span>
      ))}
    </div>
  );
};

function SectionLabel({
  children,
  compact,
}: {
  children: ReactNode;
  compact?: boolean;
}) {
  return (
    <div className={cn("flex items-center gap-2", compact ? "pb-1.5" : "pb-2.5")}>
      <span className="h-2.5 w-0.5 shrink-0 bg-primary" aria-hidden />
      <h3
        className={cn(
          "text-[11px] font-semibold uppercase tracking-[0.08em]",
          compact ? "text-foreground/75" : "text-muted-foreground"
        )}
      >
        {children}
      </h3>
    </div>
  );
}

function Field({
  label,
  children,
  mono,
  compact,
}: {
  label: string;
  children: ReactNode;
  mono?: boolean;
  compact?: boolean;
}) {
  return (
    <div className="min-w-0">
      <div className={cn("text-[11px]", compact ? "text-foreground/75" : "text-muted-foreground")}>
        {label}
      </div>
      <div
        className={cn(
          "mt-0.5 min-w-0 text-[13px] leading-snug text-foreground",
          mono && "font-mono text-[12px]"
        )}
      >
        {children}
      </div>
    </div>
  );
}

interface SuspiciousRowDetailsProps {
  item: SuspiciousItem;
  status?: "idle" | "loading" | "ready" | "expired" | "unauthorized" | "forbidden" | "error";
  detailError?: string | null;
  className?: string;
  variant?: "default" | "panel";
}

export function SuspiciousRowDetails({
  item,
  status = "ready",
  detailError,
  className,
  variant = "default",
}: SuspiciousRowDetailsProps) {
  const isPanel = variant === "panel";
  const compact = isPanel;
  const reasons = item.reason_groups?.length
    ? item.reason_groups
    : item.reasons_formatted?.length
      ? item.reasons_formatted
      : item.reasons || [];
  const details = item.details || [];
  const visibleDetails = isPanel ? details : details.slice(0, 5);
  const evidenceExpired = item.evidence_status === "expired" || item.evidence_expired === true;
  const showBreakdownTable =
    !evidenceExpired && status === "ready" && !detailError && details.length > 0;
  const hasRelatedTags =
    (item.media_names?.length ?? 0) > 0 ||
    (item.program_names?.length ?? 0) > 0 ||
    (item.affiliate_names?.length ?? 0) > 0;
  const showRelatedTagSection = hasRelatedTags && !showBreakdownTable;

  const detailBlockingState =
    status === "loading" ? (
      <StatePanel title={suspiciousCopy.states.detailLoading} tone="info" />
    ) : status === "unauthorized" ? (
      <StatePanel
        title={suspiciousCopy.states.unauthorizedTitle}
        message={suspiciousCopy.states.detailUnauthorized}
        tone="warning"
      />
    ) : status === "forbidden" ? (
      <StatePanel
        title={suspiciousCopy.states.forbiddenTitle}
        message={suspiciousCopy.states.detailForbidden}
        tone="danger"
      />
    ) : status === "error" ? (
      <StatePanel
        title={suspiciousCopy.states.detailError}
        message={detailError || suspiciousCopy.states.detailError}
        tone="warning"
      />
    ) : null;

  const clickPaddingData = [
    { label: suspiciousCopy.labels.linkedClicks, value: formatCount(item.linked_click_count) },
    {
      label: suspiciousCopy.labels.clicksPerCv,
      value: formatDecimal(item.linked_clicks_per_conversion),
    },
    {
      label: suspiciousCopy.labels.extraWindowClicks,
      value: formatCount(item.extra_window_click_count),
    },
    {
      label: suspiciousCopy.labels.extraWindowNonBrowserRatio,
      value: formatPercent(item.extra_window_non_browser_ratio),
    },
  ];

  const breakdownTable = showBreakdownTable ? (
    <div className="max-w-full overflow-x-auto rounded-md border border-border bg-muted">
      <table className={cn("w-full table-fixed", compact ? "min-w-[28rem] text-[12px]" : "text-xs")}>
        <thead className="border-b border-border bg-muted text-foreground">
          <tr>
            <th className={cn("text-left font-semibold", compact ? "px-2.5 py-2 text-[11px]" : "px-3 py-2")}>
              {suspiciousCopy.labels.media}
            </th>
            <th className={cn("text-left font-semibold", compact ? "px-2.5 py-2 text-[11px]" : "px-3 py-2")}>
              {suspiciousCopy.labels.program}
            </th>
            <th className={cn("text-left font-semibold", compact ? "px-2.5 py-2 text-[11px]" : "px-3 py-2")}>
              {suspiciousCopy.labels.affiliate}
            </th>
            <th className={cn("text-right font-semibold", compact ? "px-2.5 py-2 text-[11px]" : "px-3 py-2")}>
              {suspiciousCopy.labels.detailTableClick}
            </th>
            <th className={cn("text-right font-semibold", compact ? "px-2.5 py-2 text-[11px]" : "px-3 py-2")}>
              {suspiciousCopy.labels.detailTableCv}
            </th>
          </tr>
        </thead>
        <tbody>
          {visibleDetails.map((detail, index) => (
            <tr
              key={`${detail.media_id}-${detail.program_id}-${index}`}
              className="border-t border-border odd:bg-card even:bg-muted"
            >
              <td className={cn("min-w-0 break-words text-foreground", compact ? "px-2.5 py-2" : "px-3 py-2")}>
                {detail.media_name}
              </td>
              <td className={cn("min-w-0 break-words text-foreground", compact ? "px-2.5 py-2" : "px-3 py-2")}>
                {detail.program_name}
              </td>
              <td className={cn("min-w-0 break-words text-foreground", compact ? "px-2.5 py-2" : "px-3 py-2")}>
                {detail.affiliate_name || "-"}
              </td>
              <td className={cn("text-right tabular-nums text-foreground", compact ? "px-2.5 py-2" : "px-3 py-2")}>
                {detail.click_count ?? "-"}
              </td>
              <td className={cn("text-right tabular-nums text-foreground", compact ? "px-2.5 py-2" : "px-3 py-2")}>
                {detail.conversion_count ?? "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  ) : null;

  const relatedTags = showRelatedTagSection ? (
    <div className={cn("grid gap-2", compact ? "grid-cols-1 sm:grid-cols-3" : "gap-4 xl:grid-cols-3")}>
      {[
        { label: suspiciousCopy.labels.media, items: item.media_names },
        { label: suspiciousCopy.labels.program, items: item.program_names },
        { label: suspiciousCopy.labels.affiliate, items: item.affiliate_names },
      ].map((group) => (
        <div key={group.label} className="min-w-0">
          <div className={cn("text-muted-foreground", compact ? "text-[10px]" : "text-[12px]")}>
            {group.label}
          </div>
          <div className="mt-1">
            {renderTags(
              group.items,
              compact ? "rounded-[var(--radius)] bg-muted text-[11px] leading-tight text-foreground" : undefined
            )}
          </div>
        </div>
      ))}
    </div>
  ) : null;

  const reasonsList = reasons.length > 0 ? (
    <ul className={cn("space-y-1", !compact && "space-y-1.5")}>
      {reasons.map((reason, index) => (
        <li
          key={`${reason}-${index}`}
          className={cn(
            "border-l-2 border-primary/40 leading-snug text-foreground",
            compact ? "pl-2.5 text-[12px] leading-relaxed" : "pl-3 text-[13px] leading-relaxed"
          )}
        >
          {reason}
        </li>
      ))}
    </ul>
  ) : (
    <span className="text-xs text-muted-foreground">-</span>
  );

  const gapSummary = (
    <span className="tabular-nums">
      {suspiciousCopy.labels.minGap} {formatSeconds(item.min_click_to_conv_seconds)}
      {" / "}
      {suspiciousCopy.labels.maxGap} {formatSeconds(item.max_click_to_conv_seconds)}
    </span>
  );

  if (isPanel) {
    return (
      <div className={cn("relative isolate min-w-0", className)}>
        {detailBlockingState ? <div className="shrink-0 p-2">{detailBlockingState}</div> : null}

        <div className="space-y-1.5 pb-2">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5">
            <StatusBadge tone={riskToneMap[item.risk_level || ""] || "neutral"}>
              {item.risk_label || item.risk_level || "-"}
            </StatusBadge>
            {typeof item.risk_score === "number" ? (
              <span className="tabular-nums text-[12px] font-medium text-foreground/85">
                {suspiciousCopy.labels.score} {item.risk_score}
              </span>
            ) : null}
          </div>
          <div className="space-y-1">
            <div className="break-all font-mono text-[13px] leading-snug text-foreground">
              {item.ipaddress || "-"}
            </div>
            <div className="break-words text-[11px] leading-relaxed text-foreground/90">
              {item.useragent || "-"}
            </div>
          </div>
        </div>

        <div className="border-t border-border py-2.5">
          <div className="grid grid-cols-2 gap-x-3 gap-y-1.5">
            <Field label={suspiciousCopy.labels.firstSeen} mono compact>
              {item.first_time || "-"}
            </Field>
            <Field label={suspiciousCopy.labels.lastSeen} mono compact>
              {item.last_time || "-"}
            </Field>
            <div className="col-span-2">
              <Field label={suspiciousCopy.labels.clickToCvGap} compact>
                {gapSummary}
              </Field>
            </div>
          </div>
        </div>

        <div className="border-t border-border py-2.5">
          <SectionLabel compact>{suspiciousCopy.labels.clickPadding}</SectionLabel>
          <div className="grid grid-cols-2 gap-1.5">
            {clickPaddingData.map((stat) => (
              <div key={stat.label} className="min-w-0 rounded-md border border-border bg-muted px-2 py-1.5">
                <div className="break-words text-[10px] font-medium leading-tight text-foreground/80">
                  {stat.label}
                </div>
                <div className="mt-0.5 tabular-nums text-[14px] font-semibold text-foreground">
                  {stat.value}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-border py-2.5">
          <SectionLabel compact>{suspiciousCopy.labels.reasons}</SectionLabel>
          {reasonsList}
        </div>

        {relatedTags ? (
          <div className="border-t border-border py-2.5">
            <SectionLabel compact>{suspiciousCopy.labels.detailPanelRelatedTitle}</SectionLabel>
            {relatedTags}
          </div>
        ) : null}

        {breakdownTable ? (
          <div className="border-t border-border py-2.5">
            <SectionLabel compact>{suspiciousCopy.labels.relatedRows}</SectionLabel>
            {breakdownTable}
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div className={cn("space-y-5 border-t border-border bg-background px-4 py-4", className)}>
      {detailBlockingState ? (
        <div className="border border-border bg-card p-4">{detailBlockingState}</div>
      ) : null}

      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <StatusBadge tone={riskToneMap[item.risk_level || ""] || "neutral"}>
            {item.risk_label || item.risk_level || "-"}
          </StatusBadge>
          {typeof item.risk_score === "number" ? (
            <span className="tabular-nums text-[13px] text-muted-foreground">
              {suspiciousCopy.labels.score} {item.risk_score}
            </span>
          ) : null}
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label={suspiciousCopy.labels.columnIp} mono>
            <span className="break-all">{item.ipaddress || "-"}</span>
          </Field>
          <Field label={suspiciousCopy.labels.columnUserAgent}>
            <span className="break-all">{item.useragent || "-"}</span>
          </Field>
        </div>
      </div>

      <div className="border-t border-border pt-4">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Field label={suspiciousCopy.labels.firstSeen} mono>
            {item.first_time || "-"}
          </Field>
          <Field label={suspiciousCopy.labels.lastSeen} mono>
            {item.last_time || "-"}
          </Field>
          <Field label={suspiciousCopy.labels.clickToCvGap}>{gapSummary}</Field>
        </div>
      </div>

      <div className="border-t border-border pt-4">
        <SectionLabel>{suspiciousCopy.labels.clickPadding}</SectionLabel>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {clickPaddingData.map((stat) => (
            <div key={stat.label} className="bg-muted/15 px-3 py-2.5">
              <div className="text-[11px] text-muted-foreground">{stat.label}</div>
              <div className="mt-1 tabular-nums text-[14px] font-medium text-foreground">
                {stat.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-border pt-4">
        <SectionLabel>{suspiciousCopy.labels.reasons}</SectionLabel>
        {reasonsList}
      </div>

      {relatedTags ? (
        <div className="border-t border-border pt-4">
          <SectionLabel>{suspiciousCopy.labels.detailPanelRelatedTitle}</SectionLabel>
          {relatedTags}
        </div>
      ) : null}

      {breakdownTable ? (
        <div className="border-t border-border pt-4">
          <SectionLabel>{suspiciousCopy.labels.relatedRows}</SectionLabel>
          {breakdownTable}
          {details.length > visibleDetails.length ? (
            <div className="mt-2 text-xs text-muted-foreground">
              {visibleDetails.length} shown / {details.length} total
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
