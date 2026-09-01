"""Tests for the weather domain models.

Focus on ``MultiDayForecast.upcoming_hours``, which decides what the weather
panel shows and has to reason about the forecast location's clock, not ours.
"""

from datetime import UTC, date, datetime

import pytest

from mydash.models.weather import DayForecast, HourForecast, MultiDayForecast


def _hour(day: int, hour: int) -> HourForecast:
    return HourForecast(
        time=datetime(2026, 8, day, hour),
        temperature=20.0,
        feels_like_temperature=21.0,
        cloud_cover=10,
        wind_speed=3.0,
        chance_of_rain=0,
        amount_of_rain=0.0,
        weather_code=0,
        uv_index=4.0,
    )


def _forecast(timezone: str | None = "America/New_York") -> MultiDayForecast:
    return MultiDayForecast(
        days=[
            DayForecast(date=date(2026, 8, 30), hours=[_hour(30, h) for h in range(24)]),
            DayForecast(date=date(2026, 8, 31), hours=[_hour(31, h) for h in range(6)]),
        ],
        timezone=timezone,
    )


def test_upcoming_hours_starts_at_the_current_hour():
    hours = _forecast().upcoming_hours(3, now=datetime(2026, 8, 30, 9, 41))

    assert [hour.time.hour for hour in hours] == [9, 10, 11]


def test_upcoming_hours_crosses_midnight_into_the_next_day():
    hours = _forecast().upcoming_hours(4, now=datetime(2026, 8, 30, 22, 5))

    assert [(hour.time.day, hour.time.hour) for hour in hours] == [
        (30, 22),
        (30, 23),
        (31, 0),
        (31, 1),
    ]


def test_upcoming_hours_falls_back_when_the_forecast_is_all_past():
    hours = _forecast().upcoming_hours(2, now=datetime(2026, 9, 15, 12, 0))

    assert [hour.time.hour for hour in hours] == [0, 1]


def test_upcoming_hours_returns_at_most_count():
    assert len(_forecast().upcoming_hours(5, now=datetime(2026, 8, 30, 0, 0))) == 5


def test_upcoming_hours_on_an_empty_forecast():
    assert MultiDayForecast(days=[]).upcoming_hours(6) == []


def test_upcoming_hours_tolerates_an_aware_reference_time():

    hours = _forecast().upcoming_hours(
        1, now=datetime(2026, 8, 30, 9, 0, tzinfo=UTC)
    )

    assert hours[0].time.hour == 9


def test_local_now_uses_the_forecast_timezone():
    tokyo = _forecast("Asia/Tokyo").local_now()
    new_york = _forecast("America/New_York").local_now()

    # Tokyo is ahead of New York, every day of the year.
    assert tokyo > new_york


@pytest.mark.parametrize("timezone", [None, "Not/AZone"])
def test_local_now_falls_back_to_machine_time(timezone):
    reference = datetime.now()

    result = _forecast(timezone).local_now()

    assert abs((result - reference).total_seconds()) < 5


def test_today_is_the_first_day():
    assert _forecast().today.date == date(2026, 8, 30)


def test_today_is_none_without_days():
    assert MultiDayForecast(days=[]).today is None


def test_hour_property_mirrors_the_timestamp():
    assert _hour(30, 17).hour == 17
