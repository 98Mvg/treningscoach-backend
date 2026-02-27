# R2 Audio Pack — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Pre-generate all deterministic coaching audio, store on Cloudflare R2, play locally on iOS — eliminating ~90% of runtime ElevenLabs API calls.

**Architecture:** Backend script reads `tts_phrase_catalog.py`, generates MP3s via ElevenLabs, uploads to R2 with manifest. iOS `SpeechCoordinator` resolves utteranceId to local file before falling back to backend TTS. ~50 core phrases per language bundled in app binary.

**Tech Stack:** Python (boto3 for R2), ElevenLabs API, Swift (AVAudioPlayer, URLSession), Cloudflare R2 (S3-compatible API)

**Design doc:** `docs/plans/2026-02-27-r2-audio-pack-design.md`

---

## Task 1: Add 10 Motivation Cues to Phrase Catalog

**Files:**
- Modify: `tts_phrase_catalog.py` (add entries before the closing `]` of PHRASE_CATALOG, around line 280)

**Step 1: Add motivation phrases to PHRASE_CATALOG**

Add these 10 bilingual motivation cues after the last `zone.*` entry and before the closing `]`:

```python
    # -----------------------------------------------------------------
    # MOTIVATION — general encouragement cues
    # -----------------------------------------------------------------

    {"id": "motivation.1", "en": "You're doing great.", "no": "Du er kjempeflink.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.2", "en": "Strong work. Keep it up.", "no": "Sterkt. Fortsett slik.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.3", "en": "That's the effort I want to see.", "no": "Det er innsatsen jeg vil se.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.4", "en": "One step at a time. You got this.", "no": "Ett steg om gangen. Du klarer det.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.5", "en": "Discipline beats motivation. Keep going.", "no": "Disiplin slår motivasjon. Fortsett.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.6", "en": "This is where it counts.", "no": "Det er nå det gjelder.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.7", "en": "You showed up. Now finish it.", "no": "Du møtte opp. Nå fullfører du.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.8", "en": "Trust the process.", "no": "Stol på prosessen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.9", "en": "Every rep matters.", "no": "Hvert steg teller.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.10", "en": "Finish what you started.", "no": "Fullfør det du begynte på.", "persona": "personal_trainer", "priority": "core"},
```

**Step 2: Verify catalog integrity**

Run:
```bash
python3 tts_phrase_catalog.py
```
Expected: Static phrases count increases by 10 (157 → 167), core count increases by 10 (129 → 139).

**Step 3: Compile check**

Run:
```bash
python3 -m py_compile tts_phrase_catalog.py
```
Expected: No output (success).

**Step 4: Commit**

```bash
git add tts_phrase_catalog.py
git commit -m "Add 10 motivation cues to TTS phrase catalog"
```

---

## Task 2: Add R2 Config to config.py

**Files:**
- Modify: `config.py:133` (after TTS cache section)

**Step 1: Add R2 environment variables**

After line 133 (`TTS_AUDIO_CACHE_CLEANUP_INTERVAL_WRITES`), add:

```python

# ============================================
# R2 AUDIO PACK CONFIGURATION
# ============================================
R2_BUCKET_NAME = (os.getenv("R2_BUCKET_NAME", "coachi-audio") or "coachi-audio").strip()
R2_ACCOUNT_ID = (os.getenv("R2_ACCOUNT_ID", "") or "").strip()
R2_ACCESS_KEY_ID = (os.getenv("R2_ACCESS_KEY_ID", "") or "").strip()
R2_SECRET_ACCESS_KEY = (os.getenv("R2_SECRET_ACCESS_KEY", "") or "").strip()
R2_PUBLIC_URL = (os.getenv("R2_PUBLIC_URL", "") or "").strip()
AUDIO_PACK_VERSION = (os.getenv("AUDIO_PACK_VERSION", "v1") or "v1").strip()
```

**Step 2: Compile check**

Run:
```bash
python3 -m py_compile config.py
```
Expected: No output (success).

**Step 3: Commit**

```bash
git add config.py
git commit -m "Add R2 audio pack config variables"
```

---

## Task 3: Create Audio Pack Generation Script

**Files:**
- Create: `tools/generate_audio_pack.py`
- Dependency: `tts_phrase_catalog.py`, `elevenlabs_tts.py`, `config.py`

**Step 1: Create tools/ directory**

Run:
```bash
mkdir -p tools
```

**Step 2: Write the generation script**

Create `tools/generate_audio_pack.py`:

