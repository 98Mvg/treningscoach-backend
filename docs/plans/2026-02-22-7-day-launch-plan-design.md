# Coachi 7-Day Launch Plan — Design Document

**Date:** 2026-02-22
**Status:** Approved
**Goal:** Ship a launch-ready product in 7 days with zero lead loss, reliable coaching quality, and a conversion-focused website that drives app downloads.

---

## Guiding Principles

1. The website does ONE job: get people to download the app.
2. No web demo. No mic permission on web. Pictures + text + download CTA.
3. Coaching quality has a floor — enforcement on, templates catch failures.
4. Norwegian must sound native, not translated.
5. First workout must feel guided, not confusing.
6. Every change is measurable.

---

## Day 1: Funnel & Lead Protection

### 1A. Waitlist Persistence (Backend)

**Problem:** Waitlist is in-memory (`_waitlist_emails = []` in main.py). Every Render restart loses all captured emails.

**Fix:** Create `WaitlistSignup` SQLAlchemy model, persist to database.

**Schema:**
```python
class WaitlistSignup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    language = db.Column(db.String(10), default='no')
    source = db.Column(db.String(50), default='website')  # website, app, referral
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_hash = db.Column(db.String(64), nullable=True)
```

**Constraints:**
- Unique email constraint (no duplicates)
- `created_at` auto-populated
- `source` tracks where signup came from
- `language` captures user's selected language at signup time
- Keep existing rate limiting (5 per IP per hour) but move counter to DB too

**Verification:**
```bash
curl -X POST https://treningscoach-backend.onrender.com/waitlist \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","language":"no"}'
# Restart server, verify email persists
```

### 1B. Remove Web Demo Completely

**What to remove:**
- Live demo section (mic access, persona toggle, training level, workout controls, real-time metrics display, coaching feed, analysis panel)
- All demo-related JavaScript (WebSocket, audio recording, continuous coaching calls)
- Demo-related analytics events (`demo_started`, `demo_mic_granted`, `demo_coaching_received`)

**What to keep:**
- `/coach/continuous` endpoint (iOS uses it)
- All backend coaching logic (unchanged)

### 1C. Redesign Website — Mia Health-Style Structure

**Reference:** https://www.miahealth.no/no (adapted for Coachi's running-coach positioning)

**New page structure (8 sections):**

#### Section 1: Hero
- **Headline (NO):** "Lop med en coach som hjelper deg a holde riktig puls."
- **Headline (EN):** "Run with a coach that keeps you in the right pulse zone."
- **Sub-copy:** One sentence explaining real-time voice coaching during runs.
- **Primary CTA:** "Last ned appen" / "Download the app" (App Store + Google Play badges)
- **Visual:** Phone mockup showing active workout screen with coaching orb
- **Design:** Full-width gradient hero (keep Midnight Ember palette), no background image needed

#### Section 2: How It Works (3 Steps)
Three cards with app screenshots:
1. **"Velg okt"** / "Pick your run" — screenshot of workout mode selection (Easy Run, Intervals)
2. **"Fa korte rad underveis"** / "Get short cues while you run" — screenshot of active coaching with orb speaking
3. **"Se score og neste steg"** / "See your score and next steps" — screenshot of post-workout CoachScore

Each card: icon/number + title + 1-sentence description + app screenshot

#### Section 3: What You Get
Three benefit cards (aspirational outcomes, not features):
1. **"Enklere lopeturer"** / "Easier runs" — stop overthinking pace and zones
2. **"Bedre kontroll pa intensitet"** / "Better intensity control" — stay in the right zone without staring at your watch
3. **"Mindre overtenking"** / "Less overthinking" — let the coach handle the numbers

Each card: simple icon + title + 2-line description. Lifestyle feel, not technical.

#### Section 4: Before/After Scenario Cards
Two side-by-side scenario cards showing transformation:
- **For:** "For hard start, usikker puls, sliten for tidlig" / "Too fast start, uncertain pulse, tired too early"
- **Etter:** "Jevn puls, bedre flyt, overskudd pa slutten" / "Steady pulse, better flow, energy at the end"

Visual: contrasting colors (muted/grey for "before", Coachi gradient for "after")

