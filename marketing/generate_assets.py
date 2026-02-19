#!/usr/bin/env python3
"""
Coachi Marketing Asset Generator
Uses Google Gemini API to generate branded marketing images.
Run from project root: python3 marketing/generate_assets.py
"""
import os
import sys
import time
import base64
from pathlib import Path

try:
    from google import genai
except ImportError:
    print("ERROR: google-genai not installed. Run: pip3 install google-genai")
    sys.exit(1)

# --- Config ---
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    # Try loading from .env file
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                API_KEY = line.split("=", 1)[1].strip()
                break
    if not API_KEY:
        print("ERROR: GEMINI_API_KEY not set. Export it or add to .env")
        sys.exit(1)

ASSETS_DIR = Path(__file__).parent / "assets"

# --- Base style prefix ---
BASE_PREFIX = (
    "Cinematic, dark atmosphere, Midnight Ember palette (#1a1a2e background), "
    "neon purple (#7B68EE) and cyan (#00D9FF) accent lighting, dramatic shadows, "
    "futuristic athletic aesthetic, no text overlays, photorealistic."
)

# --- Templates ---
TEMPLATES = [
    {
        "id": "hero-workout",
        "dir": "website",
        "prompt": f"{BASE_PREFIX} An athlete mid-sprint on a dark indoor track, smartwatch glowing on their wrist with a cyan pulse line. Subtle holographic heart rate data floats near the watch. Purple rim lighting on the athlete's silhouette, deep shadows, shallow depth of field. Wide 16:9 composition with space on the left for text overlay.",
        "aspect_ratio": "16:9",
    },
    {
        "id": "hero-coach-pocket",
        "dir": "website",
        "prompt": f"{BASE_PREFIX} Close-up of a person's hand holding a phone during a gym workout, screen glowing with a coaching interface showing a pulsing orb and heart rate. Phone partially in an armband. Dark gym with equipment in background, neon purple and cyan highlights on metal surfaces. Wide 16:9 composition, phone centered-right.",
        "aspect_ratio": "16:9",
    },
    {
        "id": "ig-pulse-push",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} An athlete pushing through an intense dumbbell set, sweat visible, smartwatch prominent on wrist glowing cyan. Neon purple rim lighting defining their muscular form against the dark background. Square 1:1 composition, tight crop, high energy.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-coach-voice",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} A runner mid-stride outdoors at night, wireless earbuds visible, subtle sound wave visualization emanating from their ear in cyan. Phone in armband glowing softly. Purple streetlight glow in background, motion blur on surroundings. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-watch-connect",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} Extreme close-up of a wrist wearing a smartwatch during exercise, screen showing a glowing cyan heart rate line. Sweat droplets on the watch face catching purple and cyan light. Dark background, shallow depth of field. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-story-effort",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} Full-body shot of an athlete in explosive motion, box jump or burpee, captured mid-air. Purple and cyan rim lighting creating a dramatic silhouette. Dark gym environment, vertical 9:16 composition, dynamic angle from slightly below.",
        "aspect_ratio": "9:16",
    },
    {
        "id": "tiktok-cover-push",
        "dir": "tiktok",
        "prompt": f"{BASE_PREFIX} Intense workout moment: person gripping a barbell, phone visible in their pocket or nearby showing coaching interface. Dramatic overhead neon lighting in purple. Vertical 9:16 composition, moody, cinematic grain, coach-in-pocket concept.",
        "aspect_ratio": "9:16",
    },
    {
        "id": "tiktok-cover-tech",
        "dir": "tiktok",
        "prompt": f"{BASE_PREFIX} Flat lay of workout gear on dark surface: smartwatch showing pulse data, phone with coaching app interface, wireless earbuds, towel. Cyan and purple lighting from above casting dramatic shadows. Vertical 9:16 composition, tech-focused.",
        "aspect_ratio": "9:16",
    },
    {
        "id": "mockup-watch",
        "dir": "mockups",
        "prompt": f"{BASE_PREFIX} Apple Watch on a person's wrist during exercise, screen clearly showing a heart rate of 142 BPM with a glowing cyan pulse wave. Wrist slightly sweaty, gym equipment blurred in dark background. Purple accent light from the left. Square 1:1 composition, product photography style.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "mockup-phone",
        "dir": "mockups",
        "prompt": f"{BASE_PREFIX} iPhone held at slight angle showing a dark fitness coaching screen with a glowing purple orb and real-time heart rate display. Person's hand gripping the phone mid-workout, gym background dark and out of focus. 4:3 landscape composition, product photography style.",
        "aspect_ratio": "4:3",
    },
]


def generate_image(client, template):
    """Generate a single image using Gemini."""
    template_id = template["id"]
    output_dir = ASSETS_DIR / template["dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{template_id}.png"

    if output_path.exists():
        print(f"  SKIP {template_id} (already exists)")
        return True

    print(f"  Generating {template_id} ({template['aspect_ratio']})...")

    try:
        # Use Gemini 2.5 Flash with native image generation
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=f"Generate an image: {template['prompt']}",
            config=genai.types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract image from response parts
        if response and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    img_data = part.inline_data.data
                    output_path.write_bytes(img_data)
                    size_kb = len(img_data) / 1024
                    print(f"  OK {template_id} -> {output_path} ({size_kb:.0f} KB)")
                    return True

        print(f"  FAIL {template_id}: No image in response")
        return False

    except Exception as e:
        print(f"  FAIL {template_id}: {e}")
        return False


def main():
    print("=== Coachi Marketing Asset Generator ===\n")
    print(f"Output: {ASSETS_DIR}")
    print(f"Templates: {len(TEMPLATES)}\n")

    client = genai.Client(api_key=API_KEY)

    success = 0
    failed = []

    for i, template in enumerate(TEMPLATES, 1):
        print(f"[{i}/{len(TEMPLATES)}] {template['id']}")
        if generate_image(client, template):
            success += 1
        else:
            failed.append(template["id"])

        # Rate limit: small delay between requests
        if i < len(TEMPLATES):
            time.sleep(2)

    print(f"\n=== Done: {success}/{len(TEMPLATES)} generated ===")
    if failed:
        print(f"Failed: {', '.join(failed)}")
        print("Re-run to retry failed images (existing ones will be skipped)")


if __name__ == "__main__":
    main()
