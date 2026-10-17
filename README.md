# MindMate

MindMate is a private, always-on personal AI agent for students and early-career professionals.
It keeps a structured, user-owned memory (goals, decisions and their reasons, skills with evidence,
weaknesses), reasons over it with NVIDIA Nemotron on Nebius Token Factory, and rebuilds the user's
plan when something changes, explaining what moved and why.

**It remembers why. It adapts to you. It stays yours.**

## Repository layout

| Path | Component | Owner branch |
|---|---|---|
| `mindmate-frontend/` | React + Vite + TypeScript web app (screens, API client, mocks) | `mindmate-frontend` |
| `main.py`, `app/api`, `app/db`, `app/memory`, `app/scoring`, `app/backend.py`, `app/config.py`, `app/permissions.py`, `app/rate_limit.py`, `app/services/*` (except the two AI files), `alembic/`, `tests/`, `scripts/`, `data/` | FastAPI backend and memory layer | `mindmate-backend` |
| `app/agents`, `app/schemas`, `app/services/llm_client.py`, `app/services/memory_store.py`, `app/utils`, `test_*.py` (root) | Nemotron agents, prompts, schema-validated outputs | `mindmate-ai` |
| `docs/` | Architecture, API contracts, workflow, setup, deployment | shared |

The backend and AI code share one Python package (`app/`) and one FastAPI process; the AI agents are
a library the backend calls, not a separate server. See `docs/ARCHITECTURE.md`.

## Quick start

```bash
git clone https://github.com/basaaria123/Mindmate.git && cd Mindmate
make setup          # installs Python + Node dependencies, creates .env files, seeds the demo database
make dev            # backend on http://localhost:8000, frontend on http://localhost:5173
```

Without `make`: follow `docs/LOCAL_SETUP.md` step by step (Windows included).

## Documentation

| Document | What it covers |
|---|---|
| `docs/LOCAL_SETUP.md` | Run the complete app locally, ports, health checks, tests, troubleshooting |
| `docs/BRANCH_WORKFLOW.md` | Branches, file ownership table, shared-file rules, pull requests, GitHub settings |
| `docs/API_CONTRACTS.md` | Frontend ↔ backend ↔ AI interfaces, error format, env vars, CORS, timeouts |
| `docs/ARCHITECTURE.md` | Components, request flow, data model, decision logic |
| `docs/AI_SERVICE.md` | Model/provider configuration, running and testing the agents, hardware |
| `docs/DEPLOYMENT.md` | Vercel (frontend) and backend hosting, environment variables, verification |
| `docs/backend.md`, `docs/contracts/backend-api.md` | Backend internals and the full endpoint reference |

## Tests

```bash
make test           # backend tests, offline AI tests, frontend build
```

Agent tests that call Nemotron (`test_*_agent.py`, `test_setup.py`, `test_model_selection.py`) need
`NEBIUS_API_KEY` in `.env` and are run locally by the AI developer.

## Hackathon

NVIDIA x Nebius Global AI Hackathon 2026, Personal AI track. Models: `nvidia/Nemotron-3-Ultra-550b-a55b`
(reasoning) and `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` (fast) via Nebius Token Factory.
