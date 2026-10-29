"""Thin client for the Elexon BMRS Insights API (data.elexon.co.uk).

Only the two datasets this product needs are covered:

- FUELHH: half-hourly outturn generation by fuel type (actuals). We only
  ever ask for fuelType=WIND.
- WINDFOR: the national wind generation forecast. Each forecast "run" is
  identified by its publishTime; a run contains hourly startTime points
  stretching out over the following ~1-2 days.

No API key is required for these endpoints as of writing.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

import requests

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
TIMEOUT_S = 30


def _iso(d: dt.datetime) -> str:
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_wind_actuals(start: dt.datetime, end: dt.datetime) -> list[dict[str, Any]]:
    """Actual half-hourly wind generation (MW) for [start, end).

    Filters on fuelType=WIND server-side via the FUELHH stream endpoint.
    """
    params = {
        "publishDateTimeFrom": _iso(start),
        "publishDateTimeTo": _iso(end),
        "fuelType": "WIND",
    }
    resp = requests.get(f"{BASE_URL}/datasets/FUELHH/stream", params=params, timeout=TIMEOUT_S)
    resp.raise_for_status()
    return resp.json()


def fetch_wind_forecasts(start: dt.datetime, end: dt.datetime) -> list[dict[str, Any]]:
    """Raw WINDFOR forecast rows whose *publishTime* falls in [start, end).

    Each row also carries its own startTime (the delivery half hour/hour the
    forecast value applies to) and a generation value in MW.
    """
    params = {
        "publishDateTimeFrom": _iso(start),
        "publishDateTimeTo": _iso(end),
    }
    resp = requests.get(f"{BASE_URL}/datasets/WINDFOR/stream", params=params, timeout=TIMEOUT_S)
    resp.raise_for_status()
    return resp.json()
