# Session Learnings: Talk to Coach Live

Reference date: 2026-03-22

---

## How It Works (End-to-End)

```
User taps "Get Feedback" on WorkoutCompleteView
  → WorkoutSummarySheet opens (adaptive stat grid)
  → User taps "Talk to Coach" / "Snakk med Coach"
  → onStartCoaching callback:
      1. Track telemetry: voice_cta_tapped
      2. Check liveVoiceIsAvailable (auth + quota)
      3. Call vm.startIfNeeded()
  → LiveCoachConversationViewModel.startIfNeeded():
      1. Wake backend (handle Render cold-start)
      2. Request mic permission
      3. POST /voice/session → get WebSocket URL + client secret
      4. Configure audio: .playAndRecord + .voiceChat + .defaultToSpeaker
      5. Open WebSocket (wss://api.x.ai/v1/realtime)
      6. Send session.update (system prompt + VAD config)
      7. Start audio capture (24kHz PCM16 mono)
      8. Send response.create kickoff → coach delivers workout recap
      9. Start session timer
  → Conversation loop:
      - User speaks → xAI server-side VAD detects speech → triggers AI response
      - Coach responds via audio + text deltas → played through speaker
      - Mic suppressed while coach speaks (isOutputActive flag)
  → Session ends when:
      - Free: 30s duration OR 3 turns (opening + 2 exchanges), whichever first
      - Premium: 180s duration
      - User taps close
```

---

## File Map

| File | Role |
|------|------|
| `WorkoutCompleteView.swift` | Entry point: "Get Feedback" → WorkoutSummarySheet → onStartCoaching |
| `LiveCoachConversationView.swift` | UI + ViewModel: orb, transcript, status, auto-start |
| `XAIRealtimeVoiceService.swift` | Core: WebSocket, audio I/O, turn counting, quota |
| `LiveVoiceSessionTracker.swift` | Local daily session quota tracking (UserDefaults) |
| `BackendAPIService.swift` | `createLiveVoiceSession()`, `trackVoiceTelemetry()` |
| `Models.swift` | `PostWorkoutSummaryContext`, `VoiceSessionBootstrap`, `LiveCoachTranscriptEntry` |
| `Config.swift` (iOS) | `AppConfig.LiveVoice.*` — durations, turn limits, sessions/day |
| `main.py` | `/voice/session` endpoint, quota enforcement, history context |
| `xai_voice.py` | Prompt building, VAD config, client secret, sanitization |
| `config.py` (backend) | `XAI_VOICE_AGENT_*` — all tunable backend values |
| `persona_manager.py` | Unused by voice (persona inlined in xai_voice.py) |

---

## All Tunable Parameters

### Backend (config.py — tunable via env vars on Render)

| Config | Default | What it does |
|--------|---------|--------------|
| `XAI_VOICE_AGENT_ENABLED` | `True` | Feature gate — `False` returns 503 |
| `XAI_VOICE_AGENT_MODEL` | `"grok-3-mini"` | xAI model for voice |
| `XAI_VOICE_AGENT_VOICE` | `"Rex"` | xAI voice persona name |
| `XAI_VOICE_AGENT_REGION` | `"us-east-1"` | WebSocket region |
| `XAI_VOICE_AGENT_MAX_SESSION_SECONDS` | `300` | Default max duration (fallback) |
| `XAI_VOICE_AGENT_FREE_MAX_SESSION_SECONDS` | `30` | Free tier max duration |
| `XAI_VOICE_AGENT_PREMIUM_MAX_SESSION_SECONDS` | `180` | Premium tier max duration |
| `XAI_VOICE_AGENT_FREE_SESSIONS_PER_DAY` | `2` | Free tier daily quota |
| `XAI_VOICE_AGENT_PREMIUM_SESSIONS_PER_DAY` | `3` | Premium tier daily quota |
| `XAI_VOICE_AGENT_VAD_THRESHOLD` | `0.4` | Speech detection sensitivity (0=most sensitive, 1=least) |
| `XAI_VOICE_AGENT_VAD_PREFIX_PADDING_MS` | `300` | Audio buffered before speech detected |
| `XAI_VOICE_AGENT_VAD_SILENCE_DURATION_MS` | `500` | Silence before turn ends → AI responds |
| `XAI_VOICE_AGENT_HISTORY_RECENT_WORKOUT_LIMIT` | `12` | Recent workouts for premium (free gets none, max 50) |
| `XAI_VOICE_AGENT_CLIENT_SECRET_TIMEOUT_SECONDS` | `20.0` | HTTP timeout for xAI secret |
| `XAI_VOICE_AGENT_WEBSOCKET_URL` | `wss://api.x.ai/v1/realtime` | WebSocket endpoint |
| `XAI_VOICE_AGENT_CLIENT_SECRET_URL` | `https://api.x.ai/v1/realtime/client_secrets` | Secret endpoint |

