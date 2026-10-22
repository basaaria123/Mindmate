# Root developer commands for MindMate (works on macOS/Linux; see docs/LOCAL_SETUP.md for Windows).
.PHONY: eval smoke demo-check test-backend-postgres setup setup-backend setup-frontend dev backend frontend test test-backend test-ai test-ai-live test-frontend lint-frontend reset-demo

setup: setup-backend setup-frontend

setup-backend:
	python -m pip install -r requirements.txt
	@test -f .env || cp .env.example .env
	python scripts/reset_demo.py --seed-only

setup-frontend:
	cd mindmate-frontend && npm install
	@# Point the local frontend at the local backend (empty VITE_API_BASE_URL would mean offline mock mode).
	@test -f mindmate-frontend/.env || echo 'VITE_API_BASE_URL=http://localhost:8000' > mindmate-frontend/.env

dev:            ## start backend (8000) and frontend (5173) together
	./scripts/dev.sh

backend:
	uvicorn main:app --reload --port 8000

frontend:
	cd mindmate-frontend && npm run dev

test: test-backend test-ai test-frontend

test-backend:   ## memory layer, scoring, plans, API, migrations (no network needed)
	MINDMATE_LLM_MODE=off python -m pytest tests -q --ignore=tests/ai --ignore=tests/live

test-ai:        ## offline AI tests (tests/ai); the live agent tests in tests/live need NEBIUS_API_KEY (make test-ai-live)
	python -m pytest tests/ai -q

test-ai-live:   ## calls Nemotron on Nebius Token Factory; spends credits
	python -m pytest tests/live -q

test-frontend:
	cd mindmate-frontend && npm run lint && npm run build

lint-frontend:
	cd mindmate-frontend && npm run lint

reset-demo:
	python scripts/reset_demo.py

demo-check:     ## rehearse the scripted demo and check success criteria (in-process; add BASE_URL=... for a deployment)
	python scripts/demo_check.py $(if $(BASE_URL),--base-url $(BASE_URL),)

test-backend-postgres:  ## backend tests against PostgreSQL (docker compose up -d first)
	MINDMATE_TEST_DATABASE_URL=postgresql+psycopg://mindmate:mindmate@localhost:5432/mindmate MINDMATE_LLM_MODE=off python -m pytest tests -q --ignore=tests/ai --ignore=tests/live

eval:           ## evaluation set; add LIVE=1 to call Nemotron
	python scripts/run_eval.py $(if $(LIVE),--live,)

smoke:          ## non-destructive production smoke test: make smoke BACKEND=https://... FRONTEND=https://...
	python scripts/smoke_test.py --backend $(BACKEND) $(if $(FRONTEND),--frontend $(FRONTEND),)