#### Section 5: Social Proof
- 3 user testimonials (real beta tester quotes when available, placeholder structure ready)
- Simple stat: "X coaching sessions delivered" or "Built on NTNU exercise research"
- Trust badges: CERG/NTNU logos (keep — these are real research partnerships)

#### Section 6: FAQ
Concise answers to:
1. "Ma jeg ha klokke?" / "Do I need a watch?" — No, voice coaching works with phone only. Watch adds heart rate zones.
2. "Funker det pa norsk?" / "Does it work in Norwegian?" — Yes, native Norwegian voice coaching.
3. "Hvor raskt kommer jeg i gang?" / "How fast can I get started?" — Download, pick a run, start. Under 2 minutes.
4. "Hva koster det?" / "What does it cost?" — Free to start. Premium from 25 kr/month.

#### Section 7: Closing CTA Block
- Repeat headline: "Klar for en smartere lopeopplevelse?" / "Ready for a smarter running experience?"
- App Store + Google Play badges (large)
- "Android early access" link/waitlist for Android users
- Waitlist email form for those not ready to download yet

#### Section 8: Footer
- Clean, minimal
- Logo + one-line tagline
- Links: Home, How it works, FAQ, Privacy
- App Store badges (small)
- No developer/debug links (remove API status, Brain status, A/B compare, Claude variant)

**Design constraints:**
- Keep Midnight Ember color palette (purple/orange/teal gradients)
- Keep Poppins + Manrope typography
- Mobile-first: must work perfectly on phone screens
- Add hamburger menu for mobile navigation (currently missing)
- Bilingual: NO/EN toggle (keep existing `data-i18n` system)
- Target page weight: < 200KB total (current codex template is 121KB HTML alone)
- No JavaScript except: language toggle, smooth scroll, waitlist form submission

**Copy tone:**
- Short sentences. Active voice. Second person ("du"/"you").
- No technical terms (no "DSP", "librosa", "brain routing")
- No "breathing app" framing (R0.4)
- Benefits over features: "bedre flyt" not "real-time voice synthesis"

---

## Day 2: Deployment Safety

### 2A. Eliminate Root/Backend Mirror

**Decision:** Option A — root is the single source of truth.

**Steps:**
1. Verify root files are current production (they are — Render deploys from root)
2. Diff all `backend/*.py` against root `*.py` — identify any backend-only changes that need to be preserved
3. Copy any backend-only improvements to root
4. Delete `backend/*.py` files (keep `backend/templates/` if any templates are backend-only)
5. Update CLAUDE.md: remove all sync instructions, update file paths
6. Update any scripts that reference `backend/` paths

**What stays in backend/:**
- `backend/templates/` — only if templates differ from root `templates/`
- Nothing else. All Python development happens in root.

**Verification:**
```bash
# After cleanup, this should show no Python files in backend/
ls backend/*.py 2>/dev/null && echo "CLEANUP INCOMPLETE" || echo "CLEAN"
```

### 2B. Release Checklist

Create `scripts/release_check.sh`:
```bash
#!/bin/bash
# Pre-deploy verification
set -e

echo "=== Release Checklist ==="

# 1. Health endpoint
echo -n "Health check... "
curl -sf https://treningscoach-backend.onrender.com/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('version','?'))"

# 2. Coaching endpoint responds
echo -n "Coaching endpoint... "
STATUS=$(curl -sf -o /dev/null -w "%{http_code}" -X POST https://treningscoach-backend.onrender.com/coach/continuous -H "Content-Type: application/json" -d '{}')
[ "$STATUS" = "400" ] && echo "OK (400 = expects audio)" || echo "FAIL ($STATUS)"

# 3. Waitlist insert works
echo -n "Waitlist persistence... "
curl -sf -X POST https://treningscoach-backend.onrender.com/waitlist -H "Content-Type: application/json" -d "{\"email\":\"releasecheck-$(date +%s)@test.invalid\",\"language\":\"no\"}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','FAIL'))"

# 4. Welcome TTS
echo -n "Welcome TTS (NO)... "
curl -sf "https://treningscoach-backend.onrender.com/welcome?language=no" | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('audio_url') else 'FAIL')"

# 5. App download links resolve
echo -n "App Store link... "
echo "MANUAL CHECK"

echo "=== Done ==="
```

### 2C. Lock Environment Defaults

