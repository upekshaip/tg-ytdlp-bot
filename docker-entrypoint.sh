#!/bin/bash
set -e

# Cleanup handler for termination signals
cleanup() {
    echo "Termination signal received, stopping processes..."
    kill $BOT_PID $DASHBOARD_PID 2>/dev/null || true
    wait $BOT_PID $DASHBOARD_PID 2>/dev/null || true
    exit 0
}

# Install signal handlers
trap cleanup SIGTERM SIGINT

# Read dashboard port from config (default: 5555)
DASHBOARD_PORT=$(python -c "from CONFIG.config import Config; print(getattr(Config, 'DASHBOARD_PORT', 5555))" 2>/dev/null || echo "5555")

# Start the bot in background
echo "Starting Telegram bot..."
python magic.py &
BOT_PID=$!

# Start the dashboard in background
echo "Starting dashboard on port ${DASHBOARD_PORT}..."
python -m uvicorn web.dashboard_app:app --host 0.0.0.0 --port ${DASHBOARD_PORT} &
DASHBOARD_PID=$!

echo "Bot and dashboard started"
echo "Dashboard is available at http://localhost:${DASHBOARD_PORT}"

# Wait for processes to exit
wait $BOT_PID $DASHBOARD_PID
