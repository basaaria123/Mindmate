# MindMate backend: setup, run, test (Backend & Memory Engineer)

## What this layer provides

* **Structured memory in a database** (`app/db/models.py`): profile, goals (with hierarchy), constraints,
  skills, evidence, decisions with reasons, weaknesses, opportunities, fit assessments, plans and tasks,
  practice sessions, a unified memory-item view, an event log and action drafts.
* **Memory layer** (`app/memory/`): reference IDs that must exist, task-scoped retrieval, view/edit/soft-delete/purge.
* **Deterministic decision logic** (`app/scoring/`): fit score, gap ranking, replan priority, weakness thresholds.
* **Plan engine** (`app/services/plan_service.py`): time-budget scheduler, versioned plans, replan with a diff and a cited rationale.
* **Practice loop** (`app/services/practice_service.py`): question bank, Nemotron evaluation with a deterministic fallback.
* **Safety** (`app/permissions.py`, `app/rate_limit.py`): permission tiers outside the model, confirmation for irreversible actions, per-IP rate limiting.
* **Ops**: Alembic migrations, one-command demo reset, docker-compose PostgreSQL.

The AI role's agents and schemas (`app/agents`, `app/schemas`, `app/services/llm_client.py`) and the
frontend are untouched; `main.py` only gained two lines that register this layer.

## Run locally (SQLite, no services)

```bash
pip install -r requirements.txt
cp .env.example .env            # add NEBIUS_API_KEY for live Nemotron calls (optional)
python scripts/reset_demo.py    # seeds Meera's persona into data/mindmate.db
uvicorn main:app --reload       # http://localhost:8000/docs
```

Then in `mindmate-frontend/.env` set `VITE_API_BASE_URL=http://localhost:8000`.

## Run with PostgreSQL

```bash
docker compose up -d
export DATABASE_URL=postgresql+psycopg://mindmate:mindmate@localhost:5432/mindmate
export MINDMATE_AUTO_CREATE_SCHEMA=false
alembic upgrade head
python scripts/reset_demo.py
uvicorn main:app
```

New schema changes: edit `app/db/models.py`, then `alembic revision --autogenerate -m "..."` and `alembic upgrade head`.

## Demo path (weakness to replan)

1. `POST /practice/evaluate` with a weak Model-evaluation answer. The seeded persona already has one weak
   answer on the topic, so the second one crosses the threshold and `weakness#1` is recorded with references
   to both practice sessions.
2. `POST /plans/replan` (optionally `{"available_minutes": 30}`). The task that targets the weakness moves to
   day 1 and is marked `must_keep`; no day exceeds the budget; the rationale cites `weakness#1`, the practice
   sessions and the stored decisions.
3. `GET /memory` returns `originalPlan`, `updatedPlan` and `replanReason` for the Pipeline screen;
   `GET /agent/events` returns the trace.
4. `POST /admin/reset-demo` returns the database to the seeded state.

Cached/fallback mode for the live demo: set `MINDMATE_LLM_MODE=off` to force the deterministic evaluator
(the rest of the backend never calls a model).

## Tests

```bash
python -m pytest tests -q
```

| Area (proposal section 12) | Test file |
|---|---|
| Score arithmetic (fit, priority, thresholds) | `tests/test_scoring.py` |
| Budget test (30-minute replan) | `tests/test_budget.py`, `tests/test_scheduler.py` |
| Loop test (weakness changes plan order, rationale cites it) | `tests/test_loop.py` |
| Memory control (deleted items never reach prompts) | `tests/test_memory_control.py` |
| Permission layer | `tests/test_permissions.py` |
| API contracts, errors, rate limit, reset | `tests/test_api.py` |
| Migrations match models | `tests/test_migrations.py` |

## Configuration

All thresholds and weights are environment variables (see `.env.example`), never code.
`GET /admin/status` shows the values in effect.

## Agent orchestration (backend calls the AI agents)

`app/services/agent_bridge.py` builds agent inputs from the database, calls the agent only when live calls are
enabled, logs every call, and returns `None` on any failure so deterministic code takes over:

| Endpoint | Agent | Fallback |
|---|---|---|
| `POST /practice/evaluate` | Practice | Deterministic rubric over expected concepts |
| `POST /opportunities/{id}/fit` | Fit | Deterministic judge over skills and evidence |
| `POST /plans` with `generate_from_opportunity_id` | Planner | Deterministic tasks from the ranked gaps |
| `POST /opportunities/extract` | Opportunity | Keyword extraction |

Agent output is never trusted as-is: references must exist in the database, coverage needs evidence, and
budgets are enforced by the scheduler.

## Demo fallback, rehearsal and persona

* `MINDMATE_DEMO_CACHE=fallback` serves recorded answers for the AI endpoints when Nebius fails; `replay`
  never calls the model. The shipped recordings are hand-written defaults for the persona, validated against the
  AI schemas; run once with `record` and a real key to replace them with real Nemotron output.
* `python scripts/demo_check.py` (or `make demo-check BASE_URL=...`) resets the persona, runs the scripted demo
  path, checks success criteria 1, 2, 3 and 7, and prints step timings.
* `MINDMATE_SEED_PERSONA`, `MINDMATE_OPPORTUNITIES_FILE` and `MINDMATE_QUESTION_BANK` point the seed at other data
  files; a persona file may also carry its own `opportunities` list.
* `POST /memory/import-legacy` copies memories the AI `/practice` endpoint saved in `data/memories.json` into the
  database so they affect replanning.

## Weight tuning on the demo persona (plan days 8 to 11)

With the default weights the scripted path produces: fit 67% (Moderate) for the AI/ML Engineering Intern with
model evaluation as the top gap; the second weak model-evaluation answer records `weakness#1`; replanning at 30
minutes per day moves "Mock interview: model evaluation questions" from day 3 to day 1 (priority 0.81, must-keep)
and cites `weakness#1`, both practice sessions and both decisions. That is the intended demo behaviour, so the
defaults stay. If the product lead changes the persona, rerun `scripts/demo_check.py` and adjust the
`PRIORITY_WEIGHT_*` and `WEAKNESS_*` variables only if a check fails.

## PostgreSQL

Every backend test runs on PostgreSQL as well (`MINDMATE_TEST_DATABASE_URL=...` or `make test-backend-postgres`;
CI job "Backend tests on PostgreSQL"). Demo resets restart identities, so reference IDs are identical after every
reset on both databases.