```python
#!/usr/bin/env python3
"""
Generate Audio Pack for Coachi

Reads tts_phrase_catalog.py, generates MP3 via ElevenLabs, uploads to R2.

Usage:
    # Generate all audio locally (QA first)
    python3 tools/generate_audio_pack.py --version v1

    # Generate only core priority
    python3 tools/generate_audio_pack.py --version v1 --core-only

    # Upload generated pack to R2
    python3 tools/generate_audio_pack.py --version v1 --upload

    # Generate + upload in one step
    python3 tools/generate_audio_pack.py --version v1 --upload --generate
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tts_phrase_catalog import (
    PHRASE_CATALOG,
    expand_dynamic_templates,
    get_core_phrases,
    get_all_static_phrases,
)


# Voice settings locked per pack version — all cues same voice, pacing, energy
VOICE_SETTINGS = {
    "v1": {
        "stability": 0.50,
        "similarity_boost": 0.75,
        "style": 0.0,
        "speed": 1.0,
    },
}

LANGUAGES = ["en", "no"]


def generate_pack(version: str, core_only: bool = False, dry_run: bool = False):
    """Generate all MP3 files for the audio pack."""

    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "output", "audio_pack", version,
    )

    voice_settings = VOICE_SETTINGS.get(version, VOICE_SETTINGS["v1"])

    # Collect all phrases to generate
    phrases = []
    for p in PHRASE_CATALOG:
        if core_only and p.get("priority") != "core":
            continue
        for lang in LANGUAGES:
            phrases.append({
                "id": p["id"],
                "text": p[lang],
                "language": lang,
                "persona": p["persona"],
            })

    # Add expanded dynamic templates
    for p in expand_dynamic_templates():
        for lang in LANGUAGES:
            phrases.append({
                "id": p["id"],
                "text": p[lang],
                "language": lang,
                "persona": p["persona"],
            })

    print(f"Audio Pack Generator v{version}")
    print(f"  Phrases to generate: {len(phrases)}")
    print(f"  Voice settings: {voice_settings}")
    print(f"  Output: {output_dir}")
    print(f"  Core only: {core_only}")
    print()

    if dry_run:
        print("DRY RUN — listing phrases without generating:")
        for p in phrases[:10]:
            print(f"  [{p['language']}] {p['id']}: {p['text'][:60]}...")
        print(f"  ... and {len(phrases) - 10} more")
        return output_dir

    # Initialize ElevenLabs TTS
    from elevenlabs_tts import ElevenLabsTTS
    import config

    api_key = os.getenv("ELEVENLABS_API_KEY") or getattr(config, "ELEVENLABS_API_KEY", None)
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not set")
        sys.exit(1)

    default_voice = os.getenv("ELEVENLABS_VOICE_ID", "")
    tts = ElevenLabsTTS(api_key=api_key, voice_id=default_voice)

    # Create output directories
    for lang in LANGUAGES:
        os.makedirs(os.path.join(output_dir, lang), exist_ok=True)

    manifest_phrases = {}
    generated = 0
    skipped = 0
    errors = 0

    for i, p in enumerate(phrases):
        phrase_id = p["id"]
        lang = p["language"]
        out_path = os.path.join(output_dir, lang, f"{phrase_id}.mp3")

        # Skip if already generated (resume support)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            skipped += 1
        else:
            try:
                tts.generate_audio(
                    text=p["text"],
                    output_path=out_path,
                    language=lang,
                    persona=p["persona"],
                    voice_pacing=voice_settings,
                )
                generated += 1
            except Exception as e:
                print(f"  ERROR [{lang}] {phrase_id}: {e}")
                errors += 1
                continue

        # Compute checksum
        with open(out_path, "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()
        size = os.path.getsize(out_path)

        # Build manifest entry
        if phrase_id not in manifest_phrases:
            manifest_phrases[phrase_id] = {"id": phrase_id}
        manifest_phrases[phrase_id][lang] = {
            "file": f"{lang}/{phrase_id}.mp3",
            "size": size,
            "sha256": sha,
        }

        if (i + 1) % 20 == 0:
            print(f"  Progress: {i + 1}/{len(phrases)} (generated={generated}, skipped={skipped}, errors={errors})")

    # Write manifest
    total_size = sum(
        entry[lang]["size"]
        for entry in manifest_phrases.values()
        for lang in LANGUAGES
        if lang in entry
    )

    manifest = {
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "voice": "personal_trainer",
        "voice_settings": voice_settings,
        "languages": LANGUAGES,
        "total_files": generated + skipped,
        "total_size_bytes": total_size,
        "phrases": list(manifest_phrases.values()),
    }

    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print()
    print(f"Done! Generated={generated}, Skipped={skipped}, Errors={errors}")
    print(f"Total size: {total_size / 1024 / 1024:.1f} MB")
    print(f"Manifest: {manifest_path}")

    return output_dir


def upload_to_r2(version: str, output_dir: str):
    """Upload generated pack to Cloudflare R2."""
    import boto3

    account_id = os.getenv("R2_ACCOUNT_ID", "")
    access_key = os.getenv("R2_ACCESS_KEY_ID", "")
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY", "")
    bucket_name = os.getenv("R2_BUCKET_NAME", "coachi-audio")

    if not all([account_id, access_key, secret_key]):
        print("ERROR: R2 credentials not set (R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY)")
        sys.exit(1)

    endpoint = f"https://{account_id}.r2.cloudflarestorage.com"

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
    )

    # Walk output directory and upload
    uploaded = 0
    for root, dirs, files in os.walk(output_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            rel_path = os.path.relpath(local_path, output_dir)
            r2_key = f"{version}/{rel_path}"

            content_type = "audio/mpeg" if filename.endswith(".mp3") else "application/json"

            print(f"  Uploading: {r2_key}")
            s3.upload_file(
                local_path,
                bucket_name,
                r2_key,
                ExtraArgs={"ContentType": content_type},
            )
            uploaded += 1

    print(f"Uploaded {uploaded} files to r2://{bucket_name}/{version}/")


def main():
    parser = argparse.ArgumentParser(description="Generate Coachi Audio Pack")
    parser.add_argument("--version", default="v1", help="Pack version (default: v1)")
    parser.add_argument("--core-only", action="store_true", help="Generate only core priority phrases")
    parser.add_argument("--generate", action="store_true", default=True, help="Generate audio files")
    parser.add_argument("--upload", action="store_true", help="Upload to R2 after generation")
    parser.add_argument("--upload-only", action="store_true", help="Upload existing files without regenerating")
    parser.add_argument("--dry-run", action="store_true", help="List phrases without generating")
    args = parser.parse_args()

    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "output", "audio_pack", args.version,
    )

    if not args.upload_only:
        output_dir = generate_pack(
            version=args.version,
            core_only=args.core_only,
            dry_run=args.dry_run,
        )

    if args.upload or args.upload_only:
        if not os.path.exists(output_dir):
            print(f"ERROR: Output directory {output_dir} does not exist. Run generation first.")
            sys.exit(1)
        upload_to_r2(args.version, output_dir)


if __name__ == "__main__":
    main()
```

