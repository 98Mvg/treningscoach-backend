# Treningscoach — Claude Code Behavior Spec

You are working inside an existing, production codebase. Your job is to improve and extend it WITHOUT breaking working behavior, WITHOUT moving files across directories, and WITHOUT inventing endpoints.

This is a low-latency AI Coach app ("Coachi", v3.0) with "Midnight Ember" design system. Uses physiological signals (breath analysis) to guide users through workouts with real-time voice feedback. The backend Brain Router abstracts multiple AI providers. The iOS app never knows which provider is active.

---

## 0) Non-Negotiable Rules

**R0.1 — Do not start from scratch.** Assume the system works today. Make improvements incrementally. Always read files before editing.

**R0.2 — Never invent routes, files, or behavior.** If you don't see it in the repo, search the code first.

**R0.3 — Low latency comes first.** Any change that increases latency must be justified and optional behind a flag in `config.py`.

**R0.4 — No "breathing app" framing in user-facing copy.** Breath analysis is a backend sensing function. UI/coach language frames this as an AI coach experience.

**R0.5 — Three languages supported.** Every user-facing string needs English (`en`) and Norwegian (`no`). Danish (`da`) is supported but message banks are still incomplete.

**R0.6 — Config is king.** Tunable values live in `config.py`. Don't hardcode magic numbers elsewhere.

**R0.7 — Keep coaching messages short.** 2-5 words for real-time cues, max 15 words for pattern insights.

---

## 0.1) Latest Session Learnings (2026-02-15)

Use this as the first checklist before touching behavior quality code.

### A) Language consistency guardrails (must preserve)

1. Normalize language at ingress for:
- `/welcome`
- `/coach/continuous`
- `/coach/talk`

2. Keep locale-aware fallbacks across brains/router:
- Never return Norwegian default fallback when `language=en`.
- Preserve canonical defaults: `"Keep going!"` for English, `"Fortsett!"` for Norwegian.

3. Keep final output language guard before TTS:
- Prevent known drift fallback (e.g., `"Fortsett!"` when request language is English).

### B) Intensity normalization (must preserve)

- Canonical intensity is: `calm | moderate | intense | critical`.
- Legacy/localized aliases (`intensitet`, `moderat`, `kritisk`, etc.) must map to canonical values.

### C) Silence policy (must preserve)

- Silence state is session-scoped (not global).
- Do not reintroduce global silence counters for workout decision logic.

### D) Wake-word error loop protection (must preserve)

- Wake-word restart is bounded with exponential backoff.
- There is a retry window cap and temporary degraded mode.
- Degraded mode schedules delayed recovery.
- Diagnostics track restart attempts and degraded events.

### E) Latency observability (must preserve)

Per continuous tick, log:
- `analyze_ms`
- `decision_ms`
- `brain_ms`
- `tts_ms`
- `total_ms`

Tune behavior only using observed timing data.

### F) Files changed in this session

Backend/runtime:
- `main.py`
- `brain_router.py`
- `voice_intelligence.py`
- `brains/base_brain.py`
- `brains/openai_brain.py`
- `brains/claude_brain.py`
- `brains/gemini_brain.py`
- `brains/grok_brain.py`

iOS:
- `TreningsCoach/TreningsCoach/Services/WakeWordManager.swift`
- `TreningsCoach/TreningsCoach/Services/AudioPipelineDiagnostics.swift`

Tests:
- `tests_phaseb/test_base_brain_normalization.py`
- `tests_phaseb/test_language_consistency.py`
- `tests_phaseb/test_voice_intelligence_session_state.py`

Source of truth:
- Backend runtime source of truth is root (`main.py`, `config.py`, `brains/*.py`).
- `backend/main.py` is a compatibility shim that imports root runtime.

### G) Validation commands to run after related edits

```bash
pytest -q tests_phaseb
python3 -m py_compile main.py brain_router.py voice_intelligence.py brains/*.py
```

If Swift touched, run Xcode build when simulator/runtime is available.

Reference commit for this bundle of changes: `87414c6`.

---

## 0.2) Latest Session Learnings (2026-03-01) — Manifest Sync Audio Pack

