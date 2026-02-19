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
    "iPhone 15 Pro photo posted on Instagram by a gym member. "
    "Taken casually with a phone camera, not a professional shoot. "
    "Slightly imperfect framing, natural phone camera look with some noise and grain. "
    "Real gym with scuff marks on floors, used equipment, fluorescent and LED overhead lights. "
    "Real everyday person, not a fitness model. Normal body, wearing worn gym clothes. "
    "Visible imperfections: messy hair, flushed skin, real sweat stains on shirt. "
    "No filters, no special effects, no CGI, no holograms, no glowing outlines. "
    "Looks like a friend took this photo of you at the gym. No text overlays."
)

# --- Templates ---
TEMPLATES = [
    {
        "id": "hero-workout",
        "dir": "website",
        "prompt": f"{BASE_PREFIX} Someone running hard on a treadmill in a normal commercial gym. They are mid-stride, wearing a smartwatch and a faded t-shirt that is soaked with sweat around the neck. Other gym members visible in the far background, slightly out of focus. Overhead fluorescent lights, a wall mirror reflecting part of the gym. The photo was taken by a friend standing to the side. Wide 16:9, empty space on the left where the gym floor continues.",
        "aspect_ratio": "16:9",
    },
    {
        "id": "hero-coach-pocket",
        "dir": "website",
        "prompt": f"{BASE_PREFIX} Someone sitting on a weight bench in a gym, catching their breath between sets, looking at their iPhone. The phone screen shows a dark app with an orange glowing circle. They are sweaty, hair messy, a towel draped over one shoulder. A half-empty water bottle on the floor next to them. Dumbbells scattered nearby. The photo is taken from across the gym floor, slightly off-center. Wide 16:9, candid and unposed.",
        "aspect_ratio": "16:9",
    },
    {
        "id": "ig-pulse-push",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} Someone mid-rep doing a heavy bicep curl with a dumbbell. Shot from close up, you can see their forearm, the veins popping, a black sports watch on their wrist. Their t-shirt sleeve is pushed up. Sweat dripping down their arm. The background is blurry gym equipment and rubber mats. Taken quickly between reps by a gym buddy. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-coach-voice",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} Someone jogging on a residential street in the evening, wearing AirPods and a phone strapped to their arm with a running armband. They are wearing basic running shorts and a slightly wrinkled shirt. Streetlights casting orange light, parked cars along the road, a crosswalk in the background. Their face shows effort and focus. Looks like a photo taken by a running partner. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-watch-connect",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} A quick selfie-style photo of someone's wrist with an Apple Watch showing a heart rate screen. Their wrist is slightly sweaty, the watch band is a basic black sport band. The background is a gym floor with rubber tiles and a dumbbell rack slightly out of focus. The person took this photo themselves, pointing their phone at their wrist. Slightly shaky, natural phone camera quality. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-story-effort",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} Someone doing a box jump in a gym, caught mid-air by a friend filming on their phone. The gym has rubber flooring, a wooden plyo box, barbells on the floor nearby. Fluorescent lights overhead. The person is wearing normal gym shorts and a tank top, sneakers. Other gym equipment visible in the background. Slightly blurry from the fast motion. Vertical 9:16 composition, feels like an Instagram Story.",
        "aspect_ratio": "9:16",
    },
    {
        "id": "tiktok-cover-push",
        "dir": "tiktok",
        "prompt": f"{BASE_PREFIX} Someone setting up for a deadlift in a basic gym. They are bending down gripping the barbell, chalk on their hands. Their phone is propped against a weight plate on the floor nearby, screen lit up with an app. Scuffed gym floor, iron plates loaded on the bar. The photo is taken from ground level by the phone timer or a friend squatting down. Gritty and real. Vertical 9:16 composition.",
        "aspect_ratio": "9:16",
    },
    {
        "id": "tiktok-cover-tech",
        "dir": "tiktok",
        "prompt": f"{BASE_PREFIX} Gym gear spread out on a worn wooden bench in a locker room. An Apple Watch with a sweaty band, an iPhone with a cracked screen protector showing a dark fitness app, wireless earbuds in an open case, a wrinkled gym towel, and a dented metal water bottle. Overhead locker room lighting, slightly yellowish. The items look used and real, not arranged perfectly. Vertical 9:16 composition.",
        "aspect_ratio": "9:16",
    },
    {
        "id": "mockup-watch",
        "dir": "mockups",
        "prompt": f"{BASE_PREFIX} Someone took a photo of their wrist while hanging from a pull-up bar. You can see their hand gripping the bar with chalk residue, their forearm, and an Apple Watch showing 142 BPM on the screen. The gym ceiling with industrial lights is visible above. Their grip is tight, knuckles white. Taken one-handed with a phone, slightly tilted framing. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "mockup-phone",
        "dir": "mockups",
        "prompt": f"{BASE_PREFIX} Someone resting on a gym bench after a set, holding their iPhone in one hand, towel in the other. The phone screen shows a dark fitness app with a glowing orange circle in the middle and a timer. They are breathing heavily, shirt damp with sweat, face slightly flushed. The gym behind them has cable machines and a mirror wall. Taken by a workout partner from the next bench over. 4:3 landscape composition, casual and unposed.",
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
