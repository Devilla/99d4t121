"""Core domain logic: pick the forecast a trader actually had, and score it.

Day-ahead market mechanics (simplified for this scope):

- GB day-ahead auctions (EPEX/N2EX) close around 11:00 UK time on day D-1
  for delivery day D. We model that as the single "decision time" per
  delivery day: DECISION_HOUR_UTC on D-1. In January the UK is on GMT, so
  UTC == local time and no DST handling is needed for this dataset.
- At that decision time, the trader only has whichever WINDFOR forecast
  *runs* had already been published (publishTime <= decision time).
  WINDFOR publishes several runs a day; for every delivery hour we take
  the most recently published run as of the decision time -- i.e. exactly
  what was on screen when the buy call had to be made.
- Actual outturn (FUELHH) is half-hourly; WINDFOR is hourly. We align the
  two by averaging each pair of half-hourly actuals into an hourly mean.
"""
from __future__ import annotations

import datetime as dt
import math
from typing import Any

import pandas as pd

from . import elexon_client
from .cache import cached_fetch

DECISION_HOUR_UTC = 11


def _month_bounds(year: int, month: int) -> tuple[dt.datetime, dt.datetime]:
    start = dt.datetime(year, month, 1, tzinfo=dt.timezone.utc)
    end = (dt.datetime(year, month, 28, tzinfo=dt.timezone.utc) + dt.timedelta(days=4)).replace(day=1)
    return start, end


