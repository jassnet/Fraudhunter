"use client";

import type { ReactNode } from "react";

import { SuspiciousItem } from "@/lib/api";

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
    <div className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
      {label}
    </div>
    <div className="mt-2 text-xs text-foreground">{value}</div>
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

  return (
    <div className="space-y-4 border-t border-border bg-background px-4 py-4">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <Stat
          label="IP"
          value={<span className="font-mono text-[11px] break-all">{item.ipaddress || "-"}</span>}
        />
        <Stat
          label="USER-AGENT"
          value={<span className="text-[11px] break-all">{item.useragent || "-"}</span>}
        />
        <Stat
          label="初回検知"
          value={<span className="font-mono text-[11px]">{item.first_time || "-"}</span>}
        />
        <Stat
          label="最終検知"
          value={<span className="font-mono text-[11px]">{item.last_time || "-"}</span>}
        />
        <Stat
          label="リスク"
          value={
            <>
              {item.risk_label || item.risk_level || "-"}
              {typeof item.risk_score === "number" ? ` / ${item.risk_score}` : ""}
            </>
          }
        />
        <Stat
          label="Click→CV"
          value={`最短 ${formatSeconds(item.min_click_to_conv_seconds)} / 最長 ${formatSeconds(item.max_click_to_conv_seconds)}`}
        />
      </div>

      <div className="space-y-2">
        <div className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
          検知理由
        </div>
        {reasons.length ? (
          <div className="flex flex-wrap gap-2">
            {reasons.map((reason, idx) => (
              <span
                key={`${reason}-${idx}`}
                className="border border-border px-2 py-1 text-xs text-foreground"
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
          <div className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
            媒体
          </div>
          {renderTags(item.media_names)}
        </div>
        <div className="space-y-2">
          <div className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
            案件
          </div>
          {renderTags(item.program_names)}
        </div>
        <div className="space-y-2">
          <div className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
            アフィリエイター
          </div>
          {renderTags(item.affiliate_names)}
        </div>
      </div>

      {isLoadingDetails ? (
        <div className="text-xs text-muted-foreground">詳細を読み込み中です</div>
      ) : null}
      {detailError ? <div className="text-xs text-destructive">{detailError}</div> : null}

      {!isLoadingDetails && !detailError && details.length > 0 ? (
        <div className="space-y-2">
          <div className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
            詳細内訳
          </div>
          <div className="overflow-x-auto border border-border">
            <table className="w-full text-xs">
              <thead className="border-b border-border text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 text-left font-semibold uppercase tracking-[0.12em]">
                    媒体
                  </th>
                  <th className="px-3 py-2 text-left font-semibold uppercase tracking-[0.12em]">
                    案件
                  </th>
                  <th className="px-3 py-2 text-left font-semibold uppercase tracking-[0.12em]">
                    アフィリエイター
                  </th>
                  <th className="px-3 py-2 text-right font-semibold uppercase tracking-[0.12em]">
                    Click
                  </th>
                  <th className="px-3 py-2 text-right font-semibold uppercase tracking-[0.12em]">
                    CV
                  </th>
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
