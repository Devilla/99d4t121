# UK Wind — Day-Ahead Procurement View

A small web app for a GB electricity supplier's day-ahead trading desk. It answers the two questions
the team needs when buying power from the day-ahead market to cover demand the wind fleet won't:

1. **What did the wind forecast actually say, at the moment the buy decision had to be made?**
   (Not today's forecast — the one that existed at decision time, D-1.)
2. **How accurate has that forecast been?**, quantified (MAE, RMSE, bias, MAPE), so the error can be
   factored into the procurement decision.

Scope, by design: national-level wind only, January 2026 only, two Elexon BMRS datasets
(`FUELHH` actuals, `WINDFOR` forecasts). See [Decision rule](#decision-rule) for the modeling choices.

**Live app:** _TODO — add the Vercel URL once deployed_
**Video demo:** _TODO — add the unlisted YouTube link_

## AI tool disclosure

This project's backend, frontend, Docker setup and docs were built with the assistance of an AI coding
assistant (Claude, via Claude Code), with a human directing scope, reviewing output, and verifying the
app against live data and in a real browser before submission.

## Repo layout

```
.
├── backend/              FastAPI app — the actual application logic
│   ├── app/
│   │   ├── main.py        API routes
│   │   ├── analysis.py    forecast-selection + accuracy-metric logic (the interesting part)
│   │   ├── elexon_client.py  thin HTTP client for the two Elexon datasets
│   │   └── cache.py        on-disk cache (Jan 2026 data is historical/immutable, so we don't
│   │                       need to re-fetch it on every request)
│   ├── tests/              offline unit tests for analysis.py (no network calls)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/              React (Vite) single-page app
│   ├── src/
│   │   ├── App.jsx         page layout / data loading
│   │   ├── api.js          fetch wrappers for the backend API
│   │   └── components/     DayPicker, DailyChart, AccuracyTrend, MetricsPanel
│   ├── Dockerfile          builds the static app, serves it via nginx
│   └── nginx.conf          proxies /api/* to the backend container
├── api/
│   └── index.py           Vercel Python Function entrypoint — re-exports the same FastAPI
│                            app from backend/app/main.py (one copy of the logic, two ways to run it)
├── docker-compose.yml      runs backend + frontend together for local/dev use
└── vercel.json             routes /api/* to the Python function, everything else to the static build
```

## How to start the application

### Option A — Docker (recommended, closest to "just run it")

```sh
docker compose up --build
```

- Frontend: http://localhost:8080
- Backend API directly: http://localhost:8811/api/health

(Host ports 8811/8080 were picked to avoid clashing with other local projects; change the left-hand
side of the `ports:` mapping in `docker-compose.yml` if you need different ones. Internally the
frontend's nginx always reaches the backend at `http://backend:8000`.)

### Option B — run both locally without Docker

```sh
# backend
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# frontend, in a second terminal
cd frontend
npm install
npm run dev
```

Vite's dev server proxies `/api/*` to `http://127.0.0.1:8000` (see `vite.config.js`), so open
http://localhost:5173.

### Running the backend tests

```sh
cd backend
source .venv/bin/activate
python -m pytest
```

## Decision rule

GB day-ahead auctions (EPEX/N2EX) close around **11:00 UK time on day D-1** for delivery day D. The app
models the trading desk's decision moment as exactly that: `11:00 UTC` on D-1 (January is GMT, so UTC
and UK local time are the same — no DST handling needed for this month).

For each delivery day D, the app:

1. Takes every WINDFOR forecast **run** published at or before that decision time.
2. For each delivery hour, keeps only the **most recently published** run — i.e. exactly what would
   have been on screen at decision time, not a forecast refined afterwards.
3. Compares that curve against actual outturn (`FUELHH`, `fuelType=WIND`), averaging the two
   half-hourly actuals in each hour so the two series line up on an hourly grid.
4. Reports MAE, RMSE, bias (mean error — positive means the forecast over-stated available wind, which
   is the direction that leads to under-procuring from the day-ahead market) and MAPE, both per day and
   for the month as a whole.

This logic lives entirely in `backend/app/analysis.py` and is covered by offline unit tests in
`backend/tests/test_analysis.py`.

## Notes / known limitations (given the 16-hour scope)

- National-level wind only — no regional breakdown, no other fuel types, no demand-side data.
- January 2026 only; the API hard-codes this month rather than accepting an arbitrary date range.
- The 11:00 UTC D-1 cutoff is a reasonable approximation of the real GB day-ahead gate closure, not an
  exact replica of EPEX/N2EX auction timing.
- Data is fetched from Elexon's public BMRS API (no key required) and cached to disk after first fetch.
