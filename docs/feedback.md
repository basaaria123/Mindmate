# Feedback: Nebius Token Factory, NVIDIA Nemotron (and why not Nebius AI Cloud)

Written from what the code, its comments, `docs/DECISIONS.md` and the git history show
(2026-10-10 to 2026-10-22). Lines marked **[CONFIRM]** are things the team must check against its own
experience before submitting; they are not established by the repository. No latency, cost or
quality numbers are claimed here because none were recorded in the repository.

## Summary (for the submission form)

Nebius Token Factory's OpenAI-compatible API made it straightforward to run ten Nemotron agents from one
FastAPI backend: one client, one base URL, models chosen by environment variable, and offline testing with
a fake client. We split work between Nemotron Nano (extraction) and Nemotron Ultra (judgement over the
user's memory). The things we would most like improved are clearer guidance on structured (JSON) output
for each model, and per-request usage and latency information we could log alongside our own traces.
[CONFIRM: add one sentence on your real experience of Ultra vs Nano speed and output quality.]

## Nebius Token Factory

**What worked**

- **OpenAI-compatible API.** `app/services/llm_client.py` creates a standard `openai.OpenAI` client with
  `base_url=https://api.tokenfactory.nebius.com/v1`. All ten agents share it; no provider SDK was needed.
- **One endpoint, two model tiers.** Switching a tier between models is an environment variable
  (`MINDMATE_REASONING_MODEL`, `MINDMATE_FAST_MODEL`); the history shows the IDs and base URL moving from
  hard-coded constants to environment variables without touching any agent.
- **No infrastructure to run.** No GPUs, weights or model servers: the backend is a small CPU container.
- **Testability.** Because the API is OpenAI-shaped, `tests/ai/test_agents_offline.py` drives every agent
  through a fake client (valid reply, invalid-then-repaired reply, rejection, invented references), so CI
  covers the agent logic without spending credits.
- **JSON mode.** The Profile agent requests `response_format={"type": "json_object"}` and works with it
  [CONFIRM: that Token Factory honoured JSON mode for Nemotron Nano in your live runs].

**Issues we hit and workarounds**

- **Structured output is not guaranteed.** Every agent except Profile asks for JSON in the prompt and
  parses free text; `app/utils/json_utils.py` strips Markdown code fences "if the model includes them",
  then Pydantic validates the result and the agent retries once with the validation error before
  rejecting. [CONFIRM: that Nemotron actually returned fenced or off-schema JSON in practice, and roughly
  how often the retry was needed.]
- **Output length.** The Profile agent's `max_tokens` was raised from 500 to 1000 on 2026-10-12
  (commit `24043c6`). [CONFIRM: the reason, e.g. truncated JSON at 500 tokens.]
- **Calls can be slow or fail, so nothing depends on them.** Every model path has a deterministic
  fallback, every fallback is logged (`model_fallback` with model ID and seconds), and the UI labels
  offline answers instead of hiding them (`docs/DECISIONS.md` #6).
- **Live tests need a funded key.** The five live tests (`tests/live/`) and `scripts/run_eval.py --live`
  spend credits, so CI runs only the offline suite and live runs are manual.

**What we would improve**

- Per-model documentation of structured-output support (JSON mode / schema-constrained output) and the
  recommended way to get schema-valid JSON from each Nemotron model.
- Usage and latency returned per request (or a request ID that maps to the dashboard), so applications can
  log token counts and cost next to their own traces.
- A free, rate-limited sandbox key or model for CI, so a smoke test can hit the real endpoint on every push.
- [CONFIRM: any rate-limit (HTTP 429), model-availability or dashboard issues you saw.]

## Nebius AI Cloud

- **Not used for hosting.** The backend runs on Render (Docker web service + Render PostgreSQL) and the
  frontend on Vercel; only the model calls go to Nebius (Token Factory). A Nebius AI Cloud VM setup with
  `docker-compose.prod.yml` and Caddy is documented in `docs/DEPLOYMENT.md` but was not used.
- [CONFIRM: why the team chose Render over a Nebius AI Cloud VM (for example: a managed PostgreSQL and
  HTTPS out of the box, no VM to administer, deadline). If someone tried AI Cloud, add what got in the way.]

## NVIDIA Nemotron

- **Model split.** Nemotron 3 Nano (`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`) runs the extraction agents
  (profile, opportunity, suggestions); Nemotron 3 Ultra (`nvidia/Nemotron-3-Ultra-550b-a55b`) runs the
  judgement agents (fit, gap, planner, practice evaluation, practice questions, replan explanation). All
  calls use `temperature=0` for repeatable output.
- **Grounding.** Agents may cite only memory IDs supplied in the prompt; the backend rejects output that
  cites anything else (planner and replan agents, tested offline). This let us use Nemotron for
  explanations while scores and plans stay deterministic (`docs/DECISIONS.md` #3).
- [CONFIRM: your observations of Ultra vs Nano: speed, JSON adherence, quality of the replan explanations
  and practice feedback. Measure with `python scripts/run_eval.py --live --json` and the seconds logged in
  `GET /agent/events`; record the numbers here.]
- **Other NVIDIA tools:** none used. NemoClaw/OpenShell and Hermes Agent were considered in the proposal
  but are not integrated (see the README's "What is actually integrated" table).

## Development-environment note

The team's cloud development sandbox could not reach `api.tokenfactory.nebius.com` (its network policy
blocks the host), so live calls were not made from there. This is a limitation of that sandbox, not of
Token Factory. Live verification is done on the deployed backend with `scripts/smoke_test.sh`.