**Step 3: Add boto3 to requirements.txt**

Append to `requirements.txt`:
```
boto3>=1.34.0
```

**Step 4: Verify script loads**

Run:
```bash
python3 tools/generate_audio_pack.py --dry-run --version v1
```
Expected: Lists phrase count and first 10 phrases without calling ElevenLabs.

**Step 5: Commit**

```bash
git add tools/generate_audio_pack.py requirements.txt
git commit -m "Add audio pack generation script with R2 upload"
```

---

## Task 4: Generate Audio Pack v1 and Upload to R2

**Files:**
- Uses: `tools/generate_audio_pack.py`, `tts_phrase_catalog.py`

**Prerequisite:** Set R2 credentials as environment variables (NOT in code):
```bash
export R2_ACCOUNT_ID="..."
export R2_ACCESS_KEY_ID="..."
export R2_SECRET_ACCESS_KEY="..."
export R2_BUCKET_NAME="coachi-audio"
export ELEVENLABS_API_KEY="..."
```

**Step 1: Create R2 bucket**

Use Cloudflare dashboard or wrangler CLI to create bucket `coachi-audio` with public access enabled.

**Step 2: Generate all audio locally**

Run:
```bash
python3 tools/generate_audio_pack.py --version v1
```
Expected: ~334 MP3 files generated in `output/audio_pack/v1/` (~5-10 min).

**Step 3: QA — listen to a sample**

Open a few files and verify:
- Consistent voice across phrases
- Norwegian sounds natural (not Danish)
- Pacing matches coaching energy
- No artifacts or cutoffs

```bash
# Quick spot check
open output/audio_pack/v1/en/welcome.standard.1.mp3
open output/audio_pack/v1/no/welcome.standard.1.mp3
open output/audio_pack/v1/en/cont.critical.1.mp3
open output/audio_pack/v1/no/motivation.5.mp3
```

**Step 4: Upload to R2**

Run:
```bash
python3 tools/generate_audio_pack.py --version v1 --upload-only
```
Expected: All files uploaded to `coachi-audio/v1/`.

**Step 5: Verify R2 manifest is accessible**

```bash
curl https://<R2_PUBLIC_URL>/v1/manifest.json | python3 -m json.tool | head -20
```
Expected: JSON manifest with version, phrase list, checksums.

**Step 6: Commit manifest for reference**

```bash
git add -f output/audio_pack/v1/manifest.json
git commit -m "Add v1 audio pack manifest (reference copy)"
```