def load_month_frames(year: int, month: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Actuals and forecast-run rows covering the given delivery month.

    We pad the fetch window on both sides: actuals need the final half
    hour of the previous day for hourly alignment, and forecasts need
    runs published up to a day before the month to cover the first
    delivery day's decision time.
    """
    month_start, month_end = _month_bounds(year, month)
    actuals_from = month_start - dt.timedelta(days=1)
    forecasts_from = month_start - dt.timedelta(days=2)

    actuals_raw = cached_fetch(
        f"actuals:{actuals_from.isoformat()}:{month_end.isoformat()}",
        lambda: elexon_client.fetch_wind_actuals(actuals_from, month_end),
    )
    forecasts_raw = cached_fetch(
        f"forecasts:{forecasts_from.isoformat()}:{month_end.isoformat()}",
        lambda: elexon_client.fetch_wind_forecasts(forecasts_from, month_end),
    )

    actuals = pd.DataFrame(actuals_raw)
    if not actuals.empty:
        actuals["startTime"] = pd.to_datetime(actuals["startTime"], utc=True)
        actuals["generation"] = pd.to_numeric(actuals["generation"])

    forecasts = pd.DataFrame(forecasts_raw)
    if not forecasts.empty:
        forecasts["startTime"] = pd.to_datetime(forecasts["startTime"], utc=True)
        forecasts["publishTime"] = pd.to_datetime(forecasts["publishTime"], utc=True)
        forecasts["generation"] = pd.to_numeric(forecasts["generation"])

    return actuals, forecasts


def decision_time_for_delivery_day(delivery_day: dt.date) -> dt.datetime:
    day_before = delivery_day - dt.timedelta(days=1)
    return dt.datetime(
        day_before.year, day_before.month, day_before.day, DECISION_HOUR_UTC, tzinfo=dt.timezone.utc
    )


def decision_time_forecast_for_day(forecasts: pd.DataFrame, delivery_day: dt.date) -> pd.DataFrame:
    """The forecast curve for `delivery_day` as it stood at the decision time.

    Returns columns: startTime, forecast_mw, run_published_at
    """
    decision_time = decision_time_for_delivery_day(delivery_day)
    day_start = pd.Timestamp(delivery_day, tz="UTC")
    day_end = day_start + pd.Timedelta(days=1)

    if forecasts.empty:
        return pd.DataFrame(columns=["startTime", "forecast_mw", "run_published_at"])

    available = forecasts[forecasts["publishTime"] <= decision_time]
    in_day = available[(available["startTime"] >= day_start) & (available["startTime"] < day_end)]
    if in_day.empty:
        return pd.DataFrame(columns=["startTime", "forecast_mw", "run_published_at"])

    latest = (
        in_day.sort_values("publishTime")
        .groupby("startTime", as_index=False)
        .last()[["startTime", "generation", "publishTime"]]
        .rename(columns={"generation": "forecast_mw", "publishTime": "run_published_at"})
        .sort_values("startTime")
        .reset_index(drop=True)
    )
    return latest


def hourly_actual_for_day(actuals: pd.DataFrame, delivery_day: dt.date) -> pd.DataFrame:
    """Half-hourly actual outturn for `delivery_day`, averaged to hourly."""
    day_start = pd.Timestamp(delivery_day, tz="UTC")
    day_end = day_start + pd.Timedelta(days=1)
    if actuals.empty:
        return pd.DataFrame(columns=["startTime", "actual_mw"])
    in_day = actuals[(actuals["startTime"] >= day_start) & (actuals["startTime"] < day_end)]
    if in_day.empty:
        return pd.DataFrame(columns=["startTime", "actual_mw"])
    hourly = (
        in_day.set_index("startTime")["generation"]
        .resample("1h")
        .mean()
        .rename("actual_mw")
        .reset_index()
    )
    return hourly


def _metrics(errors: pd.Series, actuals: pd.Series) -> dict[str, float | None]:
    if errors.empty:
        return {"mae": None, "rmse": None, "bias": None, "mape": None, "n": 0}
    mae = float(errors.abs().mean())
    rmse = float(math.sqrt((errors**2).mean()))
    bias = float(errors.mean())
    nonzero = actuals.abs() > 1e-6
    mape = float((errors[nonzero].abs() / actuals[nonzero].abs()).mean() * 100) if nonzero.any() else None
    return {"mae": mae, "rmse": rmse, "bias": bias, "mape": mape, "n": int(len(errors))}


def day_comparison(actuals: pd.DataFrame, forecasts: pd.DataFrame, delivery_day: dt.date) -> dict[str, Any]:
    forecast_curve = decision_time_forecast_for_day(forecasts, delivery_day)
    actual_curve = hourly_actual_for_day(actuals, delivery_day)
    merged = pd.merge(forecast_curve, actual_curve, on="startTime", how="inner").sort_values("startTime")

    if not merged.empty:
        merged["error_mw"] = merged["forecast_mw"] - merged["actual_mw"]
        metrics = _metrics(merged["error_mw"], merged["actual_mw"])
    else:
        metrics = _metrics(pd.Series(dtype=float), pd.Series(dtype=float))

    points = [
        {
            "time": row.startTime.isoformat(),
            "forecast_mw": None if pd.isna(row.forecast_mw) else round(float(row.forecast_mw), 1),
            "actual_mw": None if pd.isna(row.actual_mw) else round(float(row.actual_mw), 1),
            "error_mw": None
            if "error_mw" not in merged.columns or pd.isna(row.error_mw)
            else round(float(row.error_mw), 1),
        }
        for row in merged.itertuples()
    ]

    return {
        "date": delivery_day.isoformat(),
        "decision_time": decision_time_for_delivery_day(delivery_day).isoformat(),
        "points": points,
        "metrics": metrics,
    }


def month_summary(actuals: pd.DataFrame, forecasts: pd.DataFrame, year: int, month: int) -> dict[str, Any]:
    import calendar

    n_days = calendar.monthrange(year, month)[1]
    days = [dt.date(year, month, d) for d in range(1, n_days + 1)]

    daily: list[dict[str, Any]] = []
    all_errors: list[float] = []
    all_actuals: list[float] = []

    for day in days:
        comparison = day_comparison(actuals, forecasts, day)
        m = comparison["metrics"]
        daily.append({"date": day.isoformat(), **m})
        for p in comparison["points"]:
            if p["error_mw"] is not None and p["actual_mw"] is not None:
                all_errors.append(p["error_mw"])
                all_actuals.append(p["actual_mw"])

    overall = _metrics(pd.Series(all_errors), pd.Series(all_actuals))
    return {
        "month": f"{year:04d}-{month:02d}",
        "decision_rule": f"latest WINDFOR run published by {DECISION_HOUR_UTC:02d}:00 UTC on D-1",
        "overall": overall,
        "daily": daily,
    }
