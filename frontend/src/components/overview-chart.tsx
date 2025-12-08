"use client"

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

interface OverviewChartProps {
  data: {
    date: string;
    clicks: number;
    conversions: number;
  }[];
}

export function OverviewChart({ data }: OverviewChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data}>
        <XAxis
          dataKey="date"
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => {
            const date = new Date(value);
            return `${date.getMonth() + 1}/${date.getDate()}`;
          }}
        />
        <YAxis
          yAxisId="left"
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => `${value}`}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => `${value}`}
        />
        <Tooltip
            contentStyle={{ backgroundColor: 'var(--background)', borderColor: 'var(--border)' }}
            labelStyle={{ color: 'var(--foreground)' }}
        />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="clicks"
          stroke="hsl(var(--primary))"
          strokeWidth={2}
          activeDot={{ r: 8 }}
          name="クリック数"
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="conversions"
          stroke="hsl(var(--destructive))"
          strokeWidth={2}
          name="成果数"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

