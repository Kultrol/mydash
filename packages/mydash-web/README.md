# mydash-web

FastAPI backend for the mydash web dashboard.

```bash
pip install mydash-web
uvicorn mydash.api.main:app --reload --port 8000
```

Pair with the Next.js app in `frontend/` of the monorepo. Depends on `mydash-core`.
