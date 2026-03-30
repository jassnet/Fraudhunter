"use client";

import type { ReactNode } from "react";
import type { SuspiciousItem } from "@/lib/api";
import { suspiciousCopy } from "@/copy/suspicious";
import { StatePanel } from "@/components/ui/state-panel";
import { StatusBadge } from "@/components/ui/status-badge";

const riskToneMap: Record<string, "high" | "medium" | "low" | "neutral"> = {
  high: "high",
  medium: "medium",
  low: "low",
};

const formatSeconds = (value?: number | null) => {
  if (typeof value !== "number" || !Number.isFinite(value)) return "-";
  const rounded = Math.round(value);
  if (rounded < 60) return `${rounded}秒`;
  const minutes = Math.floor(rounded / 60);
  const seconds = rounded % 60;
  return seconds === 0 ? `${minutes}分` : `${minutes}分${seconds}秒`;
};

const renderTags = (items?: string[]) => {
  if (!items || items.length === 0) {
    return <span className="text-xs text-muted-foreground">-</span>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item, idx) => (
        <span
          key={`${item}-${idx}`}
          className="border border-border px-2 py-1 text-xs text-foreground"
        >
          {item}
        </span>
      ))}
    </div>
  );
};

const Stat = ({ label, value }: { label: string; value: ReactNode }) => (
  <div className="border border-border px-3 py-3">
    <div className="text-[12px] text-foreground/72">{label}</div>
    <div className="mt-2 text-[13px] leading-5 text-foreground">{value}</div>
  </div>
);

interface SuspiciousRowDetailsProps {
  item: SuspiciousItem;
  status?: "idle" | "loading" | "ready" | "expired" | "unauthorized" | "forbidden" | "error";
  detailError?: string | null;
}

export function SuspiciousRowDetails({
  item,
  status = "ready",
  detailError,
}: SuspiciousRowDetailsProps) {
  const reasons = item.reasons_formatted?.length ? item.reasons_formatted : item.reasons || [];
  const details = item.details || [];
  const visibleDetails = details.slice(0, 5);
  const evidenceExpired = item.evidence_status === "expired" || item.evidence_expired === true;

  const evidencePanel =
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
    ) : evidenceExpired || status === "expired" ? (
      <StatePanel
        title="証跡保持期限切れ"
        message={`${suspiciousCopy.states.evidenceExpired}${item.evidence_expires_on ? ` 期限: ${item.evidence_expires_on}` : ""}`}
        tone="warning"
      />
    ) : (
      <StatePanel
        title="証跡利用可能"
        message={`${suspiciousCopy.states.evidenceAvailable}${item.evidence_expires_on ? ` 期限: ${item.evidence_expires_on}` : ""}`}
        tone="neutral"
      />
    );

  return (
    <div className="space-y-4 border-t border-border bg-background px-4 py-4">
      <div className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
        <div className="space-y-3">
          <div className="text-[13px] font-semibold text-foreground/88">
            {suspiciousCopy.labels.summary}
          </div>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            <Stat
              label="IP"
              value={<span className="font-mono text-[11px] break-all">{item.ipaddress || "-"}</span>}
            />
            <Stat
              label="User-Agent"
              value={<span className="text-[11px] break-all">{item.useragent || "-"}</span>}
            />
            <Stat
              label={suspiciousCopy.labels.firstSeen}
              value={<span className="font-mono text-[11px]">{item.first_time || "-"}</span>}
            />
            <Stat
              label={suspiciousCopy.labels.lastSeen}
              value={<span className="font-mono text-[11px]">{item.last_time || "-"}</span>}
            />
            <Stat
              label={suspiciousCopy.labels.risk}
              value={
                <div className="flex items-center gap-2">
                  <StatusBadge tone={riskToneMap[item.risk_level || ""] || "neutral"}>
                    {item.risk_label || item.risk_level || "-"}
                  </StatusBadge>
                  {typeof item.risk_score === "number" ? (
                    <span className="tabular-nums text-[12px] text-foreground/70">{item.risk_score}</span>
                  ) : null}
                </div>
              }
            />
            <Stat
              label={suspiciousCopy.labels.clickToCvGap}
              value={`最短 ${formatSeconds(item.min_click_to_conv_seconds)} / 最長 ${formatSeconds(
                item.max_click_to_conv_seconds
              )}`}
            />
          </div>
        </div>

        <div className="space-y-3">
          <div className="text-[13px] font-semibold text-foreground/88">
            {suspiciousCopy.labels.evidence}
          </div>
          {evidencePanel}
        </div>
      </div>

      <div className="space-y-2">
        <div className="text-[13px] font-semibold text-foreground/88">
          {suspiciousCopy.labels.reasons}
        </div>
        {reasons.length ? (
          <div className="flex flex-wrap gap-2">
            {reasons.map((reason, idx) => (
              <span
                key={`${reason}-${idx}`}
                className="border border-border bg-white/[0.02] px-2 py-1 text-[13px] leading-5 text-foreground/88"
              >
                {reason}
              </span>
            ))}
          </div>
        ) : (
          <span className="text-xs text-muted-foreground">-</span>
        )}
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-2">
          <div className="text-[12px] text-foreground/72">{suspiciousCopy.labels.media}</div>
          {renderTags(item.media_names)}
        </div>
        <div className="space-y-2">
          <div className="text-[12px] text-foreground/72">{suspiciousCopy.labels.program}</div>
          {renderTags(item.program_names)}
        </div>
        <div className="space-y-2">
          <div className="text-[12px] text-foreground/72">{suspiciousCopy.labels.affiliate}</div>
          {renderTags(item.affiliate_names)}
        </div>
      </div>

      {!evidenceExpired && status === "ready" && !detailError && details.length > 0 ? (
        <div className="space-y-2">
          <div className="text-[13px] font-semibold text-foreground/88">
            {suspiciousCopy.labels.relatedRows}
          </div>
          <div className="overflow-x-auto border border-border">
            <table className="w-full text-xs">
              <thead className="border-b border-border text-foreground/70">
                <tr>
                  <th className="px-3 py-2 text-left font-semibold">{suspiciousCopy.labels.media}</th>
                  <th className="px-3 py-2 text-left font-semibold">{suspiciousCopy.labels.program}</th>
                  <th className="px-3 py-2 text-left font-semibold">{suspiciousCopy.labels.affiliate}</th>
                  <th className="px-3 py-2 text-right font-semibold">Click</th>
                  <th className="px-3 py-2 text-right font-semibold">CV</th>
                </tr>
              </thead>
              <tbody>
                {visibleDetails.map((detail, idx) => (
                  <tr key={`${detail.media_id}-${detail.program_id}-${idx}`} className="border-t border-border">
                    <td className="px-3 py-2">{detail.media_name}</td>
                    <td className="px-3 py-2">{detail.program_name}</td>
                    <td className="px-3 py-2">{detail.affiliate_name || "-"}</td>
                    <td className="px-3 py-2 text-right tabular-nums">{detail.click_count ?? "-"}</td>
                    <td className="px-3 py-2 text-right tabular-nums">{detail.conversion_count ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {details.length > visibleDetails.length ? (
            <div className="text-xs text-muted-foreground">
              {visibleDetails.length}件表示 / 全{details.length}件
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