Note: The MP3 files themselves are NOT committed (too large). Only the manifest for reference.

---

## Task 5: Select and Bundle Core Pack for iOS

**Files:**
- Create: `TreningsCoach/TreningsCoach/Resources/CoreAudioPack/en/*.mp3`
- Create: `TreningsCoach/TreningsCoach/Resources/CoreAudioPack/no/*.mp3`

**Step 1: Create a script to select core bundle files**

Create `tools/select_core_bundle.py`:

```python
#!/usr/bin/env python3
"""
Select ~50 core phrases per language for the iOS app bundle.
Copies from generated audio pack to the iOS Resources directory.
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tts_phrase_catalog import PHRASE_CATALOG

# Core bundle selection: ~50 most essential phrases
CORE_BUNDLE_IDS = [
    # Safety/critical (5)
    "coach.critical.1",
    "cont.critical.1", "cont.critical.2", "cont.critical.3", "cont.critical.4",

    # Warmup (5)
    "cont.warmup.1", "cont.warmup.2", "cont.warmup.3", "cont.warmup.4", "cont.warmup.5",

    # Intense — one per sub-intensity (5)
    "cont.intense.calm.1", "cont.intense.calm.2",
    "cont.intense.mod.1", "cont.intense.mod.2",
    "cont.intense.intense.1",

    # Cooldown (5)
    "cont.cooldown.1", "cont.cooldown.2", "cont.cooldown.3", "cont.cooldown.4", "cont.cooldown.5",

    # Countdowns (4)
    "zone.countdown.30", "zone.countdown.15", "zone.countdown.5", "zone.countdown.start",

    # Phase changes (4)
    "zone.main_started.1", "zone.workout_finished.1", "zone.phase.warmup.1", "zone.phase.cooldown.1",

    # Zone cues (4)
    "zone.above.minimal.1", "zone.below.minimal.1", "zone.in_zone.minimal.1", "zone.in_zone.default.1",

    # Sensor notices (3)
    "zone.watch_disconnected.1", "zone.no_sensors.1", "zone.watch_restored.1",

    # Interrupts (3)
    "breath.interrupt.cant_breathe.1", "breath.interrupt.slow_down.1", "breath.interrupt.dizzy.1",

    # Welcome (3)
    "welcome.standard.1", "welcome.standard.2", "welcome.beginner.1",

    # Motivation (10)
    "motivation.1", "motivation.2", "motivation.3", "motivation.4", "motivation.5",
    "motivation.6", "motivation.7", "motivation.8", "motivation.9", "motivation.10",

    # Silence overrides (3)
    "zone.silence.work.1", "zone.silence.rest.1", "zone.silence.default.1",
]

LANGUAGES = ["en", "no"]


def select_bundle(version: str = "v1"):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source_dir = os.path.join(root, "output", "audio_pack", version)
    target_dir = os.path.join(root, "TreningsCoach", "TreningsCoach", "Resources", "CoreAudioPack")

    if not os.path.exists(source_dir):
        print(f"ERROR: Source directory {source_dir} not found. Generate pack first.")
        sys.exit(1)

    copied = 0
    missing = 0

    for lang in LANGUAGES:
        lang_dir = os.path.join(target_dir, lang)
        os.makedirs(lang_dir, exist_ok=True)

        for phrase_id in CORE_BUNDLE_IDS:
            src = os.path.join(source_dir, lang, f"{phrase_id}.mp3")
            dst = os.path.join(lang_dir, f"{phrase_id}.mp3")

            if os.path.exists(src):
                shutil.copy2(src, dst)
                copied += 1
            else:
                print(f"  MISSING: {lang}/{phrase_id}.mp3")
                missing += 1

    print(f"Core bundle: {copied} files copied, {missing} missing")
    print(f"Bundle IDs: {len(CORE_BUNDLE_IDS)} per language × {len(LANGUAGES)} languages = {len(CORE_BUNDLE_IDS) * len(LANGUAGES)} files")
    print(f"Target: {target_dir}")


if __name__ == "__main__":
    select_bundle()
```

**Step 2: Run it after Task 4 generates the audio**

Run:
```bash
python3 tools/select_core_bundle.py
```
Expected: ~54 × 2 = ~108 MP3 files copied to `TreningsCoach/TreningsCoach/Resources/CoreAudioPack/`.

**Step 3: Add to Xcode project manually**

Since `.xcodeproj` is not in git, add the `CoreAudioPack` folder to the Xcode project:
1. In Xcode, right-click `Resources` group
2. Add Existing Files → select `CoreAudioPack` folder
3. Check "Create folder references" (blue folder icon)
4. Ensure target "TreningsCoach" is checked

**Step 4: Commit the bundle files**

