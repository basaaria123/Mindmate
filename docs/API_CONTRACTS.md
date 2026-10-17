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
| `getMemory` / `getDemoState` | `GET /memory` | – | `{items[], memoryNotes[], latestPractice, trace[], originalPlan[], updatedPlan, replanReason}` |
| `addMemoryEntry` / `saveWeaknessToMemoryApi` | `POST /memory` | `{type, content, payload?, reason?}` | `{id, type, content, createdAt, ref, ...}` |
| `submitPracticeAnswer` | `POST /practice/evaluate` | `{answer, session_id?, question?, topic?}` | `{answer, score, weakness, feedback, submittedAt, rubric_scores, missing_concepts, weakness_recorded, weakness_ref}` |
| `replanLearningPathApi` | `POST /plans/replan` | `{available_minutes?, reason?}` | `{plan, diff:{before, after, added, moved, deferred}, rationale, refs}` |
| `getTraceEvents` | `GET /agent/events` | – | `{events:[{id, title, detail, occurredAt, agent, action, refs}]}` |

Other backend endpoints (not yet used by the UI): `/goals`, `/constraints`, `/decisions`, `/skills`,
`/evidence`, `/weaknesses`, `/skills/gaps`, `/opportunities`, `/opportunities/search`,
`/opportunities/{id}/fit`, `/plans`, `/plans/{id}`, `PATCH /plans/tasks/{id}`, `/practice/start`,
`/practice/topics`, `/practice/sessions`, `/memory/context`, `/memory/{id}` (GET/PATCH/DELETE),
`/memory/purge`, `DELETE /memory?confirm=true`, `/actions`, `/admin/status`, `/admin/reset-demo`.

## B. AI agent endpoints (`main.py`, AI-owned)

These call Nemotron through Nebius and validate the model output against `app/schemas/*`.
They require `NEBIUS_API_KEY` on the backend and fail with `500`/`422` without it.

| Frontend function | Method and path | Request | Response schema |
|---|---|---|---|
| `extractProfile` | `POST /profile` | `{user_message}` | `UserProfile`: `{education, goals[], skills[], interests[], daily_available_minutes, learning_preferences[]}` |
| `extractOpportunity` | `POST /opportunity` | `{opportunity_text}` | `OpportunitySpec`: `{opportunity_title, organization, opportunity_type, required_skills[{skill_name, importance, is_mandatory, description}], preferred_skills[], experience_level, summary}` |
| `assessFit` | `POST /fit` | `{user_profile, opportunity}` | `FitAssessment`: `{opportunity_title, overall_fit, matching_skills[], partial_matches[], missing_skills[], strengths[], improvement_areas[], summary}` |
| `getPersonalizedSuggestions` | `POST /suggestions` | `{user_profile}` | `{suggestions[12]: {title, organization, opportunity_type, category, explanation}}` |
| – | `POST /gap` | `{user_profile, opportunity, fit_assessment}` | `GapVectorJSON`: `{opportunity_title, gaps[{skill_name, career_impact_score, gap_type, missing_evidence, rationale, recommended_focus, evidence_refs[]}]}` |
| – | `POST /plan` | `{user_profile, opportunity, gap_vector, goal_id, existing_decisions[]}` | `PlanScheduleJSON`: `{goal_id, daily_budget_minutes, total_tasks, schedule[{task_id, day_number, title, duration_minutes, priority, why_it_matters, source_refs[]}]}` |
| – | `POST /practice` | `{question, user_answer, topic}` | `PracticeEvaluation` + `{memory_saved, memory_id?}` |
| – | `GET /memories` | – | `{total, memories[]}` (legacy JSON store) |

Note the same path `/profile` serves `POST` (AI extraction) and `GET`/`PUT` (stored profile).

## C. Backend → AI interface (in-process)

The backend calls the agents as Python functions; no HTTP hop:

| Backend caller | AI function | Contract |
|---|---|---|
| `app/services/practice_service.py` | `app.agents.practice_agent.evaluate_practice(question, user_answer, topic) -> PracticeEvaluation` | Used when `MINDMATE_LLM_MODE=live` and `NEBIUS_API_KEY` is set; any exception falls back to the deterministic rubric |
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
* Backend fallback: practice evaluation never fails because of the model (deterministic rubric).
* Rate limit: `RATE_LIMIT_PER_MINUTE` per client IP; `/health` and docs are exempt.

## E. Environment variables

| Variable | Component | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | frontend | Backend base URL (build-time; set in Vercel for production) |
| `NEBIUS_API_KEY` | backend/AI | Nebius Token Factory key (server-side only) |
| `DATABASE_URL` | backend | PostgreSQL URL; empty = SQLite |
| `MINDMATE_AUTO_CREATE_SCHEMA`, `MINDMATE_AUTO_SEED` | backend | Dev conveniences; `false` in production with Alembic |
| `MINDMATE_LLM_MODE` | backend | `live` or `off` |
| `CORS_ORIGINS` | backend | Extra allowed origins (deployed frontend) |
| `RATE_LIMIT_PER_MINUTE`, `MINDMATE_ADMIN_TOKEN` | backend | Protection |
| `WEAKNESS_*`, `PRIORITY_WEIGHT_*`, `MINDMATE_*` | backend | Tunable decision logic (`.env.example`) |

## F. Security

* Keys stay on the server; the frontend never receives `NEBIUS_API_KEY`.
* CORS allows only the configured frontend origins.
* Model output never triggers an action; permission checks (`app/permissions.py`) run in code.
* Reference IDs in any model output must exist in the database or the request is rejected.
