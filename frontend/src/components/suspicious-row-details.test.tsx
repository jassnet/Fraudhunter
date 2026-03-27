import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SuspiciousRowDetails } from "@/components/suspicious-row-details";
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
  it("shows evidence availability for recent findings", () => {
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

    expect(
      screen.getByText(/証拠は保持期間内です。詳細の関連行と判断材料を確認できます。/)
    ).toBeInTheDocument();
    expect(screen.getByText(/期限: 2026-04-20/)).toBeInTheDocument();
    expect(screen.getByText("関連行")).toBeInTheDocument();
    expect(screen.getAllByText("Media 1").length).toBeGreaterThan(0);
  });

  it("shows fallback message and hides supporting details when evidence expired", () => {
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

    expect(
      screen.getByText(/証拠保持期間を過ぎているため、この finding は要約のみ表示しています。/)
    ).toBeInTheDocument();
    expect(screen.queryByText("関連行")).not.toBeInTheDocument();
    expect(screen.getByText("Media 1")).toBeInTheDocument();
  });

  it("shows forbidden state separately from expired evidence", () => {
    render(<SuspiciousRowDetails item={buildItem()} status="forbidden" />);

    expect(screen.getByText("表示権限がありません")).toBeInTheDocument();
    expect(screen.getByText("この詳細を表示する権限がありません。")).toBeInTheDocument();
  });
});
