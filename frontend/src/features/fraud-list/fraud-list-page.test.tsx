import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fraudCopy } from "@/features/fraud-list/copy";
import FraudListPage from "@/features/fraud-list/fraud-list-page";
import { FRAUD_FINDINGS_PAGE_SIZE } from "@/features/fraud-list/fraud-findings-content";
import type { FraudFindingItem, FraudFindingsResponse } from "@/lib/api";

const navigation = vi.hoisted(() => ({
  replace: vi.fn(),
  pathname: "/suspicious/fraud",
  searchParams: new URLSearchParams(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: navigation.replace }),
  usePathname: () => navigation.pathname,
  useSearchParams: () => navigation.searchParams,
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    fetchFraudFindings: vi.fn(),
    fetchFraudFindingDetail: vi.fn(),
    getAvailableDates: vi.fn(),
  };
});

import {
  fetchFraudFindingDetail,
  fetchFraudFindings,
  getAvailableDates,
} from "@/lib/api";

function buildRows(count = 25): FraudFindingItem[] {
  return Array.from({ length: count }, (_, index) => ({
    finding_key: `fraud-${index + 1}`,
    date: "2026-01-21",
    user_id: `user-${index + 1}`,
    media_id: `media-${index + 1}`,
    promotion_id: `promo-${index + 1}`,
    user_name: `User ${index + 1}`,
    media_name: `Media ${index + 1}`,
    promotion_name: `Promotion ${index + 1}`,
    primary_metric: 100 - index,
    reasons: ["rule"],
    reasons_formatted: [`Reason ${index + 1}`],
    risk_level: index % 3 === 0 ? "high" : index % 3 === 1 ? "medium" : "low",
    risk_label: index % 3 === 0 ? "High" : index % 3 === 1 ? "Medium" : "Low",
    details: { id: index + 1 },
  }));
}

function createFetcher(rows = buildRows()) {
  return vi.fn(
    async (
      date?: string,
      limit = FRAUD_FINDINGS_PAGE_SIZE,
      offset = 0,
      options?: { search?: string; riskLevel?: string; sortBy?: string; sortOrder?: string }
    ): Promise<FraudFindingsResponse> => {
      let filtered = rows;

      if (options?.search) {
        const query = options.search.toLowerCase();
        filtered = filtered.filter(
          (item) =>
            item.user_name.toLowerCase().includes(query) ||
            item.media_name.toLowerCase().includes(query) ||
            item.promotion_name.toLowerCase().includes(query)
        );
      }

      if (options?.riskLevel) {
        filtered = filtered.filter((item) => item.risk_level === options.riskLevel);
      }

      return {
        date: date || "2026-01-21",
        data: filtered.slice(offset, offset + limit),
        total: filtered.length,
        limit,
        offset,
      };
    }
  );
}

describe("Fraud list page", () => {
  beforeEach(() => {
    navigation.replace.mockReset();
    navigation.pathname = "/suspicious/fraud";
    navigation.searchParams = new URLSearchParams("date=2026-01-21");
    vi.mocked(fetchFraudFindings).mockReset();
    vi.mocked(fetchFraudFindingDetail).mockReset();
    vi.mocked(getAvailableDates).mockReset();
    vi.mocked(getAvailableDates).mockResolvedValue({ dates: ["2026-01-21", "2026-01-20"] });
  });

  it("shows rows and paging on initial render", async () => {
    vi.mocked(fetchFraudFindings).mockImplementation(createFetcher());
    vi.mocked(fetchFraudFindingDetail).mockImplementation(async (findingKey: string) => ({
      ...buildRows(1)[0],
      finding_key: findingKey,
    }));

    render(<FraudListPage />);

    await screen.findByRole("heading", { name: fraudCopy.title });
    expect(
      await screen.findByLabelText("表示範囲")
    ).toHaveTextContent(fraudCopy.formatResultRange(1, FRAUD_FINDINGS_PAGE_SIZE, 25));
    expect(screen.getByText("User 1")).toBeInTheDocument();
  });

  it("writes search text into the URL durable state", async () => {
    const user = userEvent.setup();
    vi.mocked(fetchFraudFindings).mockImplementation(createFetcher());
    vi.mocked(fetchFraudFindingDetail).mockImplementation(async (findingKey: string) => ({
      ...buildRows(1)[0],
      finding_key: findingKey,
    }));

    render(<FraudListPage />);

    await screen.findByRole("heading", { name: fraudCopy.title });
    await user.type(screen.getByRole("searchbox", { name: fraudCopy.labels.search }), "User 2");

    await waitFor(() => {
      expect(navigation.replace).toHaveBeenLastCalledWith(
        "/suspicious/fraud?date=2026-01-21&search=User+2",
        { scroll: false }
      );
    });
  });

  it("loads the selected detail into the side panel", async () => {
    const user = userEvent.setup();
    vi.mocked(fetchFraudFindings).mockImplementation(createFetcher());
    vi.mocked(fetchFraudFindingDetail).mockImplementation(async (findingKey: string) => ({
      ...buildRows(1)[0],
      finding_key: findingKey,
      user_name: "Detail User",
      reasons_formatted: ["Detail Reason"],
      details: { source: "detail" },
    }));

    render(<FraudListPage />);

    await screen.findByRole("heading", { name: fraudCopy.title });
    await user.click(screen.getAllByRole("button", { name: fraudCopy.labels.detail })[0]!);

    await waitFor(() => {
      expect(fetchFraudFindingDetail).toHaveBeenCalledWith("fraud-1");
    });
    expect(await screen.findByText("Detail User")).toBeInTheDocument();
    expect(screen.getByText("Detail Reason")).toBeInTheDocument();
  });
});
