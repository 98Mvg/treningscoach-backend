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
    "Professional photograph taken with a DSLR camera in a real gym. "
    "Real person, natural skin texture, real sweat. Moody low-key lighting, "
    "dark environment. Shot looks like it was taken by a professional fitness "
    "photographer for a magazine editorial. No CGI, no holograms, no digital "
    "effects, no glowing outlines. Natural colors with subtle warm and cool "
    "tones from ambient gym lighting. No text overlays. High resolution, "
    "sharp focus on subject, shallow depth of field."
)

# --- Templates ---
TEMPLATES = [
    {
        "id": "hero-workout",
        "dir": "website",
        "prompt": f"{BASE_PREFIX} A real person sprinting on an indoor track in a dimly lit gym. They are wearing a smartwatch and athletic clothes. The gym has moody overhead lighting casting pools of warm light. Sweat on their skin. Shot from a low angle, dramatic perspective. Wide 16:9 composition with negative space on the left side for text overlay. Looks like a Nike or Adidas campaign photo.",
        "aspect_ratio": "16:9",
    },
    {
        "id": "hero-coach-pocket",
        "dir": "website",
        "prompt": f"{BASE_PREFIX} A real person in a gym checking their iPhone between sets. The phone screen shows a dark fitness app with a glowing orange orb and circular progress ring. They are sweaty, wearing workout clothes, gym equipment visible in the blurred background. Natural gym lighting, slightly warm tones. The phone screen is the brightest element in the image. Wide 16:9 composition, candid feel like someone snapped the photo during a real workout.",
        "aspect_ratio": "16:9",
    },
    {
        "id": "ig-pulse-push",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} A real person doing an intense dumbbell curl in a gym. Close-up showing their arm, the dumbbell, and their smartwatch on the wrist. Veins visible, real sweat on skin. Dark gym background with soft overhead lights creating rim lighting on their shoulder. Raw, gritty, authentic. Square 1:1 composition, tight crop.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-coach-voice",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} A real person running on a city street at dusk, wearing wireless earbuds and a phone armband. Natural street lighting, slightly orange from streetlights. They look focused and determined, mid-stride. You can see earbuds in their ear clearly. Background is a real urban environment slightly blurred from motion. Square 1:1 composition, editorial running photography style.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-watch-connect",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} Close-up of a real person's wrist wearing an Apple Watch during a workout. The watch screen shows heart rate data. Small sweat droplets on the watch band and skin. Background is a dark gym, blurred with bokeh from gym lights. Natural lighting, no special effects. The watch face is glowing softly as the brightest element. Square 1:1 composition, macro photography style.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-story-effort",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} A real person doing a box jump in a CrossFit-style gym, captured mid-air. Full body visible, athletic build, real gym environment with plyo boxes, barbells, and rubber flooring. Dramatic overhead lighting creating strong shadows. Raw, powerful, authentic moment. Vertical 9:16 composition, shot from slightly below looking up.",
        "aspect_ratio": "9:16",
    },
    {
        "id": "tiktok-cover-push",
        "dir": "tiktok",
        "prompt": f"{BASE_PREFIX} A real person gripping a loaded barbell, about to deadlift. Their phone is on the floor nearby, screen showing a dark fitness app with an orange glow. Chalk dust in the air, real gym floor, plates on the bar. Dramatic top-down gym lighting. Gritty, authentic, powerful. Vertical 9:16 composition, moody.",
        "aspect_ratio": "9:16",
    },
    {
        "id": "tiktok-cover-tech",
        "dir": "tiktok",
        "prompt": f"{BASE_PREFIX} Flat lay on a dark gym bench: a real smartwatch showing heart rate, an iPhone with a dark fitness app on screen, wireless earbuds in their case, a gym towel, and a water bottle. Natural overhead gym light illuminating the objects. Looks like someone placed their gear down between sets and took a photo. Vertical 9:16 composition, authentic lifestyle flat lay.",
        "aspect_ratio": "9:16",
    },
    {
        "id": "mockup-watch",
        "dir": "mockups",
        "prompt": f"{BASE_PREFIX} Close-up of a real person's wrist wearing an Apple Watch while gripping a pull-up bar. The watch screen shows 142 BPM heart rate. Their hand is chalked, forearm veins visible, real gym pull-up bar with worn rubber grip. Dark gym background. Natural lighting from above. Authentic, not posed. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "mockup-phone",
        "dir": "mockups",
        "prompt": f"{BASE_PREFIX} A real person sitting on a gym bench between sets, holding their iPhone. The phone screen shows a dark fitness coaching app with a glowing orange-amber orb in the center, a circular purple progress ring around it, a workout timer, and small audio waveform bars. They are sweaty in workout clothes, gym equipment in the blurred background. Natural gym lighting. Candid, real moment. 4:3 landscape composition.",
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