```bash
git add TreningsCoach/TreningsCoach/Resources/CoreAudioPack/
git add tools/select_core_bundle.py
git commit -m "Add core audio bundle (54 phrases × 2 languages) for iOS"
```

---

## Task 6: Create AudioPackManager.swift (R2 Download + Versioning)

**Files:**
- Create: `TreningsCoach/TreningsCoach/Services/AudioPackManager.swift`

**Step 1: Write AudioPackManager**

```swift
import Foundation

/// Manages download and versioning of audio packs from Cloudflare R2.
/// Resolution order: R2 pack → bundled core pack → nil (fallback to backend TTS).
class AudioPackManager {

    static let shared = AudioPackManager()

    // MARK: - Configuration

    /// R2 public URL — set from Config or backend /health response
    private var r2BaseURL: String {
        // TODO: Replace with actual R2 public URL from Config.swift
        return "https://pub-XXXXXXXX.r2.dev"
    }

    private let packVersion = "v1"

    // MARK: - State

    private(set) var isPackDownloaded = false
    private(set) var localManifest: AudioPackManifest?
    private(set) var downloadProgress: Double = 0.0
    private(set) var isDownloading = false

    // MARK: - Paths

    /// Root directory for downloaded audio packs
    private var packRootDir: URL {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        return docs.appendingPathComponent("audio_pack")
    }

    /// Current version directory
    private var packDir: URL {
        packRootDir.appendingPathComponent(packVersion)
    }

    /// Manifest file path
    private var manifestPath: URL {
        packDir.appendingPathComponent("manifest.json")
    }

    // MARK: - Init

    private init() {
        loadLocalManifest()
    }

    // MARK: - Resolve utterance to local file

    /// Returns URL to local audio file for the given utteranceId and language.
    /// Checks: 1) R2 downloaded pack  2) Bundled core pack  3) nil
    func resolveAudio(utteranceId: String, language: String) -> URL? {
        // 1. Check R2 downloaded pack
        let r2File = packDir
            .appendingPathComponent(language)
            .appendingPathComponent("\(utteranceId).mp3")
        if FileManager.default.fileExists(atPath: r2File.path) {
            return r2File
        }

        // 2. Check bundled core pack
        if let bundled = Bundle.main.url(
            forResource: utteranceId,
            withExtension: "mp3",
            subdirectory: "CoreAudioPack/\(language)"
        ) {
            return bundled
        }

        // 3. Not available locally
        return nil
    }

    // MARK: - Pack Download

    /// Download pack from R2 if needed (call on app launch, background-safe).
    func downloadPackIfNeeded() async {
        guard !isDownloading else { return }
        isDownloading = true
        defer { isDownloading = false }

        do {
            // Fetch remote manifest
            let manifestURL = URL(string: "\(r2BaseURL)/\(packVersion)/manifest.json")!
            let (data, _) = try await URLSession.shared.data(from: manifestURL)
            let remote = try JSONDecoder().decode(AudioPackManifest.self, from: data)

            // Compare versions
            if let local = localManifest, local.version == remote.version {
                print("📦 Audio pack up to date (v\(local.version))")
                isPackDownloaded = true
                return
            }

            print("📦 Downloading audio pack v\(remote.version) (\(remote.totalFiles) files)...")

            // Create directories
            for lang in remote.languages {
                let langDir = packDir.appendingPathComponent(lang)
                try FileManager.default.createDirectory(at: langDir, withIntermediateDirectories: true)
            }

            // Download files
            var downloaded = 0
            let total = remote.phrases.count * remote.languages.count

            for phrase in remote.phrases {
                for lang in remote.languages {
                    guard let fileInfo = phrase.files[lang] else { continue }

                    let localPath = packDir.appendingPathComponent(fileInfo.file)
                    let remoteURL = URL(string: "\(r2BaseURL)/\(packVersion)/\(fileInfo.file)")!

                    // Skip if already downloaded and checksum matches
                    if FileManager.default.fileExists(atPath: localPath.path) {
                        if let localData = try? Data(contentsOf: localPath) {
                            let localSha = localData.sha256Hex()
                            if localSha == fileInfo.sha256 {
                                downloaded += 1
                                continue
                            }
                        }
                    }

                    let (fileData, _) = try await URLSession.shared.data(from: remoteURL)
                    try fileData.write(to: localPath)
                    downloaded += 1
                    downloadProgress = Double(downloaded) / Double(total)
                }
            }

            // Save manifest locally
            try data.write(to: manifestPath)
            localManifest = remote
            isPackDownloaded = true
            downloadProgress = 1.0

            print("📦 Audio pack v\(remote.version) downloaded: \(downloaded) files")

        } catch {
            print("📦 Audio pack download failed: \(error.localizedDescription)")
        }
    }

    // MARK: - Private

    private func loadLocalManifest() {
        guard FileManager.default.fileExists(atPath: manifestPath.path) else { return }
        do {
            let data = try Data(contentsOf: manifestPath)
            localManifest = try JSONDecoder().decode(AudioPackManifest.self, from: data)
            isPackDownloaded = true
        } catch {
            print("📦 Failed to load local manifest: \(error)")
        }
    }
}

// MARK: - Models

struct AudioPackManifest: Codable {
    let version: String
    let generatedAt: String
    let voice: String
    let languages: [String]
    let totalFiles: Int
    let totalSizeBytes: Int
    let phrases: [AudioPackPhrase]

    enum CodingKeys: String, CodingKey {
        case version
        case generatedAt = "generated_at"
        case voice
        case languages
        case totalFiles = "total_files"
        case totalSizeBytes = "total_size_bytes"
        case phrases
    }
}

struct AudioPackPhrase: Codable {
    let id: String
    let files: [String: AudioPackFile]

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)

        // Decode language keys dynamically (en, no, da, etc.)
        var files: [String: AudioPackFile] = [:]
        let allKeys = try decoder.container(keyedBy: DynamicCodingKey.self)
        for key in allKeys.allKeys {
            if key.stringValue != "id" {
                if let file = try? allKeys.decode(AudioPackFile.self, forKey: key) {
                    files[key.stringValue] = file
                }
            }
        }
        self.files = files
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: DynamicCodingKey.self)
        try container.encode(id, forKey: DynamicCodingKey(stringValue: "id")!)
        for (lang, file) in files {
            try container.encode(file, forKey: DynamicCodingKey(stringValue: lang)!)
        }
    }

    enum CodingKeys: String, CodingKey {
        case id
    }
}

struct AudioPackFile: Codable {
    let file: String
    let size: Int
    let sha256: String
}

// Dynamic coding key for language fields
struct DynamicCodingKey: CodingKey {
    var stringValue: String
    var intValue: Int?

    init?(stringValue: String) { self.stringValue = stringValue; self.intValue = nil }
    init?(intValue: Int) { self.stringValue = "\(intValue)"; self.intValue = intValue }
}

// SHA256 helper
extension Data {
    func sha256Hex() -> String {
        let hash = self.withUnsafeBytes { (bytes: UnsafeRawBufferPointer) -> [UInt8] in
            var hash = [UInt8](repeating: 0, count: 32)
            CC_SHA256(bytes.baseAddress, CC_LONG(self.count), &hash)
            return hash
        }
        return hash.map { String(format: "%02x", $0) }.joined()
    }
}

import CommonCrypto
```

