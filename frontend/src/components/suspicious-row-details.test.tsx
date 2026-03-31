import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SuspiciousRowDetails } from "@/components/suspicious-row-details";
import { suspiciousCopy } from "@/copy/suspicious";
import type { SuspiciousItem } from "@/lib/api";

function buildItem(overrides: Partial<SuspiciousItem> = {}): SuspiciousItem {
  return {
    finding_key: "finding-1",
    date: "2026-01-21",
    ipaddress: "10.0.0.1",
    useragent: "Mozilla/TestAgent-1",
    total_clicks: 42,
    media_count: 2,
    program_count: 1,
    first_time: "2026-01-21T00:00:00Z",
    last_time: "2026-01-21T01:00:00Z",
    reasons: ["total_clicks >= 50"],
    reasons_formatted: ["クリック数が閾値以上です (50件以上)"],
    risk_level: "high",
    risk_score: 90,
    risk_label: "高リスク",
    media_names: ["Media 1"],
    program_names: ["Program 1"],
    affiliate_names: ["Affiliate 1"],
    ...overrides,
  };
}

describe("SuspiciousRowDetails", () => {
  it("shows related breakdown when detail is ready and evidence not expired", () => {
    render(
      <SuspiciousRowDetails
        item={buildItem({
          evidence_status: "available",
          evidence_available: true,
          evidence_expires_on: "2026-04-20",
          details: [
            {
              media_id: "m1",
              program_id: "p1",
              media_name: "Media 1",
              program_name: "Program 1",
              affiliate_name: "Affiliate 1",
              click_count: 42,
            },
          ],
        })}
        status="ready"
      />
    );

    expect(screen.queryByText(suspiciousCopy.states.detailLoading)).not.toBeInTheDocument();
    expect(screen.getByText(suspiciousCopy.labels.relatedRows)).toBeInTheDocument();
    expect(screen.getAllByText("Media 1").length).toBeGreaterThan(0);
  });

  it("hides breakdown table when evidence expired but still shows list context", () => {
    render(
      <SuspiciousRowDetails
        item={buildItem({
          evidence_status: "expired",
          evidence_expired: true,
          evidence_available: false,
          evidence_expires_on: "2026-03-01",
          details: [
            {
              media_id: "m1",
              program_id: "p1",
              media_name: "Media 1",
              program_name: "Program 1",
              affiliate_name: "Affiliate 1",
              click_count: 42,
            },
          ],
        })}
        status="expired"
      />
    );

    expect(screen.queryByText(suspiciousCopy.labels.relatedRows)).not.toBeInTheDocument();
    expect(screen.getByText("Media 1")).toBeInTheDocument();
  });

  it("shows forbidden state separately from expired evidence", () => {
    render(<SuspiciousRowDetails item={buildItem()} status="forbidden" />);

    expect(screen.getByText(suspiciousCopy.states.forbiddenTitle)).toBeInTheDocument();
    expect(screen.getByText(suspiciousCopy.states.detailForbidden)).toBeInTheDocument();
  });

  it("shows click padding stats for conversion details", () => {
    render(
      <SuspiciousRowDetails
        item={buildItem({
          total_clicks: undefined,
          total_conversions: 6,
          linked_click_count: 15,
          linked_clicks_per_conversion: 2.5,
          extra_window_click_count: 12,
          extra_window_non_browser_ratio: 0.75,
        })}
        status="ready"
      />
    );

    expect(screen.getByText(suspiciousCopy.labels.clickPadding)).toBeInTheDocument();
    expect(screen.getByText(suspiciousCopy.labels.linkedClicks)).toBeInTheDocument();
    expect(screen.getByText("15")).toBeInTheDocument();
    expect(screen.getByText(suspiciousCopy.labels.clicksPerCv)).toBeInTheDocument();
    expect(screen.getByText("2.5")).toBeInTheDocument();
    expect(screen.getByText(suspiciousCopy.labels.extraWindowClicks)).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText(suspiciousCopy.labels.extraWindowNonBrowserRatio)).toBeInTheDocument();
    expect(screen.getByText("75%")).toBeInTheDocument();
  });

  it("panel variant: hides tag summary when breakdown table is shown (no duplicate)", () => {
    render(
      <SuspiciousRowDetails
        variant="panel"
        item={buildItem({
          evidence_status: "available",
          evidence_available: true,
          media_names: ["Media 1"],
          program_names: ["Program 1"],
          affiliate_names: ["Affiliate 1"],
          details: [
            {
              media_id: "m1",
              program_id: "p1",
              media_name: "Media 1",
              program_name: "Program 1",
              affiliate_name: "Affiliate 1",
              click_count: 1,
              conversion_count: 1,
            },
          ],
        })}
        status="ready"
      />
    );

    expect(screen.getByText(suspiciousCopy.labels.relatedRows)).toBeInTheDocument();
    expect(screen.queryByText(suspiciousCopy.labels.detailPanelRelatedTitle)).not.toBeInTheDocument();
  });

  it("shows fallback dashes for missing click padding stats", () => {
    render(
      <SuspiciousRowDetails
        item={buildItem({
          total_clicks: undefined,
          total_conversions: 6,
          linked_click_count: null,
          linked_clicks_per_conversion: null,
          extra_window_click_count: null,
          extra_window_non_browser_ratio: null,
        })}
        status="ready"
      />
    );

    expect(screen.getByText(suspiciousCopy.labels.clickPadding)).toBeInTheDocument();
    expect(screen.getAllByText("-").length).toBeGreaterThan(0);
  });
});
