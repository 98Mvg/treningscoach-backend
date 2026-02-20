#!/usr/bin/env python3
"""
Coachi Marketing Asset Generator — Batch 3
10 more images with hardcoded GEAR combos (watch, earbuds, clothing).
Run from project root: python3 marketing/generate_batch3.py
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

# --- Gear combos: unique per template ---
# (watch, earbuds, clothing_top, clothing_bottom, shoes, gender_hint)
GEAR = {
    "ig-cable-crossover": (
        "a Garmin Forerunner 265 with a bright green silicone band",
        "black Jaybird Vista earbuds snug in their ears",
        "a tight-fitting dark purple compression shirt",
        "grey athletic joggers",
        "black Nike Metcon shoes",
        "a man",
    ),
    "ig-jump-rope": (
        "a Polar Pacer Pro with a white band",
        "white AirPods (3rd gen) clearly visible in both ears",
        "an oversized washed-out pink cropped tank top",
        "black high-waisted biker shorts",
        "white Puma training shoes",
        "a woman",
    ),
    "ig-treadmill-incline": (
        "an Apple Watch Series 10 with a black braided solo loop band",
        "red Beats Fit Pro earbuds visible in their ears",
        "a heather grey Under Armour dri-fit tee drenched in sweat",
        "dark navy running shorts",
        "neon green Hoka running shoes",
        "a man",
    ),
    "ig-dumbbell-lunges": (
        "a Fitbit Versa 4 with a lavender band",
        "black Sony WF-1000XM5 earbuds in their ears",
        "a forest green racerback tank top",
        "dark grey capri leggings",
        "coral-colored Nike Free shoes",
        "a woman",
    ),
    "tiktok-tire-flip": (
        "a Garmin Instinct 2 with an olive drab rugged band",
        "no earbuds visible (they fell out during the tire flip)",
        "a ripped and faded black metal band t-shirt",
        "camo cargo shorts",
        "tan Inov-8 training shoes covered in dirt",
        "a man",
    ),
    "tiktok-spin-bike": (
        "a Polar Ignite 3 with a rose gold band",
        "white Bose QuietComfort earbuds in their ears",
        "a neon orange sports bra over a mesh black tank top",
        "dark purple cycling shorts",
        "grey and pink cycling shoes clipped in",
        "a woman",
    ),
    "ig-story-foam-roll": (
        "an Apple Watch Ultra 2 with a blue Alpine loop band",
        "over-ear Marshall Major headphones around their neck",
        "a soft cream-colored oversized hoodie",
        "black jogger sweatpants",
        "barefoot on a yoga mat",
        "a man",
    ),
    "ig-story-heavy-bag": (
        "a Fitbit Charge 6 with a black sport band",
        "wireless Skullcandy Push Active earbuds in their ears",
        "a tight red compression tank top",
        "black MMA-style shorts with white side stripes",
        "black and yellow boxing shoes",
        "a woman",
    ),
    "extra-pull-up-bar": (
        "a Garmin Venu 3 with a black leather band",
        "white AirPods Pro 2 visible in both ears",
        "a sleeveless charcoal grey muscle tee with a torn collar",
        "khaki-colored gym shorts",
        "black and white Vans Old Skool shoes",
        "a man",
    ),
    "extra-sled-push": (
        "a Polar Grit X2 Pro with a dark red silicone band",
        "black Jabra Elite 8 Active earbuds visible in their ears",
        "a teal blue long-sleeve performance shirt pushed up to the elbows",
        "black training tights",
        "bright blue Reebok Nano shoes",
        "a woman",
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


TEMPLATES = [
    {
        "id": "ig-cable-crossover",
        "dir": "instagram",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('ig-cable-crossover')} "
            "They are in the middle of a cable crossover rep in a gym, arms extended "
            "outward, cables pulling from high pulleys on both sides. Sweat dripping "
            "down their face, chest muscles engaged. The cable machine station is worn "
            "with peeling rubber grips. Other people lifting in the background. "
            "Taken by a gym buddy from a few feet away. Square 1:1 composition."
        ),
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-jump-rope",
        "dir": "instagram",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('ig-jump-rope')} "
            "They are mid-jump with a speed rope in a gym open area, rope frozen "
            "mid-arc above their head, feet a few inches off the rubber floor. "
            "Slightly blurry from the fast motion. A fan in the corner, a rack of "
            "kettlebells behind them. Morning light from a high window. "
            "Taken by a friend standing nearby. Square 1:1 composition."
        ),
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-treadmill-incline",
        "dir": "instagram",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('ig-treadmill-incline')} "
            "They are power-walking on a treadmill set to steep incline, gripping "
            "the side rails with one hand. The treadmill screen shows numbers. "
            "They are drenched in sweat, face red. Row of treadmills next to them, "
            "some occupied. Large gym windows showing a parking lot outside. "
            "Shot from the side by a friend on the next treadmill. Square 1:1 composition."
        ),
        "aspect_ratio": "1:1",
    },
    {
        "id": "ig-dumbbell-lunges",
        "dir": "instagram",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('ig-dumbbell-lunges')} "
            "They are mid-lunge holding dumbbells at their sides in a gym. "
            "Front knee bent at 90 degrees, back knee nearly touching the floor. "
            "Face shows focus and effort. Rubber gym floor with scuff marks. "
            "A weight rack and mirrors in the background, fluorescent lights above. "
            "A gym buddy took the photo from a couple meters in front. Square 1:1 composition."
        ),
        "aspect_ratio": "1:1",
    },
    {
        "id": "tiktok-tire-flip",
        "dir": "tiktok",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('tiktok-tire-flip')} "
            "They are gripping the edge of a large tractor tire in an outdoor CrossFit "
            "area or gym backyard, about to flip it. Their face shows max effort, teeth "
            "clenched. Dirt and grass on the ground. A chain-link fence in the background. "
            "Bright daylight, slightly overcast. The tire is dirty and well-used. "
            "A friend standing to the side captured this. Vertical 9:16 composition."
        ),
        "aspect_ratio": "9:16",
    },
    {
        "id": "tiktok-spin-bike",
        "dir": "tiktok",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('tiktok-spin-bike')} "
            "They are on a spin bike in a dim cycling studio, pedaling hard, "
            "standing out of the saddle. Colored LED lights on the walls (blue and pink), "
            "other bikes with riders visible. Sweat flying off their arms. "
            "Their phone is mounted on the bike handlebars. The instructor's bike is "
            "visible at the front. Shot from the next bike by a friend. "
            "Vertical 9:16 composition."
        ),
        "aspect_ratio": "9:16",
    },
    {
        "id": "ig-story-foam-roll",
        "dir": "instagram",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('ig-story-foam-roll')} "
            "They are lying on a foam roller on a gym mat in the stretching area, "
            "rolling out their upper back. Eyes closed, mouth slightly open in relief. "
            "A gym bag next to them with a towel hanging out. Yoga mats rolled up "
            "against the wall, a whiteboard with a WOD written on it in the background. "
            "Quiet corner of the gym. Shot from above by a friend standing over them. "
            "Vertical 9:16 composition, Instagram Story vibe."
        ),
        "aspect_ratio": "9:16",
    },
    {
        "id": "ig-story-heavy-bag",
        "dir": "instagram",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('ig-story-heavy-bag')} "
            "They are mid-punch hitting a heavy bag in a boxing/MMA corner of a gym. "
            "The bag is swinging from the impact. Their hands are wrapped in hand wraps "
            "(no gloves). Sweat dripping, hair tied back but messy. The heavy bag "
            "has worn spots and tape repairs. Boxing posters on the wall behind. "
            "Shot by a friend from the side. Vertical 9:16 composition, Instagram Story."
        ),
        "aspect_ratio": "9:16",
    },
    {
        "id": "extra-pull-up-bar",
        "dir": "instagram",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('extra-pull-up-bar')} "
            "They are at the top of a pull-up on a gym pull-up bar, chin above the bar, "
            "arms fully engaged. Chalk dust on their hands. Face grimacing with effort, "
            "veins visible on their forearms. The gym ceiling with exposed pipes and "
            "industrial lights visible above. A few gym members walking in the background. "
            "Shot from slightly below by a friend. Square 1:1 composition."
        ),
        "aspect_ratio": "1:1",
    },
    {
        "id": "extra-sled-push",
        "dir": "instagram",
        "prompt": (
            f"{BASE_PREFIX} {make_gear_string('extra-sled-push')} "
            "They are pushing a weighted sled across a rubber turf lane in a gym, "
            "body leaning forward at a 45-degree angle, legs driving hard. The sled "
            "has weight plates stacked on it. Their face shows pure determination. "
            "The turf lane is worn and has marks from previous pushes. Gym equipment "
            "on both sides. Shot from the front by a friend at the end of the lane. "
            "Square 1:1 composition."
        ),
        "aspect_ratio": "1:1",
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
    print("=== Coachi Marketing Asset Generator — Batch 3 ===\n")
    print(f"Output: {ASSETS_DIR}")
    print(f"Templates: {len(TEMPLATES)}\n")

    # Show gear assignments
    print("Gear assignments:")
    for tid, (watch, earbuds, top, bottom, shoes, gender) in GEAR.items():
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
