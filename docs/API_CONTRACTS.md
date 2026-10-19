# API contracts: frontend ↔ backend ↔ AI

Base URL: `VITE_API_BASE_URL` in the frontend (local `http://localhost:8000`, production = deployed
backend URL). All requests and responses are JSON. No authentication is used in the MVP: the backend is
single-user per database and selects the first user (an optional `X-User-Id` header picks another).
`POST /admin/reset-demo` is protected by `X-Admin-Token` when `MINDMATE_ADMIN_TOKEN` is set.

## Error format (every endpoint)

```json
{ "detail": "Human-readable message" }
```

| Status | Meaning |
|---|---|
| 404 | Item not found |
| 403 | Permission denied (irreversible action, missing confirmation, admin token) |
| 422 | Validation error, unknown reference ID, model returned invalid JSON after one retry |
| 429 | Rate limit (`Retry-After: 60`) |
| 500 | Unexpected error (reported with a generic detail) |

The frontend's `request()` helper reads `detail` and shows it to the user.

## A. Backend memory, plans, practice, trace (`app/api/*`)

Full reference with every field: `docs/contracts/backend-api.md`. Endpoints the current frontend calls:

| Frontend function (`src/services/api.ts`) | Method and path | Request | Response (key fields) |
|---|---|---|---|
| `getProfile` | `GET /profile` | – | `{name, goal, targetRole, dailyMinutes, education, summary, ...}` |
| `updateProfile` | `PUT /profile` | `{name, goal, targetRole, dailyMinutes}` | same shape |
| `getMemory` / `getDemoState` | `GET /memory` | – | `{items[], memoryNotes[], latestPractice, trace[], originalPlan[], updatedPlan, replanReason}`; every active weakness also appears in `memoryNotes` as `"Practice focus: <topic>"`, which the Memory screen uses to show an insight as saved |
| `addMemoryEntry` / `saveWeaknessToMemoryApi` | `POST /memory` | `{type, content, payload?, reason?}` | `{id, type, content, createdAt, ref, ...}` |
| `submitPracticeAnswer` | `POST /practice/evaluate` | `{answer, session_id?, question?, topic?}` | `{answer, score, weakness, feedback, submittedAt, rubric_scores, missing_concepts, weakness_recorded, weakness_ref}` |
| `replanLearningPathApi` | `POST /plans/replan` | `{available_minutes?, reason?}` | `{plan, diff:{before, after, added, moved, deferred}, rationale, refs}` |
| `getTraceEvents` | `GET /agent/events` | – | `{events:[{id, title, detail, occurredAt, agent, action, refs}]}` |

Typed client for the memory, plan and practice screens (`src/services/backend.ts`). Each function uses the
persona snapshot mock (`src/services/personaMock.ts`) when `VITE_API_BASE_URL` is empty:

| Frontend function (`src/services/backend.ts`) | Method and path | Used by |
|---|---|---|
| `getGoals` | `GET /goals` | Memory (sorted by `priority_rank`) |
| `getActivePlan` | `GET /plans` → `active` | Pipeline, Sim |
| `replanPlan(availableMinutes?, reason?)` | `POST /plans/replan` | Pipeline (budget select, before/after diff) |
| `setTaskStatus(taskId, status)` | `PATCH /plans/tasks/{id}` | Pipeline, Sim |
| `getOpportunities` | `GET /opportunities` (each item has `fit` and `target`) | Scanner, Gap Map |
| `assessStoredFit(opportunityId)` | `POST /opportunities/{id}/fit` | Scanner ("Check fit") |
| `getGaps(opportunityId)` | `POST /skills/gaps` → `{fit, gaps[]}` | Gap Map |
| `getMemoryItems` | `GET /memory` → `items` | Memory |
| `editMemoryItem(id, content)` | `PATCH /memory/{id}` | Memory |
| `deleteMemoryItem(id)` | `DELETE /memory/{id}` | Memory |
| `startPractice(topic?)` | `POST /practice/start` → `{id, question, topic, question_source}` | Sim (the `session_id` goes to `submitPracticeAnswer`) |
| `importProfile(profile)` | `POST /profile/import` | Onboarding, after `POST /profile` |
| `getBackendStatus` | `GET /admin/status` | Model chip in the header |