### iOS (Config.swift — hardcoded, requires app update)

| Config | Default | What it does |
|--------|---------|--------------|
| `LiveVoice.isEnabled` | `true` | Feature gate (Info.plist `LIVE_COACH_VOICE_ENABLED`) |
| `LiveVoice.freeMaxDurationSeconds` | `30` | Free tier timer (UI display) |
| `LiveVoice.premiumMaxDurationSeconds` | `180` | Premium timer (UI display) |
| `LiveVoice.freeSessionsPerDay` | `2` | Free daily sessions |
| `LiveVoice.premiumSessionsPerDay` | `3` | Premium daily sessions |
| `LiveVoice.freeTurnLimit` | `3` | Max coach responses for free (opening + 2 exchanges) |

### Timing Constants (hardcoded in XAIRealtimeVoiceService.swift)

| Value | Where | What |
|-------|-------|------|
| `22s` | startupTimeout | Max wait for initial connection |
| `2s` | auto-retry delay | Wait before retry after cold-start failure |
| `2048` | audio buffer size | Capture tap frame count |
| `24000 Hz` | audio sample rate | PCM16 capture and playback |
| `8` | OutboundAudioSender max depth | Queued audio payloads before dropping |
| `0.35s` | sheet dismiss delay | Gap between sheet close → voice view open |

---

## How to Tweak Speech Responsiveness

### "Coach doesn't hear me"
**Lower VAD threshold** — makes detection more sensitive to quiet speech:
```
# Render env var (no redeploy needed if using env override)
XAI_VOICE_AGENT_VAD_THRESHOLD=0.3   # was 0.6, now 0.4, try 0.3 for very sensitive
```
Range: 0.0 (triggers on anything) → 1.0 (needs loud clear speech). Current: **0.4**.

### "Takes too long to respond after I stop talking"
**Lower silence duration** — triggers AI response faster:
```
XAI_VOICE_AGENT_VAD_SILENCE_DURATION_MS=400   # was 700, now 500
```
Trade-off: too low (< 300ms) and coach interrupts natural pauses. Current: **500ms**.

### "Coach interrupts me mid-sentence"
**Raise silence duration** — waits longer before deciding you're done:
```
XAI_VOICE_AGENT_VAD_SILENCE_DURATION_MS=800
```
And/or raise VAD threshold so it's less trigger-happy:
```
XAI_VOICE_AGENT_VAD_THRESHOLD=0.6
```

### "Coach cuts off the start of my words"
**Raise prefix padding** — captures more audio before detected speech:
```
XAI_VOICE_AGENT_VAD_PREFIX_PADDING_MS=500   # default 300
```

---

## How to Tweak the Opening Message

The coach's first message is controlled by two things:

### 1. System prompt (xai_voice.py, lines 590–608)
This tells the model what the opening should contain:
```
YOUR FIRST RESPONSE — opening recap (up to 45 words, 3 sentences):
1. Name the workout and duration.
2. Mention one or two stats from the recap brief below.
3. End with a short insight or one question.
```
The prompt also injects the actual stats as "Opening recap brief" with workout name, duration, selected metrics, and an insight cue.