**Step 2: Add file to Xcode project manually**

In Xcode: right-click Services group → Add Existing Files → `AudioPackManager.swift`.

**Step 3: Commit**

```bash
git add TreningsCoach/TreningsCoach/Services/AudioPackManager.swift
git commit -m "Add AudioPackManager for R2 pack download and versioning"
```

---

## Task 7: Create SpeechCoordinator.swift

**Files:**
- Create: `TreningsCoach/TreningsCoach/Services/SpeechCoordinator.swift`

**Step 1: Write SpeechCoordinator**

```swift
import AVFoundation
import Foundation

/// Routes utteranceId to local audio file or falls back to backend TTS.
/// Single entry point for all coaching speech during workouts.
class SpeechCoordinator {

    static let shared = SpeechCoordinator()

    private var audioPlayer: AVAudioPlayer?
    private let packManager = AudioPackManager.shared

    // MARK: - Transcript

    struct TranscriptEntry {
        let utteranceId: String
        let eventType: String
        let source: String    // "r2_pack", "bundled", "backend_tts"
        let text: String?
        let timestamp: Date
    }

    private(set) var transcript: [TranscriptEntry] = []

    // MARK: - Play

    /// Attempt to play audio for an utteranceId locally.
    /// Returns true if played from local file, false if caller should use backend TTS.
    func playLocal(utteranceId: String, language: String, eventType: String = "") async -> Bool {
        guard let fileURL = packManager.resolveAudio(utteranceId: utteranceId, language: language) else {
            return false
        }

        let source = fileURL.path.contains("audio_pack") ? "r2_pack" : "bundled"

        do {
            // Configure audio session for playback during recording
            let session = AVAudioSession.sharedInstance()
            if session.category != .playAndRecord {
                try? session.setActive(false)
                try session.setCategory(.playAndRecord, options: [.defaultToSpeaker, .allowBluetooth, .mixWithOthers])
                try session.setActive(true)
            }

            let data = try Data(contentsOf: fileURL)
            audioPlayer = try AVAudioPlayer(data: data)
            audioPlayer?.volume = 1.0
            audioPlayer?.play()

            // Wait for playback to finish
            if let duration = audioPlayer?.duration, duration > 0 {
                try await Task.sleep(nanoseconds: UInt64(duration * 1_000_000_000) + 200_000_000)
            }

            // Log transcript
            logTranscript(utteranceId: utteranceId, eventType: eventType, source: source, text: nil)

            print("📢 SPEECH utteranceId=\(utteranceId) event=\(eventType) source=\(source)")
            return true

        } catch {
            print("📢 SPEECH ERROR utteranceId=\(utteranceId) source=\(source) error=\(error.localizedDescription)")
            return false
        }
    }

    /// Log a backend TTS playback (called by WorkoutViewModel when falling back to backend).
    func logBackendTTS(text: String, eventType: String = "") {
        logTranscript(utteranceId: "dynamic", eventType: eventType, source: "backend_tts", text: text)
        print("📢 SPEECH utteranceId=dynamic event=\(eventType) source=backend_tts text=\"\(text.prefix(50))\"")
    }

    // MARK: - Pack Management

    /// Trigger pack download (call on app launch).
    func ensurePackReady() async {
        await packManager.downloadPackIfNeeded()
    }

    var isPackReady: Bool {
        packManager.isPackDownloaded
    }

    // MARK: - Private

    private func logTranscript(utteranceId: String, eventType: String, source: String, text: String?) {
        let entry = TranscriptEntry(
            utteranceId: utteranceId,
            eventType: eventType,
            source: source,
            text: text,
            timestamp: Date()
        )
        transcript.append(entry)

        // Keep last 100 entries
        if transcript.count > 100 {
            transcript.removeFirst(transcript.count - 100)
        }
    }
}
```

