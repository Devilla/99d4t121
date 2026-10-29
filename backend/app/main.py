from __future__ import annotations

import datetime as dt
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import analysis

app = FastAPI(
    title="UK Wind Day-Ahead Forecast Accuracy API",
    description=(
        "Serves national wind generation actuals vs. the forecast that was "
        "actually available at UK day-ahead decision time, for January 2026."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # scoped demo app; tighten for a real deployment
    allow_methods=["GET"],
    allow_headers=["*"],
)

YEAR, MONTH = 2026, 1


@lru_cache(maxsize=1)
def _frames():
    return analysis.load_month_frames(YEAR, MONTH)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/days")
def days():
    import calendar

    n_days = calendar.monthrange(YEAR, MONTH)[1]
    return {
        "month": f"{YEAR:04d}-{MONTH:02d}",
        "days": [dt.date(YEAR, MONTH, d).isoformat() for d in range(1, n_days + 1)],
    }


@app.get("/api/forecast-vs-actual")
def forecast_vs_actual(date: str = Query(..., description="Delivery day, YYYY-MM-DD")):
    try:
        delivery_day = dt.date.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    if delivery_day.year != YEAR or delivery_day.month != MONTH:
        raise HTTPException(status_code=400, detail="only January 2026 is in scope for this build")

    actuals, forecasts = _frames()
    return analysis.day_comparison(actuals, forecasts, delivery_day)


@app.get("/api/accuracy-summary")
def accuracy_summary():
    actuals, forecasts = _frames()
    return analysis.month_summary(actuals, forecasts, YEAR, MONTH)