### 2. iOS kickoff instruction (XAIRealtimeVoiceService.swift, line 365–367)
This is sent as `response.create` to force the first response:
```swift
"Start with the workout summary now. Name the workout, duration, and key stats."
```
This overrides any tendency to start with a generic greeting.

### What stats are available in the opening
Built by `_opening_metric_candidates()` (xai_voice.py lines 194–224). Priority order:
1. Average heart rate (preferred over final HR)
2. Distance (if available, enables pace estimate)
3. Time in target zone %
4. Coach score
5. Final heart rate (fallback)

Only top 2 metrics are picked for the opening brief.

### What insight cue is generated
Built by `_opening_insight_cue()` (xai_voice.py lines 227–275):
- If zone data: "Comment briefly on zone control using X% time in zone and Y overshoots"
- If HR data: "Comment briefly on heart rate at X BPM for a Y workout"
- Fallback: "Share one running-specific insight"

---

## How to Tweak the Coach Persona

### Persona text (inlined in xai_voice.py)
The persona is inlined directly in `build_post_workout_voice_instructions()` — no external dependency:
- **Personality:** Calm, direct, disciplined personal trainer.
- **Style:** Max 2 sentences per reply, under 25 words. One question at a time.
- **Strict:** Only reference stats explicitly provided. No invented data.

### To change personality
Edit the `persona_text` string in `xai_voice.py` `build_post_workout_voice_instructions()` (~line 560).

### To change voice
```
XAI_VOICE_AGENT_VOICE=Rex   # default, change to any xAI voice name
```

### To change model
```
XAI_VOICE_AGENT_MODEL=grok-3-mini   # default, or try other xAI models
```

---

## How Quota Enforcement Works

### Two-layer enforcement (backend + iOS)

**Backend** (`/voice/session` in main.py):
- Checks subscription tier via `resolve_user_subscription_tier(user_id)`
- Enforces daily session limit via rate limiter (key: `api.voice.session.{tier}.day`)
- Returns 429 if quota exceeded → iOS shows paywall
- Returns `max_duration_seconds` in bootstrap (30 for free, 180 for premium)

**iOS** (XAIRealtimeVoiceService.swift):
- **Duration timer:** Counts up every second. At `maxDurationSeconds`, sets `isQuotaExhausted = true` and disconnects with `.timeLimit`.
- **Turn counter:** Increments `turnCount` on each finalized assistant response. At `freeTurnLimit (3)`, sets `isQuotaExhausted = true` and disconnects.
- **Whichever hits first** triggers disconnect.

**Local tracker** (LiveVoiceSessionTracker.swift):
- Stores session count in UserDefaults per day
- Resets automatically on date change
- `canStart(isPremium:)` checked before allowing "Talk to Coach" button
- `markExhausted()` called when backend returns 429

### Post-quota flow
When `isQuotaExhausted = true` and `lastDisconnectReason == .timeLimit`:
- WorkoutCompleteView's `.onChange` observer catches this
- Shows `WatchConnectedPremiumOfferStepView` (Free/Premium/14-day trial cards)

---

## Optimization Opportunities

### Latency
- **Render cold-start:** `wakeBackend()` is called before session start, but first request can still take 10-30s on free tier. Consider: always-on Render instance, or pre-warm on workout complete.
- **Audio queue depth:** Max 8 payloads queued. If WebSocket is slow, oldest audio is dropped. Monitor if this causes missed speech.
- **22s startup timeout:** Long. If backend is warm, connection takes 2-5s. The timeout is generous for cold-start scenarios.

### Speech quality
- **isOutputActive suppression:** Mic is fully muted while coach speaks. No barge-in possible. To enable barge-in, would need to remove this guard and handle echo cancellation differently.
- **Audio format:** 24kHz PCM16 mono is standard for xAI realtime. No room to optimize here.
- **.voiceChat mode:** iOS audio session is set to voice chat mode which applies echo cancellation. Good default.

