# AI component: agents on NVIDIA Nemotron via Nebius Token Factory

Owner: AI developer, branch `mindmate-ai`. Files: `app/agents/`, `app/schemas/`,
`app/services/llm_client.py`, `app/services/memory_store.py`, `app/utils/json_utils.py`, root `test_*.py`.

## How it works

* The agents are plain Python functions imported by the FastAPI backend (same process). Each builds a
  prompt, calls the Nebius OpenAI-compatible endpoint, parses the JSON (`app/utils/json_utils.py`) and
  validates it against a Pydantic schema; on failure it retries once with a repair prompt, then raises.
* Model tiering (`app/services/llm_client.py`): `get_model("reasoning")` → `nvidia/Nemotron-3-Ultra-550b-a55b`
  (fit, gap, planner, practice); `get_model("fast")` → `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`
  (profile, opportunity, suggestions).
* No local model weights, no GPU: any laptop runs it. The only external dependency is HTTPS access to
  `https://api.tokenfactory.nebius.com/v1` and a key with credits.

| Agent | Function | Schema |
|---|---|---|
| Profile | `extract_user_profile(user_message)` | `UserProfile` |
| Opportunity | `extract_opportunity(text)` | `OpportunitySpec` |
| Fit | `assess_fit(profile, opportunity)` | `FitAssessment` |
| Skill gap | `identify_skill_gaps(profile, opportunity, fit)` | `GapVectorJSON` |
| Planner | `generate_plan(profile, opportunity, gaps, goal_id, decisions, memories)` | `PlanScheduleJSON` (budget + ref validation) |
| Practice | `evaluate_practice(question, answer, topic)` | `PracticeEvaluation` |
| Memory | `create_and_store_memory(evaluation, source)` | `MemoryItem` (JSON file store) |
| Suggestions | `generate_suggestions(profile)` | `SuggestionsResponse` (12 items) |

## Configuration (environment-driven)

| Variable | Default | Effect |
|---|---|---|
| `NEBIUS_API_KEY` | – | Required for any model call; never commit it |
| `NEBIUS_BASE_URL` | `https://api.tokenfactory.nebius.com/v1` | OpenAI-compatible endpoint |
| `MINDMATE_REASONING_MODEL` | `nvidia/Nemotron-3-Ultra-550b-a55b` | Fit, gap, planner, practice agents |
| `MINDMATE_FAST_MODEL` | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | Profile, opportunity, suggestions agents |
| `MINDMATE_LLM_MODE` | `live` | `off` makes the backend use its deterministic practice evaluator and skip model calls |

The model variables are read once at import, so restart the server after changing them.

## Cost and rate limits

Every agent call spends Token Factory credits; Ultra calls are the expensive ones. For local work prefer:
* `MINDMATE_LLM_MODE=off` while working on anything that is not the agents themselves;
* the offline tests (`test_json_utils.py`, `test_*_schema.py`) for schema changes;
* one live run per agent before opening a PR.

## Failure handling

* Invalid or off-schema JSON: one retry with the validation error, then `ValueError` (→ HTTP 422).
* Missing key: `RuntimeError("NEBIUS_API_KEY is missing")` (→ HTTP 500 on the AI endpoints; the backend's
  practice path falls back to the deterministic rubric instead).
* Timeouts/provider errors propagate from the OpenAI client; the backend practice path catches them.

## Running and testing

```bash
pip install -r requirements.txt
cp .env.example .env && echo "NEBIUS_API_KEY=..." >> .env
python -m pytest test_*.py -q --ignore=test_setup.py --ignore=test_model_selection.py --ignore=test_profile_agent.py --ignore=test_opportunity_agent.py --ignore=test_fit_agent.py   # offline
python -m pytest test_setup.py test_model_selection.py test_profile_agent.py test_opportunity_agent.py test_fit_agent.py -q   # live
uvicorn main:app --reload   # then POST /profile, /opportunity, /fit at http://localhost:8000/docs
```

## Interface with the backend

See `docs/API_CONTRACTS.md` section C. Keep function signatures and schema field names stable; when a
schema changes, update `docs/API_CONTRACTS.md` and the frontend types in `src/services/api.ts` in the same PR.
