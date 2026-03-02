# Coachi Architecture Source of Truth

Last verified: 2026-02-19
Repository: `/Users/mariusgaarder/Documents/treningscoach`
Verification basis: runtime code (`main.py`, `auth_routes.py`, iOS app), route map from Flask `url_map`, and latest commits/session learnings.

---

## 1) Product and Business Scope

Coachi is a real-time AI workout coaching product. The primary user experience is continuous voice coaching during workouts, driven by backend breath/audio analysis and AI routing, with multilingual output and persona control.

Primary user groups:
- iOS app users doing live workouts
- web visitors trying a live demo and joining waitlist

Implemented user flows:
- onboarding -> workout launch -> continuous coaching loop
- wake-word/talk-to-coach during active workout
- optional account/profile flows (`/auth/*`)
- workout history save/read (`/workouts`)
- landing page conversion flow (`/`, `/waitlist`, `/analytics/event`)

Not fully implemented yet:
- production billing/subscription backend flow
- production-grade waitlist persistence (current implementation is in-memory)
- fully integrated native auth SDK flows in iOS (`AuthManager` still uses placeholder tokens for provider sign-in calls)

---

## 2) Stack and Runtime Entry Points

Backend stack:
- Python 3.11
- Flask app served by Gunicorn in production
- SQLAlchemy for DB models
- librosa/scipy/numpy DSP path for breath analysis
- ElevenLabs cloud TTS
- multi-provider AI router (`grok`, `gemini`, `openai`, `claude`, config fallback)

iOS stack:
- Swift 5.9 / SwiftUI
- MVVM structure
- AVFoundation audio pipeline

Primary runtime entry points:
- Production backend process:
  - `Procfile` -> `web: gunicorn main:app --timeout 120 --workers 2`
- Local backend process:
  - `main.py` (`if __name__ == "__main__": app.run(...)`)
- iOS app entry:
  - `TreningsCoach/TreningsCoach/TreningsCoachApp.swift` (`@main`)

Non-primary/legacy backend path present:
- `server.py` (FastAPI-based runtime) exists in repo but is not the production entrypoint used by `Procfile`.

---

## 3) Deployment and Runtime Source of Truth

Current deployment truth:
- Render deploy target is root runtime (`main.py` in repository root).
- Root backend modules are the single runtime source of truth (`main.py`, `config.py`, `brain_router.py`, `brains/*.py`).
- `backend/main.py` is a compatibility shim that imports root `main.py` for legacy scripts.

Operational rule:
- Backend runtime logic must be edited in root files only.
- Treat older docs that describe backend->root mirroring as historical.

---

## 4) Architecture Map (Current Runtime)

High-level architecture:

1. iOS app
- UI state and workout loop in `WorkoutViewModel`.
- continuous audio capture in `ContinuousRecordingManager`.
- wake-word/speech command channel in `WakeWordManager`.
- HTTP transport in `BackendAPIService`.

2. Flask backend orchestration
- Route handling and runtime composition in `main.py`.
- Breath DSP in `breath_analyzer.py`.
- Decisioning in `coaching_intelligence.py` + `voice_intelligence.py`.
- Session/workout state in `session_manager.py`.
- Persona/system prompt control in `persona_manager.py` + `coach_personality.py`.
- AI provider routing in `brain_router.py` + `brains/*.py`.
- TTS in `elevenlabs_tts.py` (with mock fallback).

3. Data and persistence
- SQL tables: `users`, `user_settings`, `workout_history` (`database.py`).
- In-memory runtime state:
  - session state (`SessionManager.sessions`)
  - waitlist and waitlist rate-limit maps (`main.py`)
- File-based transient artifacts:
  - uploads (`uploads/`)
  - generated audio and TTS cache (`output/`, `output/cache/`)

4. Web funnel runtime
- Root route serves variant template (`index_codex.html` or `index_claude.html`) via variant resolver in `main.py`.
- Web live demo calls production backend API endpoints from template JS.

---

## 5) Request and Event Paths

### A) Core workout loop (iOS -> backend -> audio)

1. `WorkoutViewModel.startContinuousWorkout()` starts recording and wake-word listening.
2. Periodic `coachingLoopTick()` pulls latest chunk from `ContinuousRecordingManager`.
3. `BackendAPIService.getContinuousCoachFeedback(...)` posts multipart request to `POST /coach/continuous`.
4. Backend `main.py` pipeline:
   - validate request + session state
   - analyze audio (`breath_analyzer`)
   - decide whether to speak (`voice_intelligence`, `coaching_intelligence`)
   - generate text (`brain_router` and/or config templates)
   - generate TTS (`elevenlabs_tts`, with fallback policy)
