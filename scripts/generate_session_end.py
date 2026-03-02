#!/usr/bin/env python3
"""
Generate end-of-session screen concept for Coachi.
Run: python3 scripts/generate_session_end.py
"""
import os
import sys
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

OUTPUT_PATH = Path(__file__).parent.parent / "output" / "session-end-v1.png"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

PROMPT = (
    "Pure digital UI graphic. Dark iOS app workout completion screen design. "
    "9:16 vertical canvas, pixel-perfect flat digital illustration, no photos, no people, no photography. "
    "Background: solid dark #1a1a2e (deep midnight navy) with subtle radial vignette. "
    "Top third: one large circular progress ring, thick stroke, filled 78%, "
    "glowing cyan #00D9FF color with ember orange at the leading tip. "
    "Inside ring center: giant bold numeral '78' in white, tiny label 'SCORE' below in grey. "
    "Below ring: three minimal horizontal stat rows — a clock icon + '32 min', "
    "a flame icon + '340 kcal', a heart icon + '156 bpm'. Icons glow softly. "
    "Bottom: one large rounded pill button with cyan glow 'Share', "
    "and a plain white text 'Done' link below it. "
    "Small floating particles scattered across top area — 10-15 tiny glowing dots, "
    "mix of cyan and orange, varied sizes, no confetti shapes. "
    "Zero photography. Zero realism. Pure vector-style digital UI art. "
    "Maximum 6 text strings visible in total. "
    "Feels like a premium game achievement screen. Dark, glowing, cinematic. "
    "No device frame. No bezel. Just the screen content on a dark background."
)

print("=== Coachi End-of-Session Screen Generator ===\n")
print(f"Output: {OUTPUT_PATH}\n")
print("Generating...")

client = genai.Client(api_key=API_KEY)

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=f"Generate an image: {PROMPT}",
        config=genai.types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    if response and response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data and part.inline_data.mime_type.startswith("image/"):
                img_data = part.inline_data.data
                OUTPUT_PATH.write_bytes(img_data)
                size_kb = len(img_data) / 1024
                print(f"OK -> {OUTPUT_PATH} ({size_kb:.0f} KB)")
                sys.exit(0)

    print("FAIL: No image in response")
    if response and response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                print(f"Model text: {part.text[:300]}")

except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)
