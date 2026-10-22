# AI component: agents on NVIDIA Nemotron via Nebius Token Factory

Owner: AI developer, branch `mindmate-ai`. Files: `app/agents/`, `app/schemas/`, `prompts/`,
`app/services/llm_client.py`, `app/services/memory_store.py`, `app/utils/json_utils.py`, `app/utils/prompts.py`,
`data/eval/`, `scripts/run_eval.py`, `tests/ai/` (offline) and `tests/live/` (calls Nemotron).

## How it works

* The agents are plain Python functions imported by the FastAPI backend (same process). Each renders its
  prompt from `prompts/` (see below), calls the Nebius OpenAI-compatible endpoint, parses the JSON (`app/utils/json_utils.py`) and
  validates it against a Pydantic schema; on failure it retries once with a repair prompt, then raises.
* Model tiering (`app/services/llm_client.py`): `get_model("reasoning")` → `nvidia/Nemotron-3-Ultra-550b-a55b`
  (fit, gap, planner, practice evaluation, practice questions, replan explanation); `get_model("fast")` → `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`
  (profile, opportunity, suggestions).
* No local model weights, no GPU: any laptop runs it. The only external dependency is HTTPS access to
  `https://api.tokenfactory.nebius.com/v1` and a key with credits.

| Agent | Function | Schema | Called by the backend from |
|---|---|---|---|
| Profile | `extract_user_profile(user_message)` | `UserProfile` | `POST /profile` (then `POST /profile/import`) |
| Opportunity | `extract_opportunity(text)` | `OpportunitySpec` | `POST /opportunity`, `POST /opportunities/extract` |
| Fit | `assess_fit(profile, opportunity)` | `FitAssessment` | `POST /fit`, `POST /opportunities/{id}/fit` |
| Skill gap | `identify_skill_gaps(profile, opportunity, fit)` | `GapVectorJSON` | `POST /gap` |
| Planner | `generate_plan(profile, opportunity, gaps, goal_id, decisions, memories)` | `PlanScheduleJSON` (budget + ref validation) | `POST /plan`, `POST /plans` |
| Practice evaluation | `evaluate_practice(question, answer, topic)` | `PracticeEvaluation` | `POST /practice`, `POST /practice/evaluate` |
| Practice questions | `generate_practice_questions(target_role, skills, gaps, weaknesses, topic, count, allowed_refs)` | `PracticeQuestionSet` (1–5 questions, refs must be allowed) | `POST /practice/start` |
| Replan explanation | `explain_replan(changes, allowed_refs)` | `ReplanExplanation` (must cite at least one allowed ref; `cited_refs` must equal the refs in the text) | `POST /plans/replan` |
| Suggestions | `generate_suggestions(profile)` | `SuggestionsResponse` (12 items) | `POST /suggestions` |
| Memory (no model) | `create_and_store_memory(evaluation, source)` | `MemoryItem` (JSON file store) | `POST /practice` |

When the model is off or an agent fails validation twice, the backend uses its deterministic path (rubric,
keyword extraction, coverage scoring, scheduler, question bank, code-written replan rationale) and logs a
`model_fallback` event. See `docs/API_CONTRACTS.md` section C.

## Prompts

Every prompt is a versioned file in `prompts/`: `<agent>.system.md` (system message) and `<agent>.md`
(user message template with `${name}` placeholders). `app/utils/prompts.py` loads them (cached) and renders
them with `string.Template.substitute`, so a missing value fails loudly instead of sending a broken prompt.
`tests/ai/test_prompts.py` checks that every agent's files exist, that every placeholder is filled, and that no prompt
file is unused. Change a prompt in its own commit and run the eval set (below) before and after.
`prompts/README.md` lists the files and their variables.

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
* the offline tests (`tests/ai/test_json_utils.py`, `tests/ai/test_*_schema.py`) for schema changes;
* one live run per agent before opening a PR.

## Failure handling

* Invalid or off-schema JSON: one retry with the validation error, then `ValueError` (→ HTTP 422).
* Missing key, model off (`MINDMATE_LLM_MODE=off`), timeout or provider error: the AI endpoints `/profile`,
  `/opportunity`, `/fit`, `/gap` and `/suggestions` answer with offline analysis instead
  (`app/services/offline_ai.py`: keyword extraction, the fit weights, curated suggestions), in the same schema.
  The response header `X-MindMate-Source` is `nemotron` or `offline`, the screens label offline answers, and a
  model failure is logged as `model_fallback`. `/plan` and `/practice` still need the key; the backend's own
  `POST /plans` and `POST /practice/evaluate` have deterministic paths.
* In frontend mock mode (no `VITE_API_BASE_URL`) the same rules run in the browser
  (`mindmate-frontend/src/services/offlineAnalysis.ts`); `tests/test_offline_ai.py` checks that its skill
  vocabulary and hint words match the Python module.

## Running and testing

```bash
pip install -r requirements.txt
cp .env.example .env && echo "NEBIUS_API_KEY=..." >> .env
python -m pytest tests/ai -q   # offline
python -m pytest tests/live -q   # live
uvicorn main:app --reload   # then POST /profile, /opportunity, /fit at http://localhost:8000/docs
```

The offline set needs no key: schema tests, the JSON parser, model configuration, prompt files, and
`tests/ai/test_agents_offline.py`, which runs every agent against a fake OpenAI client to cover the retry-once path,
the repair prompt and every validation rule (refs, budgets, question count, replan citations).
CI runs it on every push (`make test-ai`). The five live files call Nemotron and spend credits
(`make test-ai-live`).

## Evaluation set

`data/eval/practice_answers.json` holds 10 labelled answers (weak or strong) across the question-bank topics;
`data/eval/postings.json` holds postings with their expected required skills.

```bash
python scripts/run_eval.py           # deterministic rubric and keyword extraction, no key (CI runs this)
python scripts/run_eval.py --live    # Practice evaluation and Opportunity agents on Nemotron
python scripts/run_eval.py --json    # machine-readable output
```

Practice accuracy is the share of answers whose weak/strong label matches (weak = score below
`WEAKNESS_SCORE_THRESHOLD`, default 60). Extraction is scored by precision and recall of required skills.
Offline results on the current code: practice 10/10, extraction precision 1.00 and recall 1.00. The eval set
found two matcher bugs (Deep learning matched ML fundamentals; Java matched JavaScript), fixed in
`app/scoring/fit.py`. The live run has not been recorded yet: it needs a key. Record its numbers in
`docs/feedback.md` when it is run.

## Interface with the backend

See `docs/API_CONTRACTS.md` section C. Keep function signatures and schema field names stable; when a
schema changes, update `docs/API_CONTRACTS.md` and the frontend types in `src/services/api.ts` in the same PR.
