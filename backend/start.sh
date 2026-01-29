#!/bin/bash
#
# start.sh - Start Treningscoach FastAPI server
#

echo "🎯 Starting Treningscoach Backend..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found! Copying from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it with your ANTHROPIC_API_KEY"
    echo ""
fi

# Check if reference audio exists
if [ ! -f voices/coach_voice.wav ]; then
    echo "⚠️  Reference audio not found at voices/coach_voice.wav"
    echo "   Please add your 20-second reference audio there"
    echo ""
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "Python version: $python_version"

# Check if dependencies are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  Dependencies not installed. Installing..."
    pip install -r requirements.txt
    echo ""
fi

# Start server
echo "🚀 Starting FastAPI server on port 8000..."
echo "   Health check: http://localhost:8000/health"
echo ""

uvicorn server:app --host 0.0.0.0 --port 8000 --reload
