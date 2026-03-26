"use client";

import type { ReactNode } from "react";

import type { SuspiciousItem } from "@/lib/api";
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
    <div className="text-xs tracking-[0.06em] text-foreground/78">{label}</div>
    <div className="mt-2 text-[13px] leading-5 text-foreground">{value}</div>
  </div>
);

interface SuspiciousRowDetailsProps {
  item: SuspiciousItem;
  isLoadingDetails?: boolean;
  detailError?: string | null;
}

export function SuspiciousRowDetails({
  item,
  isLoadingDetails = false,
  detailError,
}: SuspiciousRowDetailsProps) {
  const reasons = item.reasons_formatted?.length ? item.reasons_formatted : item.reasons || [];
  const details = item.details || [];
  const visibleDetails = details.slice(0, 5);
  const evidenceExpired = item.evidence_status === "expired" || item.evidence_expired === true;

  return (
    <div className="space-y-4 border-t border-border bg-background px-4 py-4">
      {item.evidence_status ? (
        <div
          className={
            evidenceExpired
              ? "border border-[hsl(var(--warning))]/45 bg-[hsl(var(--warning))]/10 px-3 py-3 text-[13px] leading-5 text-[hsl(var(--warning))]"
              : "border border-border bg-white/[0.03] px-3 py-3 text-[13px] leading-5 text-foreground/84"
          }
        >
          {evidenceExpired
            ? "証跡保持期限を過ぎているため、この finding は要約のみ表示しています。"
            : "証跡は保持期間内です。詳細調査に利用できます。"}
          {item.evidence_expires_on ? ` 保持期限: ${item.evidence_expires_on}` : ""}
        </div>
      ) : null}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <Stat
          label="IP"
          value={<span className="font-mono text-[11px] break-all">{item.ipaddress || "-"}</span>}
        />
        <Stat
          label="User-Agent"
          value={<span className="text-[11px] break-all">{item.useragent || "-"}</span>}
        />
        <Stat
          label="最初の発生"
          value={<span className="font-mono text-[11px]">{item.first_time || "-"}</span>}
        />
        <Stat
          label="最後の発生"
          value={<span className="font-mono text-[11px]">{item.last_time || "-"}</span>}
        />
        <Stat
          label="リスク"
          value={
            <div className="flex items-center gap-2">
              <StatusBadge tone={riskToneMap[item.risk_level || ""] || "neutral"}>
                {item.risk_label || item.risk_level || "-"}
              </StatusBadge>
              {typeof item.risk_score === "number" && (
                <span className="tabular-nums text-[12px] text-foreground/70">{item.risk_score}</span>
              )}
            </div>
          }
        />
        <Stat
          label="Click→CV 時間"
          value={`最短 ${formatSeconds(item.min_click_to_conv_seconds)} / 最長 ${formatSeconds(
            item.max_click_to_conv_seconds
          )}`}
        />
      </div>

      <div className="space-y-2">
        <div className="text-[11px] tracking-[0.06em] text-foreground/74">検知理由</div>
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
          <div className="text-xs tracking-[0.06em] text-foreground/78">媒体</div>
          {renderTags(item.media_names)}
        </div>
        <div className="space-y-2">
          <div className="text-xs tracking-[0.06em] text-foreground/78">案件</div>
          {renderTags(item.program_names)}
        </div>
        <div className="space-y-2">
          <div className="text-xs tracking-[0.06em] text-foreground/78">提携先</div>
          {renderTags(item.affiliate_names)}
        </div>
      </div>

      {isLoadingDetails ? (
        <div className="text-xs text-muted-foreground">詳細を読み込み中です...</div>
      ) : null}
      {detailError ? <div className="text-xs text-destructive">{detailError}</div> : null}

      {!evidenceExpired && !isLoadingDetails && !detailError && details.length > 0 ? (
        <div className="space-y-2">
          <div className="text-xs tracking-[0.06em] text-foreground/78">詳細内訳</div>
          <div className="overflow-x-auto border border-border">
            <table className="w-full text-xs">
              <thead className="border-b border-border text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 text-left font-semibold tracking-[0.12em]">媒体</th>
                  <th className="px-3 py-2 text-left font-semibold tracking-[0.12em]">案件</th>
                  <th className="px-3 py-2 text-left font-semibold tracking-[0.12em]">提携先</th>
                  <th className="px-3 py-2 text-right font-semibold tracking-[0.12em]">
                    Click
                  </th>
                  <th className="px-3 py-2 text-right font-semibold tracking-[0.12em]">CV</th>
                </tr>
              </thead>
              <tbody>
                {visibleDetails.map((detail, idx) => (
                  <tr
                    key={`${detail.media_id}-${detail.program_id}-${idx}`}
                    className="border-t border-border"
                  >
                    <td className="px-3 py-2">{detail.media_name}</td>
                    <td className="px-3 py-2">{detail.program_name}</td>
                    <td className="px-3 py-2">{detail.affiliate_name || "-"}</td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {detail.click_count ?? "-"}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {detail.conversion_count ?? "-"}
                    </td>
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
