# Deployment: Vercel frontend + separately hosted backend

Vercel hosts the static frontend. The backend (FastAPI with a database, Alembic migrations and model
calls that can take up to a minute) is a long-running Python service and is hosted separately; Vercel's
serverless functions are not a fit for it (no persistent SQLite, short execution limits). The hackathon
also requires the project to run on Nebius, so the backend targets a Nebius-hosted container.

## 1. Frontend on Vercel (production branch `main`)

Vercel project settings:

| Setting | Value |
|---|---|
| Git repository | `basaaria123/Mindmate` |
| Production branch | `main` |
| Root Directory | `mindmate-frontend` |
| Framework preset | Vite |
| Build command | `npm run build` |
| Output directory | `dist` |
| Install command | `npm ci` |
| Node version | 22 (project default) |

`mindmate-frontend/vercel.json` adds the SPA rewrite so `react-router` routes such as `/memory` load
`index.html`.

Environment variables (Project → Settings → Environment Variables):

| Name | Production | Preview |
|---|---|---|
| `VITE_API_BASE_URL` | `https://<backend-host>` (no trailing slash) | staging backend URL, or empty to use frontend mocks |

`VITE_*` variables are baked in at build time; redeploy after changing them. Preview deployments are
created automatically for pull requests and for pushes to `mindmate-frontend`, `mindmate-backend` and
`mindmate-ai` if those branches are enabled under Git → Preview branches.

## 2. Backend (FastAPI + AI agents) as a container

Build from the repository root with the provided `Dockerfile`; it runs `alembic upgrade head` and then
`uvicorn` on `$PORT`.

Recommended host: a Nebius AI Cloud VM or container service (meets the hackathon requirement). Any
Docker host works the same way (Render, Railway, Fly.io). Steps for a Docker host:

1. Create a PostgreSQL database (managed Postgres on Nebius, or Neon/Supabase/Render Postgres).
2. Create the service from the repo, Dockerfile path `Dockerfile`, port `8000`.
3. Set the environment variables below.
4. After the first deploy run `python scripts/reset_demo.py` once (or call `POST /admin/reset-demo`
   with the admin token) to seed the demo persona.

| Variable | Production value |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg://USER:PASSWORD@HOST:5432/DB` |
| `NEBIUS_API_KEY` | Token Factory key (secret) |
| `MINDMATE_AUTO_CREATE_SCHEMA` | `false` (Alembic owns the schema) |
| `MINDMATE_AUTO_SEED` | `false` |
| `MINDMATE_LLM_MODE` | `live` (`off` for a cached/deterministic demo fallback) |
| `CORS_ORIGINS` | `https://<vercel-domain>,https://<custom-domain>` |
| `RATE_LIMIT_PER_MINUTE` | `120` |
| `MINDMATE_ADMIN_TOKEN` | long random string |
| `PORT` | `8000` (or the host's injected port) |

Health check path: `/health`. Readiness and configuration: `/admin/status`.

## 3. Connect the two

1. Deploy the backend, note its public URL, confirm `https://<backend>/health` returns `{"status":"healthy"}`.
2. Set `VITE_API_BASE_URL` in Vercel to that URL and redeploy the frontend.
3. Set `CORS_ORIGINS` on the backend to the Vercel production domain (and preview domains if needed).

## 4. Verification checklist (run against production)

```bash
B=https://<backend>; F=https://<frontend>
curl -s $B/health
curl -s $B/admin/status | python -m json.tool | head -20
curl -s -H "Origin: $F" -I $B/profile | grep -i access-control-allow-origin      # CORS
curl -s -X POST $B/practice/evaluate -H 'Content-Type: application/json' -d '{"answer":"Accuracy only.","topic":"Model evaluation"}'
curl -s -X POST $B/plans/replan -H 'Content-Type: application/json' -d '{"available_minutes":30}' | head -c 400
curl -s -X POST $B/profile -H 'Content-Type: application/json' -d '{"user_message":"Second-year CS student, one hour a day, knows Python"}'   # Nemotron path
```

Then in the browser: Onboarding (AI profile extraction), Scanner (opportunity + fit via Nemotron),
Sim (practice), Memory (save weakness), Pipeline (Update my plan shows the cited rationale), Trace.

The application is only "deployed" when the last three steps work end to end on the hosted URLs.

## 5. Status

As of this commit: no Vercel project or backend host has been configured from this environment (no
Vercel/Nebius credentials available here). The configuration above is ready to apply; production
verification is pending and must be done by the person with Vercel and hosting access.