Review and lock these config values for launch:
- `BRAIN_PRIORITY = ["grok", "config"]` (no expensive fallbacks)
- `COACHING_VALIDATION_ENFORCE = True` (Day 3 flip)
- `BREATHING_TIMELINE_ENFORCE = False` (selective — see Day 3)
- `USE_HYBRID_BRAIN = False` (keep disabled)
- `TTS_CACHE_ENABLED = False` (keep disabled until stable)
- `MIN_SIGNAL_QUALITY_TO_FORCE = 0.0` (max silence override unconditional)
- ElevenLabs model: `eleven_flash_v2_5` (locked)
- Default language: `no` (Norwegian market first)

---

## Day 3: Coaching Quality Floor

### 3A. Enable Coaching Validation Enforcement

**Flip:** `COACHING_VALIDATION_ENFORCE = True` (env var override: `COACHING_VALIDATION_ENFORCE`)

**What this does:**
- AI-generated coaching text goes through `coaching_engine.validate_coaching_text()`
- Checks: word count, forbidden phrases (R0.4), language correctness, tone match
- On failure: template message plays instead (from `get_template_message()`)
- User never hears bad AI output

**Rollback guard:**
- Env var `COACHING_VALIDATION_ENFORCE=false` instantly reverts to shadow mode
- No deploy needed to rollback

### 3B. Selective Breathing Timeline Enforcement

**Rule:** Enable `BREATHING_TIMELINE_ENFORCE` ONLY when no zone-event text is active.

**Logic:**
```python
# In the continuous coaching pipeline:
if zone_event_motor.has_active_text():
    # Zone logic owns the cue — skip timeline enforcement
    pass
else:
    # No zone event — timeline can enforce phase-appropriate cues
    if config.BREATHING_TIMELINE_ENFORCE:
        apply_timeline_enforcement(phase, cue)
```

This prevents the breathing timeline from overriding deterministic running logic (Easy Run zone targeting, Interval cues) while still enforcing phase-appropriate cues during free-form coaching.

### 3C. Monitoring Counters

Add lightweight in-memory counters (logged every 60s or per-request):
- `validation_fail_rate` — % of AI responses that failed validation
- `template_fallback_rate` — % of cues that used template instead of AI
- `language_mismatch_rate` — % of responses where output language != request language
- `norwegian_rewrite_rate` — % of Norwegian responses that triggered phrase quality rewrite

**Log format:**
```
COACHING_METRICS | validation_fail=2/50 (4%) | template_fallback=3/50 (6%) | lang_mismatch=0/50 (0%) | no_rewrite=5/30 (17%)
```

Visible in Render logs. No dashboard infrastructure needed for Day 3.

---

## Day 4: Norwegian Quality & Human Timing

### 4A. Norwegian Phrasing Bank Upgrade

**Expand per intensity level with native workout expressions:**

| Intensity | Current (thin) | Target (natural) |
|-----------|----------------|------------------|
| calm | "Bra jobba", "Fortsett" | "Der ja!", "Fint tempo", "Nydelig flyt", "Bare gled deg" |
| moderate | "Godt tempo", "Hold det der" | "Trykk til!", "Litt til na", "Fint driv", "Kjenn den flyten" |
| intense | "Kjor pa!", "Gi alt!" | "Helt ratt!", "Na drar vi!", "Trykk i beina!", "Siste bit!" |
| recovery | "Pust ut", "Slapp av" | "Fint, bare pust", "La kroppen hente seg", "Rolig og godt" |

**Constraints:** All additions must be 2-5 words (R0.7). No translated-English patterns.

### 4B. Banlist Expansion

Add common "translated-English" patterns to `norwegian_phrase_quality.py` banlist:
- "Du gjor det bra" (too generic, sounds translated)
- "Fortsett a presse" (direct translation of "keep pushing")
- "Du er nesten der" (direct translation of "you're almost there")
- "Godt jobbet med det" (unnecessarily wordy)
- "Hold opp det gode arbeidet" (direct translation of "keep up the good work")

### 4C. Silence-Break Phrasing by Workout Moment

**Scope:** Non-zone mode and HR-poor/safe mode only (zone mode already has deterministic `max_silence_text`).

**When max-silence fires, select cue by current workout phase:**