Backend endpoints not called by the UI (available for scripts and the OpenAPI page): `/constraints`,
`/decisions`, `/skills`, `/evidence`, `/weaknesses`, `/opportunities/search`, `/opportunities/extract`,
`/plans/{id}`, `/practice/topics`, `/practice/sessions`, `/memory/context`, `/memory/purge`,
`DELETE /memory?confirm=true`, `/actions`, `/admin/reset-demo`.

## B. AI agent endpoints (`main.py`, AI-owned)

These call Nemotron through Nebius and validate the model output against `app/schemas/*`. Without a key
(or when the model fails) `/profile`, `/opportunity`, `/fit`, `/gap` and `/suggestions` answer with offline
analysis in the same schema; the header `X-MindMate-Source: nemotron | offline` says which, and CORS exposes it
to the browser. `/plan` and `/practice` need the key. Every function returns its result with
`mindmate_source` added (`nemotron`, `offline` or `recorded`) for the screens to label.

| Frontend function | Method and path | Request | Response schema |
|---|---|---|---|
| `extractProfile` | `POST /profile` | `{user_message}` | `UserProfile`: `{education, goals[], skills[], interests[], daily_available_minutes, learning_preferences[]}` |
| `extractOpportunity` | `POST /opportunity` | `{opportunity_text}` | `OpportunitySpec`: `{opportunity_title, organization, opportunity_type, required_skills[{skill_name, importance, is_mandatory, description}], preferred_skills[], experience_level, summary}` |
| `assessFit` | `POST /fit` | `{user_profile, opportunity}` | `FitAssessment`: `{opportunity_title, overall_fit, matching_skills[], partial_matches[], missing_skills[], strengths[], improvement_areas[], summary}` |
| `getPersonalizedSuggestions` | `POST /suggestions` | `{user_profile}` | `{suggestions[12]: {title, organization, opportunity_type, category, explanation}}` |
| – | `POST /gap` | `{user_profile, opportunity, fit_assessment}` | `GapVectorJSON`: `{opportunity_title, gaps[{skill_name, career_impact_score, gap_type, missing_evidence, rationale, recommended_focus, evidence_refs[]}]}` |
| – | `POST /plan` | `{user_profile, opportunity, gap_vector, goal_id, existing_decisions[]}` (database decisions and memory IDs are added automatically) | `PlanScheduleJSON`: `{goal_id, daily_budget_minutes, total_tasks, schedule[{task_id, day_number, title, duration_minutes, priority, why_it_matters, source_refs[]}]}` |
| – | `POST /practice` | `{question, user_answer, topic}` | `PracticeEvaluation` + `{memory_saved, memory_id?, practice_ref, weakness_recorded, weakness_ref}`; the evaluation is also stored as a database practice session and the weakness thresholds apply |
| – | `GET /memories` | – | `{total, memories[]}` (legacy JSON store) |

Note the same path `/profile` serves `POST` (AI extraction) and `GET`/`PUT` (stored profile).

## C. Backend → AI interface (in-process)

The backend calls the agents as Python functions; no HTTP hop:

