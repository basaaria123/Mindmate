# Deployment

## Current production (Render + Vercel)

| Part | Where |
|---|---|
| Frontend | Vercel: https://mindmate-lyart.vercel.app |
| Backend | Render Docker web service: https://mindmate-backend-yw5d.onrender.com (built from the repository `Dockerfile`) |
| Database | Render PostgreSQL, connected through `DATABASE_URL` (the Internal Database URL) |
| Models | NVIDIA Nemotron on Nebius Token Factory (`NEBIUS_API_KEY` on the Render service) |

Render service environment (Settings → Environment): `DATABASE_URL`, `NEBIUS_API_KEY`,
`MINDMATE_LLM_MODE=live`, `MINDMATE_DEMO_CACHE=off`, `MINDMATE_AUTO_CREATE_SCHEMA=false`,
`MINDMATE_AUTO_SEED=true`, `MINDMATE_ADMIN_TOKEN`, `CORS_ORIGINS=https://mindmate-lyart.vercel.app`,
`RATE_LIMIT_PER_MINUTE=120`. Vercel: `VITE_API_BASE_URL=https://mindmate-backend-yw5d.onrender.com`, then redeploy. Verify with
`./scripts/smoke_test.sh https://mindmate-backend-yw5d.onrender.com`. Render's step-by-step setup is section 2 below; the Nebius VM setup in
section 1 is an alternative that is not in use.

---

## Alternative: backend on a Nebius VM, frontend on Vercel

The frontend is a static Vite build on Vercel (`https://mindmate-lyart.vercel.app`). The backend
(FastAPI, PostgreSQL, Alembic migrations, Nemotron calls that can take tens of seconds) is a
long-running container. Deploy it on a Nebius AI Cloud VM with `docker-compose.prod.yml`, which runs
PostgreSQL, the backend and Caddy for automatic HTTPS. The Vercel site is served over HTTPS, so the
backend must be HTTPS too: browsers block calls from an HTTPS page to an `http://` API.

```
Browser ── https ──> Vercel (static React app)
   │
   └──── https ──> Caddy :443 ──> backend :8000 ──> PostgreSQL        (one Nebius VM, docker compose)
                                     │
                                     └── https ──> Nebius Token Factory (NVIDIA Nemotron Ultra / Nano)
```

## YOU DO THIS (needs your accounts or credentials)

- [ ] **Nebius Token Factory API key.** Create it in the Token Factory console and check that both
      model IDs below are listed for your account. **[CONFIRM]** the exact IDs match what the
      console shows; override them with the env variables if they differ.
      - `nvidia/Nemotron-3-Ultra-550b-a55b` (`MINDMATE_REASONING_MODEL`)
      - `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` (`MINDMATE_FAST_MODEL`)
- [ ] **A Nebius AI Cloud VM** (Ubuntu 22.04 or 24.04, 2 vCPU / 4 GB RAM is enough; no GPU needed,
      the models run on Token Factory). Give it a public IP and allow inbound TCP 22, 80 and 443.
      **[CONFIRM]** the console labels (Compute → Virtual machines, security group or firewall rules).
- [ ] **A domain or subdomain** for the API, e.g. `api.yourdomain.com`, with a DNS **A record** pointing
      to the VM's public IP. No domain? Use `<VM-IP>.sslip.io` (for example `203.0.113.7.sslip.io`),
      which resolves to that IP and works with Caddy's certificates.
- [ ] **Secrets** for `.env.production`: a long random `POSTGRES_PASSWORD` and `MINDMATE_ADMIN_TOKEN`
      (generate each with `openssl rand -hex 24`). Never commit this file.
- [ ] **Vercel**: set `VITE_API_BASE_URL` and redeploy (section 3).

## 1. Deploy the backend on a Nebius VM

Run on the VM (SSH in as the default user):

