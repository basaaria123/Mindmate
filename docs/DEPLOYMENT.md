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
| `MINDMATE_DEMO_CACHE` | `fallback` for the live demo (recorded answers only when Nebius fails); `replay` if the network is unreliable |
| `CORS_ORIGINS` | `https://<vercel-domain>,https://<custom-domain>` |
| `RATE_LIMIT_PER_MINUTE` | `120` |
| `MINDMATE_ADMIN_TOKEN` | long random string |
| `PORT` | `8000` (or the host's injected port) |

Liveness path: `/health`. Readiness path (checks the database, returns 503 when it is down): `/health/ready`.
Configuration and row counts: `/admin/status`.

## 2b. Everything on one Nebius VM (alternative to Vercel)

`docker-compose.prod.yml` runs PostgreSQL, the backend and the frontend (built into an nginx image by
`mindmate-frontend/Dockerfile`) on one VM, for example a Nebius AI Cloud VM:

```bash
git clone https://github.com/basaaria123/Mindmate.git && cd Mindmate
cp .env.production.example .env.production        # set passwords, NEBIUS_API_KEY, PUBLIC_API_URL, CORS_ORIGINS
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
docker compose -f docker-compose.prod.yml exec backend python scripts/reset_demo.py --seed-only
python scripts/smoke_test.py --backend http://<vm>:8000 --frontend http://<vm>
```

The backend container applies migrations on start. The frontend image serves the app on port 80 with
client-side routes, long-lived caching for hashed assets and a `/healthz` endpoint
(`mindmate-frontend/nginx.conf`). `PUBLIC_API_URL` is baked into the frontend at build time; rebuild the
frontend after changing it.

## 3. Connect the two

1. Deploy the backend, note its public URL, confirm `https://<backend>/health` returns `{"status":"healthy"}`.
2. Set `VITE_API_BASE_URL` in Vercel to that URL and redeploy the frontend.
3. Set `CORS_ORIGINS` on the backend to the Vercel production domain (and preview domains if needed).

## 4. Verification checklist (run against production)

Non-destructive smoke test (health, readiness, Nemotron configured, read-only endpoints, CORS, frontend routes):

```bash
python scripts/smoke_test.py --backend https://<backend> --frontend https://<frontend>
```

Manual checks:

```bash
B=https://<backend>; F=https://<frontend>
curl -s $B/health
curl -s $B/admin/status | python -m json.tool | head -20
curl -s -H "Origin: $F" -I $B/profile | grep -i access-control-allow-origin      # CORS
curl -s -X POST $B/practice/evaluate -H 'Content-Type: application/json' -d '{"answer":"Accuracy only.","topic":"Model evaluation"}'
curl -s -X POST $B/plans/replan -H 'Content-Type: application/json' -d '{"available_minutes":30}' | head -c 400
curl -s -X POST $B/profile -H 'Content-Type: application/json' -d '{"user_message":"Second-year CS student, one hour a day, knows Python"}'   # Nemotron path
```

Or run the whole scripted path with its checks: `python scripts/demo_check.py --base-url $B --admin-token <token>`.

Then in the browser: Onboarding (AI profile extraction), Scanner (opportunity + fit via Nemotron),
Sim (practice), Memory (save weakness), Pipeline (Update my plan shows the cited rationale), Trace.

The application is only "deployed" when the last three steps work end to end on the hosted URLs.

## 5. Status

| Item | State |
|---|---|
| Backend container (`Dockerfile`) | Written; its start command (migrate, then serve) verified by running it directly. The image itself has not been built here (no Docker daemon in the development environment). |
| Frontend container (`mindmate-frontend/Dockerfile`, `nginx.conf`) | nginx config verified with `nginx -t` and by serving the production build: routes, 404s for missing assets, cache headers, `/healthz`. Image not built here. |
| `docker-compose.prod.yml` | Written and syntax-checked; not run (no Docker daemon). |
| Vercel project | Not created: needs the repository owner's Vercel account. Settings above. |
| Nebius VM or container | Not created: needs the team's Nebius account. |
| `scripts/smoke_test.py` | Verified locally against the backend and the nginx-served frontend: 11 of 12 checks pass; the one failure is "Nemotron configured", correct because no key exists locally. |
| Backup screen recording | Captured from the integrated app running locally (no narration); kept outside the repository. |

The application is deployed only when the smoke test and `scripts/demo_check.py` pass against the hosted
URLs and the browser walkthrough above works.
