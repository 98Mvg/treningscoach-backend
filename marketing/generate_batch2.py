#!/usr/bin/env python3
"""
Coachi Marketing Asset Generator — Batch 2
10 additional images for expanded content library.
Run from project root: python3 marketing/generate_batch2.py
"""
import os
import sys
import time
from pathlib import Path

try:
    from google import genai
except ImportError:
    print("ERROR: google-genai not installed. Run: pip3 install google-genai")
    sys.exit(1)

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
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

TEMPLATES = [
    {
        "id": "ig-kettlebell-swing",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} Someone mid-swing with a kettlebell in a gym. Both hands gripping the kettlebell at chest height, legs slightly bent. Sweat on their forehead, wearing a basic grey tank top and shorts. A gym mirror behind them reflecting other equipment. Rubber floor, kettlebell rack in the background. Taken by a gym buddy from a few feet away. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-rope-battle",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} Someone doing battle ropes in a gym, ropes mid-wave creating a ripple shape. Their arms are extended, face showing intense effort, mouth slightly open. Wearing a sweat-soaked t-shirt. The gym floor is rubber, other people working out in the far background. Shot from the front by a friend standing a few meters away. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-squat-rack",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} Someone at the bottom of a barbell back squat in a squat rack. The bar is loaded with plates, their face shows concentration. Wearing flat shoes, knee sleeves, and a worn t-shirt. A gym buddy is standing behind them spotting. The squat rack has safety bars and a mirror behind. Taken from the side by another gym member. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-story-stretching",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} Someone stretching on a gym mat after a workout, sitting with one leg extended, reaching for their toes. They look tired but satisfied, sweat drying on their face. A water bottle and phone next to them on the mat. The gym is emptier now, a few people in the background. Fluorescent lights, mirrors on the wall. Vertical 9:16 composition, Instagram Story vibe.",
        "aspect_ratio": "9:16",
    },
    {
        "id": "ig-story-mirror-selfie",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} A gym mirror selfie. Someone standing in front of a large gym mirror holding their phone up to take the photo. They are sweaty, post-workout, wearing a damp t-shirt. You can see the gym behind them in the reflection — machines, other people, fluorescent lights. Their phone is clearly visible taking the selfie. Classic gym mirror selfie. Vertical 9:16 composition.",
        "aspect_ratio": "9:16",
    },
    {
        "id": "tiktok-rowing",
        "dir": "tiktok",
        "prompt": f"{BASE_PREFIX} Someone on a rowing machine in a gym, mid-pull, leaning back with the handle at their chest. Sweat on their arms, wearing shorts and a t-shirt. Their smartwatch visible on their wrist. The rowing machine display shows numbers. Other cardio machines next to them, some occupied. Taken from the side by a friend. Vertical 9:16 composition.",
        "aspect_ratio": "9:16",
    },
    {
        "id": "tiktok-plank",
        "dir": "tiktok",
        "prompt": f"{BASE_PREFIX} Someone holding a plank on the gym floor, arms shaking slightly, face showing strain and determination. Their phone is on the floor in front of them propped up against a dumbbell, screen showing a timer. Sweat dripping from their forehead onto the mat. Rubber gym flooring, equipment around them. Shot from floor level looking at them straight on. Vertical 9:16 composition.",
        "aspect_ratio": "9:16",
    },
    {
        "id": "extra-bench-press",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} Photo taken from behind the bench press, looking down at someone lying on the bench pressing a barbell. You can see their hands gripping the bar, the plates on each side, and their face showing effort from above. A spotter's hands are hovering near the bar. The gym ceiling with lights visible above. Taken by the spotter from behind the bar. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "extra-outdoor-stairs",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} Someone running up outdoor concrete stairs in a park or urban area, mid-stride on the steps. They are wearing running shoes, shorts, a basic t-shirt, and AirPods. Morning or late afternoon light, trees or buildings in the background. They look determined, slightly winded. A friend took the photo from the bottom of the stairs looking up. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "extra-water-break",
        "dir": "instagram",
        "prompt": f"{BASE_PREFIX} Someone taking a water break in a gym, tilting their head back drinking from a metal water bottle. Their other hand is resting on their hip. They are flushed and sweaty, t-shirt soaked. A barbell on the floor behind them, gym equipment in the background. Taken casually by a workout partner from a few steps away. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
]


def generate_image(client, template):
    template_id = template["id"]
    output_dir = ASSETS_DIR / template["dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{template_id}.png"

    if output_path.exists():
        print(f"  SKIP {template_id} (already exists)")
        return True

    print(f"  Generating {template_id} ({template['aspect_ratio']})...")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=f"Generate an image: {template['prompt']}",
            config=genai.types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

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
    print("=== Coachi Marketing Asset Generator — Batch 2 ===\n")
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

        if i < len(TEMPLATES):
            time.sleep(2)

    print(f"\n=== Done: {success}/{len(TEMPLATES)} generated ===")
    if failed:
        print(f"Failed: {', '.join(failed)}")
        print("Re-run to retry failed images (existing ones will be skipped)")


if __name__ == "__main__":
    main()
