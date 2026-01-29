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
        <span key={`${item}-${idx}`} className="rounded-full border px-2 py-0.5 text-xs">
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
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-1 text-xs">
          <div className="text-muted-foreground">First seen</div>
          <div className="font-mono text-xs">{item.first_time || "-"}</div>
        </div>
        <div className="space-y-1 text-xs">
          <div className="text-muted-foreground">Last seen</div>
          <div className="font-mono text-xs">{item.last_time || "-"}</div>
        </div>
        <div className="space-y-1 text-xs">
          <div className="text-muted-foreground">Risk</div>
          <div className="text-xs">
            {item.risk_label || item.risk_level || "-"}
            {typeof item.risk_score === "number" ? ` (score ${item.risk_score})` : ""}
          </div>
        </div>
        <div className="space-y-1 text-xs">
          <div className="text-muted-foreground">Click to conversion</div>
          <div className="text-xs">
            Min {formatSeconds(item.min_click_to_conv_seconds)} / Max {formatSeconds(item.max_click_to_conv_seconds)}
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <div className="text-xs text-muted-foreground">Reasons</div>
        {reasons.length ? (
          <div className="flex flex-wrap gap-2">
            {reasons.map((reason, idx) => (
              <span key={`${reason}-${idx}`} className="rounded-full border px-2 py-0.5 text-xs">
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
          <div className="text-xs text-muted-foreground">Media</div>
          {renderTags(item.media_names)}
        </div>
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground">Programs</div>
          {renderTags(item.program_names)}
        </div>
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground">Affiliates</div>
          {renderTags(item.affiliate_names)}
        </div>
      </div>

      {details.length > 0 ? (
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground">Breakdown</div>
          <div className="overflow-hidden rounded-md border">
            <table className="w-full text-xs">
              <thead className="bg-muted/40 text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">Media</th>
                  <th className="px-3 py-2 text-left font-medium">Program</th>
                  <th className="px-3 py-2 text-left font-medium">Affiliate</th>
                  <th className="px-3 py-2 text-right font-medium">Clicks</th>
                  <th className="px-3 py-2 text-right font-medium">Conversions</th>
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
              Showing {visibleDetails.length} of {details.length} rows
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
