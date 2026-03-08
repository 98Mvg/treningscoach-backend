# Website Redesign — Premium Visual Effects + How it Works Page

**Date:** 2026-03-08
**Status:** Approved

## Overview

Redesign `index_launch.html` as a single-file two-page experience (Home + How it Works) with JS hash routing, premium visual effects, and updated copy.

## Architecture

**Option B: Single HTML file with JS routing**
- Both pages live in `index_launch.html`
- Hash routing: `/` = Home, `/#how` = How it Works
- Shared nav + footer visible on both
- Fade transition between pages (300ms)
- No backend changes needed

## Changes

### Hero (Home)
- Split layout: 60/40 (text left, devices right)
- Phone mockup with app screenshot + Apple Watch with BPM
- New title: "Coachi, Få tydlig veiledning mens du løper ved hjelp av kunstig intellegens"
- New body: "Coachen hjelper deg og holde riktig tempo, basert puls og pust analyse."
- Phone fade-in from right + float bob animation
- Watch with heart pulse animation
- Parallax on background

### Two Numbers
- Delete "To tall" eyebrow
- Heading → "Få en score basert på kvaliteten på treningen"
- Score card: title → "Baseres på kvalitet", body → new copy, ring animates 0→100
- Zone card: pill → "Pulsklokke", body → new copy

### Visual Effects (Global)
- Scroll reveals: fade-up, fade-left, fade-right variants
- Stagger delays on card groups
- Counter animations (score 0→100, BPM 0→152)
- Parallax on hero background
- Phone float bob (3px, 3s loop)
- Watch heart pulse (scale 1→1.15, 0.8s)
- Hover lift on all cards (+translateY, deeper shadow)
- Nav blur (backdrop-filter)
- Page transitions (fade 300ms)

### How it Works Page
- 3-step vertical walkthrough, alternating image/text layout
- Step 1: "Last ned appen" (image left, text right)
- Step 2: "Koble til pulsklokke" (text left, image right)
- Step 3: "Få veiledning" (image left, text right)
- Phone mockup frames around screenshots
- Timeline connecting dots between steps
- Bottom CTA with download buttons

## Files Changed
- `templates/index_launch.html` — full rewrite
