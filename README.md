# MindMate

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Live demo:** https://mindmate-lyart.vercel.app (backend API: https://mindmate-backend-yw5d.onrender.com)

**Demo video:** [YOUTUBE_URL]

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
| Backend hosting | Deployed on Render as a Docker web service with a Render PostgreSQL database: https://mindmate-backend-yw5d.onrender.com. Nemotron runs on Nebius Token Factory. [CONFIRM] `./scripts/smoke_test.sh https://mindmate-backend-yw5d.onrender.com` passes. |
| Vercel frontend hosting | Deployed at https://mindmate-lyart.vercel.app. [CONFIRM] `VITE_API_BASE_URL` is set to the Render backend; without it the site runs in offline mock mode (labelled on screen). |
| Live opportunity search (Tavily) | Not integrated. The opportunity set is curated plus whatever the user pastes. |
| Daily brief job, NemoClaw / OpenShell, Hermes Agent | Not integrated. |
| Calendar, Notion, Slack, GitHub integrations | Not integrated (future scope). |

## How MindMate uses NVIDIA Nemotron and Nebius

**Models** (configured in `app/services/llm_client.py`, overridable by environment variable):

| Tier | Model ID | Env override |
|---|---|---|
| Reasoning | `nvidia/Nemotron-3-Ultra-550b-a55b` | `MINDMATE_REASONING_MODEL` |
| Fast | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | `MINDMATE_FAST_MODEL` |

**Nine agents** (`app/agents/`, prompts in `prompts/`):

| Agent | Model | What it does |
|---|---|---|
| Profile | Nano | Turns the onboarding text into a structured profile (JSON mode) |
| Opportunity | Nano | Extracts title, required and preferred skills from a pasted posting |
| Suggestions | Nano | Twelve suggestions, three per category |
| Fit | Ultra | Judges how well memory evidence covers each requirement |
| Skill gap | Ultra | Ranks gaps by career impact with the missing evidence |
| Planner | Ultra | Builds the plan within the daily budget, citing memory IDs |
| Practice evaluation | Ultra | Scores a mock-interview answer (correctness, depth, clarity) |
| Practice questions | Ultra | Writes questions aimed at the user's gaps and weaknesses |
| Replan explanation | Ultra | Explains in plain language what the code changed and why, citing only allowed memory IDs |

Why the split: Nano handles extraction, where the output mostly restates the input in a schema and
speed matters during onboarding and pasting; Ultra handles judgement over the user's memory, where a
wrong answer changes the plan. The numbers that decide things (fit score, gap ranking, replan priority,
budget scheduling, weakness thresholds) are computed by code; Nemotron supplies judgements and
explanations, and its output is validated before it is used (memory IDs must exist, budgets must hold).

**Where Nebius Token Factory helped:**

- One OpenAI-compatible endpoint (`https://api.tokenfactory.nebius.com/v1`) and one client for all nine
  agents: the standard `openai` SDK, no model hosting, no GPUs, no weights to download.
- Switching a tier between Nemotron models is an environment variable, with no code change.
- Because the API is OpenAI-compatible, every agent is tested offline against a fake client
  (`tests/ai/test_agents_offline.py`): valid output, invalid-then-repaired output, and rejection.
- Each agent parses and validates the JSON it gets back (Pydantic) and retries once with the
  validation error before rejecting; the backend then falls back to deterministic code and logs it.
- Every call is logged with the agent, the Nemotron model ID and the seconds it took
  (AI Activity page and `GET /agent/events`).

**Hosting:** the models run on Nebius Token Factory; the backend itself is hosted on Render (Docker web
service + Render PostgreSQL) and the frontend on Vercel. No other Nebius services are used.

## Quick start

```bash
git clone https://github.com/basaaria123/Mindmate.git && cd Mindmate
make setup     # Python + Node dependencies, .env files, demo database (persona: Meera)
make dev       # backend http://localhost:8000, frontend http://localhost:5173
```

Add `NEBIUS_API_KEY` to `.env` (and keep `MINDMATE_LLM_MODE=live`) for live Nemotron calls; without it the backend runs its deterministic
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
make test-ai-live   # live agent tests against Nemotron (needs NEBIUS_API_KEY; spends credits)
python scripts/run_eval.py            # evaluation set, deterministic path (--live for Nemotron)
./scripts/smoke_test.sh https://<backend>   # deployed backend must answer with Nemotron
```

Current results are in `docs/TEST_PLAN.md`.

## Documentation

| Document | Contents |
|---|---|
| `docs/ARCHITECTURE.md` | Components, request flows, data model, decision logic |
| `docs/API_CONTRACTS.md`, `docs/contracts/backend-api.md` | Frontend, backend and AI interfaces |
| `docs/LOCAL_SETUP.md` | Running and testing everything locally |
| `docs/DEPLOYMENT.md` | Render (current), Nebius VM option with HTTPS, Vercel settings, live smoke test |
| `docs/AI_SERVICE.md`, `prompts/README.md` | Agents, prompts, model configuration, evaluation |
| `docs/BRANCH_WORKFLOW.md` | Branches, file ownership, pull requests |
| `docs/DECISIONS.md` | Decisions and their reasons |
| `docs/demo-script.md`, `docs/SUBMISSION.md`, `docs/SUBMISSION_CHECKLIST.md` | Demo video script, Devpost submission pack, requirement checklist |
| `docs/TEST_PLAN.md` | Success criteria and how each is verified |
| `docs/feedback.md` | Notes on Nebius and NVIDIA tools |

## License

MIT, see [`LICENSE`](LICENSE).
