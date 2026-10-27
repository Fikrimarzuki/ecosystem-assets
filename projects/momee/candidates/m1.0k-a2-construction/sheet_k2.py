# M1.0k-A2 Mom master intake review sheet. Every image is downscaled or shown 1:1 — never enlarged.
import sys

from PyQt5.QtCore import QPointF, QRect, QRectF
from PyQt5.QtGui import QColor, QImage

sys.path.insert(0, "/Users/mfm/code/porto-projects/ecosystem-assets/projects/momee/candidates/m1.0j-construction")
from sheets_j import new_doc, layer, text, badge, frame, checker, COCOA, INK2, TERRA  # noqa: E402


def alpha_box(img, t=128):
    x0, y0, x1, y1 = img.width(), img.height(), -1, -1
    for y in range(0, img.height()):
        row_hit = False
        for x in range(0, img.width(), 2):
            if (img.pixel(x, y) >> 24) & 255 >= t:
                row_hit = True
                x0 = min(x0, x); x1 = max(x1, x)
        if row_hit:
            y0 = min(y0, y); y1 = max(y1, y)
    return x0, y0, x1, y1


def fig_at(p, img, box, feet_x, ground_y, height_px):
    """Draw img scaled so its alpha box height = height_px (must not enlarge), soles on ground_y."""
    x0, y0, x1, y1 = box
    s = height_px / (y1 - y0 + 1)
    assert s <= 1.0001, "enlargement refused"
    cx = (x0 + x1) / 2
    p.drawImage(QRectF(feet_x - cx * s, ground_y - (y1 + 1) * s, img.width() * s, img.height() * s), img)


