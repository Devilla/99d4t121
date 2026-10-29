import { useEffect, useState } from "react";
import "./App.css";
import { getAccuracySummary, getDays, getForecastVsActual } from "./api";
import AccuracyTrend from "./components/AccuracyTrend";
import DailyChart from "./components/DailyChart";
import DayPicker from "./components/DayPicker";
import MetricsPanel from "./components/MetricsPanel";

export default function App() {
  const [days, setDays] = useState([]);
  const [selectedDay, setSelectedDay] = useState(null);
  const [dayData, setDayData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  // Load the list of delivery days and the month-level accuracy summary once.
  useEffect(() => {
    getDays()
      .then((d) => {
        setDays(d.days);
        setSelectedDay(d.days[14] ?? d.days[0]); // default to mid-month
      })
      .catch((e) => setError(e.message));
    getAccuracySummary()
      .then(setSummary)
      .catch((e) => setError(e.message));
  }, []);

  // Load the per-day forecast-vs-actual curve whenever the selection changes.
  useEffect(() => {
    if (!selectedDay) return;
    getForecastVsActual(selectedDay)
      .then(setDayData)
      .catch((e) => setError(e.message));
  }, [selectedDay]);

  return (
    <div className="app-shell">
      <header>
        <h1>UK Wind — Day-Ahead Procurement View</h1>
        <p className="subtitle">
          National wind generation: the forecast available at day-ahead decision time vs. what actually
          happened, for January 2026.
        </p>
      </header>

      {error && <div className="error-banner">Error: {error}</div>}

      <section className="panel">
        <div className="panel-header">
          <h2>1. What the forecast said, at the moment it mattered</h2>
          {days.length > 0 && selectedDay && (
            <DayPicker days={days} selected={selectedDay} onSelect={setSelectedDay} />
          )}
        </div>
        {dayData ? (
          <>
            <p className="decision-note">
              Decision time for {dayData.date}:{" "}
              <strong>{new Date(dayData.decision_time).toUTCString()}</strong> — the latest WINDFOR run
              published by then is what a trader had on screen when buying day-ahead power for this day.
            </p>
            <DailyChart points={dayData.points} />
            <MetricsPanel
              metrics={dayData.metrics}
              title={`Forecast accuracy for ${dayData.date}`}
              note="Error = forecast − actual. Positive bias means the forecast over-stated available wind, i.e. the buyer would have under-procured from the day-ahead market."
            />
          </>
        ) : (
          <p>Loading…</p>
        )}
      </section>

      <section className="panel">
        <h2>2. How accurate the day-ahead forecast has been this month</h2>
        {summary ? (
          <>
            <MetricsPanel metrics={summary.overall} title="January 2026 overall" />
            <p className="chart-caption">
              Daily mean absolute error (bars) and bias (red line). Click a bar to inspect that day above.
            </p>
            <AccuracyTrend daily={summary.daily} selected={selectedDay} onSelect={setSelectedDay} />
          </>
        ) : (
          <p>Loading…</p>
        )}
      </section>

      <footer>
        <p>
          Data: Elexon BMRS (FUELHH actuals, WINDFOR forecasts), fuelType=WIND, national level. Decision
          rule: latest forecast run published by 11:00 UTC on D-1. Scope: January 2026 only.
        </p>
      </footer>
    </div>
  );
}
