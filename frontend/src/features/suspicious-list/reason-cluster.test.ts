import { describe, expect, it } from "vitest";
import {
  clusterSuspiciousItems,
  getReasonClusterKey,
  sumConversions,
  worstRiskLevel,
} from "./reason-cluster";
import type { SuspiciousItem } from "@/lib/api";

function item(partial: Partial<SuspiciousItem> & { finding_key: string }): SuspiciousItem {
  return {
    finding_key: partial.finding_key,
    date: "2026-01-01",
    ipaddress: partial.ipaddress ?? "1.1.1.1",
    useragent: partial.useragent ?? "UA",
    media_count: 1,
    program_count: 1,
    first_time: "2026-01-01T00:00:00Z",
    last_time: "2026-01-01T01:00:00Z",
    reasons: partial.reasons ?? [],
    reasons_formatted: partial.reasons_formatted ?? [],
    ...partial,
  };
}

describe("getReasonClusterKey", () => {
  it("uses reason_cluster_key when present", () => {
    expect(
      getReasonClusterKey(
        item({
          finding_key: "a",
          reason_cluster_key: "burst|spread_program",
        })
      )
    ).toBe("burst|spread_program");
  });
});

describe("clusterSuspiciousItems", () => {
  it("groups by cluster key preserving first-seen order", () => {
    const rows = [
      item({ finding_key: "1", reason_cluster_key: "volume" }),
      item({ finding_key: "2", reason_cluster_key: "burst|spread_program" }),
      item({ finding_key: "3", reason_cluster_key: "volume" }),
    ];
    const groups = clusterSuspiciousItems(rows);
    expect(groups.map((g) => g.clusterKey)).toEqual(["volume", "burst|spread_program"]);
    expect(groups[0]!.members.map((m) => m.finding_key)).toEqual(["1", "3"]);
    expect(groups[1]!.members.map((m) => m.finding_key)).toEqual(["2"]);
  });
});

describe("worstRiskLevel", () => {
  it("prefers high over medium", () => {
    expect(
      worstRiskLevel([
        item({ finding_key: "a", risk_level: "medium" }),
        item({ finding_key: "b", risk_level: "high" }),
      ])
    ).toBe("high");
  });
});

describe("sumConversions", () => {
  it("sums conversions", () => {
    expect(
      sumConversions([
        item({ finding_key: "a", total_conversions: 2 }),
        item({ finding_key: "b", total_conversions: 3 }),
      ])
    ).toBe(5);
  });
});
