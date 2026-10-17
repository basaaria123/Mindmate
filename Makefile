# Root developer commands for MindMate (works on macOS/Linux; see docs/LOCAL_SETUP.md for Windows).
.PHONY: setup setup-backend setup-frontend dev backend frontend test test-backend test-ai test-frontend reset-demo

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

test-ai:        ## schema and parser tests run offline; agent tests need NEBIUS_API_KEY
	python -m pytest test_json_utils.py test_fit_schema.py test_opportunity_schema.py test_profile_schema.py -q

test-frontend:
	cd mindmate-frontend && npm run build

lint-frontend:
	cd mindmate-frontend && npm run lint

reset-demo:
	python scripts/reset_demo.py
