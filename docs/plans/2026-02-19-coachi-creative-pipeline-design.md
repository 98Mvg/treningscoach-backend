# Coachi Creative Pipeline — NanoBanana + Marketing Assets

**Date:** 2026-02-19
**Status:** Approved
**Scope:** Phase 1 of marketing visual system. Phase 2 (ClawdBot autonomous ad operations) is a separate future project.

---

## Goal

Set up NanoBanana MCP (Gemini-powered image generation) to create a branded visual asset library for the Coachi landing page, Instagram, and TikTok. All assets follow the Midnight Ember design system. Structured for future ClawdBot automation.

---

## 1. NanoBanana MCP Setup

- **MCP server:** `nanobanana-mcp-server` via uvx
- **Auth:** `GEMINI_API_KEY` env var (same key used by Gemini brain fallback)
- **Default model:** Nano Banana Pro (Gemini 3 Pro Image) — 4K, 5-8s, best for marketing assets
- **Output directory:** `marketing/assets/`
- **Config location:** `.claude/settings.local.json` or project MCP config

```json
{
  "mcpServers": {
    "nanobanana": {
      "command": "uvx",
      "args": ["nanobanana-mcp-server@latest"],
      "env": {
        "GEMINI_API_KEY": "${GEMINI_API_KEY}",
        "IMAGE_OUTPUT_DIR": "./marketing/assets"
      }
    }
  }
}
```

---

## 2. Brand Kit

### Palette (Midnight Ember)
| Token | Hex | Usage |
|-------|-----|-------|
| Primary BG | `#1a1a2e` | Dark backgrounds, base tone |
| Secondary BG | `#16213e` | Depth layers |
| Card BG | `#1e2a3a` | Surface elements |
| Accent Purple | `#7B68EE` | Primary accent, glow effects |
| Accent Cyan | `#00D9FF` | Secondary accent, pulse/tech elements |
| Success Green | `#34D399` | Positive states, heart rate |
| Text | `#FFFFFF` | Primary text (overlaid separately, not in images) |

### Visual Mood
- **Dark, athletic, futuristic, pulse-driven**
- Cinematic lighting with dramatic shadows
- Neon purple and cyan as lighting/glow effects, not flat fills
- Photorealistic quality, not illustrated
- Think: gym at night lit by neon, smartwatch glowing on wrist, person mid-sprint

### Subjects
1. **Athletes working out** — running, lifting, HIIT, functional training
2. **Smartwatches showing pulse data** — wrist close-ups, glowing heart rate, connected tech
3. **Voice coaching visualization** — sound waves, audio cues from earbuds
4. **Gym environments** — dark, neon-lit, cinematic
5. **Coach in your pocket** — phone in hand/pocket/armband with Coachi UI glowing, pushing through a workout. Your AI coach is always with you, driving you harder.
6. **Human effort** — athlete mid-push with visible determination, coached by an invisible force

### Don'ts
- No bright/white backgrounds
- No cartoons or illustrations
- No "breathing app" or meditation imagery
- No stock-photo feel (overly clean, staged)
- No text baked into generated images (text overlaid separately)

---

## 3. Prompt Templates

### Base Style Prefix (shared by all templates)
```
Cinematic, dark atmosphere, Midnight Ember palette (#1a1a2e background),
neon purple (#7B68EE) and cyan (#00D9FF) accent lighting, dramatic shadows,
futuristic athletic aesthetic, no text overlays, photorealistic
```

### Template Catalog

| ID | Subject | Use Case | Aspect Ratio | Platform |
|----|---------|----------|-------------|----------|
| `hero-workout` | Athlete mid-sprint, smartwatch glowing on wrist, pulse data floating as subtle hologram | Hero section background | 16:9 | Website |
| `hero-coach-pocket` | Close-up of phone in hand/armband during workout, Coachi UI glowing, gym background | How It Works visual | 16:9 | Website |
| `ig-pulse-push` | Athlete pushing through intense set, smartwatch prominent, sweat + neon lighting | Grid post | 1:1 | Instagram |
| `ig-coach-voice` | Runner with earbuds, visible sound wave from phone, being coached through effort | Grid post | 1:1 | Instagram |
| `ig-watch-connect` | Wrist close-up with smartwatch, pulse line glowing cyan, dark gym backdrop | Grid post | 1:1 | Instagram |
| `ig-story-effort` | Full-body athlete in motion, dramatic vertical composition, purple/cyan rim lighting | Story | 9:16 | Instagram |
| `tiktok-cover-push` | Intense workout moment, coach-in-pocket concept, phone visible, vertical cinematic | Cover image | 9:16 | TikTok |
| `tiktok-cover-tech` | Smartwatch + phone combo, pulse data visualization, dark futuristic gym | Cover image | 9:16 | TikTok |
| `mockup-watch` | Apple Watch face showing heart rate, Coachi branding subtle, wrist during exercise | Product shot | 1:1 | Shared |
| `mockup-phone` | iPhone with Coachi workout screen, coaching orb active, held during training | Product shot | 4:3 | Shared |

### Full Prompt Example (hero-workout)
```
Cinematic, dark atmosphere, Midnight Ember palette (#1a1a2e background),
neon purple (#7B68EE) and cyan (#00D9FF) accent lighting, dramatic shadows,
futuristic athletic aesthetic, no text overlays, photorealistic.

An athlete mid-sprint on a dark indoor track, smartwatch glowing on their wrist
with a cyan pulse line. Subtle holographic heart rate data floats near the watch.
Purple rim lighting on the athlete's silhouette, deep shadows, shallow depth of field.
Wide 16:9 composition with space on the left for text overlay.
```