def build(F, checks):
    d = new_doc("Momee Mom master intake review v1", 2560, 2600)
    acc, cand = QImage(F["accepted"]), QImage(F["candidate_placed"])
    sheet = QImage(F["sheet"])
    ab, cb = alpha_box(acc), alpha_box(cand)
    layer(d, "Paper", lambda p: p.fillRect(0, 0, 2560, 2600, QColor("#fefaf1")))
    layer(d, "Header and legend", lambda p: (
        text(p, 40, 62, "MOMEE · M1.0k-A2 · MOM MASTER INTAKE — owner-supplied candidate vs accepted Mom v1.2", 36, COCOA, True),
        text(p, 40, 98, "candidates/m1.0k-a/mom-3.png (1024×1536, new high-resolution art) after a derivative glow trim, placed on the 800×1248 master canvas "
             "by the intake tool. Review only: not accepted, not approved.", 18, INK2),
        badge(p, 40, 118, "accepted"), badge(p, 560, 118, "extract")))

    def row1(p):
        text(p, 40, 210, "1 · Matched character height (the accepted figure's native 513 px) and matched head size", 28, COCOA, True)
        frame(p, 40, 236, 1500, 640, "extract")
        g = 830
        ah = ab[3] - ab[1] + 1   # accepted figure at its native size (no resampling)
        for x, img, box, h, lab in ((260, acc, ab, ah, f"accepted Mom v1.2 (native {ah} px)"),
                                     (720, cand, cb, ah, f"candidate at {ah} px (downscaled)"),
                                     (1200, cand, cb, round(ah * 3.68 / 3.38), "candidate, head size matched to v1.2")):
            fig_at(p, img, box, x, g, min(h, img.height()))
            text(p, x - 150, g + 34, lab, 16, COCOA, True)
        p.fillRect(QRectF(60, g, 1460, 2), QColor(TERRA))
        frame(p, 1560, 236, 960, 640, "extract")
        lines = ["Head count (hair top → chin): v1.2 ≈ 3.29–3.38 · candidate ≈ 3.68 (bible D13 range 3.2–3.5) → FAIL",
                 "Same head size: the candidate's body below the head is ≈ 9% longer (mostly trousers/legs).",
                 "Head + hair silhouette (head-matched): IoU 0.94 as drawn vs 0.85 mirrored → same left-facing ¾ turn.",
                 "Eyes vs head: height ≈ 0.17 and width ≈ 0.21 of head height in both → eye size preserved.",
                 "Expression: open toothy smile (v1.2 main figure: gentle closed smile).",
                 "Face: slightly fuller cheeks / softer chin — reads a little younger (owner judgement).",
                 "Palette ΔE00 by material: hair 2.2 · skin 0.9 · blouse 2.6 · trousers 1.0 · shoes 1.4",
                 "Outfit, rolled sleeves, side part, long waves, clasped hands, white shoes: match.",
                 "Line and shading: soft painterly, warm brown lines — consistent with v1.2 and the Boy."]
        for i, s in enumerate(lines):
            text(p, 1584, 280 + i * 58, s, 17, INK2)
    layer(d, "1 — Matched height and head", row1)

    def row2(p):
        text(p, 40, 940, "2 · Faces (each downscaled only): v1.2 sheet close-up · v1.2 main figure · candidate", 28, COCOA, True)
        frame(p, 40, 966, 1500, 420, "extract")
        p.drawImage(QRectF(70, 990, 292, 292), sheet, QRectF(1222, 212, 292, 292))  # sheet close-up 1:1
        p.drawImage(QRectF(420, 1066, 150, 150), acc, QRectF(60, 40, 150, 150))    # accepted native 1:1
        p.drawImage(QRectF(640, 990, 360, 288), cand, QRectF(cb[0] + 120, cb[1] + 40, 450, 360))  # candidate ×0.8
        text(p, 70, 1340, "v1.2 close-up (sheet)", 15, COCOA, True)
        text(p, 420, 1340, "v1.2 main figure (514 px)", 15, COCOA, True)
        text(p, 640, 1340, "candidate (master canvas, ×0.8)", 15, COCOA, True)
        frame(p, 1560, 966, 960, 420, "extract")
        for i, (lvl, name, det) in enumerate(checks):
            col = {"PASS": "#5d7a60", "FAIL": TERRA, "INFO": INK2}[lvl]
            line = f"{lvl}  {name}: {det}"
            text(p, 1584, 1004 + i * 22, line if len(line) <= 118 else line[:115] + "…", 14, col, lvl != "INFO")
        text(p, 1584, 1004 + len(checks) * 22 + 8, "Facing FAIL is a silhouette tie (0.800 vs 0.801), i.e. inconclusive; the head-region test decides it:", 14, INK2)
        text(p, 1584, 1004 + len(checks) * 22 + 30, "IoU 0.94 vs 0.85 and face colour Δ 27.9 vs 84.9 → same left-facing turn as v1.2. Tool unchanged.", 14, INK2)
    layer(d, "2 — Faces and intake checks", row2)

    def row3(p):
        text(p, 40, 1450, "3 · Bedroom at 1 px/u (unchanged layout; Boy 200 u at CHILD_START, Mom 290 u at MOM_SPOT) — before (M1.0j-C) · after (candidate)", 28, COCOA, True)
        before, after = QImage(F["before"]), QImage(F["after"])
        for i, im in enumerate((before, after)):
            x = 40 + i * 1250
            frame(p, x, 1476, 1236, 560, "extract")
            p.drawImage(QRectF(x + 8, 1484, 1220, 540), im, QRectF(30, 150, 1220, 540))
        text(p, 60, 2066, "Before: accepted v1.2 extraction (1.77 px/u, @1x only)", 16, COCOA, True)
        text(p, 1310, 2066, "After: candidate master (4 px/u source, downscaled); contact shadow is a study-only layer", 16, COCOA, True)
        pa, pb = QImage(F["portrait_before"]), QImage(F["portrait_after"])
        text(p, 40, 2120, "390×844 child-and-mom (device 1.17, shown 1:1): before · after", 20, COCOA, True)
        p.drawImage(QRectF(40, 2140, 333 * 0.62, 720 * 0.62), pa)
        p.drawImage(QRectF(260, 2140, 333 * 0.62, 720 * 0.62), pb)
        text(p, 500, 2180, "Both characters measure their target heights in every view (full, desktop, phone portrait/landscape,", 16, INK2)
        text(p, 500, 2206, "child-and-mom); the candidate no longer touches the 390×844 overview frame edge.", 16, INK2)
        text(p, 500, 2250, "Recommendation: REVISE (minor) — keep this candidate as the quality reference; request ≈ 3.4-head", 18, TERRA, True)
        text(p, 500, 2276, "proportions (shorter legs/trousers, unchanged head) and the gentle closed smile, then re-run intake.", 18, TERRA, True)
    layer(d, "3 — Bedroom before and after", row3)
    d.refreshProjection()
    d.waitForDone()
    return d
