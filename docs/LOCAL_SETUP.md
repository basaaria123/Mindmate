# Local setup: run the complete application

Every developer runs all three components locally. The frontend and the backend (which embeds the AI
agents) are two processes; there is no separate AI server.

## 1. Requirements

| Tool | Version | Check |
|---|---|---|
| Python | 3.11 or newer (3.12 recommended) | `python --version` |
| Node.js + npm | Node 20 or newer (22 recommended) | `node --version` |
| Git | any recent | `git --version` |
| Docker (optional) | for PostgreSQL instead of SQLite | `docker --version` |

Nothing else is required. The backend uses a local SQLite file by default and the AI agents call Nebius
over HTTPS, so no model downloads or GPUs are involved.

## 2. Clone and pick your branch

```bash
git clone https://github.com/basaaria123/Mindmate.git
cd Mindmate
git fetch origin
git switch --track origin/mindmate-frontend   # or mindmate-backend / mindmate-ai
```

## 3. Backend (+ AI agents)

```bash
python -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env                 # Windows: copy .env.example .env
```

Edit `.env`:
* `NEBIUS_API_KEY=` your Nebius Token Factory key for live Nemotron calls. Leave empty to run the
  deterministic fallback for practice evaluation; the AI endpoints (`POST /profile`, `/opportunity`,
  `/fit`, `/gap`, `/plan`, `/practice`, `/suggestions`) return an error without a key.
* `MINDMATE_LLM_MODE=off` forces the fallback even when a key is present (demo-safe mode).
* Leave `DATABASE_URL` empty for SQLite at `data/mindmate.db`.

Seed and start:

```bash
python scripts/reset_demo.py         # creates tables and seeds the demo persona (Meera)
uvicorn main:app --reload --port 8000
```

Health check: http://localhost:8000/health → `{"status":"healthy"}`. API docs: http://localhost:8000/docs.
Status with thresholds and row counts: http://localhost:8000/admin/status.

### Optional: PostgreSQL

```bash
docker compose up -d
export DATABASE_URL=postgresql+psycopg://mindmate:mindmate@localhost:5432/mindmate
export MINDMATE_AUTO_CREATE_SCHEMA=false
alembic upgrade head
python scripts/reset_demo.py
uvicorn main:app --reload --port 8000
```

## 4. Frontend

```bash
cd mindmate-frontend
npm install
cp .env.example .env
```

Set `VITE_API_BASE_URL=http://localhost:8000` in `mindmate-frontend/.env` so every screen talks to the
backend. Leave it empty for mock mode: every memory, plan, practice and opportunity screen then reads a
persona snapshot (`src/services/personaSnapshot.json`, real backend responses for the Meera persona) and keeps
your edits in `localStorage` (key `mindmate-persona-mock`; clear it to start over). The AI features
(onboarding profile, "Analyze with AI", fit, suggestions) run offline analysis in the browser and say so on
screen; for Nemotron, run the backend with a key and set `VITE_API_BASE_URL`. The header chip shows which mode
you are in.

```bash
npm run dev                          # http://localhost:5173
```

## 5. One command for both

```bash
make setup && make dev               # macOS/Linux; uses scripts/dev.sh
```

On Windows run the backend and frontend in two terminals as in steps 3 and 4.

## 6. Ports and URLs

| Service | URL |
|---|---|
| Frontend (Vite) | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| OpenAPI docs | http://localhost:8000/docs |
| PostgreSQL (optional) | localhost:5432, db/user/password `mindmate` |

CORS: the backend allows `http://localhost:5173` and `http://127.0.0.1:5173` by default; add other
origins with `CORS_ORIGINS=https://your-frontend.example` in `.env`.

## 7. Tests

```bash
# backend (no network): memory layer, scoring, plans, API, migrations
MINDMATE_LLM_MODE=off python -m pytest tests -q

# demo rehearsal with success-criteria checks
python scripts/demo_check.py

# AI, offline part: parser, schema, memory-agent and model-config tests
python -m pytest tests/ai -q

# AI, live part (needs NEBIUS_API_KEY and network; costs Token Factory credits)
python -m pytest tests/live -q

# evaluation set: practice weak/strong agreement and extraction precision/recall (add --live with a key)
python scripts/run_eval.py

# backend against PostgreSQL (docker compose up -d first)
make test-backend-postgres

# frontend (lint is a required CI step)
cd mindmate-frontend && npm run lint && npm run build
```

Production-style check of a running stack (read-only; see `docs/DEPLOYMENT.md`):

```bash
python scripts/smoke_test.py --backend http://localhost:8000 --frontend http://localhost:5173
```

Without `NEBIUS_API_KEY` the `llm_available` check fails and the rest should pass.

Integration check (backend running, no key needed):

```bash
curl -s -X POST localhost:8000/practice/evaluate -H 'Content-Type: application/json' \
  -d '{"answer":"I would only check accuracy on the test set.","topic":"Model evaluation"}'
curl -s -X POST localhost:8000/plans/replan -H 'Content-Type: application/json' -d '{"available_minutes":30}'
curl -s localhost:8000/memory | head -c 400
```

The second call's `rationale` cites `weakness#1`; `GET /memory` returns `updatedPlan` and `replanReason`.

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| Results say "Offline analysis" | No key, or `MINDMATE_LLM_MODE=off`. Add `NEBIUS_API_KEY` to `.env` (backend root), set `MINDMATE_LLM_MODE=live`, restart uvicorn, and set `VITE_API_BASE_URL` in the frontend. |
| Frontend shows "Could not reach the MindMate API" | Backend not running on 8000, or `VITE_API_BASE_URL` wrong. Restart `npm run dev` after editing `.env`. |
| CORS error in the browser | Add the frontend origin to `CORS_ORIGINS` in `.env`. |
| `429 Rate limit exceeded` | `RATE_LIMIT_PER_MINUTE=0` in `.env` for local work. |
| Database looks wrong | `python scripts/reset_demo.py` (or `POST /admin/reset-demo`). |
| `alembic` errors with SQLite | Delete `data/mindmate.db` and rerun `python scripts/reset_demo.py`; SQLite uses auto-create. |
| Mock mode shows old edits | Clear the `mindmate-persona-mock` key in the browser's local storage. |
