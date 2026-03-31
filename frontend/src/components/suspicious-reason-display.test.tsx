import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { suspiciousCopy } from "@/features/suspicious-list/copy";
import { SuspiciousListTable } from "@/features/suspicious-list/suspicious-list-table";
import { SuspiciousRowDetails } from "@/features/suspicious-list/suspicious-row-details";
import type { SuspiciousItem } from "@/lib/api";

const EXTRA_COUNT_LABEL = suspiciousCopy.labels.extraCount(1);

function buildItem(overrides: Partial<SuspiciousItem> = {}): SuspiciousItem {
  return {
    finding_key: "finding-1",
    date: "2026-01-21",
    ipaddress: "10.0.0.1",
    useragent: "Mozilla/TestAgent-1",
    total_conversions: 3,
    media_count: 2,
    program_count: 2,
    first_time: "2026-01-21T00:00:00Z",
    last_time: "2026-01-21T01:00:00Z",
    reasons: ["legacy raw reason"],
    reasons_formatted: ["Legacy formatted reason"],
    risk_level: "high",
    risk_score: 90,
    risk_label: "High",
    media_names: ["Media 1"],
    program_names: ["Program 1"],
    affiliate_names: ["Affiliate 1"],
    ...overrides,
  };
}

describe("Suspicious reason presentation", () => {
  it("renders grouped summary and extra count in the list", () => {
    render(
      <SuspiciousListTable
        data={[
          buildItem({
            reason_summary: "Grouped spread signal",
            reason_group_count: 2,
            reason_groups: ["Grouped spread signal", "Burst signal"],
          }),
        ]}
        onOpenDetail={vi.fn()}
      />
    );

    expect(screen.getByText("Grouped spread signal")).toBeInTheDocument();
    expect(screen.getByText(EXTRA_COUNT_LABEL)).toBeInTheDocument();
  });

  it("falls back to formatted reasons when grouped fields are absent", () => {
    render(<SuspiciousListTable data={[buildItem()]} onOpenDetail={vi.fn()} />);

    expect(screen.getByText("Legacy formatted reason")).toBeInTheDocument();
    expect(screen.queryByText(EXTRA_COUNT_LABEL)).not.toBeInTheDocument();
  });

  it("renders grouped reasons in details instead of raw formatted reasons", () => {
    render(
      <SuspiciousRowDetails
        item={buildItem({
          reason_groups: ["Grouped spread signal", "Burst signal"],
          reasons_formatted: ["Legacy formatted reason"],
        })}
        status="ready"
      />
    );

    expect(screen.getByText("Grouped spread signal")).toBeInTheDocument();
    expect(screen.getByText("Burst signal")).toBeInTheDocument();
    expect(screen.queryByText("Legacy formatted reason")).not.toBeInTheDocument();
  });
});
