import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  formatSuspiciousResultRange,
  suspiciousCopy,
} from "@/features/suspicious-list/copy";
import SuspiciousListPage from "@/features/suspicious-list/suspicious-list-page";
import { SUSPICIOUS_LIST_PAGE_SIZE } from "@/features/suspicious-list/use-suspicious-data";
import { ApiError } from "@/lib/api";
import type { SuspiciousItem, SuspiciousQueryOptions, SuspiciousResponse } from "@/lib/api";

const GROUP_BY_REASON_STORAGE_KEY = "suspicious:list:group-by-reason";
const navigation = vi.hoisted(() => ({
  replace: vi.fn(),
  pathname: "/suspicious/conversions",
  searchParams: new URLSearchParams(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: navigation.replace }),
  usePathname: () => navigation.pathname,
  useSearchParams: () => navigation.searchParams,
}));

function buildRows(count = 120): SuspiciousItem[] {
  return Array.from({ length: count }, (_, i) => {
    const index = i + 1;
    const riskLevel =
      index % 3 === 0 ? "medium" : index % 5 === 0 ? "low" : "high";

    return {
      finding_key: `finding-${index}`,
      date: "2026-01-21",
      ipaddress: `10.0.0.${index}`,
      useragent: `Mozilla/TestAgent-${index}`,
      ipaddress_masked: `10.0.*.${index}`,
      useragent_masked: `Mozilla/Masked-${index}`,
      sensitive_values_masked: true,
      total_conversions: 200 - i,
      media_count: (index % 4) + 1,
      program_count: (index % 3) + 1,
      first_time: `2026-01-21T00:00:${String(index % 60).padStart(2, "0")}Z`,
      last_time: `2026-01-21T01:00:${String(index % 60).padStart(2, "0")}Z`,
      reasons: ["total_conversions >= 50"],
      reasons_formatted: ["Conversions exceed threshold (50+)"],
      reason_cluster_key: `cluster-${Math.floor(i / 2)}`,
      risk_level: riskLevel,
      risk_score: riskLevel === "high" ? 90 : riskLevel === "medium" ? 60 : 20,
      risk_label: riskLevel === "high" ? "High" : riskLevel === "medium" ? "Medium" : "Low",
      media_names: [`Media ${index}`],
      program_names: [`Program ${index}`],
      affiliate_names: [`Affiliate ${index}`],
    };
  });
}

