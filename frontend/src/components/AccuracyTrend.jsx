import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function AccuracyTrend({ daily, selected, onSelect }) {
  const data = daily.map((d) => ({
    date: d.date.slice(5), // "MM-DD"
    fullDate: d.date,
    MAE: d.mae == null ? null : Math.round(d.mae),
    Bias: d.bias == null ? null : Math.round(d.bias),
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <ComposedChart
        data={data}
        margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
        onClick={(e) => {
          const point = e?.activePayload?.[0]?.payload;
          if (point) onSelect(point.fullDate);
        }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-color)" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 12 }} width={56} label={{ value: "MW", angle: -90, position: "insideLeft", fontSize: 12 }} />
        <Tooltip />
        <Legend />
        <Bar dataKey="MAE" fill="#93c5fd" radius={2} />
        <Line type="monotone" dataKey="Bias" stroke="#dc2626" strokeWidth={2} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
