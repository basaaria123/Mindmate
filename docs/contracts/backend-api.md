# MindMate Backend API Contract (Backend & Memory role)

Base URL: the FastAPI server (`http://localhost:8000` locally). All bodies are JSON.
Errors always return `{"detail": "<human readable message>"}` with status `404`, `403`, `422` or `429`.

The frontend selects this API by setting `VITE_API_BASE_URL` (see `mindmate-frontend/.env.example`).
Field names the frontend already reads (`memoryNotes`, `latestPractice`, `trace`, `originalPlan`,
`updatedPlan`, `replanReason`, `occurredAt`, `targetRole`, `dailyMinutes`, ...) are kept verbatim.

The AI role's endpoints (`POST /profile`, `POST /opportunity`, `POST /fit`, `POST /gap`, `POST /plan`,
`POST /practice`, `POST /suggestions`, `GET /memories`) are unchanged and live in `main.py`.

## Reference IDs

Every claim cites a reference: `ev#4`, `skill#2`, `decision#1`, `weakness#3`, `goal#1`,
`constraint#2`, `opp#5`, `task#9`, `plan#2`, `practice#7`, `memory#12`, `fit#3`.
Unknown or deleted references are rejected with `422`. Deleted memory never appears in any
later response, prompt bundle, plan or rationale.

## Profile and goals

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/profile` | – | `{id, name, email, goal, targetRole, dailyMinutes, education, summary, allowTaskWrites, preferences, updatedAt}` |
| PUT | `/profile` | any subset of the fields above | updated profile |
| POST | `/profile/import` | Profile agent output `{education, goals[], skills[], interests[], daily_available_minutes, learning_preferences[]}` | `{added:{goals, skills, preferences}, skipped[], profile}`; idempotent; skills are stored at beginner level without evidence |
| GET | `/goals` | – | `{goals: [goal...], current_goal}` ordered by `priority_rank`; each goal has `ref, title, target_role, deadline, hours_per_day, priority_rank, parent_goal, comes_before[]` |
| POST | `/goals` | `{title, target_role?, deadline?, hours_per_day?, priority_rank?, parent_goal_id?}` | goal |
| PATCH | `/goals/{id}` | subset | goal |
| DELETE | `/goals/{id}` | – | `{deleted, ref}` (soft delete) |
| GET/POST/DELETE | `/constraints[/{id}]` | `{kind: hours|deadline|boundary, value, valid_from?, valid_to?}` | constraint |
| GET/POST/DELETE | `/decisions[/{id}]` | `{statement, reason, goal_id?}` | decision with `goal_ref` |

## Memory

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/memory` | query `include_deleted`, `type` (repeatable) | `{total, items[], memoryNotes[], latestPractice, trace[], originalPlan[], updatedPlan, replanReason}`; `memoryNotes` starts with `"Practice focus: <topic>"` for each active weakness |
| GET | `/memory/context?task=planner` | task ∈ profile, opportunity, fit, gap, planner, practice, memory, replan | the exact memory slice that task may see: `{goals, constraints, skills, evidence, decisions, weaknesses, preferences, notes, prompt_text, refs}` |
| POST | `/memory` | `{type, content, payload?, tags?, reason?, source?}` | memory item `{id, type, content, payload, source, visibility, ref, tags, createdAt, updatedAt, deletedAt}` |
| GET | `/memory/{id}` | – | memory item |
| PATCH | `/memory/{id}` | `{content?, payload?, tags?, visibility?}` | memory item (structured fields flow back to the entity) |
| DELETE | `/memory/{id}` | – | `{deleted, id, ref}` soft delete |
| POST | `/memory/purge` | – | `{purged}` permanently removes soft-deleted rows |
| DELETE | `/memory?confirm=true` | – | `{deleted, permission}`; `403` without `confirm=true` |

`POST /memory` behaviour by `type`:

* `weakness` – content `"Practice focus: <topic>"` or `<topic>`; creates/updates a weakness entity.
* `decision` – requires `reason` (the why); creates a decision.
* `goal`, `constraint`, `skill`, `evidence` – create the typed entity (`payload` carries extras such as `kind`, `level`, `skill_id`).
* `preference`, `note`, `learning_insight`, `profile` – stored as free-form memory.

