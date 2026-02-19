# Coachi Landing Page v2 — Design Document

> **Date:** 2026-02-19
> **Status:** Approved
> **Approach:** Waitlist-first funnel (Approach A) with real-time pulse coaching focus

## Goal

Replace the developer-facing workout player at `GET /` with a professional marketing landing page. Waitlist conversion is the primary goal. Live demo is available but collapsed. Bilingual (NO/EN), Midnight Ember design system, pre-launch.

**Key messaging angle:** Real-time AI coach connected to your pulse via smartwatch. Not just a timer — it reads your heart rate and coaches you live.

---

## Page Sections (scroll order)

| # | Section | Purpose |
|---|---------|---------|
| 1 | **Nav bar** | Logo "Coachi", section links, NO/EN toggle, CTA "Fa tilgang" |
| 2 | **Hero** | H1 + subtitle + single CTA (waitlist) + secondary demo link |
| 3 | **Compatibility strip** | "Works with" — pulse focus: Apple Watch, Garmin, Polar, Fitbit, Samsung, Suunto |
| 4 | **How It Works** | 3-step: Connect watch → AI reads pulse → Real-time voice coaching |
| 5 | **Features** | 2 big cards (AI personality + pulse coaching) + 3 small cards |
| 6 | **Demo (collapsed)** | "Try it" button expands inline workout player |
| 7 | **Waitlist** | Email capture — the page's conversion goal |
| 8 | **FAQ** | 5 data-driven questions |
| 9 | **Footer** | Links, branding, API status |

---

## Detailed Section Design

### 1. Nav Bar
- Fixed top, blurred backdrop (`backdrop-blur-md`)
- Left: "Coachi" gradient logo (accent → cyan)
- Center (desktop only): section links — Slik funker det, Funksjoner, FAQ
- Right: NO/EN toggle pill + "Fa tilgang" accent button → `#waitlist`
- Mobile: logo + lang toggle + CTA (links hidden)

### 2. Hero
- Full viewport height, center-aligned
- **Badge:** Green pulse dot + "Sanntids AI-coaching basert pa pulsen din"
- **H1:** "Din personlige" (line 1) + "AI-treningscoach" (line 2, gradient)
- **Subtitle:** "Kobler seg til smartklokken din, leser pulsen i sanntid, og coacher deg med naturlig stemme — pa norsk og engelsk."
- **Primary CTA:** "Fa tidlig tilgang" (accent button → `#waitlist`)
- **Secondary:** Small text "Eller prov en demo" → `#demo`
- Bounce chevron at bottom

### 3. Compatibility Strip (Pulse Focus)
- Label: "Kobler til pulsen din via" (NO) / "Connects to your pulse via" (EN)
- Device names: Apple Watch, Garmin, Polar, Fitbit, Samsung, Suunto
- Small subtext: "Automatisk synkronisering av pulsdata" / "Automatic heart rate sync"

### 4. How It Works (Pulse-Centric Flow)
3 glass cards with gradient connectors:

| Step | Icon | Title (NO) | Description (NO) |
|------|------|------------|-------------------|
| 1 | ⌚ | Koble smartklokken | Koble til Apple Watch, Garmin eller annen klokke. Coachi leser pulsen din automatisk. |
| 2 | 💓 | AI leser pulsen din | Coachi analyserer puls og intensitet i sanntid. Vet nar du pusher og nar du hviler. |
| 3 | 🗣️ | Personlig stemmecoaching | Far motivasjon med naturlig stemme basert pa pulsen din — pa norsk eller engelsk. |

### 5. Features

**Two big cards (2-col desktop):**

1. **Sanntids pulscoaching** (NEW — primary feature)
   - "Coachi leser pulsen din i sanntid og tilpasser coachingen automatisk. Nar pulsen stiger, pusher coachen deg. Nar den synker, minner den deg pa a holde tempoet."
   - Tags: "💓 Pulsstyrt", "⚡ Sanntid"

2. **AI-coach med personlighet**
   - "Velg mellom stottende personlig trener eller toff drill sergeant. Coachi tilpasser tonen etter intensiteten din."
   - Tags: "Personlig trener", "Toxic mode"

**Three small cards (3-col):**

1. 🗣️ Naturlig stemme — Norsk og engelsk med ElevenLabs AI-stemmer
2. 📊 Smarte treningsfaser — Automatisk oppvarming, intensitet, nedkjoling
3. 🛡️ Sikkerhet forst — Overvaaker pulsen og sier fra nar du bor roe ned

