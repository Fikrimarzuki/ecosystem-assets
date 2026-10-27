# M1.0k-A3 Mom master candidate v2 review sheet. Every character image is downscaled or shown 1:1 — never enlarged.
import sys

from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QColor, QImage

sys.path.insert(0, "/Users/mfm/code/porto-projects/ecosystem-assets/projects/momee/candidates/m1.0j-construction")
import sheets_j  # noqa: E402
from sheets_j import new_doc, layer, text, badge, frame, checker, COCOA, INK2, TERRA, SAGE  # noqa: E402

sheets_j.KINDS.setdefault("candidate", ("MASTER CANDIDATE v2 · NOT ACCEPTED · NOT PRODUCTION-APPROVED", TERRA, True, "#fbe7dc"))


def alpha_box(img, t=128):
    x0, y0, x1, y1 = img.width(), img.height(), -1, -1
    for y in range(img.height()):
        hit = False
        for x in range(0, img.width(), 2):
            if (img.pixel(x, y) >> 24) & 255 >= t:
                hit = True
                x0 = min(x0, x); x1 = max(x1, x)
        if hit:
            y0 = min(y0, y); y1 = max(y1, y)
    return x0, y0, x1, y1


def fig_at(p, img, box, feet_x, ground_y, height_px):
    """Draw img scaled so its alpha box height = height_px (must not enlarge), soles on ground_y."""
    x0, y0, x1, y1 = box
    s = height_px / (y1 - y0 + 1)
    assert s <= 1.0001, "enlargement refused"
    cx = (x0 + x1) / 2
    p.drawImage(QRectF(feet_x - cx * s, ground_y - (y1 + 1) * s, img.width() * s, img.height() * s), img)