```bash
# 1. Docker Engine + compose plugin (official convenience script), then use docker without sudo
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER" && newgrp docker
docker compose version                      # must print v2.x

# 2. Code
git clone https://github.com/basaaria123/Mindmate.git && cd Mindmate

# 3. Configuration (fill in the values; see the table below)
cp .env.production.example .env.production
nano .env.production
chmod 600 .env.production

# 4. Build and start: postgres + backend + Caddy (HTTPS)
docker compose -f docker-compose.prod.yml --env-file .env.production --profile https up -d --build

# 5. Watch the first start: migrations, then uvicorn; Caddy obtains the certificate
docker compose -f docker-compose.prod.yml --env-file .env.production --profile https logs -f backend caddy
#    expect: "Running upgrade -> 0001_initial", "Running upgrade 0001_initial -> 0002_question_source",
#    "Uvicorn running on http://0.0.0.0:8000", and from Caddy "certificate obtained successfully"

# 6. Check it from anywhere
curl -s https://$API_DOMAIN/health        # nebius_key_configured: true, llm_available: true, demo_cache: "off"
./scripts/smoke_test.sh https://$API_DOMAIN
```

`.env.production` values:

| Variable | Value |
|---|---|
| `POSTGRES_PASSWORD` | long random string |
| `NEBIUS_API_KEY` | your Token Factory key (secret) |
| `MINDMATE_LLM_MODE` | `live` |
| `MINDMATE_DEMO_CACHE` | `off` (recorded answers are for offline rehearsal only; the smoke test fails if this is not `off`) |
| `MINDMATE_ADMIN_TOKEN` | long random string (protects `POST /admin/reset-demo`) |
| `API_DOMAIN` | `api.yourdomain.com` or `<VM-IP>.sslip.io` |
| `CORS_ORIGINS` | `https://mindmate-lyart.vercel.app` (exact origins, comma-separated; no wildcard) |
| `CORS_ORIGIN_REGEX` | optional, to also allow Vercel preview URLs, e.g. `https://mindmate-[a-z0-9-]+\.vercel\.app` |
| `RATE_LIMIT_PER_MINUTE` | `120` |

What the stack does on its own:

- **Migrations:** the backend container runs `alembic upgrade head` before starting uvicorn, every start.
- **Demo persona:** Meera is seeded only when the database is empty (`MINDMATE_AUTO_SEED=true`), so
  restarts never duplicate data.
- **Restart policy:** every service uses `restart: unless-stopped`; uvicorn runs as PID 1, so a crash
  restarts the container and `docker stop` shuts down cleanly.
- **Logs:** rotated at 10 MB × 3 files per container.
- **Port 8000:** published on `127.0.0.1` only; the public entry point is Caddy on 80/443. Set
  `BACKEND_BIND=0.0.0.0` only if you deliberately want plain HTTP on 8000.

### Day-2 commands

```bash
DC="docker compose -f docker-compose.prod.yml --env-file .env.production --profile https"
$DC ps                                       # status and health
$DC logs -f --tail 100 backend               # backend logs (model calls, errors)
$DC logs -f caddy                            # HTTPS / certificate logs
git pull && $DC up -d --build                # deploy a new version (migrations run on start)
$DC restart backend                          # restart after changing .env.production
$DC exec backend python scripts/reset_demo.py              # reset the demo persona (wipes app data)
curl -X POST https://$API_DOMAIN/admin/reset-demo -H "X-Admin-Token: <MINDMATE_ADMIN_TOKEN>"   # same, remotely
$DC exec postgres pg_dump -U mindmate mindmate > backup-$(date +%F).sql                # database backup
```

Model calls and fallbacks are also visible in the app (AI Activity) and at `GET /agent/events`, each
with the agent, the Nemotron model ID and the seconds it took.

## 2. Fallback host: Render (if a Nebius VM is not available)

The hackathon requires Nemotron on Nebius Token Factory; the model calls still go to Token Factory
from any host. Render runs the same `Dockerfile` (it injects `PORT`, which the image honours).

1. Render dashboard → **New → PostgreSQL**: create a database; copy its **Internal Database URL**.
2. **New → Web Service** → connect `basaaria123/Mindmate` → Language **Docker**, Dockerfile path
   `./Dockerfile`, branch `main`, health check path `/health/ready`.
