import { beforeEach, describe, expect, it, vi } from "vitest";
import SuspiciousConversionsPage from "@/app/suspicious/conversions/page";

const navigation = vi.hoisted(() => ({
  redirect: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  redirect: navigation.redirect,
}));

describe("Suspicious conversions page", () => {
  beforeEach(() => {
    navigation.redirect.mockReset();
  });

  it("redirects to the fraud list and preserves query params", () => {
    SuspiciousConversionsPage({
      searchParams: {
        date: "2026-01-21",
        risk: "high",
      },
    });

    expect(navigation.redirect).toHaveBeenCalledWith("/suspicious/fraud?date=2026-01-21&risk=high");
  });
});
