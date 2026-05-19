#!/usr/bin/env bash
set -e

cd "$(git rev-parse --show-toplevel)"
DASHBOARD_DIR="tools/dashboard"
BACKEND_DIR="$DASHBOARD_DIR/backend"
FRONTEND_DIR="$DASHBOARD_DIR/frontend"

ACTION="${1:-start}"

case "$ACTION" in
    start)
        if [ ! -d "$FRONTEND_DIR/dist" ]; then
            echo "Building frontend..."
            cd "$FRONTEND_DIR" && npm run build && cd -
        fi
        PORT="${DASHBOARD_PORT:-8501}"
        echo "Starting dashboard on http://localhost:$PORT"
        cd "$BACKEND_DIR" && python -m uvicorn app:app --host 0.0.0.0 --port "$PORT" &
        echo "Dashboard PID: $!"
        ;;
    stop)
        pkill -f "uvicorn app:app" 2>/dev/null && echo "Dashboard stopped" || echo "No dashboard running"
        ;;
    rebuild)
        echo "Rebuilding frontend..."
        cd "$FRONTEND_DIR" && npm run build
        echo "Frontend rebuilt. Restart dashboard with: bash $0 start"
        ;;
    *)
        echo "Usage: $0 [start|stop|rebuild]"
        exit 1
        ;;
esac
