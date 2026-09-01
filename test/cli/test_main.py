"""Tests for the mydash CLI surface.

Strategy: CliRunner for command smoke; mock services (not HTTP) throughout.
The wide-console fixture keeps Rich from truncating the text being asserted on.
"""

from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from typer.testing import CliRunner

from mydash import __version__
from mydash.cli import ui
from mydash.cli.main import app
from mydash.models.news import HeadLine, NewsHeadlines
from mydash.models.stocks import StockBar, StockBars, StockQuote, StockQuotes
from mydash.models.weather import DayForecast, HourForecast, MultiDayForecast
from mydash.services.brief import DailyBrief
from mydash.services.user_config import UserConfigurationService

runner = CliRunner()


@pytest.fixture(autouse=True)
def wide_console():
    """Give Rich room so assertions do not trip over ellipses."""
    original = ui.console.width
    ui.console.width = 200
    yield
    ui.console.width = original


@pytest.fixture
def config_db(tmp_path: Path, mocker) -> Path:
    """Point every command at a temp configuration database."""
    path = tmp_path / "mydash.db"
    UserConfigurationService(db_path=path).close()
    mocker.patch(
        "mydash.cli.context.UserConfigurationService",
        side_effect=lambda: UserConfigurationService(db_path=path),
    )
    return path


def _sample_brief(**overrides) -> DailyBrief:
    defaults = dict(
        headlines=NewsHeadlines(
            headlines=[
                HeadLine(
                    headline="CLI smoke headline",
                    publication="Test Wire",
                    description=None,
                    source_url="https://example.com",
                    category="politics",
                    published_time=datetime(2026, 7, 13, 12, 0, tzinfo=UTC),
                )
            ]
        ),
        stock_quotes=StockQuotes(
            quotes=[
                StockQuote(
                    ticker_name="SPY",
                    ask_price=1.0,
                    bid_price=1.0,
                    time=datetime(2026, 7, 13, 14, 0, tzinfo=UTC),
                )
            ]
        ),
        stock_bars=StockBars(
            bars=[
                StockBar(
                    ticker_name="SPY",
                    open=1.0,
                    close=1.0,
                    time=datetime(2026, 7, 13, 14, 0, tzinfo=UTC),
                )
            ]
        ),
        weather=MultiDayForecast(
            days=[
                DayForecast(
                    date=date(2026, 7, 13),
                    hours=[
                        HourForecast(
                            time=datetime(2026, 7, 13, 12),
                            temperature=25.0,
                            feels_like_temperature=26.0,
                            cloud_cover=10,
                            wind_speed=2.0,
                            chance_of_rain=0,
                            amount_of_rain=0.0,
                            weather_code=0,
                            uv_index=5.0,
                        )
                    ],
                )
            ]
        ),
        city="Miami",
        news_category="politics",
        symbols=["SPY", "AAPL", "MSFT"],
        weather_units="metric",
    )
    defaults.update(overrides)
    return DailyBrief(**defaults)


def _patch_brief(mocker, brief: DailyBrief) -> MagicMock:
    service = MagicMock()
    service.build = AsyncMock(return_value=brief)
    mocker.patch("mydash.cli.commands.brief.BriefService", return_value=service)
    return service


# --- root ------------------------------------------------------------------


def test_version_flag_prints_the_version():
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.output


def test_bare_invocation_shows_the_welcome_panel(config_db):
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "mydash" in result.output
    assert "Miami" in result.output  # current preferences
    assert "mydash brief" in result.output  # command list
    assert "mydash init" in result.output  # quick-start hint


def test_welcome_survives_unreadable_preferences(mocker):
    mocker.patch(
        "mydash.cli.context.UserConfigurationService",
        side_effect=ValueError("stored preferences have an invalid structure"),
    )

    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "Could not read your preferences" in result.output


def test_help_lists_the_command_tree():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in ("brief", "weather", "news", "stocks", "set", "config", "doctor"):
        assert command in result.output


# --- brief -----------------------------------------------------------------


def test_brief_uses_service_and_renderer(config_db, mocker):
    brief = _sample_brief()
    service = _patch_brief(mocker, brief)
    render = mocker.patch("mydash.cli.commands.brief.render_brief")

    result = runner.invoke(app, ["brief"])

    assert result.exit_code == 0, result.output
    service.build.assert_awaited_once()
    assert service.build.await_args.kwargs["refresh"] is False
    assert service.build.await_args.kwargs["domains"] is None
    render.assert_called_once()
    assert render.call_args.args[1] is brief


def test_brief_refresh_flag_reaches_the_service(config_db, mocker):
    service = _patch_brief(mocker, _sample_brief())
    mocker.patch("mydash.cli.commands.brief.render_brief")

    result = runner.invoke(app, ["brief", "--refresh"])

    assert result.exit_code == 0, result.output
    assert service.build.await_args.kwargs["refresh"] is True


def test_brief_only_flag_selects_domains(config_db, mocker):
    service = _patch_brief(mocker, _sample_brief())
    mocker.patch("mydash.cli.commands.brief.render_brief")

    result = runner.invoke(app, ["brief", "--only", "weather, news"])

    assert result.exit_code == 0, result.output
    assert service.build.await_args.kwargs["domains"] == ["weather", "news"]


