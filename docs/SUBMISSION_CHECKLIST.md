# Submission checklist: NVIDIA x Nebius Global AI Hackathon 2026 (Personal AI)

Status as of 22 October 2026. **DONE** = verified in the repository or by a command whose output was
seen. **NEEDS ME** = needs the team's accounts, key or a person. **[CONFIRM]** = not verifiable from the
repository; check before submitting.

| # | Requirement | Status | Evidence / what is left |
|---|---|---|---|
| 1 | Working project built with NVIDIA Nemotron on Nebius Token Factory or AI Cloud | **Code DONE; live run NEEDS ME** | Nine agents call Nemotron through Token Factory (`app/services/llm_client.py`, `app/agents/`, README "How MindMate uses NVIDIA Nemotron and Nebius"). With a key set, the backend called Token Factory with the configured model ID (wiring check, `docs/TEST_PLAN.md`). A successful live call has **not** been observed: the development sandbox blocks Token Factory and has no key. Left: deploy with your key and pass `scripts/smoke_test.sh`. |
| 2 | Category: Personal AI | **DONE** | `docs/SUBMISSION.md` → Category |
| 3 | Project description (what, why, how) | **DONE** | `docs/SUBMISSION.md` → Short and Full description; matches the README's "What is actually integrated" table |
| 4 | Working demo URL that calls Nemotron (not offline or mock) | **NEEDS ME** | Frontend is on Vercel (`https://mindmate-lyart.vercel.app`) [CONFIRM it currently builds from `main`]. Backend not deployed yet. Left: deploy the backend (`docs/DEPLOYMENT.md` §1), set `VITE_API_BASE_URL` in Vercel and redeploy (§3), then `./scripts/smoke_test.sh <backend>` must pass and the header chip must read `nemotron \| nebius token factory`. |
| 5 | Public YouTube video, 3:00 or less, showing the project working and how Token Factory and Nemotron are used | **NEEDS ME** | Script, shot list, rules, title and description ready: `docs/demo-script.md` (1:45–1:50). Left: record in live mode, upload as Public, paste the URL. |
| 6a | Public repository | **DONE** | `basaaria123/Mindmate` visibility: public (checked via the GitHub API, 22 Oct) |
| 6b | Open-source license visible at the top of the repo page | **DONE** | `LICENSE` (MIT) at the repo root; GitHub detects it as "MIT License" (GitHub API); MIT badge at the top of `README.md` |
| 6c | README with setup instructions | **DONE** | `README.md` → Quick start (`make setup`, `make dev`), verified in a fresh clone on 22 Oct after two fixes; full guide `docs/LOCAL_SETUP.md` |
| 6d | README highlights how Nemotron was used and where Token Factory accelerated the workflow, plus other Nebius tools | **DONE (one [CONFIRM])** | README → "How MindMate uses NVIDIA Nemotron and Nebius": model IDs, Ultra vs Nano per agent and why, Token Factory benefits. [CONFIRM] the Nebius AI Cloud hosting line after deploying. |
| 7 | Written feedback on Nebius Token Factory, AI Cloud and NVIDIA tools | **DRAFT DONE; [CONFIRM] lines** | `docs/feedback.md` and the summary in `docs/SUBMISSION.md`. Left: fill the [CONFIRM] lines from your live experience (speed, JSON adherence, AI Cloud deployment). |
| 8 | If the project predates the Submission Period: what was significantly updated during it | **[CONFIRM]** | `docs/SUBMISSION.md` → "Updated during the Submission Period" (first commit 2026-10-10, latest 2026-10-22, milestones by date). Left: check the period start in the Official Rules; omit the section if the period started on or before 10 Oct. |

## Supporting checks (DONE, 22 October 2026)

| Check | Result |
|---|---|
| `make test` | Backend 121 passed, offline AI 80 passed, frontend lint 0 problems, build passed |
| `make demo-check` | All demo checks passed (deterministic path, no key) |
| Secrets in working tree and full git history | None found; only `.env.example` files with empty or placeholder values were ever committed |
| `.gitignore` | Covers `.env`, `.env.*` (examples excepted) and local database files |
| Production Docker stack | Built and run: migrations on PostgreSQL 16, persona seeded once, CORS, Caddy HTTPS, restart after crash (`docs/DEPLOYMENT.md` §5) |
| Recorded-answer demo mode | Off by default in production (`docker-compose.prod.yml`, `.env.production.example`); `/health` shows it; the smoke test fails if it is on |
| `scripts/smoke_test.sh` | Fails loudly without a key and on an offline answer; passes against stubbed agents. Real run pending deployment |
