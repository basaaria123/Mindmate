# Root developer commands for MindMate (works on macOS/Linux; see docs/LOCAL_SETUP.md for Windows).
.PHONY: setup setup-backend setup-frontend dev backend frontend test test-backend test-ai test-ai-live test-frontend lint-frontend reset-demo

setup: setup-backend setup-frontend

setup-backend:
	python -m pip install -r requirements.txt
	@test -f .env || cp .env.example .env
	python scripts/reset_demo.py --seed-only

setup-frontend:
	cd mindmate-frontend && npm install
	@test -f mindmate-frontend/.env || cp mindmate-frontend/.env.example mindmate-frontend/.env

dev:            ## start backend (8000) and frontend (5173) together
	./scripts/dev.sh

backend:
	uvicorn main:app --reload --port 8000

frontend:
	cd mindmate-frontend && npm run dev

test: test-backend test-ai test-frontend

test-backend:   ## memory layer, scoring, plans, API, migrations (no network needed)
	MINDMATE_LLM_MODE=off python -m pytest tests -q

test-ai:        ## all offline AI tests; the five live agent tests need NEBIUS_API_KEY (make test-ai-live)
	python -m pytest . -q --ignore=tests --ignore=mindmate-frontend --ignore=test_setup.py --ignore=test_model_selection.py --ignore=test_profile_agent.py --ignore=test_opportunity_agent.py --ignore=test_fit_agent.py

test-ai-live:   ## calls Nemotron on Nebius Token Factory; spends credits
	python -m pytest test_setup.py test_model_selection.py test_profile_agent.py test_opportunity_agent.py test_fit_agent.py -q

test-frontend:
	cd mindmate-frontend && npm run build

lint-frontend:
	cd mindmate-frontend && npm run lint

reset-demo:
	python scripts/reset_demo.py
