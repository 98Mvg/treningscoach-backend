# Coachi Landing Page — Design Document

> **Date:** 2026-02-18
> **Status:** Approved
> **Approach:** Single-page rewrite (Approach A)

## Goal

Replace the developer-facing workout player at `GET /` with a professional marketing landing page that scrolls into a live workout demo. Bilingual (NO/EN), Midnight Ember design system, pre-launch (waitlist instead of App Store link).

---

## Page Sections (scroll order)

| # | Section | Purpose |
|---|---------|---------|
| 1 | **Nav bar** | Logo "Coachi", section links, NO/EN toggle, CTA "Prøv gratis" |
| 2 | **Hero** | H1 + subtitle + dual CTA (scroll to demo / early access) |
| 3 | **Compatibility strip** | "Works with" device logos (Apple Watch, Garmin, Polar, Fitbit, Samsung) |
| 4 | **How It Works** | 3-step visual flow |
| 5 | **Features** | 3 cards highlighting key selling points |
| 6 | **Live Demo** | Embedded workout player (existing functionality, polished) |
| 7 | **Early Access** | Email waitlist capture form |
| 8 | **FAQ** | 4-5 real questions, data-driven for easy editing |
| 9 | **Footer** | Links, branding, API status |

---

## Key Selling Points (user-selected)

1. **AI Coach personality** — Real-time voice coaching that adapts to your intensity
2. **Multi-language voice** — Natural Norwegian and English with real ElevenLabs voices

Not highlighted on page (backend sensing detail, per R0.4):
- Breath-driven intelligence (mentioned only as "listens and adapts")

---

## Technical Architecture

### Single HTML file

`templates/index.html` — served by existing `GET /` route. No new files, no build step.

### Internal organization

```
templates/index.html
├── <!-- Developer Guide comment block -->
├── <head>         SEO meta, OG tags, Tailwind CDN, CSS custom properties
├── <style>        Midnight Ember tokens, section styles, animations
├── <body>         9 sections (each marked with ====== comments)
└── <script>
    ├── i18n       All user-facing strings (NO + EN)
    ├── Language    Toggle logic + localStorage persistence
    ├── Demo        Workout player (audio capture, coaching loop, UI state)
    ├── Waitlist    Email form → POST /waitlist
    ├── Analytics   Lightweight event logging → POST /analytics/event
    ├── FAQ         Data-driven render from faqData array
    └── Scroll      Smooth scroll + active nav highlighting
```

### CSS Design Tokens (Midnight Ember)

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

To change the entire color scheme: edit these 8 lines.

### Bilingual System

All user-facing text lives in one JS object:

```js
const i18n = {
  no: { hero_h1: "Din personlige AI-trener", ... },
  en: { hero_h1: "Your personal AI coach", ... }
};
```

HTML elements use `data-i18n="key"` attributes. The toggle function:
1. Swaps `textContent` for every `[data-i18n]` element
2. Updates `<html lang="...">`
3. Saves to `localStorage('coachi-lang')`

**To add a string:** Add one key to both `no` and `en` objects, add `data-i18n` to the HTML element.

**To add a language:** Add a third object (e.g. `da: {...}`), add flag to toggle UI.

### FAQ System

Data-driven — no HTML editing needed to add questions:

```js
const faqData = [
  {
    q: { no: "Er Coachi gratis?", en: "Is Coachi free?" },
    a: { no: "Ja, webdemoen er gratis...", en: "Yes, the web demo is free..." }
  },
  // Add more objects here
];
```

Rendered by JS into accordion elements on page load.

---

## Backend Changes

### New endpoints (2)

#### `POST /waitlist`

```
Request:  { "email": "user@example.com", "language": "no" }
Response: { "success": true }
Errors:   400 (missing/invalid email), 429 (rate limit)
```

- Stores in `WaitlistSignup` database model (email, language, timestamp, IP hash)
- Rate limit: 5 submissions per IP per hour (in-memory counter, resets on restart — acceptable for pre-launch)
- Email validation: basic format check only

#### `POST /analytics/event`

```
Request:  { "event": "demo_started", "metadata": { "language": "no" } }
Response: { "success": true }
```

- Server-side `logger.info()` with structured data
- Valid events: `demo_started`, `demo_mic_granted`, `demo_coaching_received`, `waitlist_signup`
- No external analytics SDK

### Route count

Current: 19 routes. After: 21 routes. Update CLAUDE.md endpoint table.

---

## SEO & Meta

```html
<title>Coachi — AI Treningscoach | Din personlige stemmecoach</title>
<meta name="description" content="Sanntids AI-stemmecoaching som tilpasser seg treningen din. Prøv gratis i nettleseren.">
<meta property="og:title" content="Coachi — Din personlige AI-trener">
<meta property="og:description" content="Sanntids stemmecoaching. Norsk og engelsk.">
<meta property="og:type" content="website">
<meta property="og:image" content="/og-image.png">
<meta name="twitter:card" content="summary_large_image">
```

- Single `<h1>` in hero
- Proper `<h2>`/`<h3>` hierarchy per section
- `<html lang="no">` default, toggled to `lang="en"` by switcher

---

## Analytics Events

| Event | When | Metadata |
|-------|------|----------|
| `demo_started` | User clicks "Try demo" button | `{ language }` |
| `demo_mic_granted` | Microphone permission accepted | `{ language }` |
| `demo_coaching_received` | First coaching audio plays | `{ language, brain_provider }` |
| `waitlist_signup` | Email submitted | `{ language }` |

Logged server-side via `navigator.sendBeacon('/analytics/event', ...)`. No cookies, no external SDKs.

---

## Explicitly Out of Scope (YAGNI)

- No CMS — copy lives in `i18n` object
- No blog or content pages
- No user accounts on web
- No cookie banner (no cookies used, only `localStorage` for language)
- No build step — Tailwind via CDN
- No separate hosting — same Flask server on Render

---

## Common Tasks Quick Reference

| Task | Where to edit |
|------|--------------|
| Change any text | `i18n` object in `<script>` (search `const i18n`) |
| Change colors | CSS `:root` custom properties |
| Add FAQ question | `faqData` array (search `const faqData`) |
| Add device to compatibility strip | HTML in compatibility section |
| Replace waitlist with App Store link | Swap `#waitlist` section HTML + remove `/waitlist` endpoint |
| Add a language | Add third object to `i18n`, add flag to toggle UI |
| Change OG image | Replace `/static/og-image.png`, update `<meta>` tag |

---

## Files Changed

| File | Change |
|------|--------|
| `templates/index.html` | Full rewrite (marketing + demo) |
| `backend/main.py` | Add `/waitlist` + `/analytics/event` routes |
| `main.py` | Sync from backend/ |
| `backend/database.py` | Add `WaitlistSignup` model |
| `database.py` | Sync from backend/ |
| `CLAUDE.md` | Update endpoint table (19 → 21) |

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

# Demo coaching still works (existing endpoint)
curl "https://treningscoach-backend.onrender.com/welcome?language=no"

# Route count = 21
python3 -c "import main; print(len([r for r in main.app.url_map.iter_rules() if r.endpoint != 'static']))"
```
