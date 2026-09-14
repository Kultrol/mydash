"""Tests for provider text sanitizing.

Strategy: feed the sequences an attacker would actually send through
``clean_text`` directly, then through the models that apply it on validation.
"""

from datetime import UTC, datetime

import pytest

from mydash.models.geocoding import Coordinates, Place
from mydash.models.news import HeadLine
from mydash.models.text import clean_text
from mydash.models.weather import MultiDayForecast


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("plain headline", "plain headline"),
        ("clear\x1b[2Jscreen", "clear[2Jscreen"),
        ("clip\x1b]52;c;cHduZWQ=\x07board", "clip]52;c;cHduZWQ=board"),
        ("c1\x9b31mcsi", "c131mcsi"),
        ("two\nlines\tand\rmore", "two lines and more"),
        ("bidi ‮evil‬ done", "bidi evil done"),
        ("isolate ⁦x⁩", "isolate x"),
        ("Zürich · São Paulo · 東京", "Zürich · São Paulo · 東京"),
    ],
)
def test_clean_text(raw, expected):
    assert clean_text(raw) == expected


def test_headline_fields_are_cleaned():
    headline = HeadLine(
        headline="Markets\x1b[2J rally",
        publication="Times\x1b]0;pwned\x07",
        description="line one\nline two",
        source_url="https://example.com/\x1b\\a",
        category="tech",
        published_time=datetime(2026, 7, 13, tzinfo=UTC),
    )

    assert headline.headline == "Markets[2J rally"
    assert headline.publication == "Times]0;pwned"
    assert headline.description == "line one line two"
    assert "\x1b" not in headline.source_url


def test_place_fields_are_cleaned():
    place = Place(
        name="Spring\x1b[2Jfield",
        coordinates=Coordinates(latitude=39.8, longitude=-89.6),
        region="Illi‮nois",
    )

    assert place.label == "Spring[2Jfield, Illinois"


def test_forecast_timezone_is_cleaned():
    forecast = MultiDayForecast(days=[], timezone="Europe/\x1bParis")

    assert forecast.timezone == "Europe/Paris"