Primary source of truth:
- [`docs/plans/2026-03-01-manifest-sync-audio-pack-learnings.md`](/Users/mariusgaarder/Documents/treningscoach/docs/plans/2026-03-01-manifest-sync-audio-pack-learnings.md)
- Claude handoff note:
- [`docs/plans/2026-03-01-claude-handoff-manifest-sync.md`](/Users/mariusgaarder/Documents/treningscoach/docs/plans/2026-03-01-claude-handoff-manifest-sync.md)

Must-preserve decisions from this session:
1. Manifest is source of truth for local audio-pack contents.
2. SHA256 validation is required at both levels:
- Manifest bytes hash for change detection.
- Per-file hash verification before write.
3. Never delete stale files during active workout.
4. Version-isolated local storage (`Documents/audio_pack/{version}/...`) is required.
5. `WorkoutViewModel` must read active pack version from sync manager first (config fallback second).
6. Keep voice safety: persona-scoped lookup paths and no toxic/performance bleed into Personal Trainer runtime.
7. R2 replacement/removal flow is manifest-driven:
- Replace file: upload new MP3 + update manifest hash.
- Remove file: remove manifest entry; stale cleanup removes local file.

---

## 1) Architecture (How It All Fits Together)

```
iOS App (SwiftUI)
  ↓ HTTP POST /coach/continuous (audio bytes)
Backend (Flask on Render)
  ↓ breath_analyzer.py → breath metrics (librosa DSP)
  ↓ brain_router.py → picks AI brain
  ↓ brains/*.py → generates coaching text
  ↓ elevenlabs_tts.py → text-to-speech audio
  ↑ Returns audio file URL to iOS
iOS App plays audio through speaker
```

**Active brain:** Grok (xAI) — cheapest + fastest.
**Fallback chain:** grok → gemini → openai → claude → config (static messages).
**TTS:** ElevenLabs `eleven_flash_v2_5` model. Qwen TTS disabled (too slow on CPU). Norwegian uses `language_code="no"` (ISO 639-1). Danish uses `"da"`.
**Personas:** `personal_trainer` (supportive) and `toxic_mode` (drill sergeant), each with own voice settings + message banks.
**Languages:** English (`en`), Norwegian Bokmål (`no` → `nb-NO`), Danish (`da` → `da-DK`). Locale config in `locale_config.py`.

### Architecture Decisions (Why Things Are This Way)

- **Brain Router abstraction**: App calls ONE backend API. Backend chooses the AI provider. Enables hot-swapping, A/B testing, fallback — UI stays stable.
- **Adapter pattern**: Each provider inherits from `BaseBrain`. Adding a provider is additive; router logic stays simple.
- **Grok as default**: Cheapest API, fast response times, good enough quality for real-time coaching.
- **Priority routing with timeout**: 1.2s timeout per brain (`BRAIN_TIMEOUT`). `BRAIN_SLOW_THRESHOLD` must be > `BRAIN_TIMEOUT` (currently 3.0s) or brains get permanently disabled. Latency tracked via exponential moving average (`BRAIN_LATENCY_DECAY_FACTOR=0.9`). On failure, automatically tries next in chain. App never goes silent.
- **ElevenLabs over local TTS**: Qwen3-TTS was too slow on Render's CPU.
- **Librosa pre-warming**: First import takes ~10s. Pre-imported on startup to avoid timeout on first request.
- **Config fallback messages**: If ALL AI brains fail, `config.py` has static message banks in all supported languages.
- **Hybrid coaching engine**: Templates are the safety net (anchor). AI generates variations. If AI text fails validation (`coaching_engine.py`), the template plays instead. Validation checks: word count, forbidden phrases (R0.4), language correctness, tone match, profanity.
- **Breathing timeline**: Active at ALL times — from prep through cooldown. 5 phases: prep → warmup → intense → recovery → cooldown. Each phase has breathing pattern, cue interval, and bilingual message bank (`breathing_timeline.py`).
- **Memory is minimal by design**: Inject only at session start. Store only coaching style, safety flags, improvement markers, last session config. Never inject full memory every message.
- **Safety overrides always win**: Critical breathing patterns override humor, pushiness, and long responses. Trigger concise, authoritative coaching.

---

## 2) CRITICAL: Single Backend Source of Truth

