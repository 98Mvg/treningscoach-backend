#!/usr/bin/env python3
"""Generate a PDF snapshot from https://www.miahealth.no/no/howitworks (no external deps)."""

from __future__ import annotations

import textwrap
from pathlib import Path

OUTPUT_PDF = Path("output/pdf/miahealth_howitworks.pdf")
PAGE_W = 612.0
PAGE_H = 792.0
MARGIN_L = 54.0
MARGIN_R = 54.0
MARGIN_T = 52.0
MARGIN_B = 52.0
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class PDFDoc:
    def __init__(self) -> None:
        self.pages: list[list[str]] = []
        self._new_page()

    def _new_page(self) -> None:
        self.pages.append([])
        self.y = PAGE_H - MARGIN_T

    @property
    def current(self) -> list[str]:
        return self.pages[-1]

    def _ensure_space(self, needed: float) -> None:
        if self.y - needed < MARGIN_B:
            self._new_page()

    def text_line(self, text: str, font: str = "F1", size: float = 10.0, indent: float = 0.0, gap: float | None = None) -> None:
        step = gap if gap is not None else (size + 4.0)
        self._ensure_space(step)
        x = MARGIN_L + indent
        self.current.append(
            f"BT /{font} {size:.1f} Tf 1 0 0 1 {x:.2f} {self.y:.2f} Tm ({esc(text)}) Tj ET"
        )
        self.y -= step

    def paragraph(self, text: str, font: str = "F1", size: float = 10.0, indent: float = 0.0, bullet: bool = False, after: float = 4.0) -> None:
        width_chars = max(30, int((CONTENT_W - indent) / (size * 0.50)))
        lines = textwrap.wrap(text.strip(), width=width_chars)
        if not lines:
            self.text_line("", font=font, size=size, indent=indent)
            self.y -= after
            return

        if bullet:
            self.text_line(f"- {lines[0]}", font=font, size=size, indent=indent)
            for ln in lines[1:]:
                self.text_line(ln, font=font, size=size, indent=indent + 12.0)
        else:
            for ln in lines:
                self.text_line(ln, font=font, size=size, indent=indent)
        self.y -= after

    def heading(self, text: str, level: int = 2) -> None:
        if level == 1:
            self.text_line(text, font="F2", size=20.0, gap=24.0)
        elif level == 2:
            self.text_line(text, font="F2", size=13.0, gap=18.0)
        else:
            self.text_line(text, font="F2", size=11.0, gap=15.0)

    def rule(self) -> None:
        self._ensure_space(10.0)
        y = self.y + 4.0
        self.current.append(f"0.75 w {MARGIN_L:.2f} {y:.2f} m {PAGE_W - MARGIN_R:.2f} {y:.2f} l S")
        self.y -= 8.0


def build_doc() -> PDFDoc:
    d = PDFDoc()

    d.heading("Mia Health - Slik fungerer det", level=1)
    d.paragraph("Kilde: https://www.miahealth.no/no/howitworks", size=8.5, after=2.0)
    d.paragraph("Eksportert til PDF fra nettsideinnhold (tekstutdrag).", size=8.5)
    d.rule()

    d.heading("Intro", level=2)
    d.paragraph("Ta kontroll over helsa di. Mia Health beskrives som en forskningsbasert app som gir personlige aktivitetsmal og hjelper brukere med a holde seg aktive.")
    d.paragraph("Siden oppgir at over 120 000 personer bruker appen.")

    d.heading("Slik maler vi aktiviteten din", level=2)
    d.paragraph("Appen bruker puls for a male innsats og helseeffekt, med data hentet fra pulsmaler/smartklokke.")
    d.paragraph("Kompatibilitet omtalt pa siden inkluderer blant annet Apple Watch, Garmin, Polar, Fitbit, Withings, Samsung og Suunto.")

    d.heading("AQ og kondisjonsalder", level=2)
    d.paragraph("Siden forklarer to kjernebegreper: Activity Quotient (AQ) for siste syv dager og kondisjonsalder for langsiktig utvikling.")
    d.paragraph("AQ beskrives som et klart mal pa om aktivitetsnivaet er nok for god helse, mens kondisjonsalder brukes som motivasjon og fremgangsindikator over tid.")

    d.heading("Smarte funksjoner", level=2)
    features = [
        "Prediksjoner: viser mulig fremtidig utvikling basert pa dagens aktivitetsniva.",
        "Utfordringer: aktivitetsutfordringer for fokus og progresjon.",
        "Aktiv vennegjeng: sosial motivasjon ved a dele aktivitet med venner.",
        "Kunnskap: korte forskningsbaserte artikler om fysisk aktivitet og helse.",
    ]
    for f in features:
        d.paragraph(f, bullet=True, after=2.0)

    d.heading("Priser", level=2)
    d.paragraph("Mia Health Gratis: 0 kr. Inkluderer blant annet AQ, utfordringer, vennefunksjoner og kunnskapsinnhold.")
    d.paragraph("Mia Health Premium: fra 25 kr/maned. Oppgis a gi full historikk, utvikling over tid, prediksjoner og ekstra fordeler.")

    d.heading("Kom i gang", level=2)
    d.paragraph("Siden beskriver appen som gratis a starte med, med App Store- og Google Play-lenker pa bunnen.")

    d.heading("Merknad", level=3)
    d.paragraph("Dette dokumentet er en tekstbasert PDF-eksport av innholdet pa den oppgitte siden. Bilder, layout og interaktive elementer fra nettsiden er ikke gjenskapt 1:1.", size=9.5)

    return d


def write_pdf(doc: PDFDoc, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    objects: list[bytes] = []

    # 1: Catalog (filled later with Pages obj 2)
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")

    # 2: Pages tree placeholder, fill kids after page objects are known
    # We'll patch later after object assembly indices are known.
    objects.append(b"__PAGES_PLACEHOLDER__")

    # Font objects
    font_f1_obj = len(objects) + 1
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font_f2_obj = len(objects) + 1
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    page_obj_nums: list[int] = []
    content_obj_nums: list[int] = []

    for page_cmds in doc.pages:
        stream = ("\n".join(page_cmds) + "\n").encode("latin-1", errors="replace")
        content_obj_num = len(objects) + 1
        content_obj_nums.append(content_obj_num)
        objects.append(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream")

        page_obj_num = len(objects) + 1
        page_obj_nums.append(page_obj_num)
        page_obj = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W:.0f} {PAGE_H:.0f}] "
            f"/Resources << /Font << /F1 {font_f1_obj} 0 R /F2 {font_f2_obj} 0 R >> >> "
            f"/Contents {content_obj_num} 0 R >>"
        ).encode("ascii")
        objects.append(page_obj)

    kids = " ".join(f"{n} 0 R" for n in page_obj_nums)
    pages_obj = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_obj_nums)} >>".encode("ascii")
    objects[1] = pages_obj

    out = bytearray()
    out.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{i} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")

    xref_pos = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    out.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n"
        ).encode("ascii")
    )

    out_path.write_bytes(out)


def main() -> None:
    doc = build_doc()
    write_pdf(doc, OUTPUT_PDF)
    print(f"Generated: {OUTPUT_PDF}")
    print(f"Pages: {len(doc.pages)}")


if __name__ == "__main__":
    main()
