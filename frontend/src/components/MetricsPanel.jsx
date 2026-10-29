function fmt(n, digits = 0) {
  return n === null || n === undefined ? "—" : n.toLocaleString(undefined, { maximumFractionDigits: digits });
}

export default function MetricsPanel({ metrics, title, note }) {
  const tiles = [
    { label: "MAE", value: fmt(metrics?.mae), unit: "MW", hint: "mean absolute error" },
    { label: "RMSE", value: fmt(metrics?.rmse), unit: "MW", hint: "penalizes big misses" },
    {
      label: "Bias",
      value: metrics?.bias == null ? "—" : `${metrics.bias >= 0 ? "+" : ""}${fmt(metrics.bias)}`,
      unit: "MW",
      hint: "+ = forecast over-predicts",
    },
    { label: "MAPE", value: fmt(metrics?.mape, 1), unit: "%", hint: "mean % error" },
  ];
  return (
    <div className="metrics-panel">
      <h3>{title}</h3>
      <div className="metrics-grid">
        {tiles.map((t) => (
          <div className="metric-tile" key={t.label} title={t.hint}>
            <div className="metric-label">{t.label}</div>
            <div className="metric-value">
              {t.value} <span className="metric-unit">{t.unit}</span>
            </div>
          </div>
        ))}
      </div>
      {note && <p className="metrics-note">{note}</p>}
    </div>
  );
}