5. Backend returns text, decision metadata, timing and optional `audio_url`.
6. iOS downloads `audio_url` and plays response audio.

### B) Wake-word / command path

1. `WakeWordManager` listens on shared audio stream.
2. User utterance captured after wake word or talk button.
3. iOS sends `POST /coach/talk` with workout context.
4. Backend returns short context-aware voice response.

### C) Web conversion and telemetry path

1. `GET /` serves configured web variant.
2. Waitlist form posts to `POST /waitlist`.
3. Client analytics beacon posts to `POST /analytics/event`.
4. Live demo path uses `/welcome`, `/coach/continuous`, `/coach/talk`.

### D) Auth and profile path

1. Provider token -> `/auth/google`, `/auth/facebook`, or `/auth/vipps`.
2. Backend verifies provider token, finds/creates user, returns JWT.
3. Profile operations via `/auth/me` (GET/PUT/DELETE).

---

## 6) Endpoint Inventory (Authoritative)

Authoritative route inventory from Flask `url_map` (non-static): **30 routes total**.

Main app routes (`main.py`): **24**
- `GET /`
- `GET /preview`
- `GET /preview/<variant>`
- `GET /health`
- `GET /tts/cache/stats`
- `GET /welcome`
- `POST /analyze`
- `POST /coach`
- `POST /coach/continuous`
- `GET /download/<path:filename>`
- `GET /brain/health`
- `POST /brain/switch`
- `POST /chat/start`
- `POST /chat/stream`
- `POST /chat/message`
- `GET /chat/sessions`
- `DELETE /chat/sessions/<session_id>`
- `GET /chat/personas`
- `POST /coach/persona`
- `POST /workouts`
- `GET /workouts`
- `POST /coach/talk`
- `POST /waitlist`
- `POST /analytics/event`

Auth blueprint routes (`auth_routes.py`): **6**
- `POST /auth/google`
- `POST /auth/facebook`
- `POST /auth/vipps`
- `GET /auth/me`
- `PUT /auth/me`
- `DELETE /auth/me`

---

## 7) Integrations

AI providers (router-backed):
- xAI Grok
- Google Gemini
- OpenAI
- Anthropic Claude
- config-based fallback

TTS:
- ElevenLabs (`eleven_flash_v2_5`)
- mock synthesis fallback for failure/degraded cases

Auth providers:
- Google
- Facebook
- Vipps

Infra:
- Render for backend hosting/deploy

---

## 8) Known Documentation Drift and Reconciliation

The following docs are currently outdated vs runtime code:

1. `CLAUDE.md`
- states "19 routes in main.py"
- runtime truth: 24 `main.py` routes + 6 `/auth/*` routes = 30 non-static routes.

2. `README.md`
- states "19 API endpoints"
- runtime truth: 30 non-static routes.

3. `docs/plans/2026-02-18-coachi-landing-page-design.md`
- states "Current: 19 routes. After: 21 routes."
- runtime truth after subsequent work is now 30 routes including auth blueprint.

4. `backend/README.md`
- still reflects older backend shape (v1.1 style subset endpoints), not current production runtime behavior.

---

## 9) Operational Verification Commands

Route inventory and count:

```bash
python3 - <<'PY'
import main
rules=[r for r in main.app.url_map.iter_rules() if r.endpoint!='static']
print("TOTAL_NON_STATIC=", len(rules))
for r in sorted(rules, key=lambda x: x.rule):
    methods=','.join(sorted(m for m in r.methods if m not in {'HEAD','OPTIONS'}))
    print(methods, r.rule, r.endpoint)
PY
```

Release safety check:

```bash
./scripts/release_check.sh
```

Core route smoke checks:

```bash
curl -s http://localhost:5001/health
curl -s "http://localhost:5001/welcome?language=en&persona=personal_trainer"
curl -s http://localhost:5001/brain/health
```

---

## 10) Practical Source-of-Truth Rules

1. Treat `main.py` + Flask `url_map` as authoritative route truth.
2. Treat `Procfile` as authoritative deployment entrypoint truth.
3. Treat root files as production runtime truth for Render deploys.
4. Treat `backend/main.py` as compatibility-only; do not place runtime logic there.
5. Update route-count statements in docs when routes change.
