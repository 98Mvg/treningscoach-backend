#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# 1) Procfile must use root Flask app
if ! grep -q "gunicorn main:app" Procfile; then
  echo "[FAIL] Procfile is not pointing to root main:app"
  exit 1
fi

# 2) backend/main.py must be compatibility shim to root
if ! grep -q "from main import app" backend/main.py; then
  echo "[FAIL] backend/main.py is not importing root main.app"
  exit 1
fi

# 3) backend/start_backend.sh must start root runtime
if ! grep -q '\$ROOT_DIR/main.py' backend/start_backend.sh; then
  echo "[FAIL] backend/start_backend.sh is not launching root main.py"
  exit 1
fi

# 4) backend runtime mirrors must be compatibility wrappers
BACKEND_RUNTIME_FILES=(
  auth.py
  auth_routes.py
  brain_router.py
  breath_analyzer.py
  breathing_timeline.py
  coaching_pipeline.py
  coaching_engine.py
  coaching_intelligence.py
  config.py
  database.py
  elevenlabs_tts.py
  chat_routes.py
  locale_config.py
  norwegian_phrase_quality.py
  persona_manager.py
  running_personalization.py
  session_manager.py
  strategic_brain.py
  user_memory.py
  voice_intelligence.py
  web_routes.py
  zone_event_motor.py
)

for file in "${BACKEND_RUNTIME_FILES[@]}"; do
  if ! grep -q "Compatibility wrapper for root" "backend/${file}"; then
    echo "[FAIL] backend/${file} is not marked as compatibility wrapper"
    exit 1
  fi
done

# 5) backend brain adapters must be compatibility wrappers
BACKEND_BRAIN_FILES=(
  base_brain.py
  claude_brain.py
  gemini_brain.py
  grok_brain.py
  openai_brain.py
)

for file in "${BACKEND_BRAIN_FILES[@]}"; do
  if ! grep -q "Compatibility wrapper for root \`brains/" "backend/brains/${file}"; then
    echo "[FAIL] backend/brains/${file} is not marked as compatibility wrapper"
    exit 1
  fi
done

echo "[OK] Root runtime source-of-truth checks passed"