**Step 2: Add file to Xcode project manually**

In Xcode: right-click Services group → Add Existing Files → `SpeechCoordinator.swift`.

**Step 3: Commit**

```bash
git add TreningsCoach/TreningsCoach/Services/SpeechCoordinator.swift
git commit -m "Add SpeechCoordinator for local-first audio playback"
```

---

## Task 8: Integrate SpeechCoordinator into WorkoutViewModel

**Files:**
- Modify: `TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift`

This is the key integration point. The existing event router already maps `event_type → utteranceId`. We intercept at the playback step.

**Step 1: Add SpeechCoordinator property**

Near the top of WorkoutViewModel (around existing `private var audioPlayer` declaration), add:

```swift
private let speechCoordinator = SpeechCoordinator.shared
```

**Step 2: Modify playCoachAudio to try local first**

Find the existing `playCoachAudio` method (~line 2239). Replace its body with a local-first check:

```swift
private func playCoachAudio(_ audioURL: String, utteranceId: String? = nil, eventType: String? = nil) async {
    let lang = UserDefaults.standard.string(forKey: "app_language") ?? "en"

    // Try local file first (R2 pack → bundled core pack)
    if let uId = utteranceId {
        let playedLocally = await speechCoordinator.playLocal(
            utteranceId: uId,
            language: lang,
            eventType: eventType ?? ""
        )
        if playedLocally {
            return  // Played from local file — no backend download needed
        }
    }

    // Fallback: download from backend (existing behavior)
    do {
        let audioData = try await apiService.downloadVoiceAudio(from: audioURL)
        let timestamp = Int(Date().timeIntervalSince1970 * 1000)
        let tempURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("continuous_coach_\(timestamp).mp3")
        try audioData.write(to: tempURL)
        await playAudio(from: tempURL)

        // Log as backend TTS in transcript
        speechCoordinator.logBackendTTS(
            text: audioURL,
            eventType: eventType ?? ""
        )
    } catch {
        print("🔇 Audio playback error: \(error.localizedDescription)")
    }
}
```

**Step 3: Pass utteranceId through existing call sites**

Find each call to `playCoachAudio` and pass the resolved utteranceId. The key call site is in the continuous coaching loop (~line 2120-2122):

Change from:
```swift
await playCoachAudio(audioURL)
```

To:
```swift
await playCoachAudio(audioURL, utteranceId: lastResolvedUtteranceID, eventType: eventSpeechDecision.reason)
```

`lastResolvedUtteranceID` already exists in the event router logic.

For the welcome message call (~line 2232), pass nil utteranceId (welcome can use a known ID or fall through to backend):
```swift
await playCoachAudio(welcome.audioURL, utteranceId: "welcome.standard.1", eventType: "welcome")
```

**Step 4: Trigger pack download on app launch**

In the `startWorkout()` method or `init`, add:

```swift
Task {
    await speechCoordinator.ensurePackReady()
}
```

**Step 5: Commit**

```bash
git add TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift
git commit -m "Integrate SpeechCoordinator: local-first audio playback"
```

