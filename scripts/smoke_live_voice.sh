#!/bin/bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://treningscoach-backend.onrender.com}"
FREE_USER_BEARER_TOKEN="${FREE_USER_BEARER_TOKEN:-}"
PREMIUM_USER_BEARER_TOKEN="${PREMIUM_USER_BEARER_TOKEN:-}"
EXPECT_FREE_MAX_DURATION_SECONDS="${EXPECT_FREE_MAX_DURATION_SECONDS:-120}"
EXPECT_PREMIUM_MAX_DURATION_SECONDS="${EXPECT_PREMIUM_MAX_DURATION_SECONDS:-300}"
EXPECT_FREE_DAILY_LIMIT="${EXPECT_FREE_DAILY_LIMIT:-2}"
EXPECT_PREMIUM_DAILY_LIMIT="${EXPECT_PREMIUM_DAILY_LIMIT:-10}"
CHECK_DAILY_LIMITS="${CHECK_DAILY_LIMITS:-false}"
CURL_CONNECT_TIMEOUT="${CURL_CONNECT_TIMEOUT:-10}"
CURL_MAX_TIME="${CURL_MAX_TIME:-20}"

print_ok() {
  printf "[OK] %s\n" "$1"
}

print_fail() {
  printf "[FAIL] %s\n" "$1"
}

require_env() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    print_fail "Missing required env var: ${name}"
    exit 1
  fi
}

curl_checked() {
  curl --connect-timeout "${CURL_CONNECT_TIMEOUT}" --max-time "${CURL_MAX_TIME}" "$@"
}

summary_payload() {
  python3 - <<'PY'
import json

payload = {
    "language": "en",
    "summary_context": {
        "workout_label": "Intervals",
        "workout_mode": "interval",
        "duration_text": "32:10",
        "final_heart_rate_text": "153 BPM",
        "coach_score": 91,
        "coach_score_summary_line": "Strong finish with stable pacing.",
        "zone_time_in_target_pct": 0.78,
        "zone_overshoots": 1,
    },
}
print(json.dumps(payload, separators=(",", ":")))
PY
}

auth_me_json() {
  local token="$1"
  curl_checked -sf "${BASE_URL}/auth/me" \
    -H "Authorization: Bearer ${token}"
}

voice_session_json() {
  local token="$1"
  local payload="$2"
  curl_checked -sf -X POST "${BASE_URL}/voice/session" \
    -H "Authorization: Bearer ${token}" \
    -H "Content-Type: application/json" \
    -d "${payload}"
}

voice_session_status() {
  local token="$1"
  local payload="$2"
  local tmp_body
  tmp_body="$(mktemp)"
  local status
  status="$(curl_checked -s -o "${tmp_body}" -w "%{http_code}" -X POST "${BASE_URL}/voice/session" \
    -H "Authorization: Bearer ${token}" \
    -H "Content-Type: application/json" \
    -d "${payload}")"
  printf "%s\n%s\n" "${status}" "${tmp_body}"
}

assert_auth_tier() {
  local json="$1"
  local expected_tier="$2"
  python3 - <<'PY' "${json}" "${expected_tier}"
import json
import sys

payload = json.loads(sys.argv[1])
expected_tier = sys.argv[2]
actual_tier = payload.get("user", {}).get("subscription_tier")
assert actual_tier == expected_tier, payload
PY
}