| Backend caller | AI function | Contract |
|---|---|---|
| `app/services/practice_service.py` | `app.agents.practice_agent.evaluate_practice(question, user_answer, topic) -> PracticeEvaluation` | Used when `MINDMATE_LLM_MODE=live` and `NEBIUS_API_KEY` is set; any exception falls back to the deterministic rubric |
| `app/services/plan_service.py` via `POST /plans` | `app.agents.planner_agent.generate_plan(user_profile, opportunity, gap_vector, goal_id, existing_decisions, existing_memories)` | Inputs built from the database (`app/services/agent_bridge.py`); memory IDs are database refs; output re-validated against the database, invalid output falls back to the deterministic planner |
| `app/services/opportunity_service.py` via `POST /opportunities/{id}/fit` | `app.agents.fit_agent.assess_fit(user_profile, opportunity)` | Coverage claims without evidence in memory are downgraded to "not shown" |
| `app/services/opportunity_service.py` via `POST /opportunities/extract` | `app.agents.opportunity_agent.extract_opportunity(opportunity_text)` | Keyword extraction fallback when the model is off or fails |
| `app/services/practice_service.py` via `POST /practice/start` | `app.agents.practice_agent.generate_practice_questions(...)` | Question bank fallback |
| `app/services/plan_service.py` via `POST /plans/replan` | `app.agents.replan_agent.explain_replan(changes, allowed_refs)` | Code-written explanation kept in `rationale_detail` and used when the agent fails |
| `POST /opportunities/{id}/fit` body `ai_assessment` | `FitAssessment` dict from `POST /fit` | Converted to requirement judgements; coverage without evidence in memory is downgraded to "not shown" |
| `POST /opportunities` | `OpportunitySpec` dict from `POST /opportunity` | Accepted directly and stored |
| `POST /memory` type `weakness`/`decision` | – | Agents may propose memory; the backend validates refs and thresholds before storing |

Model configuration lives in `app/services/llm_client.py` (`REASONING_MODEL`, `FAST_MODEL`,
`NEBIUS_BASE_URL`) and is read from the environment for the key only. The AI developer owns it.

## D. Timeouts and failure handling

* Model calls: the OpenAI client default timeout (600 s) applies; agents retry invalid JSON once with a
  repair prompt, then raise `ValueError` → the backend converts it to `422` with the message.
* Frontend: `fetch` has no timeout; network failures surface as "Could not reach the MindMate API".
  Long calls (Nemotron Ultra) can take 15–60 s; screens show loading states.
* Backend fallback: practice, fit, plan generation and opportunity extraction never fail because of the model
  (deterministic code); every call and fallback is logged (`model_call`, `model_fallback`, `model_output_rejected`).
* AI endpoints in `main.py`: offline analysis when the model is unavailable (above). With
  `MINDMATE_DEMO_CACHE=fallback` a recorded answer to the exact same request wins over offline analysis;
  `replay` never calls the model (see `docs/contracts/backend-api.md`).
* Rate limit: `RATE_LIMIT_PER_MINUTE` per client IP; `/health` and docs are exempt.

## E. Environment variables

| Variable | Component | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | frontend | Backend base URL (build-time; set in Vercel for production) |
| `NEBIUS_API_KEY` | backend/AI | Nebius Token Factory key (server-side only) |
| `NEBIUS_BASE_URL`, `MINDMATE_REASONING_MODEL`, `MINDMATE_FAST_MODEL` | AI | Optional provider and model overrides |
| `DATABASE_URL` | backend | PostgreSQL URL; empty = SQLite |
| `MINDMATE_AUTO_CREATE_SCHEMA`, `MINDMATE_AUTO_SEED` | backend | Dev conveniences; `false` in production with Alembic |
| `MINDMATE_LLM_MODE` | backend | `live` or `off` |
| `MINDMATE_DEMO_CACHE`, `MINDMATE_DEMO_CACHE_DIR` | backend | Demo fallback for the AI endpoints |
| `MINDMATE_SEED_PERSONA`, `MINDMATE_OPPORTUNITIES_FILE`, `MINDMATE_QUESTION_BANK` | backend | Swap the demo data without code changes |
| `CORS_ORIGINS` | backend | Extra allowed origins (deployed frontend) |
| `RATE_LIMIT_PER_MINUTE`, `MINDMATE_ADMIN_TOKEN` | backend | Protection |
| `WEAKNESS_*`, `PRIORITY_WEIGHT_*`, `MINDMATE_*` | backend | Tunable decision logic (`.env.example`) |

## F. Security

* Keys stay on the server; the frontend never receives `NEBIUS_API_KEY`.
* CORS allows only the configured frontend origins.
* Model output never triggers an action; permission checks (`app/permissions.py`) run in code.
* Reference IDs in any model output must exist in the database or the request is rejected.
