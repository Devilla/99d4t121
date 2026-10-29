"""Unit tests for the day-ahead selection + accuracy logic.

These use small synthetic frames so they run offline and fast -- no
network calls to Elexon in the test suite.
"""
import datetime as dt

import pandas as pd

from app import analysis


def test_decision_time_is_11utc_on_d_minus_1():
    assert analysis.decision_time_for_delivery_day(dt.date(2026, 1, 15)) == dt.datetime(
        2026, 1, 14, 11, tzinfo=dt.timezone.utc
    )


def test_decision_time_forecast_picks_latest_run_before_cutoff():
    forecasts = pd.DataFrame(
        [
            # stale run, published well before cutoff
            {
                "startTime": pd.Timestamp("2026-01-15T12:00:00Z"),
                "publishTime": pd.Timestamp("2026-01-14T05:00:00Z"),
                "generation": 1000,
            },
            # best run available at the 11:00 D-1 cutoff
            {
                "startTime": pd.Timestamp("2026-01-15T12:00:00Z"),
                "publishTime": pd.Timestamp("2026-01-14T10:30:00Z"),
                "generation": 1200,
            },
            # a later run published AFTER the cutoff must be ignored
            {
                "startTime": pd.Timestamp("2026-01-15T12:00:00Z"),
                "publishTime": pd.Timestamp("2026-01-14T16:00:00Z"),
                "generation": 1500,
            },
        ]
    )
    curve = analysis.decision_time_forecast_for_day(forecasts, dt.date(2026, 1, 15))
    assert len(curve) == 1
    assert curve.iloc[0]["forecast_mw"] == 1200


def test_hourly_actual_averages_two_half_hours():
    actuals = pd.DataFrame(
        [
            {"startTime": pd.Timestamp("2026-01-15T12:00:00Z"), "generation": 1000},
            {"startTime": pd.Timestamp("2026-01-15T12:30:00Z"), "generation": 1200},
        ]
    )
    hourly = analysis.hourly_actual_for_day(actuals, dt.date(2026, 1, 15))
    assert len(hourly) == 1
    assert hourly.iloc[0]["actual_mw"] == 1100


def test_day_comparison_computes_mae_and_bias():
    forecasts = pd.DataFrame(
        [
            {
                "startTime": pd.Timestamp("2026-01-15T12:00:00Z"),
                "publishTime": pd.Timestamp("2026-01-14T10:00:00Z"),
                "generation": 1100,
            }
        ]
    )
    actuals = pd.DataFrame(
        [
            {"startTime": pd.Timestamp("2026-01-15T12:00:00Z"), "generation": 1000},
            {"startTime": pd.Timestamp("2026-01-15T12:30:00Z"), "generation": 1000},
        ]
    )
    result = analysis.day_comparison(actuals, forecasts, dt.date(2026, 1, 15))
    assert result["metrics"]["n"] == 1
    assert result["metrics"]["mae"] == 100
    assert result["metrics"]["bias"] == 100  # forecast over-estimated actual
