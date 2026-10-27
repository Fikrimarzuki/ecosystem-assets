# M1.0j-C scale-and-quality review sheet. All scene/line-up renders are placed 1:1 (no character
# enlargement); only the edge-inspection crops are zoomed, and are labelled as such.
import json
import sys

from PyQt5.QtCore import QPointF, QRect, QRectF, Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPen

sys.path.insert(0, "/Users/mfm/code/porto-projects/ecosystem-assets/projects/momee/candidates/m1.0j-construction")
from sheets_j import new_doc, layer, text, badge, frame, checker, rr, COCOA, INK2, TERRA, DUSTY  # noqa: E402

R = "/Users/mfm/code/porto-projects/ecosystem-assets/projects/momee/review/m1.0j-c/"


def build(rep, zooms):
    d = new_doc("Momee character scale and quality v1", 2560, 2720)
    img = {k: QImage(R + k + ".png") for k in ("lineup.@1x", "bedroom-full.@1x", "desktop-1280x800-overview", "phone-portrait-390x844-overview",
                                                 "phone-portrait-390x844-child-and-mom", "phone-landscape-844x390-overview",
                                                 "phone-landscape-844x390-child-and-mom")}
    meas = {}
    for v in rep["views"]:
        meas.setdefault(v["view"], {})[v["character"]] = v
    layer(d, "Paper", lambda p: p.fillRect(0, 0, 2560, 2720, QColor("#fefaf1")))
    layer(d, "Header and legend", lambda p: (
        text(p, 40, 62, "MOMEE · M1.0j-C · CHARACTER SCALE AND EDGE QUALITY — owner-accepted Boy and Mom v1.2 (cleaned extractions)", 34, COCOA, True),
        text(p, 40, 98, "Every scene and line-up image below is placed 1:1 (characters only ever downscaled). Heights are measured from character-only masks "
             "(alpha ≥ 50%), not assumed.", 18, INK2),
        badge(p, 40, 118, "extract")))

    def row1(p):
        text(p, 40, 210, "1 · Line-up on one ground line — @1x tier (1 px per world unit), unscaled", 26, COCOA, True)
        L = img["lineup.@1x"]
        frame(p, 40, 230, L.width() + 40, L.height() + 40, "extract")
        p.drawImage(QPointF(60, 250), L)
        lb, lm = rep["lineup"]["boy"], rep["lineup"]["mom"]
        x, y = L.width() + 120, 280
        for line in (f"Boy: {lb['heightPx']} px tall (target 200 u; 200 rows incl. a semi-transparent hair-tip row) · {lb['heads']} heads",
                     f"Mom v1.2: {lm['heightPx']} px tall (target 290 u) · {lm['heads']} heads (accepted candidate range 3.2–3.5)",
                     f"Ratio {rep['lineup']['ratio']} at the 50% alpha threshold; 290 / 200 = 1.450 by row count",
                     "Soles end on the row directly above the ground line in both tiers (anchor rows 216 / 304).",
                     "Heads measured on the native extractions: hair top → chin, ±2 px (±0.4%)."):
            text(p, x, y, line, 18, INK2)
            y += 32
        # edge inspection
        x0, y0 = L.width() + 120, 460
        text(p, x0, y0, "Edge cleanup (derivative only) — pixel inspection zoom 4× on dark, NOT a scale view: original (top) vs cleaned (bottom)", 17, COCOA, True)
        for i, (lab, before, after) in enumerate(zooms):
            bx = x0 + i * 300
            p.drawImage(QRectF(bx, y0 + 16, 280, 160), before)
            p.drawImage(QRectF(bx, y0 + 186, 280, 160), after)
            text(p, bx, y0 + 370, lab, 15, COCOA, True)
    layer(d, "1 — Line-up and edge cleanup", row1)

    def scene(p, key, x, y, title, chars):
        im = img[key]
        frame(p, x - 12, y - 12, im.width() + 24, im.height() + 74, "extract")
        p.drawImage(QPointF(x, y), im)
        text(p, x, y + im.height() + 26, title, 16, COCOA, True)
        parts = []
        for c in ("boy", "mom"):
            m = chars.get(c)
            if m:
                clip = (" · frame-clipped " + "/".join(m["clippedByFrame"])) if m.get("clippedByFrame") else ""
                parts.append(f"{c} {m['measuredPx']} px (expected {m['expectedPx']}){clip}")
        text(p, x, y + im.height() + 48, " · ".join(parts), 14, INK2)

    def row2(p):
        text(p, 40, 870, "2 · Full bedroom and desktop framing (shown 1:1 at 1 px/u)", 26, COCOA, True)
        scene(p, "bedroom-full.@1x", 52, 900, "Full bedroom @1x — Boy at CHILD_START (520, 630), Mom at MOM_SPOT (840, 560)", meas["full bedroom @1x (1 px/u)"])
        scene(p, "desktop-1280x800-overview", 1360, 900, "1280×800 overview — device zoom 1.10 (shown at 1.0)", meas["desktop-1280x800-overview"])
    layer(d, "2 — Full bedroom and desktop", row2)

    def row3(p):
        text(p, 40, 1720, "3 · Phone framings at real CSS size (zoom ≤ 1) or 1:1 (zoom > 1, labelled); camera frames from camera-framing.ts", 26, COCOA, True)
        y = 1750
        scene(p, "phone-portrait-390x844-overview", 52, y, "390×844 overview · zoom 0.94", meas["phone-portrait-390x844-overview"])
        scene(p, "phone-portrait-390x844-child-and-mom", 480, y, "390×844 child-and-mom · device 1.17 (shown 1.0)", meas["phone-portrait-390x844-child-and-mom"])
        scene(p, "phone-landscape-844x390-overview", 860, y, "844×390 overview · zoom 0.85", meas["phone-landscape-844x390-overview"])
        scene(p, "phone-landscape-844x390-child-and-mom", 860, y + 480, "844×390 child-and-mom · zoom 0.85", meas["phone-landscape-844x390-child-and-mom"])
        notes = ["child-and-mom renders place the Boy at Mom's approach",
                 "point (730, 590), where the story puts him for that beat;",
                 "depth is sorted by feet y.",
                 "",
                 "390×844 overview: the 416 u frame clips the Boy's left",
                 "edge (≈ 6 u) and touches Mom's hair on the right. The real",
                 "art is wider than the 92 u placeholder: gameplay follow",
                 "framing and CHILD_EXTENT need updating at integration",
                 "(not changed in M1.0j-C).",
                 "",
                 "Lighting: both figures carry soft near-frontal baked light",
                 "that reads with the window; warm palette matches the room;",
                 "the characters' painted lines are finer and darker than the",
                 "room's 1.0 u lines — acceptable, characters lead (bible §3)."]
        for i, n in enumerate(notes):
            text(p, 1760, 1790 + i * 28, n, 15, INK2)
    layer(d, "3 — Phone framings", row3)
    d.refreshProjection()
    d.waitForDone()
    return d
