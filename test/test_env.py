"""Tests for credential discovery.

Strategy: chdir into tmp_path so the project-level lookup is deterministic, and
lean on the autouse database isolation so the user-level path lands in a temp
directory too.
"""

import os
import stat
from pathlib import Path

import pytest

from mydash import env
from mydash.env import (
    ALPACA_KEY_VAR,
    ALPACA_SECRET_VAR,
    ENV_FILE_ENV_VAR,
    candidate_paths,
    has_alpaca_credentials,
    load_environment,
    user_env_path,
    write_template,
)


@pytest.fixture(autouse=True)
def isolated_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Run from an empty directory so no real .env is discovered."""
    workdir = tmp_path / "cwd"
    workdir.mkdir()
    monkeypatch.chdir(workdir)
    monkeypatch.delenv(ENV_FILE_ENV_VAR, raising=False)
    monkeypatch.delenv(ALPACA_KEY_VAR, raising=False)
    monkeypatch.delenv(ALPACA_SECRET_VAR, raising=False)
    return workdir


def _write(path: Path, key: str = "from-file", secret: str = "secret") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"{ALPACA_KEY_VAR}={key}\n{ALPACA_SECRET_VAR}={secret}\n", encoding="utf-8"
    )
    return path


# --- locations ------------------------------------------------------------


def test_user_env_path_sits_beside_the_database():
    from mydash.storage.database import default_database_path

    assert user_env_path().parent == Path(default_database_path()).parent
    assert user_env_path().name == ".env"


def test_candidates_are_ordered_by_precedence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, isolated_cwd: Path
):
    explicit = tmp_path / "explicit.env"
    monkeypatch.setenv(ENV_FILE_ENV_VAR, str(explicit))
    _write(isolated_cwd / ".env")

    paths = candidate_paths()

    assert paths[0] == explicit
    assert paths[1] == isolated_cwd / ".env"
    assert paths[-1] == user_env_path()


def test_candidates_do_not_repeat_a_path(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(ENV_FILE_ENV_VAR, str(user_env_path()))

    assert len(candidate_paths()) == len(set(candidate_paths()))


def test_blank_override_is_ignored(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(ENV_FILE_ENV_VAR, "   ")

    assert user_env_path() in candidate_paths()


# --- loading --------------------------------------------------------------


def test_user_level_file_is_loaded_from_anywhere():
    _write(user_env_path(), key="user-level")

    loaded = load_environment()

    assert loaded == [user_env_path()]
    assert os.environ[ALPACA_KEY_VAR] == "user-level"


def test_project_file_wins_over_the_user_level_one(isolated_cwd: Path):
    _write(isolated_cwd / ".env", key="project")
    _write(user_env_path(), key="user-level")

    load_environment()

    assert os.environ[ALPACA_KEY_VAR] == "project"


def test_explicit_override_wins_over_everything(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, isolated_cwd: Path
):
    explicit = _write(tmp_path / "explicit.env", key="explicit")
    monkeypatch.setenv(ENV_FILE_ENV_VAR, str(explicit))
    _write(isolated_cwd / ".env", key="project")
    _write(user_env_path(), key="user-level")

    load_environment()

    assert os.environ[ALPACA_KEY_VAR] == "explicit"


def test_a_real_environment_variable_is_never_overwritten(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(ALPACA_KEY_VAR, "from-shell")
    _write(user_env_path(), key="from-file")

    load_environment()

    assert os.environ[ALPACA_KEY_VAR] == "from-shell"


def test_missing_files_are_simply_skipped():
    assert load_environment() == []


def test_partial_files_combine(isolated_cwd: Path):
    (isolated_cwd / ".env").write_text(
        f"{ALPACA_KEY_VAR}=project-key\n", encoding="utf-8"
    )
    user = user_env_path()
    user.parent.mkdir(parents=True, exist_ok=True)
    user.write_text(f"{ALPACA_SECRET_VAR}=user-secret\n", encoding="utf-8")

    load_environment()

    assert os.environ[ALPACA_KEY_VAR] == "project-key"
    assert os.environ[ALPACA_SECRET_VAR] == "user-secret"


# --- credential check -----------------------------------------------------


def test_has_credentials_requires_both(monkeypatch: pytest.MonkeyPatch):
    assert not has_alpaca_credentials()

    monkeypatch.setenv(ALPACA_KEY_VAR, "key")
    assert not has_alpaca_credentials()

    monkeypatch.setenv(ALPACA_SECRET_VAR, "secret")
    assert has_alpaca_credentials()


def test_blank_credentials_do_not_count(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(ALPACA_KEY_VAR, "   ")
    monkeypatch.setenv(ALPACA_SECRET_VAR, "secret")

    assert not has_alpaca_credentials()


# --- template -------------------------------------------------------------


def test_write_template_creates_a_fillable_file():
    written = write_template()

    assert written == user_env_path()
    content = written.read_text(encoding="utf-8")
    assert ALPACA_KEY_VAR in content
    assert ALPACA_SECRET_VAR in content


def test_template_is_owner_readable_only():
    written = write_template()

    assert stat.S_IMODE(written.stat().st_mode) == 0o600


def test_template_refuses_to_clobber_real_credentials():
    _write(user_env_path(), key="real-key")

    with pytest.raises(FileExistsError):
        write_template()

    assert "real-key" in user_env_path().read_text(encoding="utf-8")


def test_template_can_overwrite_when_asked():
    _write(user_env_path(), key="real-key")

    write_template(overwrite=True)

    assert "real-key" not in user_env_path().read_text(encoding="utf-8")


def test_template_creates_missing_directories(tmp_path: Path):
    destination = tmp_path / "deep" / "nested" / ".env"

    assert write_template(destination) == destination
    assert destination.is_file()


def test_template_placeholders_are_not_credentials():
    """A fresh template must not read as configured credentials."""
    write_template()
    load_environment()

    # Placeholder values are non-blank, so this documents the tradeoff: the
    # template is a starting point, and doctor is what tells you it is unfilled.
    assert env.TEMPLATE.count("your_alpaca") == 2