def test_brief_rejects_an_unknown_panel(config_db, mocker):
    service = _patch_brief(mocker, _sample_brief())

    result = runner.invoke(app, ["brief", "--only", "horoscope"])

    # A usage error, not a crash: exit 2, and no fetch was attempted.
    assert result.exit_code == 2
    assert "horoscope" in result.output
    assert "stocks" in result.output
    service.build.assert_not_awaited()


def test_brief_only_flag_is_case_insensitive(config_db, mocker):
    service = _patch_brief(mocker, _sample_brief())
    mocker.patch("mydash.cli.commands.brief.render_brief")

    result = runner.invoke(app, ["brief", "--only", "Weather,NEWS"])

    assert result.exit_code == 0, result.output
    assert service.build.await_args.kwargs["domains"] == ["weather", "news"]


def test_brief_compact_flag_reaches_the_renderer(config_db, mocker):
    _patch_brief(mocker, _sample_brief())
    render = mocker.patch("mydash.cli.commands.brief.render_brief")

    runner.invoke(app, ["brief", "--compact"])

    assert render.call_args.kwargs["compact"] is True


def test_brief_json_output_is_machine_readable(config_db, mocker):
    _patch_brief(mocker, _sample_brief())

    result = runner.invoke(app, ["brief", "--json"])

    assert result.exit_code == 0, result.output
    assert '"city"' in result.output
    assert "Miami" in result.output


def test_brief_renders_panels_and_headings(config_db, mocker):
    _patch_brief(mocker, _sample_brief())

    result = runner.invoke(app, ["brief"])

    assert result.exit_code == 0, result.output
    assert "Markets" in result.output
    assert "Weather" in result.output
    assert "Headlines" in result.output
    assert "CLI smoke headline" in result.output


def test_brief_names_a_failed_panel_instead_of_crashing(config_db, mocker):
    brief = _sample_brief(errors={"stocks": "Alpaca credentials are missing"})
    _patch_brief(mocker, brief)

    result = runner.invoke(app, ["brief"])

    assert result.exit_code == 0, result.output
    assert "Unavailable" in result.output
    assert "Alpaca credentials are missing" in result.output
    # The healthy panels are still there.
    assert "CLI smoke headline" in result.output


# --- single-domain commands ------------------------------------------------


def test_weather_command_renders_the_forecast(config_db, mocker):
    service = MagicMock()
    service.fetch_forecast = AsyncMock(return_value=_sample_brief().weather)
    mocker.patch("mydash.cli.commands.brief.WeatherService", return_value=service)

    result = runner.invoke(app, ["weather"])

    assert result.exit_code == 0, result.output
    assert "Weather" in result.output
    assert "Miami" in result.output
    service.fetch_forecast.assert_awaited_once()


def test_weather_city_override_geocodes(config_db, mocker):
    from mydash.models.geocoding import Coordinates, Place

    place = Place(
        name="Austin",
        coordinates=Coordinates(latitude=30.27, longitude=-97.74),
        region="Texas",
        country="United States",
    )
    service = MagicMock()
    service.fetch_for_city = AsyncMock(return_value=(place, _sample_brief().weather))
    mocker.patch("mydash.cli.commands.brief.WeatherService", return_value=service)

    result = runner.invoke(app, ["weather", "--city", "Austin"])

    assert result.exit_code == 0, result.output
    assert "Austin, Texas, United States" in result.output


def test_weather_rejects_unknown_units(config_db):
    result = runner.invoke(app, ["weather", "--units", "kelvin"])

    assert result.exit_code != 0
    assert "metric" in result.output


def test_news_command_renders_headlines(config_db, mocker):
    service = MagicMock()
    service.fetch_news = AsyncMock(return_value=_sample_brief().headlines)
    mocker.patch("mydash.cli.commands.brief.NewsService", return_value=service)

    result = runner.invoke(app, ["news", "--limit", "3"])

    assert result.exit_code == 0, result.output
    assert "CLI smoke headline" in result.output
    assert service.fetch_news.await_args.kwargs["limit"] == 3


def test_stocks_command_renders_the_watch_list(config_db, mocker):
    brief = _sample_brief()
    service = MagicMock()
    service.fetch_stock_bars_and_quotes = AsyncMock(
        return_value=(brief.stock_quotes, brief.stock_bars)
    )
    mocker.patch("mydash.cli.commands.brief.StocksService", return_value=service)

    result = runner.invoke(app, ["stocks"])

    assert result.exit_code == 0, result.output
    assert "SPY" in result.output


def test_stocks_symbols_override_is_validated(config_db):
    result = runner.invoke(app, ["stocks", "--symbols", "not a ticker"])

    assert result.exit_code != 0


def test_stocks_with_an_empty_watch_list_explains_what_to_do(config_db, mocker):
    mocker.patch(
        "mydash.cli.context.UserConfigurationService",
        side_effect=lambda: _empty_watchlist_service(config_db),
    )

    result = runner.invoke(app, ["stocks"])

    assert result.exit_code == 0, result.output
    assert "set stocks add" in result.output


