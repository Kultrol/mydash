# mydash frontend

Next.js (App Router) + TypeScript + Tailwind + [shadcn/ui](https://ui.shadcn.com/) UI for the mydash daily brief.

The Python API is package **`mydash-web`** (`../packages/mydash-web/src/mydash/api/`). This app does **not** call external data providers directly.

## Local development

```bash
# from repo root
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Run the API in another terminal (from monorepo root):

```bash
uv run uvicorn mydash.api.main:app --reload --port 8000
```

| Script | Purpose |
|--------|---------|
| `npm run dev` | Dev server (Turbopack) |
| `npm run build` | Production build (Vercel runs this) |
| `npm run start` | Serve production build locally |
| `npm run lint` | ESLint |

## Project map

```
app/                    # routes (App Router)
  layout.tsx
  page.tsx              # daily brief dashboard
components/
  ui/                   # shadcn primitives (button, card, …)
  dashboard/            # brief panels (headlines, markets, weather)
lib/
  utils.ts              # cn() helper
  api.ts                # FastAPI client + domain types
  format.ts             # display helpers for brief panels
```

## Vercel deploy

1. Import this GitHub repo in [Vercel](https://vercel.com/).
2. Set **Root Directory** to `frontend` (not the monorepo root).
3. Framework: Next.js (auto-detected).
4. Set `NEXT_PUBLIC_API_BASE_URL` to your hosted API origin and allow that origin in API CORS.
