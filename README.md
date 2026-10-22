# MindMate

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**It remembers why. It adapts to you. It stays yours.**

MindMate is a private personal AI agent for students and early-career professionals. It keeps a
structured memory you can inspect and edit: goals in priority order, decisions with their reasons, skills
backed by evidence, and weaknesses found in practice. It uses NVIDIA Nemotron on Nebius Token Factory to
reason over that memory, and it rebuilds your 14-day plan when your time or your results change,
explaining what moved and which memory caused it.

NVIDIA x Nebius Global AI Hackathon 2026, Personal AI track.

## The loop

Goal → Memory → Reason → Act → Observe → Adapt. A weak practice answer on model evaluation becomes a
recorded weakness (only after repeated evidence, never from one answer), and the next replan moves
model-evaluation practice to day 1, keeps it even when the daily time drops from 60 to 30 minutes, and
cites the weakness, the practice sessions and the user's own decisions.

## What is actually integrated

| Capability | Status |
|---|---|
| NVIDIA Nemotron via Nebius Token Factory | Integrated: nine agents (profile, opportunity, fit, gap, planner, practice evaluation, practice questions, replan explanation, suggestions). Ultra for reasoning, Nano for fast extraction. Needs `NEBIUS_API_KEY`. |
| Structured, user-owned memory | Integrated: PostgreSQL (SQLite locally); every item viewable, editable and deletable; deleted items never reach a prompt. |
| Deterministic decisions | Integrated: fit score, gap ranking, replan priority, budget scheduler, weakness thresholds and permissions are code, not model output. |
| Model-failure handling | Integrated: every agent retries invalid output once then rejects it; every backend path has a deterministic fallback; without a key the AI endpoints (and mock mode, in the browser) give labelled offline analysis; recorded answers can replace the AI endpoints during a demo. |
| Permission tiers | Integrated: read-only, tasks-only writes, application drafts only; nothing is submitted for the user. |
| Nebius hosting (Serverless or AI Cloud) | Deployment files ready (`Dockerfile`, `docker-compose.prod.yml`); not deployed yet. |
| Vercel frontend hosting | Configuration ready (`mindmate-frontend/vercel.json`); not deployed yet. |
| Live opportunity search (Tavily) | Not integrated. The opportunity set is curated plus whatever the user pastes. |
| Daily brief job, NemoClaw / OpenShell, Hermes Agent | Not integrated. |
| Calendar, Notion, Slack, GitHub integrations | Not integrated (future scope). |

## Quick start

```bash
git clone https://github.com/basaaria123/Mindmate.git && cd Mindmate
make setup     # Python + Node dependencies, .env files, demo database (persona: Meera)
make dev       # backend http://localhost:8000, frontend http://localhost:5173
```

Add `NEBIUS_API_KEY` to `.env` for live Nemotron calls; without it the backend runs its deterministic
paths and the AI endpoints answer with clearly labelled offline analysis (keyword extraction and fit rules). Step-by-step instructions, including Windows:
`docs/LOCAL_SETUP.md`.

## Repository layout

| Path | Component |
|---|---|
| `mindmate-frontend/` | React + Vite + TypeScript app (Home, Tasks & Practice, Plan & Progress, AI Activity, My Memory, Skill Gaps, Opportunities, Activity History) |
| `main.py`, `app/api`, `app/db`, `app/memory`, `app/scoring`, `app/services` | FastAPI backend and memory layer |
| `app/agents`, `app/schemas`, `prompts/` | Nemotron agents, schema-validated outputs, versioned prompts |
| `data/` | Demo persona, curated opportunities, question bank, evaluation set, recorded demo answers |
| `tests/` (backend), `tests/ai/` (offline AI), `tests/live/` (live Nemotron) | Tests |
| `docs/` | Architecture, API contracts, setup, deployment, workflow, demo script, submission pack |

## Tests

```bash
make test           # backend, offline AI and frontend build
make demo-check     # rehearse the scripted demo and check the success criteria
python scripts/run_eval.py            # evaluation set, deterministic path
```

Current results are in `docs/TEST_PLAN.md`.

## Documentation

| Document | Contents |
|---|---|
| `docs/ARCHITECTURE.md` | Components, request flows, data model, decision logic |
| `docs/API_CONTRACTS.md`, `docs/contracts/backend-api.md` | Frontend, backend and AI interfaces |
| `docs/LOCAL_SETUP.md` | Running and testing everything locally |
| `docs/DEPLOYMENT.md` | Vercel, Nebius VM or container, smoke test, deployment status |
| `docs/AI_SERVICE.md`, `prompts/README.md` | Agents, prompts, model configuration, evaluation |
| `docs/BRANCH_WORKFLOW.md` | Branches, file ownership, pull requests |
| `docs/DECISIONS.md` | Decisions and their reasons |
| `docs/demo-script.md`, `docs/SUBMISSION.md` | Three-minute demo and the Devpost submission pack |
| `docs/TEST_PLAN.md` | Success criteria and how each is verified |
| `docs/feedback.md` | Notes on Nebius and NVIDIA tools |

## License

MIT, see `LICENSE`.