function createFetcher(rows = buildRows()) {
  return vi.fn(
    async (
      date?: string,
      limit = SUSPICIOUS_LIST_PAGE_SIZE,
      offset = 0,
      options?: SuspiciousQueryOptions
    ): Promise<SuspiciousResponse> => {
      const query = (options?.search || "").trim().toLowerCase();
      let filtered = query
        ? rows.filter(
            (row) =>
              row.ipaddress.toLowerCase().includes(query) ||
              row.useragent.toLowerCase().includes(query) ||
              (row.media_names || []).some((media) => media.toLowerCase().includes(query))
          )
        : rows;

      if (options?.riskLevel) {
        filtered = filtered.filter((row) => row.risk_level === options.riskLevel);
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

function createDetailFetcher() {
  return vi.fn(async (findingKey: string) => ({
    finding_key: findingKey,
    date: "2026-01-21",
    ipaddress: "10.0.0.1",
    useragent: "Mozilla/TestAgent-1",
    total_conversions: 200,
    media_count: 2,
    program_count: 1,
    first_time: "2026-01-21T00:00:01Z",
    last_time: "2026-01-21T01:00:01Z",
    reasons: ["total_conversions >= 50"],
    reasons_formatted: ["Conversions exceed threshold (50+)"],
    risk_level: "high" as const,
    risk_score: 90,
    risk_label: "High",
    media_names: ["Media 1"],
    program_names: ["Program 1"],
    affiliate_names: ["Affiliate 1"],
    evidence_status: "available" as const,
    evidence_available: true,
    evidence_expires_on: "2026-04-20",
    details: [
      {
        media_id: "M-1",
        program_id: "P-1",
        media_name: "Media 1",
        program_name: "Program 1",
        affiliate_name: "Affiliate 1",
        click_count: 61,
        conversion_count: 4,
      },
    ],
  }));
}

function renderPage(
  fetcher: ReturnType<typeof createFetcher>,
  detailFetcher = createDetailFetcher()
) {
  vi.mocked(fetchSuspiciousConversions).mockImplementation(fetcher);
  vi.mocked(fetchSuspiciousConversionDetail).mockImplementation(detailFetcher);
  return render(<SuspiciousListPage />);
}

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    fetchSuspiciousConversions: vi.fn(),
    fetchSuspiciousConversionDetail: vi.fn(),
  };
});

import {
  fetchSuspiciousConversionDetail,
  fetchSuspiciousConversions,
} from "@/lib/api";

describe("Suspicious list page", () => {
  beforeEach(() => {
    localStorage.setItem(GROUP_BY_REASON_STORAGE_KEY, "0");
    navigation.replace.mockReset();
    navigation.pathname = "/suspicious/conversions";
    navigation.searchParams = new URLSearchParams("date=2026-01-21");
    vi.mocked(fetchSuspiciousConversions).mockReset();
    vi.mocked(fetchSuspiciousConversionDetail).mockReset();
  });

  it("shows the first page count and list rows on initial render", async () => {
    const fetcher = createFetcher();
    renderPage(fetcher);

    await screen.findByRole("heading", { name: suspiciousCopy.conversionsTitle });
    expect(await screen.findByLabelText(suspiciousCopy.labels.resultRange)).toHaveTextContent(
      formatSuspiciousResultRange(1, SUSPICIOUS_LIST_PAGE_SIZE, 120)
    );

    expect(screen.getByText("10.0.*.1")).toBeInTheDocument();
    expect(screen.getAllByText("High").length).toBeGreaterThan(0);
  });

  it("groups duplicate patterns by default and paginates by grouped rows", async () => {
    localStorage.removeItem(GROUP_BY_REASON_STORAGE_KEY);
    const fetcher = createFetcher(buildRows(20));
    renderPage(fetcher);

    await screen.findByRole("heading", { name: suspiciousCopy.conversionsTitle });
    expect(await screen.findByLabelText(suspiciousCopy.labels.resultRange)).toHaveTextContent(
      formatSuspiciousResultRange(1, SUSPICIOUS_LIST_PAGE_SIZE, 10)
    );
    expect(screen.getByRole("checkbox", { name: suspiciousCopy.labels.groupByReasonPattern })).toBeChecked();
    expect(fetcher).toHaveBeenCalledWith(
      "2026-01-21",
      10000,
      0,
      expect.objectContaining({
        includeDetails: false,
        maskSensitive: true,
      })
    );
  });

  it("writes search text into the URL durable state", async () => {
    const fetcher = createFetcher();
    const user = userEvent.setup();
    renderPage(fetcher);

    await screen.findByLabelText(suspiciousCopy.labels.resultRange);
    await user.click(screen.getByRole("button", { name: suspiciousCopy.labels.searchOpenButton }));
    const input = screen.getByRole("searchbox", { name: suspiciousCopy.labels.search });

    await user.type(input, "10.0.0.120");

    await waitFor(() => {
      expect(navigation.replace).toHaveBeenLastCalledWith(
        "/suspicious/conversions?date=2026-01-21&search=10.0.0.120",
        { scroll: false }
      );
    });
  });

  it("loads details lazily and keeps the list visible while the drawer is open", async () => {
    const fetcher = createFetcher();
    const detailFetcher = createDetailFetcher();
    const user = userEvent.setup();
    renderPage(fetcher, detailFetcher);

    await screen.findByLabelText(suspiciousCopy.labels.resultRange);
    await user.click(screen.getAllByRole("button", { name: suspiciousCopy.labels.detail })[0]);

    await screen.findByText(suspiciousCopy.labels.detailBreadcrumb);
    expect(detailFetcher).toHaveBeenCalledWith("finding-1");
    expect(screen.getByText("10.0.*.1")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: suspiciousCopy.labels.backToList }));
    await waitFor(() => {
      expect(screen.queryByText(suspiciousCopy.labels.detailBreadcrumb)).not.toBeInTheDocument();
    });
  });

  it("writes risk filtering into the URL durable state", async () => {
    const fetcher = createFetcher();
    const user = userEvent.setup();
    renderPage(fetcher);

    await screen.findByLabelText(suspiciousCopy.labels.resultRange);
    await user.selectOptions(screen.getByLabelText(suspiciousCopy.labels.riskFilter), "high");

    await waitFor(() => {
      expect(navigation.replace).toHaveBeenLastCalledWith(
        "/suspicious/conversions?date=2026-01-21&risk=high",
        { scroll: false }
      );
    });
  });

  it("restores initial values from the query string and updates the URL", async () => {
    navigation.searchParams = new URLSearchParams(
      "date=2026-01-21&search=10.0.0&page=2&risk=high&sort=risk"
    );
    const fetcher = createFetcher();
    const user = userEvent.setup();
    renderPage(fetcher);

    await waitFor(() => {
      expect(fetcher).toHaveBeenCalledWith(
        "2026-01-21",
        SUSPICIOUS_LIST_PAGE_SIZE,
        SUSPICIOUS_LIST_PAGE_SIZE,
        expect.objectContaining({
          search: "10.0.0",
          riskLevel: "high",
          sortBy: "risk",
        })
      );
    });

    expect(screen.getByRole("searchbox", { name: suspiciousCopy.labels.search })).toHaveValue("10.0.0");
    expect(screen.getByRole("combobox", { name: suspiciousCopy.labels.sort })).toHaveValue("risk");

    navigation.replace.mockClear();
    await user.selectOptions(screen.getByLabelText(suspiciousCopy.labels.riskFilter), "low");

    await waitFor(() => {
      expect(navigation.replace).toHaveBeenLastCalledWith(
        "/suspicious/conversions?date=2026-01-21&search=10.0.0&risk=low&sort=risk",
        { scroll: false }
      );
    });
  });

  it("shows forbidden state in the state panel", async () => {
    const fetcher = vi.fn(async () => {
      const error = new ApiError(suspiciousCopy.states.forbiddenMessage);
      error.status = 403;
      throw error;
    });

    renderPage(fetcher as ReturnType<typeof createFetcher>);

    await screen.findByRole("heading", { name: suspiciousCopy.states.forbiddenTitle });
    expect(screen.getByText(suspiciousCopy.states.forbiddenMessage)).toBeInTheDocument();
  });
});