## Skills, evidence, weaknesses, gaps

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/skills` | – | `{skills: [{ref, name, level, confidence, last_updated, evidence_refs[]}]}` |
| POST | `/skills` | `{name, level, confidence}` | skill |
| PATCH | `/skills/{id}` | `{level?, confidence?}` | skill |
| DELETE | `/skills/{id}` | – | soft delete |
| GET | `/evidence` | – | `{evidence: [{ref, skill_ref, type, description, url}]}` |
| POST | `/skills/{id}/evidence` or `/evidence` | `{type: project|repo|cert|internship|course|other, description, url?, skill_id?}` | evidence |
| GET | `/weaknesses` | – | `{weaknesses: [{ref, topic, severity, evidence_count, last_seen, refs[]}]}` |
| POST | `/skills/gaps` | `{opportunity_id}` | `{opportunity, fit, gaps: [{requirement, impact_score, weight, coverage, mandatory, refs, rationale, recommended_focus}]}` |

## Opportunities and fit

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/opportunities` | – | `{total, opportunities[]}` each with `fit` when assessed |
| POST | `/opportunities` | backend shape `{title, org, type, deadline, requirements:[{name, weight, mandatory}]}` **or** the Opportunity Agent's `OpportunitySpec` | opportunity |
| POST | `/opportunities/search` | `{query, limit?}` | `{query, source: "curated", results[]}` (ranked over the stored set; no live search is claimed) |
| GET | `/opportunities/{id}` | – | opportunity + `latest_fit` |
| POST | `/opportunities/{id}/fit` | optional `{judgments: [{requirement, weight, coverage, evidence_refs[], mandatory}]}` or `{ai_assessment: <FitAssessment from app/schemas/fit.py>}` | `{score, band, per_requirement[], top_gap, refs[], judged_by}` |

Fit arithmetic (`app/scoring/fit.py`): `fit% = 100 × Σ(weight × coverage) / Σ(weight)`;
weight High=3, Medium=2, Low=1; coverage not_shown=0, partial=0.5, demonstrated=1;
bands 75+ Strong, 50–74 Moderate, below 50 Weak. Any non-zero coverage must cite evidence that exists.

## Plans

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/plans` | – | `{active: plan, history[]}` |
| POST | `/plans` | `{tasks:[{title, minutes, priority, day_number?, why?, refs[], role_impact?, goal_id?, deadline?}], daily_budget_minutes?, goal_id?, rationale?, refs?, generate_from_opportunity_id?}` | plan (new version) |
| GET | `/plans/{id}` | – | plan |
| PATCH | `/plans/tasks/{id}` | `{status: todo|done|deferred|dropped}` | task |
| POST | `/plans/replan` | `{available_minutes?, reason?}` | `{plan, previous_plan_id, daily_budget_minutes, diff:{before[], after[], added[], moved[], deferred[], kept[]}, rationale, refs[]}` |

Plan shape: `{id, ref, version, status, goal, daily_budget_minutes, rationale, refs, minutes_by_day, tasks[]}`;
task: `{id, ref, title, minutes, priority, day_number, deadline, status, why, refs[], role_impact, must_keep, priority_score, goal}`.

Replan priority (`app/scoring/priority.py`):
`priority = 0.40×role_impact + 0.25×weakness_boost + 0.20×goal_hierarchy_weight + 0.15×deadline_urgency`;
`must_keep` = task tied to an active weakness or a deadline within `MINDMATE_HARD_DEADLINE_DAYS`.
The scheduler places must-keep tasks first, never exceeds the budget on any day, clips oversized tasks,
and defers (never drops) what does not fit in 14 days.

## Practice

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/practice/topics` | – | `{topics[]}` |
| GET | `/practice/sessions` | – | `{sessions[]}` |
| POST | `/practice/start` | `{topic?, question?}` | session `{id, ref, topic, question, status: "open"}` |
| POST | `/practice/evaluate` | `{answer, session_id?, question?, topic?}` | `{session_id, topic, question, answer, score, rubric_scores:{correctness, depth, clarity}, matched_concepts, missing_concepts, feedback, weakness, weakness_detail, weakness_recorded, weakness_ref, weakness_reason, evaluator, submittedAt}` |

Weakness thresholds (`app/scoring/weakness.py`): a topic becomes a weakness after
`WEAKNESS_MIN_OCCURRENCES` (default 2) answers below `WEAKNESS_SCORE_THRESHOLD` (default 60),
or one answer at or below `WEAKNESS_SEVERE_SCORE` (default 35). The seeded persona already has one
weak Model-evaluation answer, so the demo's second weak answer crosses the threshold.

## Trace, actions, admin

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/agent/events?limit=&agent=` | – | `{total, events:[{id, timestamp, agent, action, summary, refs, payload, title, detail, occurredAt}]}` |
| GET | `/actions/permissions` | – | the permission table |
| GET | `/actions` | – | `{drafts[]}` |
| POST | `/actions` | `{action, payload?, refs?, confirmed?}` | draft (`201`) or `403` with the reason |
| POST | `/actions/{id}/confirm` / `/cancel` | – | draft |
| POST | `/admin/reset-demo` | header `X-Admin-Token` when `MINDMATE_ADMIN_TOKEN` is set | `{status: "reset", ...counts}` |
| GET | `/admin/status` | – | database backend, LLM mode, thresholds, weights, row counts |

Permission levels (`app/permissions.py`): read-only (profile, opportunities, memory), optional write
(tasks only in the MVP, opt-in via `allowTaskWrites`), application actions (drafts only).
`submit_application` and `send_message` are always refused; the user submits manually.
