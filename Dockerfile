# syntax=docker/dockerfile:1

# mydash in a container: no Python toolchain required on the host.
#
#   docker build -t mydash .
#   docker run --rm -it -v mydash-data:/data mydash brief
#
# The image is built from uv.lock, so it runs the same dependency versions CI
# resolves rather than a fresh float of the >= floors in pyproject.toml.

# ---------------------------------------------------------------- builder ---
FROM ghcr.io/astral-sh/uv:0.9.30-python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies first, without the project itself: this layer is cached until
# the lockfile actually moves, so editing src/ does not re-resolve the world.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-dev --no-install-project

# README.md is not documentation here: pyproject.toml declares it as the
# readme, and hatchling reads it while building the wheel.
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
# --no-editable is required, not a preference: uv installs the project in
# editable mode by default, which leaves a .pth pointing at /app/src. Only
# the venv is copied into the runtime stage, so an editable install would
# import nothing there.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# ---------------------------------------------------------------- runtime ---
FROM python:3.14-slim-bookworm AS runtime

# Pointing the database at /data puts the credentials file there too:
# env.user_env_path() returns the directory holding the database. One mount
# therefore covers every piece of state mydash keeps.
#
# LANG matters more than it looks — the panels are full of box-drawing
# characters and emoji, and Rich mangles them under the default POSIX locale.
ENV PATH="/app/.venv/bin:$PATH" \
    MYDASH_DB_PATH=/data/mydash.db \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C.UTF-8 \
    TERM=xterm-256color

RUN useradd --create-home --uid 10001 mydash \
 && install -d -o mydash -g mydash /data

COPY --from=builder --chown=mydash:mydash /app/.venv /app/.venv

USER mydash
WORKDIR /data

# Deliberately no VOLUME: this is a CLI people run dozens of times a day with
# --rm, and VOLUME would orphan an anonymous volume on every one of them.
# Persist state by asking for it: -v mydash-data:/data

ENTRYPOINT ["mydash"]
CMD ["brief"]