def _empty_watchlist_service(path: Path) -> UserConfigurationService:
    service = UserConfigurationService(db_path=path)
    service.set_stock_symbols([])
    return service


# --- config and cache ------------------------------------------------------


def test_config_show_renders_a_settings_table(config_db):
    result = runner.invoke(app, ["config", "show"])

    assert result.exit_code == 0, result.output
    assert "Miami" in result.output
    assert "Weather units" in result.output


def test_config_show_json(config_db):
    result = runner.invoke(app, ["config", "show", "--json"])

    assert result.exit_code == 0, result.output
    assert '"weather_units"' in result.output


def test_config_path_prints_the_database_location(config_db):
    result = runner.invoke(app, ["config", "path"])

    assert result.exit_code == 0, result.output
    assert "mydash.db" in result.output


def test_config_reset_restores_defaults(config_db):
    runner.invoke(app, ["set", "news", "category", "science"])

    result = runner.invoke(app, ["config", "reset", "--yes"])

    assert result.exit_code == 0, result.output
    assert UserConfigurationService(db_path=config_db).get_news_category() == "tech"


def test_config_reset_can_be_declined(config_db):
    runner.invoke(app, ["set", "news", "category", "science"])

    result = runner.invoke(app, ["config", "reset"], input="n\n")

    assert result.exit_code == 0, result.output
    assert UserConfigurationService(db_path=config_db).get_news_category() == "science"


def test_config_env_lists_where_credentials_come_from(config_db):
    result = runner.invoke(app, ["config", "env"])

    assert result.exit_code == 0, result.output
    assert ".env" in result.output
    assert "precedence" in result.output


def test_config_env_create_writes_a_template(config_db, monkeypatch, tmp_path):
    from mydash.env import user_env_path

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "env", "--create"])

    assert result.exit_code == 0, result.output
    assert user_env_path().is_file()
    assert "STOCK_ALPACA_API_KEY_ID" in user_env_path().read_text(encoding="utf-8")


def test_config_env_create_refuses_to_clobber(config_db, monkeypatch, tmp_path):
    from mydash.env import user_env_path

    monkeypatch.chdir(tmp_path)
    path = user_env_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("STOCK_ALPACA_API_KEY_ID=real-key\n", encoding="utf-8")

    result = runner.invoke(app, ["config", "env", "--create"])

    assert result.exit_code == 1
    assert "already exists" in result.output
    assert "real-key" in path.read_text(encoding="utf-8")


def test_doctor_reports_the_credentials_file(config_db, monkeypatch, tmp_path):
    from mydash.env import user_env_path

    monkeypatch.chdir(tmp_path)
    path = user_env_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "STOCK_ALPACA_API_KEY_ID=k\nSTOCK_ALPACA_API_SECRET_KEY=s\n", encoding="utf-8"
    )

    result = runner.invoke(app, ["doctor", "--offline"])

    assert result.exit_code == 0, result.output
    assert "Credentials file" in result.output


def test_cache_info_reports_an_empty_cache(config_db):
    result = runner.invoke(app, ["cache", "info"])

    assert result.exit_code == 0, result.output
    assert "Fresh entries" in result.output


def test_cache_clear_reports_nothing_to_do(config_db):
    result = runner.invoke(app, ["cache", "clear"])

    assert result.exit_code == 0, result.output
    assert "No cached entries" in result.output


# --- doctor ----------------------------------------------------------------


def test_doctor_offline_checks_local_state(config_db):
    result = runner.invoke(app, ["doctor", "--offline"])

    assert result.exit_code == 0, result.output
    assert "Database" in result.output
    assert "Preferences" in result.output
    assert "--offline" in result.output


def test_doctor_reports_a_failing_provider(config_db, mocker):
    async def boom(*_args, **_kwargs):
        raise RuntimeError("provider unreachable")

    mocker.patch("mydash.cli.commands.doctor._describe_weather", side_effect=boom)
    mocker.patch("mydash.cli.commands.doctor._describe_news", side_effect=boom)
    mocker.patch("mydash.cli.commands.doctor._describe_geocoding", side_effect=boom)
    mocker.patch("mydash.cli.commands.doctor._describe_stocks", side_effect=boom)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "provider unreachable" in result.output


# --- init ------------------------------------------------------------------


def test_init_non_interactive_sets_preferences(config_db):
    result = runner.invoke(
        app,
        ["init", "--units", "imperial", "--category", "science", "-s", "tsla,nvda"],
    )

    assert result.exit_code == 0, result.output
    saved = UserConfigurationService(db_path=config_db)
    assert saved.get_weather_forecast_units() == "imperial"
    assert saved.get_news_category() == "science"
    assert saved.get_stock_symbols() == ["TSLA", "NVDA"]


def test_init_rejects_a_bad_ticker(config_db):
    result = runner.invoke(app, ["init", "-s", "not a ticker"])

    assert result.exit_code != 0
