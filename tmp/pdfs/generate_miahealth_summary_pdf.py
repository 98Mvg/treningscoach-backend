#!/usr/bin/env python3
"""Generate a one-page repo-evidenced app summary PDF (no external deps)."""

from __future__ import annotations

import textwrap
from pathlib import Path

OUTPUT_PDF = Path("output/pdf/miahealth_app_summary.pdf")
PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT = 54
RIGHT = PAGE_WIDTH - 54
CONTENT_WIDTH = RIGHT - LEFT


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class Canvas:
    def __init__(self) -> None:
        self.y = 758.0
        self.cmds: list[str] = []

    def line(self, text: str, font: str = "F1", size: int = 10, indent: int = 0, gap: float | None = None) -> None:
        x = LEFT + indent
        self.cmds.append(
            f"BT /{font} {size} Tf 1 0 0 1 {x:.2f} {self.y:.2f} Tm ({esc(text)}) Tj ET"
        )
        self.y -= gap if gap is not None else (size + 5)

    def rule(self) -> None:
        y = self.y + 4
        self.cmds.append(f"0.75 w {LEFT:.2f} {y:.2f} m {RIGHT:.2f} {y:.2f} l S")
        self.y -= 8

    def space(self, points: float = 6) -> None:
        self.y -= points

    def wrap(self, text: str, font: str = "F1", size: int = 10, indent: int = 0, bullet: bool = False) -> None:
        approx_cpl = max(33, int((CONTENT_WIDTH - indent) / (size * 0.53)))
        lines = textwrap.wrap(text, width=approx_cpl)
        if not lines:
            self.line("", font=font, size=size, indent=indent)
            return

        if bullet:
            self.line(f"- {lines[0]}", font=font, size=size, indent=indent)
            for cont in lines[1:]:
                self.line(cont, font=font, size=size, indent=indent + 12)
        else:
            for ln in lines:
                self.line(ln, font=font, size=size, indent=indent)


def build_content() -> bytes:
    c = Canvas()

    c.line("MIAHEALTH - One-Page App Summary", font="F2", size=20, gap=26)
    c.wrap(
        "Repo evidence source: /Users/mariusgaarder/Documents/treningscoach (README.md + iOS/Flask runtime files)",
        font="F1",
        size=8,
    )
    c.rule()

    c.line("WHAT IT IS", font="F2", size=12, gap=17)
    c.wrap(
        "A real-time AI workout coach app: iOS captures breathing audio and a Python backend returns short spoken coaching cues.",
        size=10,
    )
    c.wrap(
        "Brand name status: \"MIAHEALTH\" is Not found in repo. Product strings found are \"Coachi\" and \"TreningsCoach\".",
        size=10,
    )
    c.space(3)

    c.line("WHO IT'S FOR", font="F2", size=12, gap=17)
    c.wrap(
        "Primary user/persona: people doing gym or endurance workouts who want live voice-guided pacing and breathing feedback.",
        size=10,
    )
    c.space(3)

    c.line("WHAT IT DOES", font="F2", size=12, gap=17)
    feature_bullets = [
        "Runs a continuous coaching loop: records 6-10s audio chunks and posts to /coach/continuous.",
        "Analyzes breathing signal and intensity from uploaded audio using BreathAnalyzer (librosa/numpy pipeline).",
        "Routes coaching text generation through BrainRouter with provider fallback logic.",
        "Synthesizes response audio with ElevenLabs TTS and serves files via /download/<file>.",
        "Supports personas, language selection, and mid-workout talk-to-coach interactions.",
        "Stores workout history in SQLAlchemy models (with optional user association via JWT).",
        "Includes auth endpoints for Google, Facebook, and Vipps in the Flask API.",
    ]
    for bullet in feature_bullets:
        c.wrap(bullet, size=10, bullet=True)
    c.space(3)

    c.line("HOW IT WORKS (Repo-Evidenced Architecture)", font="F2", size=12, gap=17)
    arch_bullets = [
        "iOS app entry: TreningsCoachApp -> RootView -> MainTabView -> WorkoutViewModel.",
        "ContinuousRecordingManager captures mic audio; BackendAPIService sends multipart requests to Flask endpoints.",
        "main.py /coach/continuous saves chunk, runs breath analysis, applies session/decision logic, and decides speak vs silence.",
        "BrainRouter selects/queries AI path; coaching text is then converted to audio by ElevenLabsTTS.",
        "Backend returns {text, should_speak, audio_url, wait_seconds}; iOS downloads audio and schedules next tick.",
        "Data layer: SQLAlchemy models (users, user_settings, workout_history) plus in-memory session state in SessionManager.",
    ]
    for bullet in arch_bullets:
        c.wrap(bullet, size=10, bullet=True)
    c.space(3)

    c.line("HOW TO RUN (Minimal)", font="F2", size=12, gap=17)
    run_steps = [
        "Install backend deps: pip3 install -r requirements.txt",
        "Set env vars: ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, and one AI provider key (for example XAI_API_KEY).",
        "Start backend: PORT=5001 python3 main.py",
        "Run iOS app: open TreningsCoach/TreningsCoach.xcodeproj (Xcode Cmd+R).",
        "If testing locally, point iOS backend URL to http://localhost:5001 in Config.swift.",
    ]
    for step in run_steps:
        c.wrap(step, size=10, bullet=True)

    c.space(3)
    c.wrap(
        "Note: Payment/billing flow is Not found in repo.",
        size=9,
    )

    if c.y < 40:
        raise RuntimeError(f"Content overflow: remaining y={c.y:.2f}")

    return ("\n".join(c.cmds) + "\n").encode("latin-1", errors="replace")


def write_pdf(path: Path, stream: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    objs: list[bytes] = []

    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objs.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 4 0 R >>"
    )
    objs.append(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream")
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    out = bytearray()
    out.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    offsets = [0]
    for i, obj in enumerate(objs, start=1):
        offsets.append(len(out))
        out.extend(f"{i} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")

    xref_pos = len(out)
    out.extend(f"xref\n0 {len(objs) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    out.extend(
        (
            f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n"
        ).encode("ascii")
    )

    path.write_bytes(out)


def main() -> None:
    stream = build_content()
    write_pdf(OUTPUT_PDF, stream)
    print(f"Generated: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
