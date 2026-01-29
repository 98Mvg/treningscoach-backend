#!/bin/bash
# Stop Treningscoach Backend

echo "🛑 Stopping Treningscoach Backend..."

# Kill backend process
pkill -f "python.*main.py" 2>/dev/null && echo "✅ Backend stopped" || echo "⚠️ No backend process found"

# Kill port 10000
lsof -ti:10000 | xargs kill -9 2>/dev/null && echo "✅ Port 10000 freed" || true

sleep 1

# Verify stopped
if lsof -ti:10000 > /dev/null 2>&1; then
    echo "⚠️ Something still running on port 10000"
else
    echo "✅ Backend fully stopped"
fi