### Prompt quality
- **Opening recap:** 45 words / 3 sentences is good. If model still says generic greetings, strengthen the kickoff instruction — that's the `response.create` message sent from iOS.
- **Workout history injection:** Up to 12 recent workouts in prompt. If prompt is too long / model loses focus, reduce `XAI_VOICE_AGENT_HISTORY_RECENT_WORKOUT_LIMIT`.
- **Question discipline:** Persona says "one question at a time, then wait." If model asks multiple questions, this instruction may need reinforcement.

### Cost
- **Model:** `grok-3-mini` is cheapest. Could try `grok-3` for better quality at higher cost.
- **Session duration:** Free=30s, Premium=180s. These directly control xAI API cost per session.
- **Turn limit:** Free=3 turns caps API calls. Consider if 2 turns (opening + 1 exchange) is enough for free tier.

---

## Data Flow Diagram

```
iOS                          Backend                    xAI
─────                        ───────                    ───
PostWorkoutSummaryContext
  ├─ workoutMode
  ├─ durationText
  ├─ coachScore
  ├─ averageHeartRate
  ├─ zoneTimeInTargetPct
  ├─ distanceMeters
  └─ ...
       │
       ├──POST /voice/session──→ sanitize context
       │                         query workout history
       │                         build system prompt:
       │                           persona + emotional_mode
       │                           + workout mode description
       │                           + opening recap brief
       │                           + summary stats
       │                           + history context
       │                         ├──POST /client_secrets──→ xAI API
       │                         │                          returns secret
       │                         build session_update JSON:
       │                           voice, instructions, VAD
       │  ←──bootstrap response──┤
       │    (websocketURL, secret,
       │     session_update_json,
       │     max_duration_seconds)
       │
       ├──WebSocket connect──────────────────────────→ wss://api.x.ai/v1/realtime
       │  (sec-websocket-protocol: xai-client-secret.<token>)
       │
       ├──session.update─────────────────────────────→ (system prompt + VAD config)
       │
       ├──response.create────────────────────────────→ (kickoff: "deliver workout recap")
       │
       │  ←──response.text.delta─────────────────────┤ (streaming text)
       │  ←──response.audio.delta────────────────────┤ (streaming PCM16 audio)
       │  ←──response.done───────────────────────────┤ (turn complete)
       │
       ├──input_audio_buffer.append──────────────────→ (user speech PCM16)
       │  ←──conversation.item.input_audio_transcription.completed──┤
       │
       │  ... (conversation loop) ...
       │
       ├──WebSocket close────────────────────────────→
       │
       ├──POST /voice/telemetry──→ log event
       │  ←──200 OK──────────────┤
```

---

## Known Issues & Gotchas

1. **Generic opening message:** If the xAI model ignores the system prompt and says "what can I help you with", the fix is in the iOS kickoff instruction (`response.create`), not in adding more rules to `xai_voice.py`.

2. **Config.swift vs config.py duplication:** Free tier limits exist in both iOS and backend. iOS values are for UI display and local enforcement; backend values are the authoritative gate. They should match but can drift.

3. **No barge-in:** User cannot interrupt the coach mid-sentence. The mic is suppressed via `isOutputActive`. This is by design to avoid echo but reduces conversational feel.

4. **Render cold-start:** Free-tier Render instance sleeps after inactivity. First `/voice/session` call can take 10-30s. `wakeBackend()` mitigates but doesn't eliminate this.

5. **Turn counting:** `turnCount` increments on `response.done`, not on first audio. If the model sends multiple `response.done` events per logical turn, the counter over-counts.

6. **Audio queue drops:** `OutboundAudioSender` drops oldest payload when queue depth > 8. Under heavy load or slow WebSocket, user speech may be clipped.

7. **History tier gating:** Free users get no workout history in the prompt (current session only). Premium users get 7 days. This is enforced in `main.py` `_build_live_voice_history_context(is_premium=)`.
