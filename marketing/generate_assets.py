#!/usr/bin/env python3
"""
Coachi Marketing Asset Generator
Uses Google Gemini API to generate branded marketing images.
Run from project root: python3 marketing/generate_assets.py

Every person wears:
  - Earbuds/headphones (AirPods, over-ear, Beats, etc.)
  - A smartwatch (Garmin, Polar, Fitbit, or Apple Watch)
  - Different clothing (hardcoded per template, no two the same)
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

# --- Config ---
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

# --- Gear combos: each template gets a unique combination ---
# (watch, earbuds, clothing_top, clothing_bottom, shoes, gender_hint)
GEAR = {
    "hero-workout": (
        "a Garmin Forerunner watch with a black band",
        "white AirPods Pro clearly visible in both ears",
        "a faded navy blue t-shirt soaked with sweat around the collar",
        "black running shorts",
        "white Nike running shoes",
        "a man",
    ),
    "hero-coach-pocket": (
        "a Polar Vantage watch with an orange band",
        "black Beats Fit Pro earbuds visible in their ears",
        "a dark green hoodie with the sleeves pushed up",
        "grey jogger pants",
        "black Adidas sneakers",
        "a woman",
    ),
    "ig-pulse-push": (
        "an Apple Watch Ultra with an orange Alpine band",
        "black over-ear Bose headphones around their neck between sets",
        "a worn red tank top",
        "black gym shorts",
        "grey New Balance training shoes",
        "a man",
    ),
    "ig-coach-voice": (
        "a Fitbit Sense on their wrist with a grey band",
        "white AirPods clearly visible in both ears",
        "a light blue running jacket half-unzipped over a white t-shirt",
        "black running tights",
        "neon yellow Asics running shoes",
        "a woman",
    ),
    "ig-watch-connect": (
        "a Garmin Fenix with a dark grey silicone band",
        "no earbuds visible (just the watch is the focus)",
        "a sweaty black compression shirt",
        "dark blue shorts",
        "not visible in frame",
        "a man",
    ),
    "ig-story-effort": (
        "a Polar Grit X watch with a black band",
        "wireless Jabra earbuds visible in their ears",
        "a bright yellow tank top",
        "black compression shorts",
        "red Reebok CrossFit shoes",
        "a woman",
    ),
    "tiktok-cover-push": (
        "an Apple Watch Series 9 with a black sport band",
        "white AirPods Pro in their ears, clearly visible",
        "a washed-out black t-shirt with small holes",
        "dark grey cargo-style gym shorts",
        "flat black Converse lifting shoes",
        "a man",
    ),
    "tiktok-cover-tech": (
        "a Garmin Venu with a teal silicone band",
        "Samsung Galaxy Buds in an open case on the bench",
        "not applicable (flat lay, no person)",
        "not applicable",
        "not applicable",
        "no person",
    ),
    "mockup-watch": (
        "an Apple Watch SE with a white sport band",
        "black Bose earbuds tucked in their ears",
        "a dark maroon compression top",
        "black shorts",
        "not visible",
        "a woman",
    ),
    "mockup-phone": (
        "a Fitbit Charge 6 on their wrist with a black band",
        "white AirPods Max over-ear headphones",
        "an oversized grey crewneck sweatshirt, sleeves pushed up, sweat-stained",
        "navy blue jogger shorts",
        "white On Cloud running shoes",
        "a man",
    ),
}

# --- Base style prefix ---
BASE_PREFIX = (
    "iPhone 15 Pro photo posted on Instagram. "
    "Taken casually with a phone camera, not a professional shoot. "
    "Slightly imperfect framing, natural phone camera look with some noise and grain. "
    "Real everyday person, not a fitness model. Normal body. "
    "Visible imperfections: messy hair, flushed skin, real sweat. "
    "No filters, no special effects, no CGI, no holograms, no glowing outlines. "
    "Looks like a friend took this photo. No text overlays."
)


def make_gear_string(template_id):
    """Build the gear description for a template."""
    watch, earbuds, top, bottom, shoes, gender = GEAR[template_id]
    parts = []
    if gender != "no person":
        parts.append(f"The person is {gender}")
    if "not applicable" not in top:
        parts.append(f"wearing {top}")
    if "not applicable" not in bottom:
        parts.append(f"{bottom}")
    if "not visible" not in shoes and "not applicable" not in shoes:
        parts.append(f"and {shoes}")
    parts.append(f"They have {watch} on their wrist")
    if "no earbuds" not in earbuds and "not applicable" not in earbuds:
        parts.append(f"and {earbuds}")
    return ". ".join(parts) + "."


# --- Templates ---
TEMPLATES = [
    {
        "id": "hero-workout",
        "dir": "website",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('hero-workout')} "
            "They are running hard on a treadmill in a normal commercial gym, mid-stride. "
            "Other gym members visible in the far background, slightly out of focus. "
            "Overhead fluorescent lights, a wall mirror reflecting part of the gym. "
            "The photo was taken by a friend standing to the side. "
            "Wide 16:9 composition with empty space on the left."
        ),
        "aspect_ratio": "16:9",
    },
    {
        "id": "hero-coach-pocket",
        "dir": "website",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('hero-coach-pocket')} "
            "Photo taken from behind and slightly above them sitting on a weight bench "
            "in a gym between sets. Over-the-shoulder view, you can see them holding "
            "their iPhone in front of them, the phone screen visible showing a dark "
            "fitness app with an orange glowing circle. Their sweaty neck visible, "
            "a towel on one shoulder. A water bottle on the floor, dumbbells nearby. "
            "Wide 16:9, candid and unposed."
        ),
        "aspect_ratio": "16:9",
    },
    {
        "id": "ig-pulse-push",
        "dir": "instagram",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('ig-pulse-push')} "
            "They are mid-rep doing a heavy dumbbell curl. Shot from close up, "
            "you can see their forearm, veins popping, sweat dripping down their arm. "
            "The background is blurry gym equipment and rubber mats. "
            "Taken by a gym buddy from a few feet away. Square 1:1 composition."
        ),
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-coach-voice",
        "dir": "instagram",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('ig-coach-voice')} "
            "They are jogging on a residential street in the evening. "
            "Streetlights casting orange light, parked cars along the road. "
            "Their face shows effort and focus. Phone in a running armband. "
            "Looks like a photo taken by a running partner. Square 1:1 composition."
        ),
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-watch-connect",
        "dir": "instagram",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('ig-watch-connect')} "
            "A quick selfie-style photo of their wrist showing the watch with a "
            "heart rate screen. Wrist slightly sweaty. Background is a gym floor "
            "with rubber tiles and a dumbbell rack out of focus. They pointed their "
            "phone at their wrist. Slightly shaky, natural phone camera quality. "
            "Square 1:1 composition."
        ),
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-story-effort",
        "dir": "instagram",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('ig-story-effort')} "
            "They are doing a box jump in a gym, caught mid-air by a friend. "
            "Rubber flooring, a wooden plyo box, barbells nearby. Fluorescent "
            "lights overhead. Slightly blurry from fast motion. "
            "Vertical 9:16 composition, feels like an Instagram Story."
        ),
        "aspect_ratio": "9:16",
    },
    {
        "id": "tiktok-cover-push",
        "dir": "tiktok",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('tiktok-cover-push')} "
            "They are setting up for a deadlift, bending down gripping the barbell, "
            "chalk on their hands. Their phone is propped against a weight plate on "
            "the floor nearby, screen showing a dark fitness app. Scuffed gym floor, "
            "iron plates loaded on the bar. Photo taken from ground level. "
            "Gritty and real. Vertical 9:16 composition."
        ),
        "aspect_ratio": "9:16",
    },
    {
        "id": "tiktok-cover-tech",
        "dir": "tiktok",
        "prompt": (
            f"{BASE_PREFIX} Gym gear spread out on a worn wooden bench in a locker room. "
            f"A {GEAR['tiktok-cover-tech'][0]}, an iPhone with a cracked screen protector "
            f"showing a dark fitness app, {GEAR['tiktok-cover-tech'][1]}, "
            "a wrinkled gym towel, and a dented metal water bottle. "
            "Overhead locker room lighting, slightly yellowish. "
            "The items look used and real, not arranged perfectly. "
            "Vertical 9:16 composition."
        ),
        "aspect_ratio": "9:16",
    },
    {
        "id": "mockup-watch",
        "dir": "mockups",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('mockup-watch')} "
            "They took a photo of their wrist while hanging from a pull-up bar. "
            "You can see their hand gripping the bar with chalk residue, their forearm, "
            "and the watch showing 142 BPM. The gym ceiling with industrial lights is "
            "visible above. Grip tight, knuckles white. Taken one-handed with a phone, "
            "slightly tilted framing. Square 1:1 composition."
        ),
        "aspect_ratio": "1:1",
    },
    {
        "id": "mockup-phone",
        "dir": "mockups",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('mockup-phone')} "
            "They are resting on a gym bench after a set, holding their iPhone in one "
            "hand, towel in the other. The phone screen shows a dark fitness app with "
            "a glowing orange circle and a timer. Breathing heavily, face slightly "
            "flushed. The gym behind them has cable machines and a mirror wall. "
            "Taken by a workout partner from the next bench over. "
            "4:3 landscape composition, casual and unposed."
        ),
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
    print("=== Coachi Marketing Asset Generator ===\n")
    print(f"Output: {ASSETS_DIR}")
    print(f"Templates: {len(TEMPLATES)}\n")

    # Show gear assignments
    print("Gear assignments:")
    for tid, (watch, earbuds, top, bottom, shoes, gender) in GEAR.items():
        if gender != "no person":
            print(f"  {tid}: {gender} | {watch} | {earbuds} | {top}")
    print()

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
