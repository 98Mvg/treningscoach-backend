#!/bin/bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://treningscoach-backend.onrender.com}"
EXPECT_APP_STORE_URL="${EXPECT_APP_STORE_URL:-}"
EXPECT_GOOGLE_PLAY_URL="${EXPECT_GOOGLE_PLAY_URL:-}"
CURL_CONNECT_TIMEOUT="${CURL_CONNECT_TIMEOUT:-10}"
CURL_MAX_TIME="${CURL_MAX_TIME:-20}"

print_ok() {
  printf "[OK] %s\n" "$1"
}

print_fail() {
  printf "[FAIL] %s\n" "$1"
}

curl_checked() {
  curl --connect-timeout "${CURL_CONNECT_TIMEOUT}" --max-time "${CURL_MAX_TIME}" "$@"
}

echo "=== Coachi Release Check ==="
echo "Base URL: ${BASE_URL}"

# 0) Runtime source-of-truth guard (local repo check)
./scripts/check_root_runtime.sh
print_ok "Root runtime source-of-truth guard passed"

# 0b) CODEBASE_GUIDE sync guard (local repo check)
python3 ./scripts/generate_codebase_guide.py --check
print_ok "CODEBASE_GUIDE sync guard passed"

# 1) Health endpoint
health_json="$(curl_checked -sf "${BASE_URL}/health")"
python3 - <<'PY' "$health_json"
import json
import sys
payload = json.loads(sys.argv[1])
assert payload.get("status") == "healthy", payload
assert payload.get("version"), payload
assert isinstance(payload.get("quality_guards"), dict), payload
for key in ("validation_checks", "validation_failures", "timeline_overrides", "language_guard_rewrites"):
    assert key in payload["quality_guards"], payload
PY
print_ok "Health endpoint returned healthy status"

# 2) Continuous coaching contract (expects audio -> should reject empty request)
continuous_status="$(curl_checked -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/coach/continuous")"
if [ "${continuous_status}" = "400" ]; then
  print_ok "Continuous coaching endpoint rejects invalid payload with 400"
else
  print_fail "Continuous coaching endpoint returned ${continuous_status} (expected 400)"
  exit 1
fi

# 3) Waitlist insert works (persistent lead capture)
waitlist_email="releasecheck-$(date +%s)-$RANDOM@test.invalid"
waitlist_json="$(curl_checked -sf -X POST "${BASE_URL}/waitlist" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${waitlist_email}\",\"language\":\"no\",\"source\":\"release_check\"}")"
python3 - <<'PY' "$waitlist_json"
import json
import sys
payload = json.loads(sys.argv[1])
assert payload.get("success") is True, payload
PY
print_ok "Waitlist capture endpoint accepted signup"

# 4) Welcome TTS smoke check (NO)
welcome_json="$(curl_checked -sf "${BASE_URL}/welcome?language=no&persona=personal_trainer")"
python3 - <<'PY' "$welcome_json"
import json
import sys
payload = json.loads(sys.argv[1])
assert payload.get("text"), payload
assert payload.get("audio_url"), payload
PY
print_ok "Welcome endpoint returned text + audio"

# 5) Landing page CTA instrumentation
landing_html="$(curl_checked -sf "${BASE_URL}/")"
printf "%s" "$landing_html" | grep -q 'data-landing-event="app_store_click"'
printf "%s" "$landing_html" | grep -q 'data-landing-event="google_play_click"'
printf "%s" "$landing_html" | grep -q 'data-landing-event="android_early_access_click"'
print_ok "Landing page includes tracked download CTAs"

if [ -n "${EXPECT_APP_STORE_URL}" ]; then
  printf "%s" "$landing_html" | grep -q "${EXPECT_APP_STORE_URL}"
  print_ok "Landing page includes expected App Store URL"
fi

if [ -n "${EXPECT_GOOGLE_PLAY_URL}" ]; then
  printf "%s" "$landing_html" | grep -q "${EXPECT_GOOGLE_PLAY_URL}"
  print_ok "Landing page includes expected Google Play URL"
fi

echo "=== Release Check Passed ==="