Render deploys from **ROOT**. Backend runtime changes must be made in root files only.

```
treningscoach/              ← Render deploys THIS directory
├── main.py                 ← PRODUCTION + development source of truth
├── requirements.txt        ← PRODUCTION dependencies
├── Procfile                ← "web: gunicorn main:app --timeout 120 --workers 2"
├── config.py, brain_router.py, etc.  ← Runtime Python modules
├── brains/                 ← Brain adapters
├── backend/                ← Legacy tooling/docs + compatibility shim only
│   └── main.py             ← Imports root main.py (do not add runtime logic here)
└── TreningsCoach/          ← iOS app (Xcode project)
```

### When you change backend code, ALWAYS:

```bash
# 1. Edit root runtime files only
# 2. Validate changed files
python3 -m py_compile main.py config.py brain_router.py brains/*.py
# 3. Commit changed root files
git add main.py config.py brain_router.py brains/ requirements.txt
git commit -m "Description of change"
git push
```

If you see older docs mentioning backend->root mirroring, treat them as historical and follow this section.

### CRITICAL: Xcode project.pbxproj is NOT in git

`TreningsCoach/TreningsCoach.xcodeproj/project.pbxproj` is NOT tracked by git (it's in `.gitignore`).
- Adding/deleting Swift files requires manual pbxproj edits (PBXBuildFile, PBXFileReference, PBXGroup, PBXSourcesBuildPhase)
- The `.xcodeproj` lives in the main repo only, NOT in git worktrees
- Xcode builds from the main repo checkout — worktree branch changes must be merged to the branch checked out in main repo before they appear in Xcode builds

---

## 3) Operating Mode: Problem-Driven Playbook

### When you encounter missing context:
- Search the codebase for the relevant file/function/route
- Quote exact filenames and line references
- Only then propose changes

### When asked to add a new AI provider:
1. Add a new adapter under `brains/` conforming to `BaseBrain` interface
2. Add it to the router mapping in `brain_router.py`
3. Add health checks + timeout handling
4. Add env var for API key
5. Update config.py BRAIN_PRIORITY list

### When asked to change routing/switching:
- Keep the iOS app unaware of provider selection
- Implement switching in Brain Router via config + runtime `/brain/switch` API
- Maintain fallback order and timeouts (currently 1.2s per brain)
- Use usage/quota-aware selection if metrics exist (`config.BRAIN_USAGE`)

### When encountering latency issues:
- Prefer short prompts and template responses
- Memory injection only at session start
- Use strict timeouts per provider (config.BRAIN_TIMEOUT = 1.2s)
- Stream responses where supported
- Maintain fast fallback chain

### When encountering "stateful" features (memory, last session):
- Keep memory minimal: coaching style, safety flags, improvement markers, last session config
- Store in a single durable place and load once per session
- Do NOT inject full memory every message

### When encountering endpoint drift:
- Update the endpoint table in section 4 immediately
- If code and docs disagree, update docs to match code OR propose a safe refactor
- Never remove or rename endpoints without migration plan

---

## 4) All Backend Endpoints (30 non-static routes total)

Current route inventory:
- `24` routes in `main.py`
- `6` routes in `auth_routes.py` (registered as `/auth/*` blueprint)

### 4a) Main App Routes (`main.py`) — 24

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Web root (variant-resolved landing page) |
| GET | `/preview` | Variant compare page |
| GET | `/preview/<variant>` | Direct variant preview |
| GET | `/health` | Health/version |
| GET | `/tts/cache/stats` | TTS cache observability |
| GET | `/welcome` | Welcome text + TTS audio |
| POST | `/analyze` | Breath analysis only |
| POST | `/coach` | Single-shot coach response |
| POST | `/coach/continuous` | Main continuous coaching endpoint |
| GET | `/download/<path:filename>` | Download generated audio |
| GET | `/brain/health` | Brain health + stats |
| POST | `/brain/switch` | Runtime brain switch |
| POST | `/chat/start` | Create chat session |
| POST | `/chat/stream` | SSE streaming chat |
| POST | `/chat/message` | Non-stream chat |
| GET | `/chat/sessions` | List sessions |
| DELETE | `/chat/sessions/<session_id>` | Delete session |
| GET | `/chat/personas` | List personas |
| POST | `/coach/persona` | Switch persona mid-workout |
| POST | `/workouts` | Save workout |
| GET | `/workouts` | Read workouts |
| POST | `/coach/talk` | Wake-word / conversational coach response |
| POST | `/waitlist` | Landing waitlist capture |
| POST | `/analytics/event` | Landing analytics ingest |

### 4b) Auth Blueprint Routes (`auth_routes.py`) — 6

| Method | Route | Purpose |
|---|---|---|
| POST | `/auth/google` | Google sign-in |
| POST | `/auth/facebook` | Facebook sign-in |
| POST | `/auth/vipps` | Vipps sign-in |
| GET | `/auth/me` | Get authenticated profile |
| PUT | `/auth/me` | Update authenticated profile |
| DELETE | `/auth/me` | Delete authenticated account |

---

**Verification rule:** After any route change, confirm non-static route count and update this section.

```bash
python3 - <<'PY'
import main
rules=[r for r in main.app.url_map.iter_rules() if r.endpoint!='static']
print(f"TOTAL_NON_STATIC={len(rules)}")
PY
```

---

## 5) iOS App Key Files

| File | What it does | When to edit |
|------|-------------|--------------|
| `AppTheme.swift` | CoachiTheme design system — colors, gradients, view modifiers | Changing colors, fonts, card styles |
| `AppViewModel.swift` | App-level state: onboarding, language, user profile | Onboarding flow, app-wide state |
| `RootView.swift` | Root navigation: onboarding vs MainTabView | App entry flow changes |
| `Config.swift` | Backend URL, phase timings, version | Changing backend URL or timing |
| `WorkoutViewModel.swift` | Main workout logic + state machine | Workout flow changes |
| `ContinuousRecordingManager.swift` | Real-time audio capture | Audio recording issues |
| `BackendAPIService.swift` | All HTTP calls to backend | API changes |
| `TreningsCoachApp.swift` | Entry point, injects AppViewModel + AuthManager | App startup changes |
| `CoachOrbView.swift` | Animated coaching orb (idle/listening/speaking) | UI animation changes |
| `AudioPipelineDiagnostics.swift` | Debug overlay for audio pipeline | Debugging audio |
| `AudioDiagnosticOverlayView.swift` | Debug overlay for breath analysis + coach decisions | Long-press orb during workout to toggle |
| `L10n.swift` | All bilingual strings (en/no) | Adding user-facing text |

### iOS Design Rules
- Workout screen must be immersive. No settings UI during workout.
- User picks voice/persona/language BEFORE workout.
- During workout: minimal controls only.

## 5b) Backend Key Files

| File | What it does | When to edit |
|------|-------------|--------------|
| `main.py` | Flask app (24 app routes + auth blueprint registration) | Adding/changing endpoints |
| `auth_routes.py` | `/auth/*` provider auth + profile endpoints | Changing auth/profile behavior |
| `config.py` | All tunable values, message banks, brain config | Changing thresholds, messages, feature flags |
| `brain_router.py` | Priority routing across AI providers, latency tracking | Changing brain selection, timeouts, observability |
| `brains/*.py` | AI provider adapters (grok, claude, openai, gemini) | Adding/modifying AI providers |
| `breath_analyzer.py` | Librosa DSP for breath metrics | Changing breath analysis |
| `elevenlabs_tts.py` | ElevenLabs TTS (`eleven_flash_v2_5` model) | Changing voice synthesis, model, language codes |
| `locale_config.py` | Single source of truth: languages, voice IDs, BCP47 codes | Adding languages, changing voice IDs |
| `persona_manager.py` | AI personas + emotional modifiers (EN/NO) | Changing coach personality, adding personas |
| `coaching_engine.py` | Text validation, anti-repetition, template anchors | Changing coaching quality rules |
| `breathing_timeline.py` | 5-phase breathing guidance (prep→cooldown) | Changing breathing cues, phase timing |
| `coaching_intelligence.py` | Pattern detection, strategic insights | Changing AI-driven coaching logic |

### Backend Design Rules
- **TTS model is `eleven_flash_v2_5`** — NOT `eleven_multilingual_v2` (that one sounds Danish for Norwegian text)
- **Always pass `language_code`** for non-English TTS (Norwegian = `"nb"`, Danish = `"da"`)
- **`BRAIN_SLOW_THRESHOLD` must be > `BRAIN_TIMEOUT`** or brains get permanently disabled after one timeout
- **Coaching text validation** via `coaching_engine.validate_coaching_text()` before sending to TTS
- **Breathing timeline is always active** — never skip phases, even during warmup

---

## 6) Solving Common Problems

### "Backend deployed but nothing changed"
1. Did you edit root runtime files (`main.py`, `config.py`, `brains/*`)?
2. Did you push to `main` branch? Auto-deploy only triggers on `main`.
3. Check Render dashboard for deploy status/errors.
4. Verify: `curl https://treningscoach-backend.onrender.com/health`
5. Verify guard: `./scripts/check_root_runtime.sh`

### "New dependency not found on Render"
1. Add to root `requirements.txt`
2. Push.

### "iOS Error -10875 (Audio Session)"
Audio session category conflict. Fix pattern:
```swift
try? audioSession.setActive(false)
try audioSession.setCategory(.playAndRecord, options: [.defaultToSpeaker, .allowBluetooth])
try audioSession.setActive(true)
```

### "Onboarding not showing / stuck"
`has_completed_onboarding` is true in UserDefaults. Delete the app or reset:
```swift
UserDefaults.standard.removeObject(forKey: "has_completed_onboarding")
```

### "No voice/audio in coaching response"
1. Check `ELEVENLABS_API_KEY` is set in Render env vars
2. Check voice IDs: `ELEVENLABS_VOICE_ID` (English), `ELEVENLABS_VOICE_ID_NO` (Norwegian)
3. Check backend logs for TTS errors
4. Test: `curl "https://treningscoach-backend.onrender.com/welcome?language=en"`

### "Norwegian voice sounds Danish"
1. Check TTS model is `eleven_flash_v2_5` (NOT `eleven_multilingual_v2`)
2. Check `language_code="no"` (ISO 639-1) is being passed to ElevenLabs `convert()` call — NOT `"nor"` (ISO 639-3 returns 400)
3. Check voice ID is Norwegian-native: `nhvaqgRyAq6BmFs3WcdX` (not an English voice)
4. See `elevenlabs_tts.py` — `LANGUAGE_CODES` dict and `generate_audio()`

### "Brain/AI not responding"
1. Check active brain: `curl https://treningscoach-backend.onrender.com/brain/health`
2. Check API key for that brain is set in Render env vars
3. Priority routing tries: grok → gemini → openai → claude → config (static)
4. Switch brain: `curl -X POST .../brain/switch -H "Content-Type: application/json" -d '{"brain":"claude"}'`

### "Grok always skipped / $0.00 usage"
1. Check `BRAIN_SLOW_THRESHOLD` > `BRAIN_TIMEOUT` in config.py (currently 3.0 > 1.2)
2. If threshold equals timeout, ANY single timeout permanently disables the brain
3. Check brain stats: `curl .../brain/health` — look at `brain_stats.grok.avg_latency` and `brain_stats.grok.timeouts`
4. Latency uses exponential moving average (`BRAIN_LATENCY_DECAY_FACTOR=0.9`) — recovers over time

### "Coach not speaking during workout (silent coach)"
1. `voice_intelligence.py` is the ONLY signal quality gate (threshold `< 0.03`). `coaching_intelligence.py` had a second gate at `< 0.05` that was removed to prevent cascading silence.
2. Check `config.py` `MIN_SIGNAL_QUALITY_TO_FORCE` is `0.0` — max silence override must fire unconditionally
3. Check `main.py` `getattr` fallback matches config (both should be `0.0`)
4. Voice intelligence has a hard cap: max 3 consecutive silent ticks. If changed, cascading silence returns.
5. Mock TTS (`.wav` beeps) vs real ElevenLabs (`.mp3`) — check audio URL extension in response

### "Worktree branch behind main"
If using git worktrees (e.g. `claude/elegant-bardeen`), the worktree branch can fall behind `main`.
Since Xcode builds from the main repo, worktree changes must be merged to main (or main merged into worktree).
Check with: `cd /path/to/worktree && git log --oneline main..HEAD` (shows worktree-only commits)
Sync with: `git merge main` (from within the worktree)

### "Breath analysis timing out / first request slow"
Librosa is pre-warmed on startup. Render free tier cold-starts take 30-60s. Procfile has `--timeout 120` to handle this.

---

## 7) Environment Variables (Render Dashboard)

| Variable | Required | Used by |
|----------|----------|---------|
| `XAI_API_KEY` | Yes (active brain) | brains/grok_brain.py |
| `ELEVENLABS_API_KEY` | Yes (TTS) | elevenlabs_tts.py |
| `ELEVENLABS_VOICE_ID` | Yes (English voice) | config.py |
| `ELEVENLABS_VOICE_ID_NO` | Yes (Norwegian voice) | config.py |
| `ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_EN` | Optional override | locale_config.py |
| `ELEVENLABS_VOICE_ID_PERSONAL_TRAINER_NO` | Optional override | locale_config.py (default: nhvaqgRyAq6BmFs3WcdX) |
| `ELEVENLABS_VOICE_ID_TOXIC_EN` | Optional override | locale_config.py |
| `ELEVENLABS_VOICE_ID_TOXIC_NO` | Optional override | locale_config.py |
| `ANTHROPIC_API_KEY` | If using Claude brain | brains/claude_brain.py |
| `OPENAI_API_KEY` | If using OpenAI brain | brains/openai_brain.py |
| `GEMINI_API_KEY` | If using Gemini brain | brains/gemini_brain.py |

---

## 8) Quick Verification Commands

```bash
# Health check
curl https://treningscoach-backend.onrender.com/health

# Test welcome audio
curl "https://treningscoach-backend.onrender.com/welcome?language=en"

# Check active brain
curl https://treningscoach-backend.onrender.com/brain/health

# Local release smoke check
./scripts/release_check.sh
```

---

## 9) Output Expectations (How You Respond)

When you propose changes:
- Start with what exists (files/paths/line numbers)
- Explain why the change is needed
- Provide minimal diff approach
- Include "how to verify" steps (curl examples, tests)

When you touch routes:
- Update the endpoint table in section 4 immediately
- Provide curl commands for each modified/added route

When you touch provider routing:
- State the routing order and timeouts
- Provide failure behavior examples

---

## 10) Guardrails for Coach Personality

- Humor allowed only when user is calm/performing well. No humor in intense/critical states.
- Keep coaching lines short (often < 10 words in realtime mode).
- Use the user's name in the FIRST welcome message of a session (if known). During workout, name appears max 1-2 times total — never on consecutive messages. Prompt must be explicit about this or LLMs will overuse it.
- Safety overrides always win over personality/humor.
- Breath analysis is a sensor signal — never expose DSP internals to the user.
- Emotional progression: personas adapt intensity (supportive → pressing → intense → peak) per `EMOTIONAL_MODIFIERS` in `persona_manager.py`.
- Breathing interruptions ("can't breathe", "dizzy", "slow down") force safety responses — see `breathing_timeline.py` `BREATHING_INTERRUPTS`.
- Norwegian coaching must sound natural: "Nydelig", "Kjør på!", "Helt inn nå!", "Trøkk i beina!" — NOT translated English.

## 11) Coaching Engine Architecture

```
Workout session timeline:
  PREP (20s cues) → WARMUP (4-4 pattern, 45s) → INTENSE (power, 90s) → RECOVERY (4-6, 30s) → COOLDOWN (4-7, 60s)
```

- **Prep phase**: Safety words, hydration/stretching reminders, countdown to start, motivating words
- **Template-anchor pattern**: `get_template_message()` always returns a valid message. AI generates variations. If `validate_coaching_text()` fails, template plays.
- **Anti-repetition**: `SessionCoachState` tracks last 10 messages + last 5 themes. Cue types (pace/effort/form/breathing/motivation) are weighted by phase.
- **Forbidden phrases** (R0.4): "breathing exercise", "breathing app", "as an ai", etc. — see `FORBIDDEN_PHRASES` in `coaching_engine.py`.
- **Integration status**: `coaching_engine.py`, `breathing_timeline.py`, and `locale_config.py` are standalone modules ready to be wired into `main.py`'s `/coach/continuous` endpoint.
