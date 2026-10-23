# Devpost submission pack

Ready to paste. Replace every `[PLACEHOLDER]` and resolve every **[CONFIRM]** before submitting.
Requirement-by-requirement status: `docs/SUBMISSION_CHECKLIST.md`.

---

## Project name and tagline

**MindMate**
*It remembers why. It adapts to you. It stays yours.*

## Category

Personal AI

## Short description

MindMate is a private personal AI agent for students chasing an internship. It keeps an editable memory of
your goals, decisions, skills and weaknesses, and uses NVIDIA Nemotron on Nebius Token Factory to evaluate
your practice and rebuild your study plan when your time or results change, citing the memory behind every
change.

## Full description

### What it does

MindMate keeps a structured memory that you can see, edit and delete: goals in priority order, decisions
with their reasons ("college exams come before GATE"), skills backed by evidence, and weaknesses found in
practice. From that memory it:

- extracts the requirements of an internship or job posting you paste, and scores your fit against the
  evidence you actually have (a skill without evidence counts as "not shown");
- ranks your skill gaps and builds a 14-day plan that fits your daily time;
- runs mock-interview practice and evaluates your answers;
- records a weakness only after repeated evidence (two low answers, or one very low answer), never from a
  single answer;
- replans when your time or results change. Drop from 60 to 30 minutes a day and the plan is re-fitted;
  record a weakness and practice on it moves to day 1. Every replan explains what moved and cites the
  memory items that caused it.

You can also ask the AI Assistant anything about your studies; it answers from your memory and plan.
Every memory item can be edited or deleted, deleted items never reach a prompt, and MindMate only drafts:
it never submits anything for you. The AI Activity page shows every model call with the agent, the
Nemotron model and how long it took.

### Why I built it

Today's assistants answer one question and forget. A student preparing for an internship re-explains their
goals, time limits and history in every chat, and nothing they learn in practice changes their plan. We
wanted an assistant that remembers *why* (the reasons behind your decisions), adapts when your situation
changes, and stays yours: inspectable, editable, and never acting on your behalf without you.

### How it works

- **Ten NVIDIA Nemotron agents on Nebius Token Factory.** Nemotron 3 Nano
  (`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`) handles extraction: profile, opportunity, suggestions.
  Nemotron 3 Ultra (`nvidia/Nemotron-3-Ultra-550b-a55b`) handles judgement over your memory: fit, skill
  gaps, planning, practice evaluation, practice questions and replan explanations. The AI Assistant chat
  answers questions grounded in your memory on Nano, or on Ultra with "Think harder". All agents share one
  OpenAI-compatible Token Factory endpoint.
- **Models propose, code decides.** Fit scores, gap ranking, replan priority, the budget scheduler,
  weakness thresholds and permissions are deterministic code, so the same inputs give the same plan.
  Agent output is validated before use: JSON must match a schema (one retry with the validation error,
  then rejection), and cited memory IDs must exist in the database.
- **Memory layer.** FastAPI with PostgreSQL (SQLite locally) and Alembic migrations; every memory item has
  a reference ID (`goal#1`, `weakness#1`, `decision#2`) that explanations cite.
- **Honest failure handling.** If Nemotron is unavailable, each path falls back to deterministic logic and
  the screen says so ("offline analysis") instead of passing it off as model output.
- **Hosting.** React, TypeScript and Vite frontend on Vercel; the backend runs as a Docker web service on
  Render with a Render PostgreSQL database; the models run on Nebius Token Factory, so we host no GPUs.

### Challenges

- **Making model output safe to act on.** Free-text JSON can be malformed or invent references, so every
  agent validates its output and the backend rejects citations of memory that does not exist.
- **Keeping decisions reproducible.** We moved every number that changes the plan into code and use the
  model for judgement and explanation, so a replan can always say exactly which inputs caused it.
- **Not hiding failures.** We had to design fallbacks that keep the app usable without the model while
  labelling those answers clearly, and added a smoke test that fails if a deployment answers offline.
- **Matching skills honestly.** Our evaluation set caught our own matcher crediting "Deep learning" for
  "Machine learning fundamentals" and "Java" for "JavaScript"; we fixed it before scoring anyone.

### What's next

Live opportunity search, a daily brief, calendar and notes integrations, and more agents on the same memory
(exam preparation, project planning). None of these are in the current build.

## Built with

NVIDIA Nemotron 3 Ultra · NVIDIA Nemotron 3 Nano · Nebius Token Factory · Python · FastAPI · Pydantic · SQLAlchemy · Alembic · PostgreSQL · SQLite · OpenAI Python SDK
(as the Token Factory client) · React · TypeScript · Vite · Tailwind CSS · Docker · Docker Compose · Caddy ·
Vercel · Render · GitHub Actions

## Links

- Repository: https://github.com/basaaria123/Mindmate (must be **public**) [CONFIRM visibility]
- Live demo: https://mindmate-lyart.vercel.app
- Backend API: https://mindmate-backend-yw5d.onrender.com (health: https://mindmate-backend-yw5d.onrender.com/health)
- Demo video: [YOUTUBE_URL] (public, 3:00 or less)

## Feedback on Nebius and NVIDIA tools

Full notes: `docs/feedback.md`. Summary to paste:

> Nebius Token Factory's OpenAI-compatible API let us run ten Nemotron agents from one FastAPI backend:
> one client, one base URL, models chosen by environment variable, no GPUs or model hosting, and offline
> tests with a fake client. We used Nemotron 3 Nano for fast extraction and Nemotron 3 Ultra for judgement
> over the user's memory, with deterministic code making the final decisions. We would like clearer
> per-model guidance on structured JSON output, and per-request usage and latency we could log alongside
> our own traces. [CONFIRM: one sentence on your observed Ultra vs Nano speed and quality.]

## Updated during the Submission Period

Only needed if the project existed before the Submission Period. The Submission Period started on
**[CONFIRM: start date from the Official Rules]**. The repository's first commit is **2026-10-10** and the
latest is **2026-10-22** (`git log --reverse --format='%h %ad %s' --date=short`).

If the period started on or before 10 October 2026, everything below was built during it and this section
can be omitted. If it started later, paste this, keeping only the dates before the start:

> The repository began on 10 October 2026. Before [START DATE] it contained: a frontend starter
> (10 Oct, `d2a797e`), a first profile-extraction agent (11 Oct, `d77a934`), early agents and their
> API (12 Oct, `f09d657`, `24043c6`), and a first frontend connection to that API (14 Oct, `1675a79`).
> Significantly updated during the Submission Period:
> - personalised suggestions agent (15 Oct) and memory integration for the agents (16 Oct);
> - the backend memory layer: database schema, memory APIs, deterministic fit, gap, priority and
>   weakness engines, and the replan engine (17 Oct, `77f5350`);
> - the remaining Nemotron agents and their tests (18–19 Oct): planner, practice evaluation, practice
>   question generation and replan explanation, with versioned prompts (`47b4cbb`, `f66e052`);
> - agent orchestration over database memory, PostgreSQL support, and integration of every screen with
>   real data, including memory edit and delete and the before/after plan diff (19 Oct);
> - production deployment (Docker, migrations on start; backend on Render with PostgreSQL), a live smoke
>   test, and model and latency logging for every Nemotron call (22 Oct onwards).
