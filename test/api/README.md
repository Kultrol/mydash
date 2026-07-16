# API tests

The FastAPI app lives in package **`mydash-web`**
(`packages/mydash-web/src/mydash/api/`). Prefer tests that import
`mydash.api.main:app` and mock `BriefService` so providers are not hit.

## Health

```python
from fastapi.testclient import TestClient

from mydash.api.main import app


def test_health_ok():
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

With the monorepo workspace: `uv sync --group dev` (includes `mydash-web`).

## Brief route tests

Mock `BriefService.build` so tests do not hit Open-Meteo / Noozra / Alpaca.
See `packages/mydash-web/src/mydash/api/routers/brief.py`.

## Config route tests

Config HTTP is deferred. When added, pass a temp `config_path` via
FastAPI `dependency_overrides` on a config-service dependency.
