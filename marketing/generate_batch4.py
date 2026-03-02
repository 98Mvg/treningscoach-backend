#!/usr/bin/env python3
"""
Coachi Marketing Asset Generator — Batch 4
Outdoor, nature, relaxing themes — mountain, blurry running, smiling.
Run from project root: python3 marketing/generate_batch4.py
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

OUTDOOR_PREFIX = (
    "iPhone 15 Pro photo posted on Instagram. "
    "Taken casually with a phone camera, not a professional shoot. "
    "Natural outdoor lighting, slightly imperfect framing. "
    "Real everyday athletic person, not a fitness model. Normal body. "
    "Visible imperfections: messy hair, flushed skin, real sweat. "
    "No filters, no special effects, no CGI, no holograms, no glowing outlines. "
    "No text overlays, no captions, no watermarks baked into the image."
)

TEMPLATES = [
    {
        "id": "mountain-trail-runner",
        "dir": "website",
        "prompt": f"{OUTDOOR_PREFIX} Someone running on a mountain trail at golden hour. Norwegian-style mountains and fjord-like scenery in the far background. Wearing a grey performance t-shirt and black running shorts, smartwatch visible on wrist. Shot from slightly below looking up at the runner on the trail. Warm sunset light, lush green trail with some rocks. Mist or haze in the valley below. Sharp focus on the runner, soft dreamy mountains behind. Wide angle feel. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "runner-blurry-background",
        "dir": "website",
        "prompt": f"{OUTDOOR_PREFIX} Someone running on a tree-lined forest path. The background is beautifully blurred with green trees and dappled sunlight creating a dreamy bokeh. Sharp focus only on the runner in the center. Wearing grey t-shirt and dark shorts, smartwatch on wrist. Mid-stride dynamic running pose, one foot off the ground. Shallow depth of field like f/1.8 portrait mode. Warm natural light filtering through trees. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "smiling-after-workout",
        "dir": "website",
        "prompt": f"{OUTDOOR_PREFIX} Someone standing outdoors in a green park after a run, smiling naturally and looking genuinely happy. Wearing a grey performance t-shirt, slightly sweaty. Smartwatch on wrist. Relaxed confident posture, hands on hips or one hand wiping forehead. Soft natural daylight, beautiful blurred green park and trees in background. Warm golden tones. Chest-up portrait framing. The smile should look real and natural, not posed. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "mountain-landscape",
        "dir": "website",
        "prompt": "Dramatic Norwegian mountain landscape at sunrise. Fjord with perfectly calm water reflecting the mountains like a mirror. Soft morning mist rising from the water. Purple, orange and pink sky gradient. No people in the image. Moody cinematic atmosphere, wide angle panoramic view. Snow-capped peaks, green slopes lower down. Could be used as an app background. Professional landscape photography feel. 16:9 composition.",
        "aspect_ratio": "16:9",
    },
    {
        "id": "recovery-park-stretch",
        "dir": "website",
        "prompt": f"{OUTDOOR_PREFIX} Someone sitting on green grass in a park after a run, doing a relaxed hamstring stretch with one leg extended. They are smiling contentedly, looking satisfied and peaceful. Wearing grey t-shirt and dark shorts, smartwatch on wrist. A water bottle next to them on the grass. Beautiful soft golden hour lighting from the side. Blurred trees and park scenery in background. Calm, relaxing mood. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "runner-open-road",
        "dir": "website",
        "prompt": f"{OUTDOOR_PREFIX} Someone running away from the camera on an open country road with mountains ahead in the distance. Early morning light creating long shadows on the road. Wearing grey t-shirt and dark shorts, smartwatch on wrist. Sense of freedom, space and adventure. Norwegian-style countryside with green rolling hills on both sides of the road. Wide angle perspective shot, the road leading the eye into the distance. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "sunset-hilltop-rest",
        "dir": "website",
        "prompt": f"{OUTDOOR_PREFIX} Someone sitting on a hilltop at sunset, looking out over a valley view after a trail run. Seen from behind/side angle. Wearing grey t-shirt, smartwatch on wrist. Warm orange and purple sunset colors. They look peaceful and reflective, catching their breath. Mountains or hills in the distance. Grass and wildflowers around them. Atmospheric and calming. Square 1:1 composition.",
        "aspect_ratio": "1:1",
    },
    {
        "id": "morning-fog-runner",
        "dir": "website",
        "prompt": f"{OUTDOOR_PREFIX} Someone running through morning fog on a path by a lake or river. Misty, atmospheric, dreamy feel. The fog creates natural depth and mystery. Trees are silhouetted in the background. Wearing grey t-shirt and dark shorts, smartwatch on wrist. Early dawn light with cool blue and warm gold tones mixing. The runner is slightly silhouetted but still visible. Peaceful, almost meditative scene. Square 1:1 composition.",
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
    print("=== Coachi Marketing Asset Generator — Batch 4 (Outdoor/Relaxing) ===\n")
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
