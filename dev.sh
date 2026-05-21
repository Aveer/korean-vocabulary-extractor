#!/usr/bin/env bash
# Start both backend and frontend dev servers.
# Kill both when this script is stopped (Ctrl+C or kill).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

BACKEND_PORT=8000
FRONTEND_PORT=5173

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  local status="${1:-$?}"
  trap - SIGINT SIGTERM EXIT
  echo ""
  echo "Shutting down..."
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null && echo "  Backend (PID $BACKEND_PID) stopped."
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null && echo "  Frontend (PID $FRONTEND_PID) stopped."
  wait 2>/dev/null || true
  echo "Done."
  exit "$status"
}

trap 'cleanup $?' EXIT
trap 'cleanup 130' SIGINT
trap 'cleanup 143' SIGTERM

echo "Starting Korean Vocab Extractor..."
echo ""

# Start backend
echo -n "Starting backend on port $BACKEND_PORT... "
cd "$BACKEND_DIR"
source venv/bin/activate
uvicorn main:app --reload --port "$BACKEND_PORT" &
BACKEND_PID=$!
sleep 1
if kill -0 "$BACKEND_PID" 2>/dev/null; then
  echo "running (PID $BACKEND_PID)"
else
  echo "FAILED to start backend."
  exit 1
fi

# Start frontend
echo -n "Starting frontend on port $FRONTEND_PORT... "
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!
sleep 2
if kill -0 "$FRONTEND_PID" 2>/dev/null; then
  echo "running (PID $FRONTEND_PID)"
else
  echo "FAILED to start frontend."
  exit 1
fi

echo ""
echo "=========================================="
echo "  Korean Vocab Extractor is running!"
echo "=========================================="
echo "  Backend:  http://localhost:$BACKEND_PORT"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo "  API:      http://localhost:$BACKEND_PORT/api/extract-vocab"
echo "=========================================="
echo ""
echo "Press Ctrl+C to stop both servers."
echo ""

# Wait for foreground (frontend) process; cleanup handles the rest
wait "$FRONTEND_PID" 2>/dev/null
