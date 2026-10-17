# Branch workflow and file ownership

## Branches

| Branch | Purpose | Who pushes |
|---|---|---|
| `main` | Stable integration and production branch (Vercel production deploys from it) | Only through reviewed pull requests |
| `mindmate-frontend` | Frontend development | Frontend developer |
| `mindmate-backend` | Backend and memory-layer development | Backend developer |
| `mindmate-ai` | AI agents, prompts, schemas | AI developer |

Legacy branches `nishitha-mindmate-frontend` and `Kris-backend` are preserved as history; new work goes
on the three branches above. `main` was created from the latest integrated state (frontend tip plus the
backend layer), so all three branches start from identical content.

## File ownership

| Path | Owner | Notes |
|---|---|---|
| `mindmate-frontend/**` | Frontend | UI, routing, styles, assets, `src/services/api.ts` (API client), mocks, Vite/ESLint/TS config, `package.json` + lockfile, `vercel.json` |
| `main.py` | Backend (shared with AI) | AI developer owns the agent endpoints (`/profile` POST, `/opportunity`, `/fit`, `/gap`, `/plan`, `/practice` POST, `/suggestions`, `/memories`); backend owns the two `register_backend` lines and CORS. Coordinate before editing. |
| `app/api/**`, `app/db/**`, `app/memory/**`, `app/scoring/**`, `app/backend.py`, `app/config.py`, `app/permissions.py`, `app/rate_limit.py` | Backend | Routers, models, memory layer, deterministic logic |
| `app/services/*` except the two AI files | Backend | plan, practice, opportunity, seed, events, users, weakness services |
| `app/services/llm_client.py`, `app/services/memory_store.py` | AI | Nebius client, model tiering, legacy JSON memory store |
| `app/agents/**`, `app/schemas/**`, `app/utils/**`, root `test_*.py` | AI | Agents, prompts (inline today; `prompts/` when extracted), output schemas, agent tests |
| `alembic/**`, `alembic.ini`, `tests/**`, `scripts/**`, `data/*.json`, `Dockerfile`, `.dockerignore` | Backend | Migrations, backend tests, seed/reset, container |
| `requirements.txt` | Shared (backend + AI) | Announce dependency changes in the PR description |
| `.env.example`, `.gitignore`, `Makefile`, `scripts/dev.sh`, `.github/**`, `README.md`, `docs/**` | Shared | Edit through a PR that names the change in its title |
| `docs/contracts/backend-api.md`, `docs/API_CONTRACTS.md` | Shared contract | Any change needs a reviewer from each affected component |
| `.github/CODEOWNERS` | Shared | Frontend reviewer required for frontend paths; add backend/AI logins to enable the same for their paths |

### Shared-file rules

1. Edit only the files your branch owns unless the change is coordinated in the PR or in stand-up.
2. API contract changes land in `docs/API_CONTRACTS.md` (and `docs/contracts/backend-api.md`) in the same PR as the code.
3. Never replace another developer's implementation without their review; open a PR and request them.
4. Keep `main.py` edits additive: the AI endpoints and the backend registration coexist in one file.
5. Avoid unnecessary changes to `package.json`, `package-lock.json` and `requirements.txt`; when needed, say why in the PR.
6. Secrets never enter git. `.env` is ignored; only `.env.example` with placeholders is committed.
7. Resolve conflicts by merging `main` into your branch (`git merge origin/main`), never by force-pushing.

## Daily workflow

```bash
git clone https://github.com/basaaria123/Mindmate.git
cd Mindmate
git fetch origin

# first time: track your branch
git switch --track origin/mindmate-frontend     # or mindmate-backend / mindmate-ai

# every session: update your branch and pick up what landed on main
git fetch origin
git pull --ff-only
git merge origin/main                           # keeps your branch compatible with integration

# work, then commit only your files
git add <your-files>
git commit -m "Describe your change"
git push -u origin <your-branch>
```

If `git pull --ff-only` refuses because the branch diverged, run `git pull --rebase` only on your own
branch, never on a branch someone else also pushes to.

## Pull requests into `main`

1. Open a PR from your branch into `main` with a description of the change, any shared files touched, and
   any new environment variables or dependencies.
2. CI runs backend tests, offline AI tests, and the frontend build (`.github/workflows/ci.yml`).
3. Reviewers check: API compatibility with `docs/API_CONTRACTS.md`, shared-file changes, dependency updates,
   secrets, tests.
4. Merge with "Squash and merge" (short-lived branches) once checks are green and at least one review is in.
5. After the merge, every developer runs `git fetch origin && git merge origin/main` on their branch.

## GitHub settings (repository owner: `basaaria123`)

Collaborators already present: `nishithalingala-com`, `juttigaharshitha7`, `krisalynlaurel` (write).
To add or change: **Settings → Collaborators → Add people**, role **Write**.

Set the default branch to `main`: **Settings → General → Default branch → switch to `main`**.

Protect `main`: **Settings → Branches → Add branch ruleset / protection rule** for `main`:
* Require a pull request before merging (1 approval; dismiss stale approvals on new commits).
* Require status checks to pass: `Backend tests`, `AI schema and parser tests`, `Frontend lint and build`.
* Block force pushes and deletions. Optionally "Require review from Code Owners".

Branch creation never grants access; collaborator permissions are configured by the owner.
