import { describe, expect, it } from "vitest";

import { formatDateLabel, formatDateTime, formatShortDate } from "./format";

describe("format", () => {
  it("日本時間で日付を表示する", () => {
    expect(formatDateLabel("2026-04-05T00:30:00+09:00")).toBe("2026/04/05");
  });

  it("日本時間で日時を表示する", () => {
    expect(formatDateTime("2026-04-05T10:05:00+09:00")).toBe("2026/04/05 10:05");
  });

  it("日本時間で短い日付を表示する", () => {
    expect(formatShortDate("2026-04-05T00:30:00+09:00")).toBe("04/05");
  });
});
