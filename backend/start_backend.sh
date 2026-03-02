#!/bin/bash
# Start Treningscoach backend using ROOT runtime (single source of truth).

# Kill any existing backend
pkill -f "python.*main.py" 2>/dev/null || true
lsof -ti:10000 | xargs kill -9 2>/dev/null || true
sleep 2

# Resolve directories
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load environment variables from .env file
if [ -f "$ROOT_DIR/.env" ]; then
    export $(grep -v '^#' "$ROOT_DIR/.env" | xargs)
    echo "✅ Loaded environment variables from root .env"
elif [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
    echo "✅ Loaded environment variables from backend/.env"
else
    echo "⚠️ No .env file found - some features may be disabled"
fi

# Set port
export PORT=10000

# Start backend
echo "🚀 Starting Treningscoach Backend (root runtime)..."
python3 "$ROOT_DIR/main.py" > /tmp/backend.log 2>&1 &

# Wait for startup
sleep 4

# Show status
if lsof -ti:10000 > /dev/null 2>&1; then
    echo "✅ Backend is LIVE on port 10000!"
    echo ""
    echo "📊 Status:"
    tail -10 /tmp/backend.log | grep "✅"
    echo ""
    echo "🌐 URLs:"
    echo "   - Local: http://127.0.0.1:10000"
    echo "   - Network: http://192.168.10.87:10000"
    echo ""
    echo "📝 Logs: tail -f /tmp/backend.log"
    echo "🛑 Stop: ./stop_backend.sh"
else
    echo "❌ Backend failed to start"
    echo ""
    echo "📝 Last 20 log lines:"
    tail -20 /tmp/backend.log
fi
