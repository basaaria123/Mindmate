# Test plan and results

Success criteria from the proposal (section 3.3) and how each is verified. Results below were produced on
`main` on 19 October 2026 in the development environment, without a Nebius key.

## Success criteria

| # | Criterion | How it is checked | Automated in |
|---|---|---|---|
| 1 | A recorded weakness changes the next plan's priorities | Weak answer, replan, assert the model-evaluation task moves to day 1 and the rationale cites the weakness | `tests/test_loop.py`, `scripts/demo_check.py`, browser walkthrough |
| 2 | Cutting time from 60 to 30 minutes gives a valid reduced plan | No day above 30 minutes; must-keep tasks survive; completed tasks carry over | `tests/test_budget.py`, `tests/test_scheduler.py`, `scripts/demo_check.py` |
| 3 | Every recommendation cites memory | References must exist in the database; agent output citing unknown references is rejected | `tests/test_agent_bridge.py`, `test_agents_offline.py`, `tests/test_api.py` |
| 4 | Every memory item is viewable, editable and deletable; deleted items never reach prompts | API and UI edit/delete; prompt bundles exclude deleted items | `tests/test_memory_control.py`, browser walkthrough |
| 5 | No irreversible action without confirmation | Submissions and messages refused; drafts only; delete-all needs confirmation | `tests/test_permissions.py` |
| 6 | Invalid model output is retried once, then rejected | Every agent with a fake client: valid, invalid-then-valid, invalid twice | `test_agents_offline.py` |
| 7 | Replan fast enough for a live demo (target 15 s) | Timed scripted path | `scripts/demo_check.py` (replan ≈ 0.03 s deterministic; the optional Replanning agent adds one Nemotron call) |

## Results (19 October 2026)

| Check | Result |
|---|---|
| Backend tests on SQLite | 114 passed (includes the offline-analysis tests) |
| Backend tests on PostgreSQL 16 | 106 passed locally before the offline-analysis change; CI runs the full suite on PostgreSQL on every push |
| Offline AI tests (agents with a fake client, prompts, schemas, memory agent, model config) | 80 passed |
| Evaluation set, deterministic path | Practice labels 10/10; requirement extraction precision 1.00, recall 1.00 |
| Demo rehearsal (`scripts/demo_check.py`) | All checks passed |
| Migrations vs models on PostgreSQL | No differences |
| Frontend lint and production build | 0 problems; build passes |
| Browser walkthrough, API mode (every screen and key interaction) | 20 of 20 checks passed, no HTTP or console errors |
| Browser walkthrough, offline mock mode | 7 of 7 checks passed |
| Opportunities screen without a key: analyse a pasted posting, assess fit, suggestions | 10 of 10 checks in mock mode (no network calls) and 10 of 10 against the backend without a key (`X-MindMate-Source: offline`) |
| Browser and backend offline analysis give the same result | Identical on 3 postings, 2 profiles and 6 fits; suggestion order can differ on ties |
| Phone width (390 px), every screen | No horizontal scrolling |
| Production smoke test against local backend and nginx-served frontend | 11 of 12; the failure is "Nemotron configured", correct without a key |
| Live Nemotron agent tests (`make test-ai-live`) | Not run: no Nebius key in the development environment |
| Evaluation set with live agents (`make eval LIVE=1`) | Not run: no Nebius key |
| Deployed app | Not tested: not deployed yet (see `docs/DEPLOYMENT.md`) |

## Still to run before submission (needs a key or the deployment)

1. `make test-ai-live` and `make eval LIVE=1` with `NEBIUS_API_KEY` set; record the numbers here.
2. One run with `MINDMATE_DEMO_CACHE=record` to replace the hand-written recorded answers with real ones.
3. `python scripts/smoke_test.py` and `python scripts/demo_check.py --base-url` against the hosted URLs.
4. Three demo rehearsals on the deployed app (plan days 11, 13, 14).
