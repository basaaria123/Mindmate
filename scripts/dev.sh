#!/usr/bin/env bash
# Start the MindMate backend (FastAPI, :8000) and frontend (Vite, :5173) together.
# Stop both with Ctrl+C. Requires: Python 3.11+, Node 20+, dependencies installed
# (see docs/LOCAL_SETUP.md or `make setup`).
set -euo pipefail
cd "$(dirname "$0")/.."

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

if [ ! -f .env ]; then
  echo "No .env found; copying .env.example (edit it to add NEBIUS_API_KEY for live model calls)."
  cp .env.example .env
fi
if [ ! -f mindmate-frontend/.env ]; then
  printf 'VITE_API_BASE_URL=http://localhost:%s\n' "$BACKEND_PORT" > mindmate-frontend/.env
  echo "Created mindmate-frontend/.env pointing at the local backend."
fi

python scripts/reset_demo.py --seed-only

uvicorn main:app --reload --port "$BACKEND_PORT" &
BACKEND_PID=$!
trap 'kill "$BACKEND_PID" 2>/dev/null || true' EXIT

(cd mindmate-frontend && npm run dev -- --port "$FRONTEND_PORT")
