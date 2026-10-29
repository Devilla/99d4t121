// In dev, Vite proxies /api to the local FastAPI server (see vite.config.js).
// In prod on Vercel, /api is routed to the Python serverless function.
// VITE_API_BASE lets you point at a separately-hosted backend if needed.
const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function getJSON(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json();
}

export function getDays() {
  return getJSON("/api/days");
}

export function getForecastVsActual(date) {
  return getJSON(`/api/forecast-vs-actual?date=${date}`);
}

export function getAccuracySummary() {
  return getJSON("/api/accuracy-summary");
}
