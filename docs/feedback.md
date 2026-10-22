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

* **Observed so far (offline, 2026-10-19).** All nine agents run against a fake OpenAI client in
  `tests/ai/test_agents_offline.py`; this exercises prompt rendering, the retry-once repair path and every validation rule,
  but not model quality. Because Token Factory is OpenAI-compatible, the fake client needed no provider-specific code.
* **Structured output.** Agents parse JSON from the reply text and validate it with Pydantic; invalid output gets one
  repair prompt that includes the validation error. Whether Nemotron needs that retry, and how often, is not yet
  measured.
* **Evaluation set.** `scripts/run_eval.py` runs offline in CI. Its first run exposed two bugs in our own skill matcher
  (not in the model), now fixed. The `--live` run has not been done yet.
* **To capture during the first live run:** `python scripts/run_eval.py --live --json` (practice agreement, extraction
  precision/recall), Ultra vs Nano seconds per call from the `model_call` events, how many calls needed the repair
  retry (`model_output_rejected` events), any 429 responses, and credits spent for one full demo.

## Frontend (FE)

* The frontend never talks to Token Factory directly; it calls the backend, so no key reaches the browser.
* The header chip reads `GET /admin/status` and shows whether the model is live, off, or the screens are in mock mode,
  so the demo can't silently present fallback output as model output.
* Long calls (Ultra) need loading states; actual waiting times will be noted after the live run.

## Deployment (DX)

* **Prepared and checked locally:** the frontend production image's nginx config (`nginx -t`, then served the built
  app with client-side routes), `docker-compose.prod.yml` for a single VM, and a read-only smoke test
  (`scripts/smoke_test.py`), which passed 11 of 12 checks against a local stack; the failing check is
  `llm_available`, expected without a key.
* **Not yet done:** building the images (no Docker daemon in the development container), deploying to Vercel or a
  Nebius VM, and any observation of Nebius hosting. Add notes here after the first deployment.
