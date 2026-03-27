import { http, HttpResponse } from "msw";
import { API_BASE_URL } from "@/lib/api";

export const DEFAULT_DATES = ["2026-01-21", "2026-01-20", "2026-01-19"];

export function buildSummaryResponse(targetDate: string) {
  return {
    date: targetDate,
    stats: {
      clicks: {
        total: 1200,
        unique_ips: 840,
        media_count: 24,
        prev_total: 1100,
      },
      conversions: {
        total: 210,
        unique_ips: 150,
        prev_total: 190,
      },
      suspicious: {
        click_based: 42,
        conversion_based: 17,
      },
    },
  };
}

function buildDailyStats() {
  return {
    data: Array.from({ length: 30 }, (_, i) => {
      const date = new Date("2026-01-21T00:00:00Z");
      date.setDate(date.getDate() - (29 - i));
      const isoDate = date.toISOString().slice(0, 10);
      return {
        date: isoDate,
        clicks: 700 + i * 7,
        conversions: 120 + i * 2,
        suspicious_clicks: 20 + (i % 5),
        suspicious_conversions: 8 + (i % 3),
      };
    }),
  };
}

type SuspiciousKind = "clicks" | "conversions";

function buildSuspiciousRows(kind: SuspiciousKind) {
  return Array.from({ length: 120 }, (_, i) => {
    const index = i + 1;
    const ipaddress = `10.0.${Math.floor(i / 255)}.${(i % 255) + 1}`;
    const common = {
      date: DEFAULT_DATES[0],
      ipaddress,
      useragent: `Mozilla/TestAgent-${index}`,
      media_count: (index % 4) + 1,
      program_count: (index % 3) + 1,
      first_time: `${DEFAULT_DATES[0]}T00:00:${String(index % 60).padStart(2, "0")}Z`,
      last_time: `${DEFAULT_DATES[0]}T01:00:${String(index % 60).padStart(2, "0")}Z`,
      reasons: ["ip_frequency_high"],
      reasons_formatted: ["IP からのアクセス頻度が高すぎます"],
      risk_level: index % 2 === 0 ? "high" : "medium",
      risk_score: 70 + (index % 20),
      risk_label: index % 2 === 0 ? "高リスク" : "中リスク",
      media_names: [`媒体 ${index}`],
      program_names: [`案件 ${index}`],
      affiliate_names: [`アフィリエイター ${index}`],
      details: [
        {
          media_id: `M-${index}`,
          program_id: `P-${index}`,
          media_name: `媒体 ${index}`,
          program_name: `案件 ${index}`,
          affiliate_name: `アフィリエイター ${index}`,
          click_count: 100 - (index % 40),
          conversion_count: 30 - (index % 20),
        },
      ],
    };

    if (kind === "clicks") {
      return {
        ...common,
        total_clicks: 220 - i,
      };
    }

    return {
      ...common,
      total_conversions: 140 - i,
      min_click_to_conv_seconds: 15 + (i % 10),
      max_click_to_conv_seconds: 90 + (i % 25),
    };
  });
}

function paginateBySearch<T extends { ipaddress: string; useragent: string }>(
  rows: T[],
  search: string | null,
  offset: number,
  limit: number
) {
  const normalized = (search || "").trim().toLowerCase();
  const filtered = normalized
    ? rows.filter(
        (row) =>
          row.ipaddress.toLowerCase().includes(normalized) ||
          row.useragent.toLowerCase().includes(normalized)
      )
    : rows;
  return {
    filtered,
    paginated: filtered.slice(offset, offset + limit),
  };
}

const suspiciousClickRows = buildSuspiciousRows("clicks");
const suspiciousConversionRows = buildSuspiciousRows("conversions");

export const handlers = [
  http.get(`${API_BASE_URL}/api/dates`, () => {
    return HttpResponse.json({ dates: DEFAULT_DATES });
  }),

  http.get(`${API_BASE_URL}/api/summary`, ({ request }) => {
    const url = new URL(request.url);
    const targetDate = url.searchParams.get("target_date") || DEFAULT_DATES[0];
    return HttpResponse.json(buildSummaryResponse(targetDate));
  }),

  http.get(`${API_BASE_URL}/api/stats/daily`, () => {
    return HttpResponse.json(buildDailyStats());
  }),

  http.get(`${API_BASE_URL}/api/suspicious/clicks`, ({ request }) => {
    const url = new URL(request.url);
    const date = url.searchParams.get("date") || DEFAULT_DATES[0];
    const limit = Number(url.searchParams.get("limit") || "50");
    const offset = Number(url.searchParams.get("offset") || "0");
    const search = url.searchParams.get("search");
    const { filtered, paginated } = paginateBySearch(
      suspiciousClickRows,
      search,
      offset,
      limit
    );

    return HttpResponse.json({
      date,
      data: paginated,
      total: filtered.length,
      limit,
      offset,
    });
  }),

  http.get(`${API_BASE_URL}/api/suspicious/conversions`, ({ request }) => {
    const url = new URL(request.url);
    const date = url.searchParams.get("date") || DEFAULT_DATES[0];
    const limit = Number(url.searchParams.get("limit") || "50");
    const offset = Number(url.searchParams.get("offset") || "0");
    const search = url.searchParams.get("search");
    const { filtered, paginated } = paginateBySearch(
      suspiciousConversionRows,
      search,
      offset,
      limit
    );

    return HttpResponse.json({
      date,
      data: paginated,
      total: filtered.length,
      limit,
      offset,
    });
  }),

  http.get(`${API_BASE_URL}/api/job/status`, () => {
    return HttpResponse.json({
      status: "idle",
      message: "まだジョブは登録されていません",
      job_id: null,
      result: null,
    });
  }),
];
