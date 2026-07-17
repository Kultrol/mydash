# Reviewing and extending the mydash monorepo

Working checklist for the current package layout (July 2026).  
Product overview and install: [README.md](../README.md).  
System shape and layer rules: [ARCHITECTURE.md](ARCHITECTURE.md).

This is not a public product README. Use it when reviewing a checkout, onboarding, or adding features without breaking boundaries.

---

## 1. Purpose

After the monorepo split you should be able to:

1. **Review** that workspace wiring, imports, layers, smoke paths, and docs still match reality.
2. **Extend** providers, domains, CLI commands, API routes, or UI panels in the right package.

---

## 2. Mental model (quick)

**Two products, one shared core.** Presentation never owns providers; core never imports Typer, Rich, FastAPI, or React.

| Product | Install | Stack (outer → inner) |
|---------|---------|------------------------|
| **CLI** | `mydash` | Rich → Typer → `mydash.core` |
| **Web** | `mydash-web` + `frontend/` | Next.js → FastAPI → `mydash.core` |

| Distribution | Monorepo path | Import roots |
|--------------|---------------|--------------|
| **`mydash-core`** | `packages/mydash-core/` | `mydash.core` |
| **`mydash`** (CLI) | `packages/mydash-cli/` | `mydash.cli` |
| **`mydash-web`** | `packages/mydash-web/` | `mydash.api` |
| **Frontend** (npm) | `frontend/` | Next.js app; HTTP only to the API |

**Namespace package:** `mydash` is a PEP 420 namespace. Each distribution contributes one portion (`core/`, `cli/`, `api/`) and **none** ships a root `mydash/__init__.py`, so runtime and Pyright can merge all three `packages/*/src` trees.

Root `pyproject.toml` is a **uv workspace** (`mydash-workspace`, `package = false`) that depends on the product packages for local dev.

---

## 3. Layout map

```
packages/
  mydash-core/                 # PyPI: mydash-core
    pyproject.toml
    src/mydash/core/           # PEP 420 portion (no mydash/__init__.py)
      services/                # BriefService, domain services, UserConfigurationService
      models/
      client/                  # factories + providers
  mydash-cli/                  # PyPI: mydash
    pyproject.toml
    src/mydash/cli/
      main.py                  # load_dotenv, Typer app
      commands/set/            # mydash set …
      renderers/               # Rich panels
  mydash-web/                  # PyPI: mydash-web
    pyproject.toml
    src/mydash/api/
      main.py                  # FastAPI app, CORS, routers
      routers/                 # health, brief; config scaffold deferred

frontend/                      # Next.js → HTTP → mydash-web
test/
  core/                        # client + services
  cli/
  api/                         # guidance / future route tests
pyproject.toml                 # uv workspace root
pyrightconfig.json             # extraPaths for the three src trees
uv.lock
```

---

## 4. Review checklist

Work top-down. Check a box only when you have evidence (command output or file read).

### Workspace and install

- [ ] `uv sync --group dev` at repo root succeeds.
- [ ] Root `[tool.uv.workspace].members` lists `packages/mydash-core`, `packages/mydash-cli`, `packages/mydash-web`.
- [ ] `[tool.uv.sources]` pins `mydash-core`, `mydash`, and `mydash-web` to `{ workspace = true }`.
- [ ] Each package has its own `pyproject.toml` + hatchling wheel config (`packages = ["src/mydash"]`).
- [ ] Console script: `mydash` → `mydash.cli.main:app` (CLI package).
- [ ] API entry: `uvicorn mydash.api.main:app` (web package).

### Imports and layers

- [ ] Domain imports are `mydash.core.*` (not legacy `mydash.client`, `mydash.services`, `mydash.models` at the old top level).
- [ ] CLI imports stay under `mydash.cli.*` and call services, not provider modules directly.
- [ ] API routers call services / Pydantic DTOs; no provider HTTP in `api/`.
- [ ] Frontend uses `frontend/lib/api.ts` only — no direct Open-Meteo / Noozra / Alpaca calls.
- [ ] Core has **no** imports of Typer, Rich, FastAPI, Next, or React.

### Smoke paths

- [ ] **CLI:** with venv active / `uv run`, `mydash brief` and `mydash set show` work (Alpaca optional for markets).
- [ ] **API:** `uv run uvicorn mydash.api.main:app --reload --port 8000`
  - [ ] `GET /api/v1/health` → OK
  - [ ] `GET /api/v1/brief` → JSON `DailyBrief`
  - [ ] OpenAPI at `http://localhost:8000/docs`
- [ ] **Frontend:** `cd frontend && cp .env.local.example .env.local && npm install && npm run dev`
  - [ ] `NEXT_PUBLIC_API_BASE_URL` points at the API (default `http://localhost:8000`)
  - [ ] Dashboard loads brief panels (or shows a clear error if API is down)

### Tests and tooling

- [ ] `uv run pytest` — clients, services, CLI smoke.
- [ ] Pytest `addopts` includes `--import-mode=importlib` (provider test modules share names).
- [ ] `test/api/` — today mostly guidance in `test/api/README.md`; route tests may still be thin or absent.
- [ ] `pyrightconfig.json` `extraPaths` includes all three `packages/*/src` trees.
- [ ] Frontend: `cd frontend && npm run build` (and `npm run lint` when touching UI).

### Secrets and docs

- [ ] `.env` exists locally from `.env.example` when testing markets; **never committed**.
- [ ] `frontend/.env.local` is gitignored.
- [ ] [README.md](../README.md), [ARCHITECTURE.md](ARCHITECTURE.md), and [CHANGELOG.md](../CHANGELOG.md) Unreleased section match the package split and web stack.
- [ ] Package one-liners under `packages/*/README.md` still accurate.

