#!/bin/bash
# Check voice generation progress

echo "=========================================="
echo "🎙️  Voice Generation Progress"
echo "=========================================="
echo ""

# Check if process is running
if pgrep -f pregenerate_phrases.py > /dev/null; then
    echo "✅ Generation is RUNNING"
    PID=$(pgrep -f pregenerate_phrases.py)
    echo "   Process ID: $PID"
else
    echo "⏸️  Generation is NOT running"
fi

echo ""

# Count cached phrases
CACHE_DIR="output/cache"
if [ -d "$CACHE_DIR" ]; then
    CACHED=$(ls "$CACHE_DIR" 2>/dev/null | wc -l | tr -d ' ')
    echo "📦 Cached phrases: $CACHED / 32"

    # Calculate percentage
    PERCENT=$((CACHED * 100 / 32))
    echo "📊 Progress: $PERCENT%"

    # Show progress bar
    printf "["
    for i in $(seq 1 32); do
        if [ $i -le $CACHED ]; then
            printf "="
        else
            printf " "
        fi
    done
    printf "] $CACHED/32\n"
else
    echo "📦 Cache not created yet"
fi

echo ""

# Show recent log entries
echo "📝 Recent activity:"
tail -5 pregenerate.log 2>/dev/null || echo "   No log file yet"

echo ""
echo "=========================================="
echo "Commands:"
echo "  Check progress: bash check_progress.sh"
echo "  Watch live:     tail -f pregenerate.log"
echo "  Stop:           pkill -f pregenerate_phrases.py"
echo "  Resume:         nohup python3 pregenerate_phrases.py >> pregenerate.log 2>&1 &"
echo "=========================================="
