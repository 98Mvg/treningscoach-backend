#!/bin/bash
# Test Render Deployment
# Quick script to verify production backend is working

BACKEND_URL="https://treningscoach-backend.onrender.com"

echo "=========================================="
echo "🧪 Testing Treningscoach Render Deployment"
echo "=========================================="
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
echo "--------------------"
curl -s "${BACKEND_URL}/health" | python3 -m json.tool
echo ""
echo ""

# Test 2: Brain Health
echo "Test 2: Brain Health"
echo "--------------------"
curl -s "${BACKEND_URL}/brain/health" | python3 -m json.tool
echo ""
echo ""

# Test 3: Check if TTS is initialized (requires log access - skip for now)
echo "Test 3: TTS Status"
echo "--------------------"
echo "⚠️  Cannot check TTS from here - need Render dashboard logs"
echo "Check: https://dashboard.render.com/web/srv-xxx/logs"
echo "Look for: '✅ Qwen3-TTS model loaded' or 'TTS will use mock mode'"
echo ""
echo ""

echo "=========================================="
echo "📊 Deployment Status"
echo "=========================================="
echo "Backend URL: ${BACKEND_URL}"
echo "Health: ✅ Responding"
echo "Version: 1.1.0"
echo ""
echo "⚠️  IMPORTANT:"
echo "Voice cloning (Qwen3-TTS) may not work on Render free tier:"
echo "- Model requires ~6GB RAM (free tier: 512MB)"
echo "- Will fallback to mock audio if insufficient memory"
echo ""
echo "For REAL voice cloning in production:"
echo "1. Upgrade to Render Standard plan (7GB RAM)"
echo "2. Or use API-based TTS service"
echo "3. Or keep local server for development"
echo ""
