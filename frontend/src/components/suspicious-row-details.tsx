"use client";

import { SuspiciousItem } from "@/lib/api";

const formatSeconds = (value?: number | null) => {
  if (typeof value !== "number" || !Number.isFinite(value)) return "-";
  const rounded = Math.round(value);
  if (rounded < 60) return `${rounded}s`;
  const minutes = Math.floor(rounded / 60);
  const seconds = rounded % 60;
  return `${minutes}m ${seconds}s`;
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
          className="rounded-md border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-700"
        >
          {item}
        </span>
      ))}
    </div>
  );
};

export function SuspiciousRowDetails({ item }: { item: SuspiciousItem }) {
  const reasons = item.reasons_formatted?.length
    ? item.reasons_formatted
    : item.reasons || [];
  const details = item.details || [];
  const visibleDetails = details.slice(0, 5);

  return (
    <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-5">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-md border border-slate-200 bg-white p-4 text-xs">
          <div className="text-muted-foreground">初回検知時刻</div>
          <div className="mt-2 font-mono text-xs text-slate-800">{item.first_time || "-"}</div>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4 text-xs">
          <div className="text-muted-foreground">最終検知時刻</div>
          <div className="mt-2 font-mono text-xs text-slate-800">{item.last_time || "-"}</div>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4 text-xs">
          <div className="text-muted-foreground">リスク</div>
          <div className="mt-2 text-xs text-slate-800">
            {item.risk_label || item.risk_level || "-"}
            {typeof item.risk_score === "number" ? ` (スコア ${item.risk_score})` : ""}
          </div>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4 text-xs">
          <div className="text-muted-foreground">クリックから CV まで</div>
          <div className="mt-2 text-xs text-slate-800">
            最短 {formatSeconds(item.min_click_to_conv_seconds)} / 最長 {formatSeconds(item.max_click_to_conv_seconds)}
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <div className="text-xs text-muted-foreground">検知理由</div>
        {reasons.length ? (
          <div className="flex flex-wrap gap-2">
            {reasons.map((reason, idx) => (
              <span
                key={`${reason}-${idx}`}
                className="rounded-md border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-700"
              >
                {reason}
              </span>
            ))}
          </div>
        ) : (
          <span className="text-xs text-muted-foreground">-</span>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground">メディア</div>
          {renderTags(item.media_names)}
        </div>
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground">案件</div>
          {renderTags(item.program_names)}
        </div>
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground">アフィリエイター</div>
          {renderTags(item.affiliate_names)}
        </div>
      </div>

      {details.length > 0 ? (
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground">内訳</div>
          <div className="overflow-hidden rounded-md border border-slate-200 bg-white">
            <table className="w-full text-xs">
              <thead className="bg-slate-50/85 text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">メディア</th>
                  <th className="px-3 py-2 text-left font-medium">案件</th>
                  <th className="px-3 py-2 text-left font-medium">アフィリエイター</th>
                  <th className="px-3 py-2 text-right font-medium">クリック数</th>
                  <th className="px-3 py-2 text-right font-medium">CV 数</th>
                </tr>
              </thead>
              <tbody>
                {visibleDetails.map((detail, idx) => (
                  <tr key={`${detail.media_id}-${detail.program_id}-${idx}`} className="border-t">
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
              {visibleDetails.length}件を表示中 / 全{details.length}件
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
