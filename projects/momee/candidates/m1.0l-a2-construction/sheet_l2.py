# M1.0l-A2 facial-animation concept intake review sheet. Character images are shown 1:1 or downscaled — never enlarged.
import sys

from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QColor, QImage

sys.path.insert(0, "/Users/mfm/code/porto-projects/ecosystem-assets/projects/momee/candidates/m1.0j-construction")
import sheets_j  # noqa: E402
from sheets_j import new_doc, layer, text, badge, frame, checker, COCOA, INK2, TERRA, SAGE  # noqa: E402

sheets_j.KINDS.setdefault("reference", ("REFERENCE ONLY · NOT EXTRACTABLE · NOT ACCEPTED", "#8a8580", True, "#ecebea"))
CROP = QRectF(240, 150, 340, 330)


def build(F, A, inv, missing, ready):
    d = new_doc("Momee Mom facial concept intake v1 review sheet", 2560, 2190)
    master = QImage(F["master"])
    layer(d, "Paper", lambda p: p.fillRect(0, 0, 2560, 2190, QColor("#fefaf1")))
    layer(d, "Header", lambda p: (
        text(p, 40, 56, "MOMEE · M1.0l-A2 · FACIAL ANIMATION ARTWORK INTAKE — concept sheet vs accepted Mom v2 and the M1.0l-A1 head layers", 32, COCOA, True),
        text(p, 40, 90, "review/m1.0l-a2/mom-facial-animation-concept-v1.png (1536×1024). Result: every expression is REFERENCE ONLY — no candidate extracted, "
             "nothing redrawn, nothing enlarged on this sheet.", 17, INK2),
        badge(p, 40, 102, "accepted"), badge(p, 570, 102, "reference")))

    def s1(p):
        text(p, 40, 175, "1 · Accepted v2 face · A1 neutral layers (1:1)", 24, COCOA, True)
        frame(p, 40, 190, 760, 400, "extract")
        checker(p, 60, 210, 340, 330)
        p.drawImage(QRectF(60, 210, 340, 330), master, CROP)
        p.fillRect(QRectF(420, 210, 340, 330), QColor("#1d1a18"))
        for n in ("face-eyes__open__eye-near", "face-eyes__open__eye-far", "face-brows__neutral__brow-far", "face-mouth__neutral"):
            p.drawImage(QRectF(420, 210, 340, 330), QImage(F["a1layers"] + n + ".png"), CROP)
        text(p, 60, 568, "master head, 1:1", 13, COCOA, True)
        text(p, 420, 568, "eyes open · far brow · mouth neutral", 13, COCOA, True)
        text(p, 840, 175, "2 · Concept sheet (whole file, shown ×0.5)", 24, COCOA, True)
        frame(p, 840, 190, 812, 560, "reference", bg="#f4f3f1")
        sh = QImage(F["sheet"])
        checker(p, 862, 210, 768, 512)
        p.drawImage(QRectF(862, 210, 768, 512), sh)
        text(p, 862, 742, "Generated restyle of the M1.0l-A1 review sheet (garbled title); its panels are new illustrations, not A1 pixels.", 13, TERRA, True)
        x = 1690
        rows = ["Identification", f"sha256 {F['sha'][:16]}… · 2,745,454 bytes · PNG 1536×1024 RGBA8, sRGB",
                "XMP Core 6.0.0 + eXIf (same macOS writer as v1/v2); no C2PA, no generator tags",
                "Only new file since M1.0l-A1; name matches the brief", "",
                "Misleading content to note",
                "• shows a clean separated near eyebrow, which A1 found NOT separable",
                "• labels its head close-up '1:1 from master' — it is a redraw",
                "• the expression row (section 6) is the only intended new artwork"]
        for i, s in enumerate(rows):
            text(p, x, 222 + i * 30, s, 15 if i not in (0, 5) else 17, COCOA if i in (0, 5) else INK2, i in (0, 5))
    layer(d, "1–2 — Accepted face and concept sheet", s1)

    def s2(p):
        text(p, 40, 810, "3 · Expression references from the concept sheet — native pixels, 1:1 (each ≈ 85–112 × 103 px)", 24, COCOA, True)
        frame(p, 40, 826, 2480, 380, "reference", bg="#f4f3f1")
        x = 64
        mat = QImage(F["analysis"] + "master-at-thumb-scale.png")
        p.drawImage(QRectF(x, 850, mat.width(), mat.height()), mat)
        text(p, x, 975, "v2 master ↓ to ×0.36", 12, SAGE, True)
        text(p, x, 991, "(same scale, for fidelity)", 12, SAGE)
        x += 130
        for key, lab in inv:
            im = QImage(F["analysis"] + "thumb-" + key + ".png")
            p.drawImage(QRectF(x, 850, im.width(), im.height()), im)
            text(p, x, 975, lab[0], 12, COCOA, True)
            text(p, x, 991, lab[1], 12, TERRA if "REF" in lab[1] else INK2)
            x += im.width() + 26
        y = 1030
        notes = ["Scale: the thumbnails are drawn at ×0.36–0.39 of the master; using them at 4 px/u would need ×2.6–2.8 ENLARGEMENT (forbidden).",
                 "Feature size: near eye ≈ 33 px wide in a thumbnail vs 92 px on the master; mouth ≈ 22 px vs 59 px.",
                 "Frame consistency: each panel is a separate redraw of the whole face — outside the eye/mouth band, frames differ from their 'existing' partner by",
                 "  7.5–11.8 levels mean (the two 'open (existing)' panels differ from each other by 12.0), and the head sits 1–4 px differently in each panel.",
                 "Eye frames use thick BLACK lashes and a heavy lid line (v2: warm brown lines, softer lashes; bible: no black). Mouth frames are the most on-model."]
        for i, s in enumerate(notes):
            text(p, 64, y + i * 30, s, 15, INK2)
    layer(d, "3 — Expression references", s2)

    def s3(p):
        text(p, 40, 1260, "4 · Extracted candidates", 24, COCOA, True)
        frame(p, 40, 1276, 760, 180, "reference", bg="#f4f3f1")
        text(p, 64, 1320, "None.", 22, TERRA, True)
        for i, s in enumerate(["No expression passes the resolution check (needs ×2.6–2.8", "enlargement) or the frame-consistency check, so nothing was", "extracted and the A1 neutral layers are unchanged."]):
            text(p, 64, 1356 + i * 26, s, 15, INK2)
        text(p, 840, 1260, "5 · Missing artwork per expression (M1.0l-A1 map; nothing filled)", 24, COCOA, True)
        frame(p, 840, 1276, 1680, 470, "extract")
        p.drawImage(QRectF(864, 1296, 340, 330), QImage(F["missing"]))
        text(p, 864, 1650, "red: under attachments · hatched: neck", 13, COCOA, True)
        for i, (k, v) in enumerate(missing):
            text(p, 1230, 1316 + i * 46, k, 16, COCOA, True)
            text(p, 1230, 1338 + i * 46, v, 14, INK2)
        text(p, 40, 1500, "6 · Readiness", 24, COCOA, True)
        frame(p, 40, 1516, 760, 230, "extract")
        for i, (k, st, why) in enumerate(ready):
            text(p, 64, 1556 + i * 64, f"{k}:", 17, COCOA, True)
            text(p, 330, 1556 + i * 64, st, 17, TERRA if st == "BLOCKED" else SAGE, True)
            text(p, 64, 1580 + i * 64, why, 13, INK2)
    layer(d, "4–6 — Candidates, missing art, readiness", s3)

    def s4(p):
        text(p, 40, 1810, "7 · Recommended next step", 24, COCOA, True)
        frame(p, 40, 1826, 2480, 330, "extract")
        for i, s in enumerate(F["next"]):
            text(p, 64, 1868 + i * 30, s, 16, TERRA if i == 0 else INK2, i == 0)
    layer(d, "7 — Next step", s4)
    d.refreshProjection()
    d.waitForDone()
    return d