---

## Task 9: Add Transcript to AudioPipelineDiagnostics

**Files:**
- Modify: `TreningsCoach/TreningsCoach/Services/AudioPipelineDiagnostics.swift`

**Step 1: Add speech transcript stage to PipelineStage enum**

Find the `PipelineStage` enum (~line 27) and add a new case:

```swift
case speechTranscript = "SPEECH"
```

**Step 2: Add transcript logging method**

After the existing `log()` method (~line 236), add:

```swift
/// Log a speech coordinator event (local playback or backend fallback)
func logSpeech(utteranceId: String, eventType: String, source: String) {
    log(.speechTranscript, detail: "[\(source)] \(utteranceId) event=\(eventType)")
}
```

**Step 3: Call from SpeechCoordinator**

In `SpeechCoordinator.swift`, after each successful play, call:

```swift
AudioPipelineDiagnostics.shared.logSpeech(
    utteranceId: utteranceId,
    eventType: eventType,
    source: source
)
```

**Step 4: Commit**

```bash
git add TreningsCoach/TreningsCoach/Services/AudioPipelineDiagnostics.swift
git add TreningsCoach/TreningsCoach/Services/SpeechCoordinator.swift
git commit -m "Add speech transcript logging to diagnostics overlay"
```

---

## Task 10: Enable Backend TTS Cache + Add R2 Env Vars to Render

**Files:**
- Render dashboard (environment variables)

**Step 1: Set environment variables on Render**

In Render dashboard → Environment:

```
TTS_AUDIO_CACHE_ENABLED=true
R2_ACCOUNT_ID=<your account id>
R2_ACCESS_KEY_ID=<your access key>
R2_SECRET_ACCESS_KEY=<your secret key>
R2_BUCKET_NAME=coachi-audio
R2_PUBLIC_URL=<your R2 public URL>
AUDIO_PACK_VERSION=v1
```

**Step 2: Verify cache is enabled**

After deploy:
```bash
curl https://treningscoach-backend.onrender.com/tts/cache/stats
```
Expected: `"enabled": true` in response.

**Step 3: No commit needed** (env vars only)

---

## Task 11: Add .gitignore for Generated Audio

**Files:**
- Modify: `.gitignore`

**Step 1: Add audio pack output to gitignore**

Append to `.gitignore`:

```
# Generated audio packs (large MP3 files)
output/audio_pack/*/en/
output/audio_pack/*/no/
# Keep manifests
!output/audio_pack/*/manifest.json
```

**Step 2: Commit**

```bash
git add .gitignore
git commit -m "Ignore generated audio pack MP3s in git"
```

---

## Task 12: End-to-End Verification

**Step 1: Backend verification**

```bash
# Health check
curl https://treningscoach-backend.onrender.com/health

# TTS cache enabled
curl https://treningscoach-backend.onrender.com/tts/cache/stats

# Manifest accessible from R2
curl https://<R2_PUBLIC_URL>/v1/manifest.json | head -5
```

**Step 2: iOS verification**

1. Build and run in simulator
2. Check console for `📦 Audio pack v1 downloaded` on launch
3. Start a workout
4. Check console for `📢 SPEECH utteranceId=... source=r2_pack` (local playback)
5. Long-press orb → diagnostics overlay → verify SPEECH entries appear

**Step 3: Verify no backend TTS for deterministic cues**

During workout, check backend logs — deterministic phrases should NOT trigger ElevenLabs calls. Only dynamic text (names, BPM targets) should hit TTS.

**Step 4: Verify bundled fallback**

1. Turn off WiFi on simulator
2. Delete downloaded pack: `FileManager.default.removeItem(at: packDir)`
3. Start workout
4. Console should show `📢 SPEECH utteranceId=... source=bundled`

---

## Summary: Execution Order

| Task | What | Commits |
|------|------|---------|
| 1 | Add motivation cues to catalog | 1 |
| 2 | Add R2 config to config.py | 1 |
| 3 | Create generation script | 1 |
| 4 | Generate audio + upload to R2 | 1 |
| 5 | Select + bundle core pack | 1 |
| 6 | AudioPackManager.swift | 1 |
| 7 | SpeechCoordinator.swift | 1 |
| 8 | Integrate into WorkoutViewModel | 1 |
| 9 | Transcript logging | 1 |
| 10 | Enable cache + R2 env vars on Render | 0 |
| 11 | .gitignore for audio files | 1 |
| 12 | End-to-end verification | 0 |
| **Total** | | **9 commits** |

Tasks 1-5 are backend/tooling. Tasks 6-9 are iOS. Tasks 10-12 are deployment + verification. Backend and iOS can be done in parallel after Task 4.
