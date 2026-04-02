"use client";

import { useCallback, useId, useMemo, useRef, useState } from "react";
import { dashboardCopy } from "@/features/dashboard/copy";
import type { DailyStatsItem } from "@/lib/api";
import { cn } from "@/lib/utils";

/* ── helpers ── */

const safe = (v?: number) => (Number.isFinite(v) ? v! : 0);

const fmtDate = (s: string) => {
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return m ? `${+m[2]}/${+m[3]}` : s;
};

const fmtNum = (v: number) => v.toLocaleString("ja-JP");

const fmtAxis = (v: number) =>
  v >= 10_000
    ? v.toLocaleString("ja-JP", { notation: "compact", maximumFractionDigits: 1 })
    : fmtNum(v);

function niceScale(max: number, ticks = 3) {
  if (max <= 0) return { top: 1, ticks: [0] };
  const raw = max / ticks;
  const exp = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].find((n) => n * exp >= raw)! * exp;
  const vals: number[] = [];
  for (let i = 0; ; i++) {
    const v = Math.round(step * i * 100) / 100;
    vals.push(v);
    if (v >= max) break;
  }
  return { top: vals.at(-1)!, ticks: vals };
}

/* ── series config ── */

type MK = "clicks" | "conversions" | "fraud_findings";

interface Series {
  key: MK;
  label: string;
  css: string; // CSS variable name (without hsl wrapper)
  panel: 0 | 1;
}

const SERIES: Series[] = [
  { key: "clicks", label: dashboardCopy.chart.legends.clicks, css: "var(--foreground)", panel: 0 },
  { key: "conversions", label: dashboardCopy.chart.legends.conversions, css: "var(--info)", panel: 0 },
  { key: "fraud_findings", label: dashboardCopy.chart.legends.suspiciousConversions, css: "var(--destructive)", panel: 1 },
];

/* ── SVG viewBox ── */

const W = 700;
const H = 300;
const PAD = { t: 6, r: 8, b: 22, l: 44 };
const GAP = 18;
const RATIOS = [0.58, 0.42];

/* ── component ── */

