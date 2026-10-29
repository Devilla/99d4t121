import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function hourLabel(iso) {
  return iso.slice(11, 16); // "HH:MM" from an ISO timestamp
}

export default function DailyChart({ points }) {
  const data = points.map((p) => ({
    time: hourLabel(p.time),
    Forecast: p.forecast_mw,
    Actual: p.actual_mw,
  }));

  return (
    <ResponsiveContainer width="100%" height={340}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-color)" />
        <XAxis dataKey="time" tick={{ fontSize: 12 }} interval={2} />
        <YAxis
          tick={{ fontSize: 12 }}
          width={56}
          label={{ value: "MW", angle: -90, position: "insideLeft", fontSize: 12 }}
        />
        <Tooltip formatter={(v) => (v == null ? "—" : `${v.toLocaleString()} MW`)} />
        <Legend />
        <Line type="monotone" dataKey="Forecast" stroke="#2563eb" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Actual" stroke="#16a34a" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
