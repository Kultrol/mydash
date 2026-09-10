# Contributing to mydash

Thanks for taking a look. This file covers how a change gets from your machine
into `main`.

## The short version

`main` is protected. Every change — including mine — goes through a pull
request, and a pull request cannot merge until CI is green.

```bash
git switch -c service/some-change
# ... work ...
uv run pytest && uv run ruff check src test
git push -u origin service/some-change
gh pr create
```

Then wait for the checks and squash-merge.

## Branch naming

The history uses a domain prefix, and following it keeps the branch list
readable:

| Prefix | For |
| --- | --- |
| `service/` | a service or client layer change |
| `cli/` | commands, renderers, terminal output |
| `test/` | test-only work |
| `refactor/` | restructuring without behaviour change |
| `docs/` | documentation |
| `experimental/` | spikes that may never merge |

## Before you push

```bash
uv sync --group dev
uv run pytest
uv run ruff check src test
```

The suite is fast — a few hundred tests in a couple of seconds — and needs no
network, no database server, and no API keys. An autouse fixture pins
`MYDASH_DB_PATH` to a temp file and credential discovery follows it, so a test
run can never read or rewrite your own configuration.

If you touched the `Dockerfile` or anything it copies, build it too:

```bash
docker build -t mydash:local . && docker run --rm mydash:local doctor --offline
```

## What CI checks

Every pull request runs:

- **test** — the suite on Linux and macOS across Python 3.12, 3.13, and 3.14
- **lint** — `ruff check src test`
- **oldest supported dependencies** — resolves to the lowest versions the `>=`
  floors in `pyproject.toml` allow, so the floors are tested rather than assumed
- **build artifacts** — builds the wheel and sdist, installs the wheel, and runs
  it from a neutral directory
- **docker image** — builds the image and runs the CLI inside it
- **all checks passed** — the single check branch protection requires; it
  depends on all of the above

Only `all checks passed` is required by the protection rule. That is
deliberate: requiring the six matrix legs by name would silently break the rule
every time the matrix changes.

## Merging

Squash-merge is the only option, and the branch is deleted afterwards. Write the
squash commit message as prose describing what changed and why — that is the
style the existing history uses, not Conventional Commits.

## Changelog

If a change is user-visible, add a line under `## [Unreleased]` in
[CHANGELOG.md](CHANGELOG.md). The release workflow parses that file's `## [x.y.z]`
headings to build release notes, so the heading format is load-bearing.

## Releasing

Releases are cut from a tag, and the tag has to agree with the code:

1. Bump `__version__` in `src/mydash/__init__.py` — it is the single source of
   truth, and `pyproject.toml` reads it via hatchling. Nowhere else.
2. Move the `## [Unreleased]` entries under a new `## [x.y.z]` heading.
3. Tag and push:

   ```bash
   git tag vX.Y.Z && git push origin vX.Y.Z
   ```

`release.yml` verifies the tag matches the packaged version, builds the wheel
and sdist, extracts the changelog section, and creates the GitHub release. It
fails loudly if the tag and the version disagree.

## Reporting a security issue

Please don't open a public issue — see [SECURITY.md](SECURITY.md).