---

## 5. Known gaps / deferred work

Track these so reviews do not treat them as regressions.

| Area | Status | Notes |
|------|--------|--------|
| Config HTTP | Deferred | `packages/mydash-web/.../api/routers/config.py` is a scaffold; not mounted in `main.py` |
| API DI for config | Deferred | Prefer FastAPI `Depends` + temp `config_path` in tests when wiring config |
| API tests | Thin | Follow `test/api/README.md`; mock `BriefService` |
| Frontend settings UI | Deferred | Settings called out as deferred on the dashboard page |
| Production CORS | Deferred | Local origins only; add concrete Vercel origin later (no `*.vercel.app` wildcard) |
| Caching | Deferred | No shared cache layer yet |
| CLI single-run pref overrides | Deferred | Path to 1.0 in README |
| Stale scaffold comments | Cleanup | Some API modules still say “scaffold / implement me” while health/brief already work — tidy when you touch those files |

**Still intentional:** weather/news without keys; stocks need Alpaca env vars; Vercel hosts **only** `frontend/` (API is a separate process).

---

## 6. How to extend

Keep new code on the correct side of the boundary. Prefer copying an existing domain (weather or news) over inventing a new pattern.

### New provider (same domain)

Example: second weather backend.

1. Implement under `packages/mydash-core/src/mydash/core/client/<domain>/providers/<name>/`.
2. Satisfy the domain protocol / base client in `base.py`.
3. Register in `factory.py` (`get_*_client`).
4. Extend models only if the DTO surface must change.
5. Tests under `test/core/client/<domain>/` — mock HTTP at `httpx` / request layer.
6. Optional: expose provider name via `UserConfig` + `mydash set` if users should choose it.

### New domain (e.g. calendar)

1. **Models** — `core/models/<domain>.py` (Pydantic).
2. **Client** — protocol, errors, factory, first provider under `core/client/<domain>/`.
3. **Service** — `core/services/<domain>.py` (orchestration, no Rich/FastAPI).
4. **Compose** — call from `BriefService` and/or a dedicated service used by CLI/API.
5. **CLI** — Typer command or brief renderer panel in `packages/mydash-cli/`.
6. **API** — router in `packages/mydash-web/.../routers/`, `include_router` in `main.py`.
7. **Frontend** — types + fetch in `lib/api.ts`, panel under `components/dashboard/`, wire `app/page.tsx`.
8. **Tests** — `test/core/client/…`, `test/core/services/…`, CLI/API as needed.
9. **CHANGELOG** — Unreleased bullet.

### New CLI command

1. Add Typer command under `packages/mydash-cli/src/mydash/cli/` (or `commands/`).
2. Call **core services** only; put Rich layout in `renderers/` or set helpers.
3. Cover with smoke tests in `test/cli/` (mock services).

### New API route

1. Add router module under `packages/mydash-web/src/mydash/api/routers/`.
2. Return / accept Pydantic models from `mydash.core` (or thin API schemas if you must).
3. Register with prefix `/api/v1` in `main.py`.
4. Tests: `TestClient` + mock services / `dependency_overrides` (see `test/api/README.md`).
5. Mirror types and fetch helpers in `frontend/lib/api.ts` if the UI needs them.

### Frontend panel

1. Confirm the API returns stable JSON (OpenAPI `/docs`).
2. Types + `fetch` helpers in `lib/api.ts` (mirror core field names).
3. UI under `components/dashboard/`; reuse `components/ui/` (shadcn).
4. Compose in `app/page.tsx` (loading / error states).
5. `npm run build` before considering it done.

### New installable Python package

1. Create `packages/mydash-<name>/` with hatchling + `src/mydash/<subpackage>/`.
2. Add workspace member + `[tool.uv.sources]` entry in root `pyproject.toml`.
3. If it shares the `mydash` namespace, ship only a subpackage portion (e.g. `src/mydash/<name>/`) — **no** root `mydash/__init__.py` (PEP 420).
4. `uv lock` / `uv sync`, update `pyrightconfig.json` `extraPaths`, document in README + ARCHITECTURE.

---

## 7. Dev loops

```bash
# Install (repo root)
uv sync --group dev

# CLI
uv run mydash brief
uv run mydash set show

# API
uv run uvicorn mydash.api.main:app --reload --port 8000

# Frontend (second terminal)
cd frontend
cp -n .env.local.example .env.local   # if needed
npm install
npm run dev

# Tests
uv run pytest
cd frontend && npm run build
```

**When to update CHANGELOG Unreleased:** user-visible behavior, new packages/commands/routes, or layout changes reviewers must know about. Skip pure typo churn.

**IDE:** open the monorepo root so `pyrightconfig.json` extra paths resolve all three packages.

---

## 8. Links

| Doc | Role |
|-----|------|
| [README.md](../README.md) | Product, install, usage, web dev |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Layers, packages, providers, tests map |
| [CHANGELOG.md](../CHANGELOG.md) | Released + Unreleased history |
| [packages/mydash-core/README.md](../packages/mydash-core/README.md) | Core one-liner |
| [packages/mydash-cli/README.md](../packages/mydash-cli/README.md) | CLI package |
| [packages/mydash-web/README.md](../packages/mydash-web/README.md) | API package |
| [frontend/README.md](../frontend/README.md) | Next.js app, Vercel root |
| [test/api/README.md](../test/api/README.md) | How to test FastAPI routes |

---

*Companion to ARCHITECTURE.md · monorepo review guide*
