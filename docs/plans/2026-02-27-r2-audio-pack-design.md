# R2 Audio Pack — Pre-Generated Speech System

**Date:** 2026-02-27
**Status:** Approved
**Approach:** Backend-First R2 (Approach A)

## Problem

Every coaching cue during a workout triggers an ElevenLabs TTS API call (~$0.50/1000 chars). At 20-40 cues per workout, TTS is the dominant variable cost (~$1-3/user/month). Most of these cues are deterministic — the same phrase every time.

## Decision

Pre-generate all deterministic phrases as MP3 files, store on Cloudflare R2, download to iOS on first launch. Only call ElevenLabs at runtime for dynamic content (user names, custom BPM targets, summaries).

## Scope (v1)

- **Persona:** personal_trainer only (one voice per language)
- **Languages:** EN + NO
- **Static phrases:** ~130 core + ~30 extended = ~160 per language
- **Dynamic expanded:** ~23 (countdown/BPM variants)
- **Core bundle:** ~50 per language baked into iOS binary (~3-4MB)
- **Includes:** 10 motivation cues (new, to be added to catalog)

---

## 1. File Key & Pack Structure

### Naming

```
{lang}/{utteranceId}.mp3

Examples:
  en/welcome.standard.1.mp3
  no/cont.intense.calm.3.mp3
```

No voice/persona in path for v1. Future: `{lang}/{voiceKey}/{utteranceId}.mp3`.

### R2 Bucket Layout

```
coachi-audio/
  v1/
    manifest.json
    en/*.mp3
    no/*.mp3
```

### manifest.json

```json
{
  "version": "v1",
  "generated_at": "2026-02-27T14:00:00Z",
  "voice": "personal_trainer",
  "languages": ["en", "no"],
  "total_files": 260,
  "total_size_bytes": 8500000,
  "phrases": [
    {
      "id": "welcome.standard.1",
      "en": {"file": "en/welcome.standard.1.mp3", "size": 34200, "sha256": "abc123..."},
      "no": {"file": "no/welcome.standard.1.mp3", "size": 31800, "sha256": "def456..."}
    }
  ]
}
```

### iOS Core Bundle

~50 phrases per language selected from `priority: "core"`:
- 5 safety/critical
- 5 warmup
- 5 intense (one per sub-intensity)
- 5 cooldown
- 4 countdowns (30/15/5/start)
- 4 phase changes
- 4 zone cues
- 3 sensor notices
- 3 interrupt responses
- 2-3 welcome messages
- 10 motivation cues

---

## 2. Generation Pipeline

### Script: `tools/generate_audio_pack.py`

1. Reads `tts_phrase_catalog.py` (single source of truth)
2. Calls ElevenLabs for each phrase x each language
3. Saves to `output/audio_pack/v1/{lang}/{utteranceId}.mp3`
4. Generates `manifest.json` with SHA256 checksums
5. Uploads to R2

### Run manually, not on startup

```bash
python3 tools/generate_audio_pack.py --version v1
python3 tools/generate_audio_pack.py --version v1 --upload
```

### Voice settings locked per pack

```python
VOICE_SETTINGS_V1 = {
    "stability": 0.50,
    "similarity_boost": 0.75,
    "style": 0.0,
    "speed": 1.0,
}
```

All cues generated in one session with same voice, pacing, energy.

---

## 3. Runtime ElevenLabs Policy

### When ElevenLabs IS called

| Scenario | Example | Cached? |
|----------|---------|---------|
| User name personalization | "Nice work, Marius" | Yes |
| Custom interval targets | "Build toward 142-158 bpm" | Yes |
| Long motivational (AI) | Post-set encouragement | Yes |
| Post-workout summary | "Great session..." | Yes |

Rule: generate once, cache locally, reuse.

### When ElevenLabs is NEVER called

- Phase cues, zone cues, countdowns, sensor notices, safety, breathing timeline, motivation cues -> all local files.

### Backend TTS cache enabled

`TTS_AUDIO_CACHE_ENABLED=true` on Render for any remaining live calls.

---

## 4. Voice Quality Protocol

- Record all cues in one generation session
- Same voice ID, same pacing, same energy
- QA locally before upload to R2
- Pack version changes = full regeneration (not piecemeal patches)

---

## 5. iOS SpeechCoordinator

### Resolution order

```
event_type → utteranceId (existing mapper)
    ↓
SpeechCoordinator.play(utteranceId, language)
    ↓
1. R2 pack (Documents/audio_pack/v1/)
2. Bundled core pack (app binary)
3. Backend TTS download (current path, fallback)
```

### Pack download flow

```
App launch → check manifest version → download diff → save locally
No network → bundled core pack covers full workout
```

### Debug transcript

```
SPEECH utteranceId=zone.countdown.15 event=interval_countdown_15 source=r2_pack
SPEECH utteranceId=dynamic source=backend_tts text="Nice work, Marius"
```

Visible in AudioPipelineDiagnostics overlay.

---

## 6. Files

### New

| File | Type | Purpose |
|------|------|---------|
| `tts_phrase_catalog.py` | Backend | Source of truth (created) |
| `tools/generate_audio_pack.py` | Script | Generate + upload to R2 |
| `SpeechCoordinator.swift` | iOS | utteranceId -> local file playback |
| `AudioPackManager.swift` | iOS | R2 pack download + versioning |
| `Resources/CoreAudioPack/` | iOS | ~100 bundled MP3s |

### Modified

| File | Change |
|------|--------|
| `config.py` | R2 env vars, AUDIO_PACK_VERSION |
| `tts_phrase_catalog.py` | Add 10 motivation cues |
| `WorkoutViewModel.swift` | Route through SpeechCoordinator |
| `AudioPipelineDiagnostics.swift` | Transcript log display |

---

## 7. Cost Impact

| Metric | Before | After |
|--------|--------|-------|
| TTS calls per workout | 20-40 | 2-5 (dynamic only) |
| ElevenLabs cost/user/month | $1-3 | $0.10-0.30 |
| One-time generation cost | - | ~$0.50 |
| App size increase | - | ~3-4MB (core bundle) |

## 8. Future Expansion (zero refactor)

- Add toxic_mode: new pack v2 with different voice ID
- Add Danish: add `da` to catalog, regenerate
- Add second voice: manifest maps voiceKey, key becomes `{lang}/{voiceKey}/{id}.mp3`
- Update phrasing: edit catalog, regenerate, upload -> iOS auto-updates
