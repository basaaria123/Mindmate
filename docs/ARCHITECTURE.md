# MindMate architecture

## Components

```
User
 |
 v
Frontend  (mindmate-frontend/, React + Vite + TypeScript, port 5173)
 |   fetch(VITE_API_BASE_URL + path)
 v
Backend API  (main.py + app/, FastAPI, port 8000)
 |-- Memory layer, scoring, plans, practice, permissions  (app/api, app/db, app/memory, app/scoring, app/services)
 |-- AI agents (library call, same process)               (app/agents, app/schemas)
 |        |
 |        v
 |   Nebius Token Factory (OpenAI-compatible HTTPS API) -> NVIDIA Nemotron models
 |        |
 |        v
 |   JSON validated by Pydantic schemas; invalid output is retried once, then rejected
 v
Frontend renders the result; every change cites memory references (ev#4, decision#1, weakness#3)
```

There is **one** server process. The AI component is an in-process library (`app/agents/*`) that the
backend imports; model calls go out to Nebius over HTTPS. No separate AI server is needed or deployed.

## Request flows

| Flow | Path |
|---|---|
| Onboarding text -> profile | Frontend `POST /profile` -> `app/agents/profile_agent.py` -> Nemotron Nano -> `UserProfile` schema -> JSON |
| Opportunity text -> spec -> fit | Frontend `POST /opportunity` then `POST /fit` -> Opportunity/Fit agents (Nemotron) -> schemas |
| Deterministic fit over stored memory | Frontend `POST /opportunities/{id}/fit` -> `app/scoring/fit.py` (code, no model) |
| Practice answer -> weakness -> replan | Frontend `POST /practice/evaluate` -> Practice agent (Nemotron, or deterministic rubric) -> thresholds (`app/scoring/weakness.py`) -> memory -> `POST /plans/replan` -> `app/services/plan_service.py` -> diff + rationale |
| Memory screen | Frontend `GET/POST/PATCH/DELETE /memory` -> `app/memory/service.py` |
| Trace screen | Frontend `GET /agent/events` -> `app/services/events.py` |

Models propose; deterministic code validates, stores and decides what is allowed
(scores, budgets, permissions, reference validation).

## Data model (PostgreSQL in production, SQLite locally)

users, goals (hierarchy via `parent_goal_id`, `priority_rank`), constraints, skills, evidence,
decisions (statement + reason), weaknesses (thresholds, severity, refs), opportunities,
fit_assessments, plans (versioned), tasks, practice_sessions, memory_items (unified view with
soft delete), events (trace), action_drafts. Schema: `app/db/models.py`; migrations: `alembic/`.

## Decision logic (all tunable through environment variables)

* Fit: `fit% = 100 × Σ(weight × coverage) / Σ(weight)`; High=3, Medium=2, Low=1; not shown=0, partial=0.5, demonstrated=1; bands 75+/50-74/<50.
* Replan priority: `0.40 role_impact + 0.25 weakness_boost + 0.20 goal_hierarchy + 0.15 deadline_urgency`; must-keep = active weakness or hard deadline; schedule never exceeds the daily budget.
* Weakness: created after N low-scoring answers on a topic (default 2) or one severe answer, never a single ordinary miss.
* Permissions: read-only / optional write (tasks only) / application actions (drafts only). Submission is never automated.

## Why this layout

The code already lives as a Python package at the repository root and a Vite app in
`mindmate-frontend/`. Moving `app/` into `backend/` and splitting the AI agents into `ai/` would break
every import, the Alembic config, the test paths and the Vercel root directory, so ownership is
organised by path and branch instead (see `docs/BRANCH_WORKFLOW.md`).
