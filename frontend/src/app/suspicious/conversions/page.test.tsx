import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import SuspiciousConversionsPage from "@/app/suspicious/conversions/page";
import { suspiciousCopy } from "@/copy/suspicious";
import { SUSPICIOUS_LIST_PAGE_SIZE } from "@/features/suspicious-list/use-suspicious-data";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
  usePathname: () => "/suspicious/conversions",
  useSearchParams: () => new URLSearchParams("date=2026-01-21"),
}));

describe("不審コンバージョン画面", () => {
  it("画面タイトルと CV 数列を表示する", async () => {
    render(<SuspiciousConversionsPage />);

    await screen.findByRole("heading", { name: suspiciousCopy.conversionsTitle });
    expect(await screen.findByLabelText("表示件数")).toHaveTextContent(
      `1〜${SUSPICIOUS_LIST_PAGE_SIZE}件（全120件）`
    );
    expect(screen.getByRole("columnheader", { name: suspiciousCopy.countLabelConversions })).toBeInTheDocument();
  });
});
