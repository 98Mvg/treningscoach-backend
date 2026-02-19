# Coachi Creative Pipeline — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Set up NanoBanana MCP image generation, create marketing docs (brand kit, prompt templates, content calendar), generate 10 branded assets, and wire website images into the landing page.

**Architecture:** NanoBanana MCP server connects to Claude Code via project settings, uses Gemini API for image generation. Marketing docs and directory structure live in `marketing/`. Generated images tracked via Git LFS. Two website images integrated into `templates/index.html` as hero background and How It Works visual. Flask serves them from a new `static/` directory.

**Tech Stack:** NanoBanana MCP (Gemini 3 Pro Image), Git LFS, Flask static file serving, Tailwind CSS

---

### Task 1: Install Git LFS and configure image tracking

**Files:**
- Create: `.gitattributes`

**Step 1: Install Git LFS**

Run: `brew install git-lfs`
Expected: `==> git-lfs ... installed`

**Step 2: Initialize Git LFS in repo**

Run: `cd /Users/mariusgaarder/Documents/treningscoach/.claude/worktrees/elegant-bardeen && git lfs install`
Expected: `Updated git hooks. Git LFS initialized.`

**Step 3: Track image files in marketing/assets/**

Run:
```bash
git lfs track "marketing/assets/**/*.png"
git lfs track "marketing/assets/**/*.jpg"
git lfs track "marketing/assets/**/*.webp"
git lfs track "static/**/*.png"
git lfs track "static/**/*.jpg"
git lfs track "static/**/*.webp"
```
Expected: `.gitattributes` created/updated with 6 entries.

**Step 4: Verify .gitattributes**

Run: `cat .gitattributes`
Expected: 6 lines with `filter=lfs diff=lfs merge=lfs -text`

**Step 5: Commit**

```bash
git add .gitattributes
git commit -m "chore: configure Git LFS for marketing/assets and static images"
```

---

### Task 2: Create marketing directory structure

**Files:**
- Create: `marketing/assets/website/.gitkeep`
- Create: `marketing/assets/instagram/.gitkeep`
- Create: `marketing/assets/tiktok/.gitkeep`
- Create: `marketing/assets/mockups/.gitkeep`

**Step 1: Create all directories with .gitkeep files**

Run:
```bash
cd /Users/mariusgaarder/Documents/treningscoach/.claude/worktrees/elegant-bardeen
mkdir -p marketing/assets/website marketing/assets/instagram marketing/assets/tiktok marketing/assets/mockups static
touch marketing/assets/website/.gitkeep marketing/assets/instagram/.gitkeep marketing/assets/tiktok/.gitkeep marketing/assets/mockups/.gitkeep static/.gitkeep
```
Expected: Directories created, no errors.

**Step 2: Verify structure**

Run: `find marketing -type f`
Expected: 4 `.gitkeep` files in correct subdirectories.

**Step 3: Commit**

```bash
git add marketing/ static/
git commit -m "chore: create marketing asset directory structure + static dir"
```

---

### Task 3: Write brand-kit.md

**Files:**
- Create: `marketing/brand-kit.md`

**Step 1: Write the brand kit document**

Create `marketing/brand-kit.md` with the full brand identity from the design doc Section 2:
- Midnight Ember palette table (7 colors with hex + usage)
- Visual mood rules (dark, athletic, futuristic, pulse-driven, cinematic lighting, photorealistic)
- Subject list (6 subjects including "Coach in your pocket")
- Don'ts list (5 rules: no white backgrounds, no cartoons, no breathing imagery, no stock-photo feel, no baked text)
- Quality checklist (8 checkboxes)

**Step 2: Verify**

Run: `wc -l marketing/brand-kit.md`
Expected: ~60-80 lines.

**Step 3: Commit**

```bash
git add marketing/brand-kit.md
git commit -m "docs: Coachi brand kit — Midnight Ember visual identity for marketing assets"
```

---

### Task 4: Write prompt-templates.md

**Files:**
- Create: `marketing/prompt-templates.md`

**Step 1: Write the prompt templates document**

Create `marketing/prompt-templates.md` with all 10 templates from design doc Section 3. Each template MUST include:
- Template ID
- Full prompt text (base style prefix + subject-specific description + composition notes + aspect ratio instruction)
- Platform and use case
- Aspect ratio

The base style prefix shared by all:
```
Cinematic, dark atmosphere, Midnight Ember palette (#1a1a2e background),
neon purple (#7B68EE) and cyan (#00D9FF) accent lighting, dramatic shadows,
futuristic athletic aesthetic, no text overlays, photorealistic
```

Full prompts for all 10 templates:

1. **hero-workout** (16:9, website hero):
```
[base prefix]. An athlete mid-sprint on a dark indoor track, smartwatch glowing on their wrist with a cyan pulse line. Subtle holographic heart rate data floats near the watch. Purple rim lighting on the athlete's silhouette, deep shadows, shallow depth of field. Wide 16:9 composition with space on the left for text overlay.
```

2. **hero-coach-pocket** (16:9, website How It Works):
```
[base prefix]. Close-up of a person's hand holding a phone during a gym workout, screen glowing with a coaching interface showing a pulsing orb and heart rate. Phone partially in an armband. Dark gym with equipment in background, neon purple and cyan highlights on metal surfaces. Wide 16:9 composition, phone centered-right.
```

3. **ig-pulse-push** (1:1, Instagram grid):
```
[base prefix]. An athlete pushing through an intense dumbbell set, sweat visible, smartwatch prominent on wrist glowing cyan. Neon purple rim lighting defining their muscular form against the dark background. Square 1:1 composition, tight crop, high energy.
```

4. **ig-coach-voice** (1:1, Instagram grid):
```
[base prefix]. A runner mid-stride outdoors at night, wireless earbuds visible, subtle sound wave visualization emanating from their ear in cyan. Phone in armband glowing softly. Purple streetlight glow in background, motion blur on surroundings. Square 1:1 composition.
```

5. **ig-watch-connect** (1:1, Instagram grid):
```
[base prefix]. Extreme close-up of a wrist wearing a smartwatch during exercise, screen showing a glowing cyan heart rate line. Sweat droplets on the watch face catching purple and cyan light. Dark background, shallow depth of field. Square 1:1 composition.
```

6. **ig-story-effort** (9:16, Instagram story):
```
[base prefix]. Full-body shot of an athlete in explosive motion — box jump or burpee — captured mid-air. Purple and cyan rim lighting creating a dramatic silhouette. Dark gym environment, vertical 9:16 composition, dynamic angle from slightly below.
```

7. **tiktok-cover-push** (9:16, TikTok cover):
```
[base prefix]. Intense workout moment: person gripping a barbell, phone visible in their pocket or nearby showing coaching interface. Dramatic overhead neon lighting in purple. Vertical 9:16 composition, moody, cinematic grain, coach-in-pocket concept.
```

8. **tiktok-cover-tech** (9:16, TikTok cover):
```
[base prefix]. Flat lay of workout gear on dark surface: smartwatch showing pulse data, phone with coaching app interface, wireless earbuds, towel. Cyan and purple lighting from above casting dramatic shadows. Vertical 9:16 composition, tech-focused.
```

9. **mockup-watch** (1:1, shared product shot):
```
[base prefix]. Apple Watch on a person's wrist during exercise, screen clearly showing a heart rate of 142 BPM with a glowing cyan pulse wave. Wrist slightly sweaty, gym equipment blurred in dark background. Purple accent light from the left. Square 1:1 composition, product photography style.
```

10. **mockup-phone** (4:3, shared product shot):
```
[base prefix]. iPhone held at slight angle showing a dark fitness coaching screen with a glowing purple orb and real-time heart rate display. Person's hand gripping the phone mid-workout, gym background dark and out of focus. 4:3 landscape composition, product photography style.
```

**Step 2: Verify**

Run: `grep -c "^##" marketing/prompt-templates.md`
Expected: ~12-13 (section headers for each template + intro sections).

**Step 3: Commit**

```bash
git add marketing/prompt-templates.md
git commit -m "docs: 10 NanoBanana prompt templates for Coachi marketing assets"
```

---

### Task 5: Write content-calendar.md

**Files:**
- Create: `marketing/content-calendar.md`

**Step 1: Write the content calendar**

Create `marketing/content-calendar.md` with content from design doc Section 5:
- Week 1 table: "Meet Your AI Coach" (6 posts: Mon-Sat)
- Week 2 table: "Push Harder" (4 posts: Mon-Thu)
- Each entry: Day, Platform, Template ID, Caption (NO), Caption (EN)
- Hashtag strategy section (Norwegian + English hashtag sets)
- Posting time recommendations (Norwegian timezone, optimal engagement windows)

**Step 2: Verify**

Run: `wc -l marketing/content-calendar.md`
Expected: ~50-70 lines.

**Step 3: Commit**

```bash
git add marketing/content-calendar.md
git commit -m "docs: 2-week Instagram/TikTok content calendar for Coachi launch"
```

---

### Task 6: Configure NanoBanana MCP server

**Files:**
- Modify: `.claude/settings.local.json`

**Step 1: Read current settings**

Read `.claude/settings.local.json` to understand current structure (has `permissions.allow` array).

**Step 2: Add NanoBanana MCP server config**

Add `mcpServers` key to the existing settings JSON:
```json
{
  "permissions": { ... existing ... },
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

**Important:** Preserve ALL existing permissions. Only ADD the `mcpServers` key.

**Step 3: Verify JSON is valid**

Run: `python3 -c "import json; json.load(open('.claude/settings.local.json')); print('VALID JSON')"`
Expected: `VALID JSON`

**Step 4: No commit** — `.claude/settings.local.json` is local config, not committed.

---

### Task 7: Generate all 10 images with NanoBanana

**Files:**
- Create: `marketing/assets/website/hero-workout.png`
- Create: `marketing/assets/website/hero-coach-pocket.png`
- Create: `marketing/assets/instagram/ig-pulse-push.png`
- Create: `marketing/assets/instagram/ig-coach-voice.png`
- Create: `marketing/assets/instagram/ig-watch-connect.png`
- Create: `marketing/assets/instagram/ig-story-effort.png`
- Create: `marketing/assets/tiktok/tiktok-cover-push.png`
- Create: `marketing/assets/tiktok/tiktok-cover-tech.png`
- Create: `marketing/assets/mockups/mockup-watch.png`
- Create: `marketing/assets/mockups/mockup-phone.png`

**Step 1: Generate website images (2)**

Use NanoBanana MCP `generate_image` tool with full prompts from `marketing/prompt-templates.md`:
- `hero-workout` → save to `marketing/assets/website/hero-workout.png` (16:9, high resolution)
- `hero-coach-pocket` → save to `marketing/assets/website/hero-coach-pocket.png` (16:9, high resolution)

Use **Nano Banana Pro** model for maximum quality (these are hero images).

**Step 2: Review website images against quality checklist**

For each generated image, verify:
- [ ] Dark background (Midnight Ember base)
- [ ] Purple/cyan accent lighting present
- [ ] No text baked in
- [ ] Cinematic, not stock-photo
- [ ] Correct 16:9 aspect ratio
- [ ] Subject matches template description

Re-generate any that fail. Adjust prompt if needed (add details about lighting, remove unwanted elements).

**Step 3: Generate Instagram images (4)**

- `ig-pulse-push` → `marketing/assets/instagram/ig-pulse-push.png` (1:1)
- `ig-coach-voice` → `marketing/assets/instagram/ig-coach-voice.png` (1:1)
- `ig-watch-connect` → `marketing/assets/instagram/ig-watch-connect.png` (1:1)
- `ig-story-effort` → `marketing/assets/instagram/ig-story-effort.png` (9:16)

**Step 4: Review Instagram images against quality checklist**

Same checklist. Ensure 1:1 and 9:16 ratios are correct.

**Step 5: Generate TikTok images (2)**

- `tiktok-cover-push` → `marketing/assets/tiktok/tiktok-cover-push.png` (9:16)
- `tiktok-cover-tech` → `marketing/assets/tiktok/tiktok-cover-tech.png` (9:16)

**Step 6: Generate mockup images (2)**

- `mockup-watch` → `marketing/assets/mockups/mockup-watch.png` (1:1)
- `mockup-phone` → `marketing/assets/mockups/mockup-phone.png` (4:3)

**Step 7: Review all 10 images**

Run: `ls -la marketing/assets/website/ marketing/assets/instagram/ marketing/assets/tiktok/ marketing/assets/mockups/`
Expected: 10 PNG files across 4 directories (plus .gitkeep files).

**Step 8: Commit via Git LFS**

```bash
git add marketing/assets/
git commit -m "feat: generate 10 branded marketing assets via NanoBanana"
```

Verify LFS tracking: `git lfs ls-files`
Expected: 10 PNG files listed.

---

### Task 8: Copy website images to static/ and add Flask static route

**Files:**
- Create: `static/hero-workout.png` (copy from marketing/assets/website/)
- Create: `static/hero-coach-pocket.png` (copy from marketing/assets/website/)

**Step 1: Copy website images to static directory**

Run:
```bash
cp marketing/assets/website/hero-workout.png static/
cp marketing/assets/website/hero-coach-pocket.png static/
```

**Step 2: Verify Flask serves static files**

Flask auto-serves from `static/` directory by default. Verify:

Run: `python3 -c "from flask import Flask; app = Flask(__name__); print(app.static_folder)"`
Expected: path ending in `/static`

No backend code change needed — Flask's built-in static file serving handles `/static/<filename>`.

**Step 3: Commit**

```bash
git add static/
git commit -m "chore: add website hero images to static/ for Flask serving"
```

---

### Task 9: Integrate hero image into landing page

**Files:**
- Modify: `templates/index.html` (lines 209-230, hero section)

**Step 1: Add hero background image to the hero section**

Current hero section (line 210):
```html
<section class="min-h-screen flex flex-col items-center justify-center text-center px-6 pt-24 pb-16 relative">
```

Change to:
```html
<section class="min-h-screen flex flex-col items-center justify-center text-center px-6 pt-24 pb-16 relative" style="background: linear-gradient(to right, rgba(26,26,46,0.92), rgba(26,26,46,0.6)), url('/static/hero-workout.png') center/cover no-repeat;">
```

This adds:
- `hero-workout.png` as background image (cover, centered)
- Dark gradient overlay (0.92 opacity on left for text readability, 0.6 on right for image visibility)
- Text remains fully readable

**Step 2: Verify in browser**

Run: `PORT=5001 python3 main.py` (or use running server)
Open: `http://localhost:5001`
Expected: Hero section shows the athlete image behind the text with dark gradient overlay.

**Step 3: Commit**

```bash
git add templates/index.html
git commit -m "feat: add hero background image to landing page"
```

---

### Task 10: Integrate How It Works image into landing page

**Files:**
- Modify: `templates/index.html` (lines 248-270, How It Works section)

**Step 1: Add coach-pocket image to How It Works section**

Current How It Works section has 3 glass cards in a row. Add the image as a visual element above or beside the cards.

Insert after the subtitle `<p>` (line 252) and before the cards `<div>` (line 253):
```html
<div class="mb-12 max-w-2xl mx-auto rounded-2xl overflow-hidden border border-white/10">
    <img src="/static/hero-coach-pocket.png" alt="AI coach on your phone during workout" loading="lazy" class="w-full h-auto">
</div>
```

This adds:
- Full-width image between subtitle and cards
- Rounded corners matching design system
- Lazy loading for performance
- Border matching glass-card style

**Step 2: Verify in browser**

Open: `http://localhost:5001`
Scroll to How It Works section.
Expected: Coach-pocket image visible above the 3-step cards.

**Step 3: Commit**

```bash
git add templates/index.html
git commit -m "feat: add coach-pocket image to How It Works section"
```

---

### Task 11: Final verification and sync

**Files:**
- Verify all changes

**Step 1: Verify marketing directory completeness**

Run:
```bash
echo "=== Marketing docs ==="
ls marketing/*.md
echo "=== Asset counts ==="
ls marketing/assets/website/*.png | wc -l
ls marketing/assets/instagram/*.png | wc -l
ls marketing/assets/tiktok/*.png | wc -l
ls marketing/assets/mockups/*.png | wc -l
echo "=== Git LFS ==="
git lfs ls-files | wc -l
echo "=== Static ==="
ls static/*.png
```

Expected:
- 3 markdown docs (brand-kit, prompt-templates, content-calendar)
- 2 website, 4 instagram, 2 tiktok, 2 mockup PNGs
- 12+ LFS-tracked files
- 2 static PNGs

**Step 2: Verify landing page loads with images**

Run: `curl -s http://localhost:5001/ | grep -c "hero-workout.png"`
Expected: `1`

Run: `curl -s http://localhost:5001/ | grep -c "hero-coach-pocket.png"`
Expected: `1`

**Step 3: Verify backend sync (root ↔ backend)**

The only backend file that could have changed is `main.py` — but we're not modifying backend code (Flask auto-serves static/). Verify:

Run: `diff backend/main.py main.py && echo "SYNCED" || echo "OUT OF SYNC"`
Expected: `SYNCED`

**Step 4: Push**

Run: `git push origin claude/elegant-bardeen`
Expected: Push succeeds, LFS objects uploaded.