### 6. Demo (Collapsed)
- Heading: "Prov Coachi na"
- One sentence: "Test stemmecoachingen direkte i nettleseren."
- **"Start demo" button** (secondary/outline style)
- On click: button hides → orb + workout player expands inline with smooth transition
- Full existing functionality preserved (mic, coaching loop, timer, pause/stop)
- Language follows current page language (`currentLang`)

### 7. Waitlist (Conversion Goal)
- Extra padding, visually prominent
- Heading: "Fa tidlig tilgang"
- Subtitle: "Coachi-appen kommer snart til App Store. Legg igjen e-posten din, sa varsler vi deg forst."
- Inline form: email input + "Registrer meg" button
- Below: "Ingen spam. Bare en melding nar appen er klar."
- States: success (green text), error (red text), loading (button disabled)

### 8. FAQ (Data-Driven)
5 questions in accordion:
1. Er Coachi gratis?
2. Hvordan fungerer pulscoachingen?
3. Fungerer Coachi med norsk?
4. Hvilke klokker stotter?
5. Hva er 'Toxic mode'?

### 9. Footer
- Logo + v3.0
- Links: API Status, Personvern, Vilkar
- Copyright: "2026 Coachi. Laget med <3 i Norge."

---

## Technical Architecture

### Single HTML file
`templates/index.html` — served by existing `GET /` route. No new files, no build step.

### Tailwind CSS via CDN
```html
<script src="https://cdn.tailwindcss.com"></script>
```
Custom config extends with Midnight Ember colors.

### CSS Design Tokens
```css
:root {
  --bg-primary:   #1a1a2e;
  --bg-secondary: #16213e;
  --bg-card:      #1e2a3a;
  --accent:       #7B68EE;
  --accent-cyan:  #00D9FF;
  --text:         #ffffff;
  --text-muted:   rgba(255,255,255,0.6);
  --text-dim:     rgba(255,255,255,0.4);
  --radius:       12px;
}
```

### Bilingual System
All text in one JS `i18n` object (`no` + `en`). HTML uses `data-i18n="key"`. Toggle swaps `textContent`, updates `<html lang>`, saves to `localStorage('coachi-lang')`.

### FAQ System
Data-driven `faqData` array. Rendered by JS into accordion. No HTML editing needed to add questions.

---

## Backend Changes

### New endpoints (2)

#### `POST /waitlist`
```
Request:  { "email": "user@example.com", "language": "no" }
Response: { "success": true }
Errors:   400 (missing/invalid email), 429 (rate limit)
```
- In-memory storage (list + rate limit counter)
- Rate limit: 5 per IP per hour
- Basic email format validation

#### `POST /analytics/event`
```
Request:  { "event": "demo_started", "metadata": { "language": "no" } }
Response: { "success": true }
```
- Server-side `logger.info()` only
- Valid events: `demo_started`, `demo_mic_granted`, `demo_coaching_received`, `waitlist_signup`

### Route count: 19 → 21

---

## Analytics Events

| Event | When | Metadata |
|-------|------|----------|
| `demo_started` | Click "Start demo" button | `{ language }` |
| `demo_mic_granted` | Microphone permission accepted | `{ language }` |
| `demo_coaching_received` | First coaching audio plays | `{ language }` |
| `waitlist_signup` | Email submitted | `{ language }` |

---

## Key Differences from v1 Design Doc

1. **Single CTA in hero** — waitlist only, not dual CTA
2. **Demo is collapsed** — expand on click, not a hero-level section
3. **Pulse coaching is primary feature** — "real-time heart rate coaching" messaging
4. **Compatibility strip is pulse-focused** — "Connects to your pulse via" not "Works with"
5. **How It Works is pulse-centric** — connect watch → AI reads pulse → voice coaching
6. **FAQ updated** — "How does pulse coaching work?" replaces generic question

---

## Quick Edit Reference

| Task | Where |
|------|-------|
| Change text | `i18n` object in `<script>` |
| Change colors | CSS `:root` custom properties |
| Add FAQ | `faqData` array |
| Add device | Compatibility strip HTML |
| Replace waitlist with App Store | Swap `#waitlist` HTML + remove `/waitlist` endpoint |
| Add language | Third object in `i18n` + flag in toggle |

---

## Verification

```bash
# Page loads
curl -s https://treningscoach-backend.onrender.com/ | grep -o '<title>.*</title>'

# Waitlist works
curl -X POST https://treningscoach-backend.onrender.com/waitlist \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","language":"no"}'

# Analytics works
curl -X POST https://treningscoach-backend.onrender.com/analytics/event \
  -H "Content-Type: application/json" \
  -d '{"event":"demo_started","metadata":{"language":"no"}}'

# Route count = 21
python3 -c "import main; print(len([r for r in main.app.url_map.iter_rules() if r.endpoint != 'static']))"
```