export function OverviewChart({
  data,
  className,
  layout = "default",
}: {
  data: DailyStatsItem[];
  className?: string;
  layout?: "default" | "fill";
}) {
  const uid = useId();
  const containerRef = useRef<HTMLDivElement>(null);
  const [hi, setHi] = useState<number | null>(null);

  const rows = useMemo(() => data.slice(-14), [data]);
  const n = rows.length;

  const onMove = useCallback(
    (e: React.PointerEvent) => {
      const el = containerRef.current;
      if (!el || n < 2) return;
      const { left, width } = el.getBoundingClientRect();
      const vx = ((e.clientX - left) / width) * W;
      const pw = W - PAD.l - PAD.r;
      setHi(Math.max(0, Math.min(n - 1, Math.round(((vx - PAD.l) / pw) * (n - 1)))));
    },
    [n],
  );

  /* ── empty ── */

  if (!data || n === 0) {
    return (
      <div
        className={cn(
          "flex items-center justify-center text-sm text-muted-foreground",
          layout === "fill" ? "min-h-[10rem] flex-1" : "h-64",
          className,
        )}
      >
        {dashboardCopy.chart.empty}
      </div>
    );
  }

  /* ── geometry ── */

  const pw = W - PAD.l - PAD.r;
  const totalH = H - PAD.t - PAD.b - GAP;
  const xOf = (i: number) => PAD.l + (i / Math.max(n - 1, 1)) * pw;

  const panels = RATIOS.map((r, pi) => {
    const h = totalH * r;
    const top = pi === 0 ? PAD.t : PAD.t + totalH * RATIOS[0]! + GAP;
    const bot = top + h;
    const series = SERIES.filter((s) => s.panel === pi);
    const max = Math.max(...series.flatMap((s) => rows.map((row) => safe(row[s.key]))), 1);
    const scale = niceScale(max);
    const yOf = (v: number) => bot - (v / scale.top) * h;
    return { top, bot, h, series, scale, yOf };
  });

  /* ── SVG defs: gradient fills ── */

  const defs = SERIES.map((s) => {
    const panel = panels[s.panel]!;
    return (
      <linearGradient
        key={s.key}
        id={`${uid}-${s.key}`}
        gradientUnits="userSpaceOnUse"
        x1="0"
        y1={String(panel.top)}
        x2="0"
        y2={String(panel.bot)}
      >
        <stop offset="0%" style={{ stopColor: `hsl(${s.css})`, stopOpacity: 0.2 }} />
        <stop offset="100%" style={{ stopColor: `hsl(${s.css})`, stopOpacity: 0 }} />
      </linearGradient>
    );
  });

  /* ── panel rendering ── */

  const panelEls = panels.flatMap((panel, pi) => {
    const { scale, yOf } = panel;
    const els: React.ReactNode[] = [];

    // Y-axis grid + labels
    for (const t of scale.ticks) {
      els.push(
        <g key={`g${pi}-${t}`}>
          <line
            x1={PAD.l}
            x2={W - PAD.r}
            y1={yOf(t)}
            y2={yOf(t)}
            strokeWidth={0.5}
            opacity={0.4}
            style={{ stroke: "hsl(var(--border))" }}
            strokeDasharray={t === 0 ? undefined : "3 3"}
          />
          <text
            x={PAD.l - 6}
            y={yOf(t) + 3.5}
            textAnchor="end"
            fontSize={9}
            style={{ fill: "hsl(var(--muted-foreground))" }}
          >
            {fmtAxis(t)}
          </text>
        </g>,
      );
    }

    // Area fill + line + hover dot per series
    for (const s of panel.series) {
      const pts = rows.map((r, i) => ({ x: xOf(i), y: yOf(safe(r[s.key])) }));
      const d = pts.map((p, i) => `${i ? "L" : "M"}${p.x},${p.y}`).join("");

      els.push(
        <g key={s.key}>
          <path
            d={`${d}L${pts.at(-1)!.x},${panel.bot}L${pts[0]!.x},${panel.bot}Z`}
            fill={`url(#${uid}-${s.key})`}
          />
          <path
            d={d}
            fill="none"
            style={{ stroke: `hsl(${s.css})` }}
            strokeWidth={1.5}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          {hi !== null && (
            <circle
              cx={pts[hi]!.x}
              cy={pts[hi]!.y}
              r={3.5}
              style={{ fill: `hsl(${s.css})` }}
            />
          )}
        </g>,
      );
    }

    // Divider between panels
    if (pi === 0) {
      els.push(
        <line
          key="divider"
          x1={PAD.l}
          x2={W - PAD.r}
          y1={panel.bot + GAP / 2}
          y2={panel.bot + GAP / 2}
          strokeWidth={0.5}
          opacity={0.3}
          style={{ stroke: "hsl(var(--border))" }}
        />,
      );
    }

    return els;
  });

  /* ── X-axis date labels ── */

  const step = n > 10 ? 2 : 1;
  const xLabels = rows.map((r, i) =>
    i % step === 0 || i === n - 1 ? (
      <text
        key={r.date}
        x={xOf(i)}
        y={H - 3}
        textAnchor="middle"
        fontSize={9}
        style={{ fill: "hsl(var(--muted-foreground))" }}
      >
        {fmtDate(r.date)}
      </text>
    ) : null,
  );

  /* ── hover crosshair ── */

  const crosshair =
    hi !== null ? (
      <line
        x1={xOf(hi)}
        x2={xOf(hi)}
        y1={PAD.t}
        y2={H - PAD.b}
        strokeWidth={1}
        strokeDasharray="3 2"
        style={{ stroke: "hsl(var(--foreground) / 0.15)" }}
      />
    ) : null;

  /* ── tooltip (fixed top-right) ── */

  const tr = hi !== null ? rows[hi] : null;
  const tooltip = tr ? (
    <div className="pointer-events-none absolute right-2 top-1 z-10 rounded border border-border bg-popover/95 px-2.5 py-2 text-[11px] leading-relaxed shadow-md backdrop-blur-sm">
      <div className="mb-1 font-semibold tabular-nums text-foreground">{tr.date}</div>
      {SERIES.map((s) => (
        <div key={s.key} className="flex items-center gap-2">
          <span
            className="h-1.5 w-1.5 shrink-0 rounded-full"
            style={{ backgroundColor: `hsl(${s.css})` }}
          />
          <span className="text-muted-foreground">{s.label}</span>
          <span className="ml-auto pl-3 tabular-nums font-medium text-foreground">
            {fmtNum(safe(tr[s.key]))}
          </span>
        </div>
      ))}
    </div>
  ) : null;

  /* ── header: title + legend ── */

  const subtitle = dashboardCopy.chart.subtitle(rows.length);

  const legend = (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-muted-foreground">
      {SERIES.map((s) => (
        <span key={s.key} className="inline-flex items-center gap-1.5">
          <span
            className="h-2 w-2 rounded-full"
            style={{ backgroundColor: `hsl(${s.css})` }}
          />
          {s.label}
        </span>
      ))}
    </div>
  );

  const header = (
    <div className="flex shrink-0 flex-wrap items-end justify-between gap-x-4 gap-y-2">
      <div className="space-y-0.5">
        <div className="text-[13px] font-medium text-foreground/86">
          {dashboardCopy.chart.title}
        </div>
        <div className="text-[11px] text-muted-foreground">{subtitle}</div>
      </div>
      {legend}
    </div>
  );

  /* ── chart body ── */

  const chart = (
    <div
      ref={containerRef}
      className="relative min-h-0 flex-1"
      onPointerMove={onMove}
      onPointerLeave={() => setHi(null)}
    >
      {tooltip}
      <svg
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="xMidYMid meet"
        className="h-full w-full"
        style={{ minHeight: 180 }}
      >
        <defs>{defs}</defs>
        {panelEls}
        {xLabels}
        {crosshair}
      </svg>
    </div>
  );

  /* ── layout variants ── */

  if (layout === "fill") {
    return (
      <div className={cn("flex min-h-0 flex-1 flex-col gap-2", className)}>
        {header}
        {chart}
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      {header}
      {chart}
    </div>
  );
}
