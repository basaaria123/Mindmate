# Devpost submission pack

Everything the product lead needs to submit. Items marked "to do" need an account, a key or a person.

## Checklist (proposal section 15)

| Item | Requirement | Status |
|---|---|---|
| Working project on Nebius | Runs on Token Factory or AI Cloud with an NVIDIA open model | Code integrated with Nemotron on Token Factory; hosting files ready. **To do:** deploy (`docs/DEPLOYMENT.md`) and verify with a key. |
| Category | Personal AI | Ready |
| Project description | What, why, how | Draft below |
| Demo URL | Hosted app | **To do:** after deployment |
| Demo video | Public YouTube, 3 minutes or less, shows Token Factory and Nemotron | Script in `docs/demo-script.md`; shot list below. **To do:** record with narration and upload. |
| Public repository | Open-source license visible at the top | MIT `LICENSE` added; badge at the top of the README. **To do:** make the repository public if it is private. |
| README | Setup, where Nemotron and Token Factory are used, which track tools are really used | Done (`README.md`, "What is actually integrated") |
| Tool feedback | Nebius Token Factory, AI Cloud, NVIDIA tools | Draft below from `docs/feedback.md`. **To do:** add live latency and quality notes once a key is used. |
| Pre-existing work | Explain anything that existed before the submission period | Draft below. **To do:** confirm against the official submission period. |
| Optional | City Winner (IRL event), Tavily prize | Not applicable: no IRL event recorded; Tavily is not integrated. |

## Project description (draft)

**MindMate: it remembers why. It adapts to you. It stays yours.**

Today's assistants answer one question and forget. Students chasing an internship re-explain their goals,
time limits and history in every chat, and nothing they learn in practice changes their plan.

MindMate is a private personal agent that keeps a structured memory the user can inspect and edit: goals in
priority order, decisions with their reasons ("college exams come before GATE"), skills backed by evidence,
and weaknesses found in practice. NVIDIA Nemotron on Nebius Token Factory reads postings, judges fit,
generates interview questions, evaluates answers and explains plan changes. Deterministic code decides
everything with consequences: fit scores, gap ranking, the 14-day schedule within the user's daily time,
when a weakness is real, and what actions are allowed.

The loop is visible: a weak practice answer on model evaluation becomes a recorded weakness once there is
repeated evidence; the next replan moves model-evaluation practice to day 1, keeps it even when the time drops
from 60 to 30 minutes, and cites the weakness, the practice answers and the user's own decisions. Every item in
memory can be edited or deleted, deleted items never reach a prompt, and MindMate only drafts; the user
submits.

**How it is built:** React + Vite + TypeScript frontend; FastAPI backend with PostgreSQL, Alembic migrations
and a memory layer with reference IDs that must exist in the database; nine Nemotron agents (Ultra for
reasoning, Nano for extraction) with schema-validated JSON, one retry, then rejection; deterministic
fallbacks and recorded answers so the demo survives provider trouble.

**What's next:** live opportunity search, a daily brief job, calendar and notes integrations, and more agents
on the same memory (exam preparation, project planning).

## Video shot list (≤ 3:00)

Follow `docs/demo-script.md` scene by scene. Production notes from the proposal:

* Show Token Factory and Nemotron explicitly: the header chip reads "nemotron | nebius token factory" when the
  key is set; add one short shot of `app/services/llm_client.py` or a `model_call` event in Activity History.
* Record at 1080p; record the voice-over separately; add captions.
* Keep it under 3:00; upload as a public YouTube video; test the link in a signed-out browser.
* A silent backup recording of the full path exists (captured locally); use it only if a live take fails.

## Tool feedback (draft, from `docs/feedback.md`)

* **Nebius Token Factory.** The OpenAI-compatible endpoint meant one client library for every agent; switching
  models or endpoints is an environment variable. To add after a live run: latency for Ultra vs Nano, rate
  limits hit, credit use for the demo path.
* **NVIDIA Nemotron.** To add after a live run: JSON-schema adherence per agent (how often the retry was
  needed), quality of requirement extraction and answer grading against the evaluation set (`make eval LIVE=1`).
* **Designing around the model.** Because responses can be slow or off-schema, every model call has a
  validated schema, one repair retry, and a deterministic fallback; this kept the product demoable even
  without a key.

## Pre-existing work (draft; confirm the submission period)

The repository history starts on 10 October 2026 with the frontend starter, followed by the first agents on
12 October; all code was written by the team for this project. The 15-day plan treats 15 October as day 1.
If the official submission period began after 10 October, state: "A frontend starter (10 Oct) and early
agent prototypes (12 Oct) existed before the period; during it we built the memory layer, database,
deterministic engines, practice and replan loop, the remaining agents, the integrated screens and the
deployment setup." Use `git log --format='%cs %an %s'` to cite exact commits.
