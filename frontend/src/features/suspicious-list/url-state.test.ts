import { describe, expect, it } from "vitest";
import {
  buildSuspiciousListQueryString,
  parseSuspiciousListUrlState,
} from "@/features/suspicious-list/url-state";

describe("suspicious list url state", () => {
  it("parses valid query state", () => {
    const state = parseSuspiciousListUrlState(
      new URLSearchParams("date=2026-01-21&page=3&search=10.0.0&risk=high&sort=risk&sort_order=asc")
    );

    expect(state).toEqual({
      date: "2026-01-21",
      page: 3,
      search: "10.0.0",
      risk: "high",
      sort: "risk",
      sortOrder: "asc",
    });
  });

  it("serializes only non-default fields", () => {
    const query = buildSuspiciousListQueryString({
      date: "2026-01-21",
      page: 1,
      search: "",
      risk: "all",
      sort: "count",
      sortOrder: "desc",
    });

    expect(query).toBe("date=2026-01-21");
  });
});
