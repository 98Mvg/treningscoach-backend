# Manifest-as-Source-of-Truth Audio Pack Sync (2026-03-01)

## What we built

A manifest-driven sync system for the R2 audio pack. The iOS app now checks R2 for the latest manifest on every launch, downloads new/changed files, and deletes stale files — all based on SHA256 hashes. This replaces the previous lazy per-file download approach (no version tracking, no cleanup, no replace support).

## Why

Codex's original R2 audio pack implementation (Tasks 1-11) inlined lazy download into `WorkoutViewModel`. Once a file was cached locally, it stayed forever — even if the MP3 sounded bad and we uploaded a replacement. There was no way to:
- Replace a bad-sounding MP3 (same utteranceId, new audio)
- Remove a phrase from rotation
- Know which version the user has
- Clean up orphaned files

## Files created/changed

| File | Action | Purpose |
|------|--------|---------|
| `Services/AudioPackSyncManager.swift` | **CREATED** | Manifest sync engine (~386 lines) |
| `ViewModels/WorkoutViewModel.swift` | **EDITED** (3 changes) | Dynamic version, sync trigger, post-workout purge |
| `Views/ContentView.swift` | **EDITED** (1 line) | Trigger sync on app launch |
| `Views/Settings/SettingsView.swift` | **EDITED** | Voice Pack section with status/reset/purge |
| `Localization/L10n.swift` | **EDITED** (3 strings) | voicePackTitle, resetVoicePack, purgeStaleFiles |

All files are in `TreningsCoach/TreningsCoach/` (iOS project).

## How the sync works

1. App launches → `MainTabView.onAppear` calls `workoutViewModel.triggerAudioPackSync()`
2. `AudioPackSyncManager.syncIfNeeded()` fetches `{r2PublicURL}/latest.json`
3. Fetches `manifest.json` from URL in latest.json
4. Computes SHA256 of manifest bytes → compares to stored hash in UserDefaults
5. If hash OR version changed:
   - Parses manifest, iterates all phrases × languages
   - For each file: compares local SHA256 vs manifest SHA256
   - Downloads missing/changed files (atomic write after hash verification)
   - Deletes local `.mp3` files NOT in manifest (only when workout is idle)
6. Persists new version + manifest hash + timestamp to UserDefaults

## Key design decisions

### SHA256 double-check
- **Manifest-level**: SHA256 of raw manifest.json bytes detects ANY manifest change (even same version, updated content)
- **Per-file**: SHA256 of each MP3 detects replacements (same path, new audio)
- Uses `CryptoKit.SHA256` (iOS 13+ system framework, no deps)

### Workout safety
- Stale file cleanup ONLY runs when `workoutState == .idle || .complete`
- During active workout: new files download, but no deletions
- `resetWorkout()` calls `purgeStaleFiles()` to catch deferred cleanup

### Version directory isolation
- Each pack version gets its own folder: `Documents/audio_pack/v1/`
- Files stored at: `Documents/audio_pack/{version}/{lang}/{phraseId}.mp3`

### Re-entry guard
- `syncIfNeeded()` checks `syncState` at entry — only runs from `.idle`, `.complete`, or `.failed`
- Prevents duplicate syncs from multiple triggers

## UserDefaults keys

| Key | Type | Purpose |
|-----|------|---------|
| `audio_pack_current_version` | String | e.g. "v1" |
| `audio_pack_manifest_hash` | String | SHA256 hex of manifest.json raw bytes |
| `audio_pack_last_sync_at` | Double | epoch timestamp |

## WorkoutViewModel integration (3 changes)

1. **`audioPackVersion`** now reads from `AudioPackSyncManager.shared.currentPackVersion` with fallback to `AppConfig.AudioPack.version`. This makes ALL existing methods (`localPackFileURL`, `downloadAudioPackFileIfNeeded`, `remotePackFileURLs`) automatically use the synced version — zero changes to those methods.

2. **`triggerAudioPackSync()`** — new method, called from `MainTabView.onAppear`. Fires async, doesn't block UI.

3. **`resetWorkout()`** — added `AudioPackSyncManager.shared.purgeStaleFiles()` after `workoutState = .idle` for deferred cleanup.

## Settings UI (Voice Pack section)

SettingsView now shows:
- Voice pack status: version, file count, size in MB, last sync relative time
- Live progress during sync (ProgressView spinner, "Downloading 12/60...")
- "Reset Voice Pack" button (red) — deletes all local files and re-syncs from scratch
- "Purge Stale Files" button (secondary) — manual stale cleanup

Observes `AudioPackSyncManager.shared` via `@ObservedObject` for live state updates.

## How to replace a bad MP3

This is the primary use case the sync system was built for:

1. Generate a new MP3 for the same utteranceId
2. Upload it to R2 at the same path (overwrites old file)
3. Update `manifest.json` with the new SHA256 hash
4. Upload updated `manifest.json` to R2
5. On next app launch, sync detects hash mismatch → downloads new file → overwrites local

## How to remove a phrase from rotation

1. Remove the phrase entry from `manifest.json`
2. Upload updated `manifest.json` to R2
3. On next app launch, sync sees the local file has no manifest entry → deletes it

## Verified behavior (2026-03-01)

First sync on real device:
- **60 files downloaded** (new/changed)
- **382 stale files cleaned** (orphaned from previous lazy-download approach)
- Version locked to `v1`

## Fallback chain (unchanged)

The 4-tier fallback in `WorkoutViewModel.playCoachAudio()` is unaffected:
1. Local pack file (now manifest-synced)
2. Bundled core pack (`CoreAudioPack/`)
3. R2 on-demand download
4. Backend TTS generation

## Rules for future changes

- **Never delete files during active workout** — the guard is in `syncIfNeeded(workoutState:)` and `resetWorkout()` purge
- **Always verify SHA256 before writing** — prevents corrupt/partial downloads from persisting
- **Manifest is source of truth** — if a file isn't in the manifest, it shouldn't exist locally
- **`AudioPackSyncManager` is `@MainActor` singleton** — all UI observation is safe
- **New file must be in Xcode project** — `AudioPackSyncManager.swift` was manually added to the Services group (not in git-tracked pbxproj)
