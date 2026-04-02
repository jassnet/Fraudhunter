import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SuspiciousConversionsPage from "@/app/suspicious/conversions/page";
import {
  formatSuspiciousResultRange,
  suspiciousCopy,
} from "@/features/suspicious-list/copy";
import { SUSPICIOUS_LIST_PAGE_SIZE } from "@/features/suspicious-list/use-suspicious-data";

const GROUP_BY_REASON_STORAGE_KEY = "suspicious:list:group-by-reason";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
  usePathname: () => "/suspicious/conversions",
  useSearchParams: () => new URLSearchParams("date=2026-01-21"),
}));

describe("Suspicious conversions page", () => {
  beforeEach(() => {
    localStorage.setItem(GROUP_BY_REASON_STORAGE_KEY, "0");
  });

  it("shows the page title and conversion count column", async () => {
    render(<SuspiciousConversionsPage />);

    await screen.findByRole("heading", { name: suspiciousCopy.conversionsTitle });
    expect(await screen.findByLabelText(suspiciousCopy.labels.resultRange)).toHaveTextContent(
      formatSuspiciousResultRange(1, SUSPICIOUS_LIST_PAGE_SIZE, 120)
    );
    expect(
      screen.getByRole("columnheader", { name: suspiciousCopy.countLabelConversions })
    ).toBeInTheDocument();
  });
});