| Phase | Silence-break cues (NO) | Silence-break cues (EN) |
|-------|------------------------|------------------------|
| WARMUP | "Fint, vi er i gang", "Kjenn at kroppen losner" | "Good, we're moving", "Let your body warm up" |
| INTENSE | "Trykk i beina!", "Na gir vi litt ekstra" | "Push through!", "Give it a little extra now" |
| RECOVERY | "Bare pust, la det roe seg", "Fint, bare slapp av" | "Just breathe, let it settle", "Good, just relax" |
| COOLDOWN | "Fint tempo ned", "La pulsen synke rolig" | "Nice and easy now", "Let your heart rate come down" |

**Implementation:** Add `phase` parameter to the silence-break decision in `voice_intelligence.py`, with a phase-to-cue-bank lookup. Falls back to current generic cues if phase is unknown.

### 4D. Tests

Add/expand tests:
- `test_norwegian_phrase_quality.py` — verify banlist catches translated patterns, verify new phrases pass validation
- `test_silence_break_phase.py` — verify phase-aware cue selection in non-zone mode

---

## Day 5: First-Workout Onboarding Polish (iOS)

### 5A. Coach Intro Before First Run

**When:** After user taps "Start" on their very first workout ever (check `UserDefaults` flag `has_completed_first_workout`).

**What:** 15-second audio from selected persona:
- Personal Trainer (NO): "Hei! Jeg er coachen din. Jeg folger med pa pulsen din og gir deg korte rad underveis. Bare lop — jeg tar meg av resten."
- Personal Trainer (EN): "Hey! I'm your coach. I'll track your heart rate and give you short cues along the way. Just run — I'll handle the rest."
- Toxic Mode adapts tone accordingly.

**How:** Call existing `/welcome` endpoint with a `context=first_workout` parameter. Backend returns workout-context welcome instead of generic welcome.

**After playing:** Set `has_completed_first_workout = true`. Never plays again.

### 5B. One-Time Orb State Overlay

**When:** First workout, after coach intro plays.

**What:** Semi-transparent overlay showing 3 orb states:
1. Idle (dim) — "Coach is analyzing" / "Coachen analyserer"
2. Listening (pulse) — "Coach is listening" / "Coachen lytter"
3. Speaking (bright) — "Coach is talking" / "Coachen snakker"

**Dismiss:** Tap anywhere or auto-dismiss after 8 seconds.

**After dismiss:** Set `has_seen_orb_guide = true`. Never shows again.

### 5C. First-Minute Reassurance Text

**When:** First 60 seconds of first workout, if no coaching cue has fired yet.

**What:** Subtle text below the orb: "Coachen er med deg na" / "Coach is with you now"

**Disappears:** After first coaching cue plays, or after 60 seconds, whichever comes first.

**Implementation:** `WorkoutViewModel` checks `has_completed_first_workout` and shows overlay text. Timer removes it.

---

## Day 6: Retention Loop

### 6A. CoachScore Explanation

**After workout completion, show simple breakdown:**
```
CoachScore: 78

Jevn intensitet      ████████░░  80%
Riktig sone-tid      ███████░░░  70%
God avslutning       █████████░  85%

Neste gang: Prov a holde pulsen mer jevn i intervallene.
```

Three components, each scored 0-100, averaged. One "next run" tip based on lowest component.

**Components:**
1. Intensity consistency — how steady was effort within target zones
2. Zone accuracy — % time in intended zone
3. Recovery quality — how well cooldown was executed

### 6B. Last-5-Session Trend

**Home screen addition:** Simple sparkline or bar chart showing last 5 CoachScores.

**Data source:** `WorkoutHistory` (already saved via `POST /workouts` and read via `GET /workouts`).

**Visual:** Minimal — 5 small bars with score labels, inside existing home screen layout. Teal gradient for bars.

### 6C. Share Card (Stretch Goal)

**After workout:** "Del okten" / "Share workout" button generates image:
- Coachi branding (logo + gradient background)
- CoachScore (large number)
- Workout summary: duration, distance (if available), mode
- "coachi.app" URL

**Implementation:** SwiftUI view rendered to UIImage, shared via `UIActivityViewController`.

### 6D. Free vs Premium Framing (MVP, Stretch Goal)

**In-app, post-workout or settings:**
- Free: Live coaching, daily CoachScore, workout history
- Premium (25 kr/mo): Full history, predictions, extended coaching sessions, priority voice

