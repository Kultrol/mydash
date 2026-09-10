## What changed

<!-- The change in a sentence or two. -->

## Why

<!-- The problem this solves. Link an issue if there is one. -->

## Checks

- [ ] `uv run pytest` passes locally
- [ ] `uv run ruff check src test` is clean
- [ ] `CHANGELOG.md` has an entry under `## [Unreleased]`, or this change is not user-visible

<!-- CI runs the full matrix, the lint, the oldest-dependencies leg, the build,
     and the Docker image build. `all checks passed` has to be green to merge. -->
