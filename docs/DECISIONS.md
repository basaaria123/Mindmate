# Decisions log

MindMate's own principle applied to the project: every decision is recorded with its reason.

| # | Decision | Reason | Date |
|---|---|---|---|
| 1 | The demo persona is Meera, a 2nd-year B.E. CSE (AI & ML) student aiming for an AI/ML internship, with exams before GATE. | It is the persona defined in the proposal (section 3.1) and the one the demo script, seed data, question bank and evaluation set are built around. The earlier medical-student placeholders in the frontend were replaced. Another persona can be loaded without code changes (`MINDMATE_SEED_PERSONA`). | 2026-10-19 |
| 2 | Backend and AI agents run in one FastAPI process; agents are a library, not a separate service. | One deployable, no extra network hop, simpler hosting. Model calls already go out to Nebius over HTTPS. | 2026-10-17 |
| 3 | Models propose; code decides. Fit, gaps, priority, budgets, weakness thresholds and permissions are deterministic. | Same inputs give the same plan; explanations can cite exact inputs; hallucinated evidence cannot change a score. | 2026-10-17 |
| 4 | A weakness is recorded only after two low answers on a topic, or one very low answer. | One bad answer is noise; the proposal requires thresholds, not single answers. | 2026-10-17 |
| 5 | A skill without evidence counts as "not shown" in fit scoring. | Evidence over assertion (proposal principle). This is why the demo fit is 67%, not an inflated number. | 2026-10-17 |
| 6 | Every model-backed path has a deterministic fallback, and recorded answers can stand in for the AI endpoints. | The live demo must survive a slow or failing provider; cached answers are labelled in the trace. | 2026-10-19 |
| 7 | PostgreSQL in production, SQLite locally; Alembic owns the production schema. | Matches the proposal's stack while keeping local setup to zero services. Both are tested in CI. | 2026-10-19 |
| 8 | Vercel hosts the frontend; the backend runs as a container on Nebius. | Vercel functions cannot hold the database or long model calls; the hackathon requires Nebius. | 2026-10-17 |
| 9 | Prompts live in versioned files under `prompts/`. | Prompt changes are reviewed like code; tests check every placeholder. | 2026-10-19 |
| 10 | Completed tasks carry into new plan versions as done. | Progress and history must survive a replan. | 2026-10-19 |
| 11 | The backend is hosted on Render (Docker web service + Render PostgreSQL); the models stay on Nebius Token Factory. Supersedes the hosting part of #8. | Managed PostgreSQL and HTTPS with no server to administer. [CONFIRM the team's reason.] | 2026-10-23 |
