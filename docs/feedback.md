# Tool feedback log (Nebius Token Factory, NVIDIA Nemotron)

Shared log for the required submission feedback section. Each role adds dated notes; the product lead turns
them into the final text. Only record what you actually observed.

## Backend and memory (BE)

* **Integration effort.** Token Factory exposes an OpenAI-compatible API, so the backend reuses the AI role's
  `openai` client with one base URL; no provider-specific SDK was needed. The base URL and model IDs are now
  environment variables (`NEBIUS_BASE_URL`, `MINDMATE_REASONING_MODEL`, `MINDMATE_FAST_MODEL`).
* **Designing for model failure.** Because agent calls can be slow or return off-schema JSON, every backend path
  that calls a Nemotron agent has a deterministic fallback, and recorded responses can replace the AI endpoints
  during the demo (`MINDMATE_DEMO_CACHE`). Agent output is validated in code (references, evidence, budgets).
* **Not yet measured by the backend role.** The backend was developed and tested without a Token Factory key, so
  latency, rate limits and credit use were not observed here. To capture during a live run:
  `python scripts/demo_check.py --base-url <staging>` with `MINDMATE_LLM_MODE=live` (timings per step), and the
  `model_call` events in `GET /agent/events`, which record the seconds each agent call took.

## AI agents (AI)

_To be added by the AI developer: model quality per agent, JSON adherence, Ultra vs Nano latency, rate limits._

## Deployment (DX)

_To be added: Nebius hosting experience, deployment steps, any platform issues._