assert_voice_bootstrap() {
  local json="$1"
  local expected_subscription_tier="$2"
  local expected_access_tier="$3"
  local expected_duration="$4"
  local expected_daily_limit="$5"
  python3 - <<'PY' "${json}" "${expected_subscription_tier}" "${expected_access_tier}" "${expected_duration}" "${expected_daily_limit}"
import json
import sys

payload = json.loads(sys.argv[1])
expected_subscription_tier = sys.argv[2]
expected_access_tier = sys.argv[3]
expected_duration = int(sys.argv[4])
expected_daily_limit = int(sys.argv[5])

assert payload.get("voice") == "Rex", payload
assert payload.get("websocket_url", "").startswith("wss://"), payload
assert payload.get("client_secret"), payload
assert payload.get("voice_session_id"), payload
assert payload.get("subscription_tier") == expected_subscription_tier, payload
assert payload.get("voice_access_tier") == expected_access_tier, payload
assert int(payload.get("max_duration_seconds")) == expected_duration, payload
assert int(payload.get("daily_session_limit")) == expected_daily_limit, payload
assert payload.get("session_update_json"), payload
PY
}

assert_rate_limited() {
  local status="$1"
  local body_path="$2"
  python3 - <<'PY' "${status}" "${body_path}"
import json
import pathlib
import sys

status = sys.argv[1]
body = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
payload = json.loads(body)
assert status == "429", status
assert payload.get("error") == "Rate limit exceeded", payload
PY
}

echo "=== Coachi Live Voice Smoke Test ==="
echo "Base URL: ${BASE_URL}"

require_env "FREE_USER_BEARER_TOKEN"
require_env "PREMIUM_USER_BEARER_TOKEN"

payload="$(summary_payload)"

free_me="$(auth_me_json "${FREE_USER_BEARER_TOKEN}")"
assert_auth_tier "${free_me}" "free"
print_ok "Free user /auth/me returns free tier"

premium_me="$(auth_me_json "${PREMIUM_USER_BEARER_TOKEN}")"
assert_auth_tier "${premium_me}" "premium"
print_ok "Premium user /auth/me returns premium tier"

free_voice="$(voice_session_json "${FREE_USER_BEARER_TOKEN}" "${payload}")"
assert_voice_bootstrap "${free_voice}" "free" "free" "${EXPECT_FREE_MAX_DURATION_SECONDS}" "${EXPECT_FREE_DAILY_LIMIT}"
print_ok "Free user /voice/session returns live bootstrap with free limits"

premium_voice="$(voice_session_json "${PREMIUM_USER_BEARER_TOKEN}" "${payload}")"
assert_voice_bootstrap "${premium_voice}" "premium" "premium" "${EXPECT_PREMIUM_MAX_DURATION_SECONDS}" "${EXPECT_PREMIUM_DAILY_LIMIT}"
print_ok "Premium user /voice/session returns live bootstrap with premium limits"

if [ "${CHECK_DAILY_LIMITS}" = "true" ]; then
  echo "Daily limit verification is enabled; this will consume real session quota."

  free_attempt=1
  while [ "${free_attempt}" -lt "${EXPECT_FREE_DAILY_LIMIT}" ]; do
    voice_session_json "${FREE_USER_BEARER_TOKEN}" "${payload}" >/dev/null
    free_attempt=$((free_attempt + 1))
  done
  mapfile -t free_limit_probe < <(voice_session_status "${FREE_USER_BEARER_TOKEN}" "${payload}")
  assert_rate_limited "${free_limit_probe[0]}" "${free_limit_probe[1]}"
  rm -f "${free_limit_probe[1]}"
  print_ok "Free user daily live voice limit returns HTTP 429"

  premium_attempt=1
  while [ "${premium_attempt}" -lt "${EXPECT_PREMIUM_DAILY_LIMIT}" ]; do
    voice_session_json "${PREMIUM_USER_BEARER_TOKEN}" "${payload}" >/dev/null
    premium_attempt=$((premium_attempt + 1))
  done
  mapfile -t premium_limit_probe < <(voice_session_status "${PREMIUM_USER_BEARER_TOKEN}" "${payload}")
  assert_rate_limited "${premium_limit_probe[0]}" "${premium_limit_probe[1]}"
  rm -f "${premium_limit_probe[1]}"
  print_ok "Premium user daily live voice limit returns HTTP 429"
fi

echo "=== Live Voice Smoke Test Passed ==="