**MVP level:** Just a card showing what's free vs premium. No paywall enforcement yet. Establishes the value frame before billing is built.

---

## Day 7: Stabilize & Launch

### 7A. Full Regression Test

**Test matrix:**

| Test | EN | NO | Pass? |
|------|----|----|-------|
| First-run onboarding flow | | | |
| Coach intro plays (first workout) | | | |
| Orb state overlay shows + dismisses | | | |
| Active workout: cues fire within 10s | | | |
| Active workout: Norwegian sounds natural | | | |
| Workout completion: CoachScore shows | | | |
| CoachScore breakdown renders | | | |
| Session history trend on home | | | |
| Website loads on mobile | | | |
| Website: download CTA works | | | |
| Website: waitlist form persists | | | |
| Website: NO/EN toggle works | | | |
| Website: FAQ expands/collapses | | | |
| Language switch mid-app | | | |

### 7B. Fix Only Launch Blockers

**Definition of launch blocker:**
- App crashes
- Coaching goes silent for > 30 seconds
- Waitlist loses data
- Website download links broken
- Website broken on mobile

**NOT a launch blocker:**
- Cosmetic polish
- Share card edge cases
- Premium framing copy tweaks

### 7C. Production Release

1. Push final commits to `main`
2. Verify Render auto-deploy succeeds
3. Run `scripts/release_check.sh`
4. Submit iOS build to TestFlight / App Store
5. Monitor first 24h:
   - Render logs for coaching metrics
   - Waitlist signup count
   - Crash reports (Xcode Organizer)

---

## Launch KPIs

| Metric | Target | How to measure |
|--------|--------|---------------|
| Waitlist data loss | 0 | DB row count vs signup events logged |
| Website app-download click-through | Up from current | Analytics event tracking on CTA clicks |
| First workout completion rate | Up from current | `POST /workouts` count / app installs |
| Day-1 return rate | Up from current | Unique users day 2 / unique users day 1 |
| Coaching fallback/validation errors | Stable, < 10% | `COACHING_METRICS` log line |

---

## If Time Gets Tight

**Non-negotiable (Days 1-4):**
- Waitlist persistence
- Website redesign (download-focused)
- Backend mirror elimination
- Coaching enforcement on
- Norwegian quality upgrade

**Stretch (Days 5-7):**
- Share card
- Premium value framing
- Full trend view (can ship with just CoachScore breakdown)
- Orb overlay (can skip — coach intro alone helps)

---

## Files Expected to Change

**Day 1:**
- `main.py` — add WaitlistSignup model, update `/waitlist` endpoint
- `templates/index_codex.html` — full rewrite (new Mia-style structure)
- `templates/index_claude.html` — remove or redirect to codex

**Day 2:**
- Delete `backend/*.py` mirror files
- `CLAUDE.md` — remove sync instructions, update file paths
- `scripts/release_check.sh` — new file
- `config.py` — lock environment defaults

**Day 3:**
- `config.py` — flip `COACHING_VALIDATION_ENFORCE = True`
- `main.py` — add conditional timeline enforcement logic
- `voice_intelligence.py` or `coaching_engine.py` — add monitoring counters

**Day 4:**
- `norwegian_phrase_quality.py` — expand phrase bank + banlist
- `voice_intelligence.py` — phase-aware silence-break cues
- `config.py` — new silence-break cue banks per phase
- `tests_phaseb/test_norwegian_phrase_quality.py` — expand
- `tests_phaseb/test_silence_break_phase.py` — new

**Day 5:**
- `BackendAPIService.swift` — add `context` param to welcome call
- `WorkoutViewModel.swift` — first-workout detection, intro playback, reassurance text
- `Views/Components/OrbStateOverlayView.swift` — new view
- `main.py` — handle `context=first_workout` in `/welcome`

**Day 6:**
- `Views/Tabs/WorkoutCompletionView.swift` — CoachScore breakdown
- `Views/Tabs/HomeView.swift` — session trend sparkline
- `Views/Components/ShareCardView.swift` — new (stretch)
- `Views/Components/PremiumFramingCard.swift` — new (stretch)

**Day 7:**
- Bug fixes only
- `scripts/release_check.sh` — run and verify
