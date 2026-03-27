import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import SuspiciousConversionsPage from "@/app/suspicious/conversions/page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
  usePathname: () => "/suspicious/conversions",
  useSearchParams: () => new URLSearchParams("date=2026-01-21"),
}));

describe("不審コンバージョン画面", () => {
  it("画面タイトルと CV 数列を表示する", async () => {
    render(<SuspiciousConversionsPage />);

    await screen.findByRole("heading", { name: "不審コンバージョン" });
    expect(await screen.findAllByText("1-50件 / 全120件")).toHaveLength(2);
    expect(screen.getByRole("columnheader", { name: "CV数" })).toBeInTheDocument();
  });
});
