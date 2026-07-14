"""Tests for mydash set CLI commands.

Strategy: CliRunner against the root Typer app; patch
``mydash.cli.commands.set._helpers.UserConfigurationService`` so commands
write under tmp_path. Cover bare set, -lo, incomplete paths, and happy paths.
"""

from pathlib import Path
from unittest.mock import MagicMock

from typer.testing import CliRunner

from mydash.cli.main import app
from mydash.models.geocoding import Coordinates
from mydash.services.user_config import UserConfigurationService

runner = CliRunner()


def test_set_without_subcommand_prompts_for_help():
    result = runner.invoke(app, ["set"])
    assert result.exit_code == 0, result.output
    assert "mydash set --help" in result.output
    assert "No configuration change specified" in result.output
    assert "mydash set" in result.output


def test_set_list_options_short_and_long():
    for flag in ("-lo", "--list-options"):
        result = runner.invoke(app, ["set", flag])
        assert result.exit_code == 0, result.output
        assert "weather city" in result.output
        assert "stocks add" in result.output
        assert "news category" in result.output
        assert "geocoding provider" in result.output
        assert "show" in result.output
        assert "set options" in result.output


def test_set_weather_units(tmp_path: Path, mocker):
    path = tmp_path / "config.json"
    mocker.patch(
        "mydash.cli.commands.set._helpers.UserConfigurationService",
        side_effect=lambda: UserConfigurationService(config_path=path),
    )

    result = runner.invoke(app, ["set", "weather", "units", "imperial"])
    assert result.exit_code == 0, result.output
    assert "imperial" in result.output
    assert "Weather" in result.output

    svc = UserConfigurationService(config_path=path)
    assert svc.get_weather_forecast_units() == "imperial"


def test_set_stocks_add_and_news_category(tmp_path: Path, mocker):
    path = tmp_path / "config.json"
    mocker.patch(
        "mydash.cli.commands.set._helpers.UserConfigurationService",
        side_effect=lambda: UserConfigurationService(config_path=path),
    )

    r1 = runner.invoke(app, ["set", "stocks", "add", "goog"])
    assert r1.exit_code == 0, r1.output
    assert "GOOG" in r1.output

    r2 = runner.invoke(app, ["set", "news", "category", "politics"])
    assert r2.exit_code == 0, r2.output
    assert "politics" in r2.output

    svc = UserConfigurationService(config_path=path)
    assert "GOOG" in svc.get_stock_symbols()
    assert svc.get_news_category() == "politics"


def test_set_weather_city(tmp_path: Path, mocker):
    path = tmp_path / "config.json"
    coords = Coordinates(latitude=30.27, longitude=-97.74)
    geo = MagicMock()
    geo.get_coordinates.return_value = coords
    mocker.patch(
        "mydash.services.user_config.get_geocoding_client", return_value=geo
    )
    mocker.patch(
        "mydash.cli.commands.set._helpers.UserConfigurationService",
        side_effect=lambda: UserConfigurationService(config_path=path),
    )

    result = runner.invoke(app, ["set", "weather", "city", "Austin"])
    assert result.exit_code == 0, result.output
    assert "Austin" in result.output

    svc = UserConfigurationService(config_path=path)
    assert svc.get_city() == "Austin"
    assert svc.get_coordinates() == coords


def test_set_show(tmp_path: Path, mocker):
    path = tmp_path / "config.json"
    UserConfigurationService(config_path=path)
    mocker.patch(
        "mydash.cli.commands.set._helpers.UserConfigurationService",
        side_effect=lambda: UserConfigurationService(config_path=path),
    )

    result = runner.invoke(app, ["set", "show"])
    assert result.exit_code == 0, result.output
    assert "Miami" in result.output
    assert "weather_units" in result.output
    assert "Config" in result.output


def test_set_invalid_units_exits_nonzero(tmp_path: Path, mocker):
    path = tmp_path / "config.json"
    mocker.patch(
        "mydash.cli.commands.set._helpers.UserConfigurationService",
        side_effect=lambda: UserConfigurationService(config_path=path),
    )

    result = runner.invoke(app, ["set", "weather", "units", "kelvin"])
    assert result.exit_code == 1
    assert "Error" in result.output
    assert "invalid weather units" in result.output


def test_provider_help_lists_available_providers():
    cases = [
        (["set", "weather", "provider", "--help"], "open-meteo"),
        (["set", "stocks", "provider", "--help"], "alpaca"),
        (["set", "news", "provider", "--help"], "noozra"),
        (["set", "geocoding", "provider", "--help"], "open-meteo"),
        (["set", "weather", "units", "--help"], "imperial"),
        (["set", "weather", "units", "--help"], "metric"),
    ]
    for args, expected in cases:
        result = runner.invoke(app, args)
        assert result.exit_code == 0, result.output
        assert expected in result.output, (args, result.output)


def test_incomplete_domain_paths_show_hints():
    cases = [
        (["set", "weather"], ["city", "units", "provider", "Next steps"]),
        (["set", "stocks"], ["add", "remove", "provider", "Next steps"]),
        (["set", "news"], ["category", "provider", "Next steps"]),
        (["set", "geocoding"], ["provider", "Next steps"]),
    ]
    for args, expected_parts in cases:
        result = runner.invoke(app, args)
        assert result.exit_code == 0, result.output
        assert "Missing command" not in result.output
        for part in expected_parts:
            assert part in result.output, (args, part, result.output)


def test_incomplete_leaf_paths_show_hints():
    cases = [
        (
            ["set", "weather", "provider"],
            ["open-meteo", "Available", "provider"],
        ),
        (
            ["set", "weather", "units"],
            ["imperial", "metric", "Available"],
        ),
        (
            ["set", "weather", "city"],
            ["city", "Next steps"],
        ),
        (
            ["set", "stocks", "add"],
            ["symbol", "AAPL"],
        ),
        (
            ["set", "stocks", "provider"],
            ["alpaca", "Available"],
        ),
        (
            ["set", "news", "category"],
            ["category", "tech"],
        ),
        (
            ["set", "news", "provider"],
            ["noozra", "Available"],
        ),
        (
            ["set", "geocoding", "provider"],
            ["open-meteo", "Available"],
        ),
    ]
    for args, expected_parts in cases:
        result = runner.invoke(app, args)
        assert result.exit_code == 0, result.output
        assert "Missing argument" not in result.output
        for part in expected_parts:
            assert part in result.output, (args, part, result.output)
