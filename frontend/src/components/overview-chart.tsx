"use client"

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from "recharts"
import { DailyStatsItem } from "@/lib/api"

interface OverviewChartProps {
  data: DailyStatsItem[];
}

export function OverviewChart({ data }: OverviewChartProps) {
  return (
    <ResponsiveContainer width="100%" height={350}>
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
          label={{ value: "クリック数", angle: -90, position: "insideLeft" }}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => `${value}`}
          label={{ value: "成果 / 不正件数", angle: 90, position: "insideRight" }}
        />
        <Tooltip
          contentStyle={{ 
            backgroundColor: 'hsl(var(--background))', 
            borderColor: 'hsl(var(--border))',
            borderRadius: '8px'
          }}
          labelStyle={{ color: 'hsl(var(--foreground))' }}
          labelFormatter={(value) => {
            const date = new Date(value);
            return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`;
          }}
        />
        <Legend />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="clicks"
          stroke="hsl(217, 91%, 60%)"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 6 }}
          name="クリック数"
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="conversions"
          stroke="hsl(142, 71%, 45%)"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 6 }}
          name="成果数"
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="suspicious_clicks"
          stroke="hsl(45, 93%, 47%)"
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={false}
          activeDot={{ r: 6 }}
          name="不正クリック"
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="suspicious_conversions"
          stroke="hsl(0, 84%, 60%)"
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={false}
          activeDot={{ r: 6 }}
          name="不正成果"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