def build(F, checks, spec8):
    d = new_doc("Momee Mom master candidate v2 review", 2560, 3000)
    acc, v1, v2 = QImage(F["accepted"]), QImage(F["v1_placed"]), QImage(F["v2_master"])
    sheet = QImage(F["sheet"])
    ab, b1, b2 = alpha_box(acc), alpha_box(v1), alpha_box(v2)
    layer(d, "Paper", lambda p: p.fillRect(0, 0, 2560, 3000, QColor("#fefaf1")))
    layer(d, "Header and legend", lambda p: (
        text(p, 40, 62, "MOMEE · M1.0k-A3 · REVISED MOM MASTER — candidate v2 vs accepted Mom v1.2 (and the A2 candidate v1)", 36, COCOA, True),
        text(p, 40, 98, "candidates/m1.0k-a/mom-three-quarter-master-candidate-v2.png (1284×1225, figure 1195 px) → alpha-only glow trim → "
             "intake `place` (×0.9683) onto the 800×1248 master canvas. Review only.", 18, INK2),
        badge(p, 40, 118, "accepted"), badge(p, 560, 118, "candidate")))

    def row1(p):
        text(p, 40, 210, "1 · Matched character height (the accepted figure's native 513 px; candidates downscaled)", 28, COCOA, True)
        frame(p, 40, 236, 1500, 640, "extract")
        g, ah = 830, ab[3] - ab[1] + 1
        for x, img, box, lab, col in ((280, acc, ab, f"accepted Mom v1.2 (native {ah} px)", COCOA),
                                      (760, v2, b2, f"candidate v2 at {ah} px", COCOA),
                                      (1240, v1, b1, "A2 candidate v1 (history; revise)", INK2)):
            fig_at(p, img, box, x, g, ah)
            text(p, x - 150, g + 34, lab, 16, col, True)
        p.fillRect(QRectF(60, g, 1460, 2), QColor(TERRA))
        frame(p, 1560, 236, 960, 640, "extract")
        lines = ["Head count (hair top → chin): v1.2 ≈ 3.29–3.38 · v2 3.42 (3.40–3.44) · v1 3.68 → v2 PASS (D13 3.2–3.5)",
                 "Expression: gentle closed-mouth smile, as v1.2 (v1 had an open toothy smile).",
                 "Facing: left-facing ¾, ear on the viewer's left — automated check decides it (IoU 0.884 vs 0.800);",
                 "   head-and-shoulders test agrees (0.938 vs 0.851). No manual override needed.",
                 "Eye line 0.195 of figure height vs 0.206 (Δ 1.1 % ≤ ±2 %); eye size ≈ v1.2 (≤ 8 % larger, near reading error).",
                 "Hair: same side part, sweep and mid-back waves; slightly fuller on the viewer's left.",
                 "Outfit: coral rolled-sleeve blouse, beige wide-leg trousers (≈ 1–2 u wider), white shoes, clasped hands.",
                 "Palette ΔE00 by material: hair 2.8 · skin 0.9 · blouse 3.8 (a touch lighter) · trousers 0.8 · shoes 1.1",
                 "Rendering: soft painterly shading, warm brown lines; crisper and glossier hair than the 514 px cutout."]
        for i, s in enumerate(lines):
            text(p, 1584, 280 + i * 62, s, 17, INK2)
    layer(d, "1 — Matched height", row1)

    def row2(p):
        text(p, 40, 940, "2 · Faces (downscaled only): v1.2 sheet close-up · v1.2 main figure (1:1) · v2 at v1.2 head size · v2 (×0.8)", 28, COCOA, True)
        frame(p, 40, 966, 1500, 470, "extract")
        p.drawImage(QRectF(70, 990, 292, 292), sheet, QRectF(1222, 212, 292, 292))       # sheet close-up 1:1
        p.drawImage(QRectF(400, 1040, 200, 200), acc, QRectF(28, 0, 200, 200))           # accepted native 1:1
        s = 156 / (395 - 56)                                                               # v2 head → v1.2 head size
        p.drawImage(QRectF(630, 1040, 200, 200), v2, QRectF(420 - 100 / s, 56 - 16 / s, 200 / s, 200 / s))  # ×0.46, framed like v1.2
        p.drawImage(QRectF(860, 990, 640, 400), v2, QRectF(20, 40, 800, 500))            # ×0.8
        for x, lab in ((70, "v1.2 close-up (sheet)"), (400, "v1.2 main figure"), (630, "v2, same head size"), (860, "v2 master (×0.8)")):
            text(p, x, 1420, lab, 15, COCOA, True)
        frame(p, 1560, 966, 960, 470, "extract")
        text(p, 1584, 998, "Intake `check` on the 800×1248 master (tool unchanged; --chin-y 395)", 16, COCOA, True)
        for i, (lvl, name, det) in enumerate(checks):
            col = {"PASS": SAGE, "FAIL": TERRA, "INFO": INK2}[lvl]
            line = f"{lvl}  {name}: {det}"
            text(p, 1584, 1024 + i * 22, line if len(line) <= 118 else line[:115] + "…", 14, col, lvl != "INFO")
        text(p, 1584, 1024 + len(checks) * 22 + 10, "@2x and @1x tiers: same 12 PASS / 0 FAIL (3.43 and 3.45 heads).", 14, INK2, True)
    layer(d, "2 — Faces and intake checks", row2)

    def row3(p):
        text(p, 40, 1500, "3 · Bedroom at 1 px/u (unchanged layout; Boy 200 u at CHILD_START, Mom 290 u at MOM_SPOT) — before (M1.0j-C) · after (v2)", 28, COCOA, True)
        before, after = QImage(F["before"]), QImage(F["after"])
        for i, im in enumerate((before, after)):
            x = 40 + i * 1250
            frame(p, x, 1526, 1236, 560, "extract")
            p.drawImage(QRectF(x + 8, 1534, 1220, 540), im, QRectF(30, 150, 1220, 540))
        text(p, 60, 2116, "Before: accepted v1.2 extraction (1.77 px/u, @1x only)", 16, COCOA, True)
        text(p, 1310, 2116, "After: master candidate v2 (4 px/u source, downscaled); contact shadow is a study-only layer", 16, COCOA, True)
    layer(d, "3 — Bedroom before and after", row3)

    def row4(p):
        text(p, 40, 2190, "4 · Tier exports (1:1) · silhouette vs accepted @1x · phone child-and-mom", 28, COCOA, True)
        t1, t2, dm = QImage(F["tier1"]), QImage(F["tier2"]), QImage(F["iou_diff"])
        checker(p, 40, 2220, 400, 624)
        p.drawImage(QRectF(40, 2220, 400, 624), t2)
        checker(p, 460, 2532, 200, 312)
        p.drawImage(QRectF(460, 2532, 200, 312), t1)
        p.drawImage(QRectF(680, 2532, 200, 312), dm)
        text(p, 40, 2870, "@2x 400×624, anchor (200, 608)", 15, COCOA, True)
        text(p, 460, 2870, "@1x 200×312", 15, COCOA, True)
        text(p, 680, 2870, "IoU 0.884: grey both · red v2 only · blue v1.2 only", 15, COCOA, True)
        pa, pb = QImage(F["portrait_before"]), QImage(F["portrait_after"])
        text(p, 1080, 2240, "390×844 child-and-mom (device 1.17), shown ×0.62: before · after", 18, COCOA, True)
        p.drawImage(QRectF(1080, 2260, 333 * 0.62, 720 * 0.62), pa)
        p.drawImage(QRectF(1300, 2260, 333 * 0.62, 720 * 0.62), pb)
        x0 = 1540
        text(p, x0, 2290, "Spec §8 visual-fidelity checks", 20, COCOA, True)
        for i, (state, s) in enumerate(spec8):
            col = {"PASS": SAGE, "NEAR": TERRA, "OWNER": "#3f6488", "N/A": INK2, "OPEN": TERRA}[state]
            text(p, x0, 2324 + i * 30, f"{state:5}  {s}", 15, col, state != "N/A")
        y = 2324 + len(spec8) * 30 + 30
        text(p, x0, y, "Recommendation: ACCEPT v2 as the Mom master candidate for owner visual review.", 19, TERRA, True)
        text(p, x0, y + 28, "Owner to judge the §8.2 near-miss (outline-width, not pose) and record provenance before any", 16, TERRA)
        text(p, x0, y + 50, "production approval. Layering and hidden overlaps (§5–6) remain for the rig milestone.", 16, TERRA)
    layer(d, "4 — Tiers, silhouette and verdict", row4)
    d.refreshProjection()
    d.waitForDone()
    return d