3. Environment variables: `DATABASE_URL` = the Internal Database URL (a `postgres://` URL is fine; the
   backend switches it to the psycopg driver), `NEBIUS_API_KEY`, `MINDMATE_LLM_MODE=live`,
   `MINDMATE_DEMO_CACHE=off`, `MINDMATE_AUTO_CREATE_SCHEMA=false`, `MINDMATE_AUTO_SEED=true`,
   `MINDMATE_ADMIN_TOKEN`, `CORS_ORIGINS=https://mindmate-lyart.vercel.app`, `RATE_LIMIT_PER_MINUTE=120`.
4. Deploy. Render provides HTTPS on `https://<service>.onrender.com`; use that as the API URL.
5. `./scripts/smoke_test.sh https://<service>.onrender.com`

**[CONFIRM]** current Render free-tier limits: free web services sleep when idle, so the first request
after a pause is slow. Open `/health` a minute before recording or judging.

Railway and Fly.io work the same way: deploy the repository's `Dockerfile`, attach a PostgreSQL
database, set the same variables (Railway: `DATABASE_URL=${{Postgres.DATABASE_URL}}`; Fly:
`fly launch` then `fly postgres create` and `fly secrets set NEBIUS_API_KEY=...`), and use the
HTTPS URL the platform gives you.

## 3. Point the Vercel frontend at the backend

Vercel → project `mindmate` → **Settings → Environment Variables**:

| Name | Environment | Value |
|---|---|---|
| `VITE_API_BASE_URL` | Production (and Preview, if previews should use the live API) | `https://api.yourdomain.com` (your backend URL, no trailing slash) |

`VITE_*` values are compiled into the bundle, so a **redeploy is required** after setting or changing
it: **Deployments** → latest production deployment → **⋯ → Redeploy**. Check that the new build log
shows the latest commit. Then open the site on a laptop-width window: the header chip must read
**`nemotron | nebius token factory`** (green dot), not `offline mocks` or `deterministic mode | no model key`.

Vercel project settings (already in use; listed for reference): root directory `mindmate-frontend`,
framework Vite, build `npm run build`, output `dist`; `mindmate-frontend/vercel.json` rewrites app
routes such as `/memory` to `index.html`. **[CONFIRM]** the root directory setting in the Vercel project.

## 4. Verify the live deployment

```bash
B=https://api.yourdomain.com
./scripts/smoke_test.sh $B
#  PASS GET /health, GET /memory, POST /opportunity (Nemotron), POST /plans/replan (Nemotron explanation)
#  fails loudly on any offline, mock or recorded answer
python scripts/smoke_test.py --backend $B --frontend https://mindmate-lyart.vercel.app   # read-only, adds CORS + frontend routes
curl -s -H "Origin: https://mindmate-lyart.vercel.app" -I $B/profile | grep -i access-control-allow-origin
```

Then in the browser on the Vercel URL: Tasks & Practice (answer weakly) → AI Activity shows Nemotron
calls with model IDs and seconds → Plan & Progress (drop to 30 minutes, replan cites the weakness).

## 5. What was verified in development (22 October 2026)

| Item | Result |
|---|---|
| Backend image (`Dockerfile`) | Built and run with Docker 29. The sandbox needed its proxy certificate added in a scratch copy of the Dockerfile; the repository Dockerfile is unchanged by that. |
| Migrations on PostgreSQL 16 at container start | `0001_initial` and `0002_question_source` applied; `alembic current` = head |
| Demo persona seeding | Seeded into the empty database; not duplicated after a restart |
| `/health`, `/health/ready` | Healthy; key presence reported without the key; `demo_cache: off` by default |
| CORS | Configured origin and preview-regex origin allowed; other origins get no CORS header |
| Caddy HTTPS | Served `/health` over HTTPS (local certificate for `localhost`; a real domain gets a Let's Encrypt certificate) |
| Restart policy | Backend killed with SIGKILL came back on its own (restart count 1); `docker stop` exits cleanly in under 1 s |
| Frontend image (`mindmate-frontend/Dockerfile`) | Built; serves `/`, app routes and `/healthz` |
| `scripts/smoke_test.sh` | Fails loudly without a key and when an answer falls back to offline; passes against a backend whose agents were replaced by stubs. Not yet run against a real Nemotron deployment. |
| Real Nemotron calls from a deployment | **Not verified**: Token Factory is not reachable from the development sandbox and no key is available there. |
