#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "============================================"
echo "  SCI LitLab — Starting up (BYOK base)"
echo "============================================"
echo

# Reuse the existing start.sh logic, but swap the backend entrypoint.

if ! command -v uv &>/dev/null; then
  echo "uv not found — please run ./start.sh once to install dependencies."
  exit 1
fi

echo "Installing Python packages..."
uv sync --quiet

echo "Installing frontend packages..."
(cd web && npm install --silent)

echo "Loading environment from kady_agent/.env..."
set -a
source kady_agent/.env
set +a

echo "Preparing sandbox..."
uv run python prep_sandbox.py

echo "Starting services..."

echo "  → LiteLLM proxy on port 4000"
uv run litellm --config litellm_config.yaml --port 4000 &
LITELLM_PID=$!
sleep 2

echo "  → Backend on port 8000 (FastAPI + ADK + SCI LitLab API)"
uv run uvicorn server_sci_litlab:app --reload --port 8000 &
BACKEND_PID=$!

echo "  → Frontend on port 3000 (Next.js UI)"
cd web && npm run dev &
FRONTEND_PID=$!

echo
echo "============================================"
echo "  All services running!"
echo "  UI: http://localhost:3000"
echo "  SCI LitLab API: http://localhost:8000/api/health"
echo "============================================"

trap "kill $LITELLM_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
