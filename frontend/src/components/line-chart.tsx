import { formatShortDate } from "@/lib/format";

type LineChartProps = {
  data: Array<{
    date: string;
    alerts: number;
  }>;
};

export function LineChart({ data }: LineChartProps) {
  if (data.length === 0) {
    return <div className="empty-state">グラフ化できるデータがありません。</div>;
  }

  const width = 820;
  const height = 280;
  const paddingX = 48;
  const paddingTop = 20;
  const paddingBottom = 36;
  const maxAlerts = Math.max(...data.map((item) => item.alerts), 1);
  const chartHeight = height - paddingTop - paddingBottom;
  const chartWidth = width - paddingX * 2;

  const points = data.map((item, index) => {
    const x = paddingX + (chartWidth * index) / Math.max(data.length - 1, 1);
    const y = paddingTop + chartHeight - (item.alerts / maxAlerts) * chartHeight;
    return {
      ...item,
      x,
      y,
    };
  });

  const linePoints = points.map((point) => `${point.x},${point.y}`).join(" ");
  const areaPoints = [
    `${points[0].x},${paddingTop + chartHeight}`,
    ...points.map((point) => `${point.x},${point.y}`),
    `${points[points.length - 1].x},${paddingTop + chartHeight}`,
  ].join(" ");

  return (
    <div className="chart" role="img" aria-label="日別フラウド検知件数の推移">
      <svg viewBox={`0 0 ${width} ${height}`}>
        <defs>
          <linearGradient id="chart-area-gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.15" />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {Array.from({ length: 5 }, (_, index) => {
          const ratio = index / 4;
          const y = paddingTop + chartHeight * ratio;
          const value = Math.round(maxAlerts - maxAlerts * ratio);
          return (
            <g key={index}>
              <line className="chart-grid-line" x1={paddingX} x2={width - paddingX} y1={y} y2={y} />
              <text className="chart-axis-label" x={12} y={y + 4}>
                {value}
              </text>
            </g>
          );
        })}

        <polygon className="chart-area" points={areaPoints} fill="url(#chart-area-gradient)" />

        <polyline
          className="chart-line"
          fill="none"
          points={linePoints}
        />

        {points.map((point) => (
          <g key={point.date}>
            <circle className="chart-point" cx={point.x} cy={point.y} r="3.5" />
            <text className="chart-axis-label" x={point.x} y={height - 12} textAnchor="middle">
              {formatShortDate(point.date)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