---

## 4. Directory Structure

```
marketing/
├── brand-kit.md                    — Visual identity rules (Section 2 above)
├── prompt-templates.md             — All 10 templates with full prompts
├── content-calendar.md             — 2-week Instagram/TikTok launch plan
├── assets/
│   ├── website/
│   │   ├── hero-workout.png
│   │   └── hero-coach-pocket.png
│   ├── instagram/
│   │   ├── ig-pulse-push.png
│   │   ├── ig-coach-voice.png
│   │   ├── ig-watch-connect.png
│   │   └── ig-story-effort.png
│   ├── tiktok/
│   │   ├── tiktok-cover-push.png
│   │   └── tiktok-cover-tech.png
│   └── mockups/
│       ├── mockup-watch.png
│       └── mockup-phone.png
```

### Git LFS
Generated images tracked via Git LFS:
```bash
git lfs install
git lfs track "marketing/assets/**/*.png"
git lfs track "marketing/assets/**/*.jpg"
git lfs track "marketing/assets/**/*.webp"
```

`.gitattributes` updated automatically by `git lfs track`.

---

## 5. Content Calendar (2-Week Launch Plan)

### Week 1 — "Meet Your AI Coach"

| Day | Platform | Template | Caption Theme (NO) | Caption Theme (EN) |
|-----|----------|----------|-------------------|-------------------|
| Mon | Instagram | `ig-pulse-push` | "Din puls. Din coach. Din trening." | "Your pulse. Your coach. Your workout." |
| Tue | TikTok | `tiktok-cover-push` | Video: "Hva om treneren din kjente pulsen din?" | Video: "What if your coach could feel your heartbeat?" |
| Wed | Instagram | `ig-watch-connect` | "Kobler til klokka di. Kjenner kroppen din." | "Connects to your watch. Knows your body." |
| Thu | TikTok | `tiktok-cover-tech` | Video: "Se hvordan AI-coaching funker i sanntid" | Video: "See how AI coaching works in real-time" |
| Fri | Instagram | `ig-coach-voice` | "En stemme som pusher deg videre." | "A voice that pushes you further." |
| Sat | IG Story | `ig-story-effort` | Poll: "Trener du med coach?" | Poll: "Do you train with a coach?" |

### Week 2 — "Push Harder"

| Day | Platform | Template | Caption Theme (NO) | Caption Theme (EN) |
|-----|----------|----------|-------------------|-------------------|
| Mon | Instagram | `ig-pulse-push` (variant) | "Coachi kjenner når du kan gi mer." | "Coachi knows when you can give more." |
| Tue | TikTok | `tiktok-cover-push` (variant) | Video: "Prøvde AI-coach for første gang" | Video: "Tried AI coaching for the first time" |
| Wed | Instagram | `mockup-watch` | "Apple Watch + Garmin + Polar. Coachi funker med alt." | "Apple Watch + Garmin + Polar. Coachi works with everything." |
| Thu | TikTok | User-generated concept | Video: Reaction to first AI coaching session | Same |

### Hashtag Strategy
**Norwegian:** #trening #aicoach #pulscoaching #smarttrening #treningscoach #coachi
**English:** #AIcoach #pulsecoaching #smartfitness #workouttech #coachi #fitnessAI

---

## 6. Landing Page Integration

### Hero Section
- `hero-workout.png` as `background-image` on hero div
- Dark gradient overlay: `linear-gradient(to right, rgba(26,26,46,0.9), rgba(26,26,46,0.5))`
- Text remains readable on left side
- Lazy loading via `loading="lazy"` on `<img>` or CSS background

### How It Works Section
- `hero-coach-pocket.png` as inline image beside the 3-step cards
- Placed on the right side, cards on the left (desktop), stacked on mobile

### Serving
- Images served from `static/` directory or via Flask `send_from_directory`
- Consider WebP conversion for faster loading (optional, PNG acceptable for launch)

---

## 7. Generation Workflow

1. Open Claude Code in the project
2. NanoBanana MCP is available as a tool
3. Use prompt template (copy from `prompt-templates.md`)
4. Generate image, review output
5. Re-generate with tweaks if needed (adjust lighting, composition, subject)
6. Save approved image to correct `marketing/assets/{platform}/` folder
7. Commit via Git LFS

### Quality Checklist Per Image
- [ ] Dark background (Midnight Ember base)
- [ ] Purple/cyan accent lighting present
- [ ] No text baked in
- [ ] No bright/white backgrounds
- [ ] No meditation/breathing imagery
- [ ] Matches intended platform aspect ratio
- [ ] Cinematic, not stock-photo
- [ ] Subject matches template description

---

## 8. Future: ClawdBot Integration (Phase 2, separate project)

The asset library and content calendar are structured for a future ClawdBot setup:
- **Dedicated physical computer** running Claude-powered automation
- **Autonomous Instagram/TikTok ad operations** — posting, engagement, ad management
- **Assets from this pipeline** feed directly into ClawdBot's content queue
- **Content calendar** becomes the scheduling input
- Design and implementation deferred to a separate project

---

## Implementation Steps

1. Set up Git LFS for image tracking
2. Create `marketing/` directory structure
3. Write `brand-kit.md` with full visual identity rules
4. Write `prompt-templates.md` with all 10 full prompts
5. Write `content-calendar.md` with 2-week plan
6. Configure NanoBanana MCP server
7. Generate all 10 images (review + iterate)
8. Integrate website images into `templates/index.html`
9. Commit everything (docs via git, assets via LFS)
