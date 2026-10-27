# M1.0l-A3 closed-eye candidate validation review sheet.
# Character images are 1:1 or downscaled, except the clearly labelled eye inspection zooms (×3, nearest neighbour, display only).
import sys

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QColor, QImage, QPainter

sys.path.insert(0, "/Users/mfm/code/porto-projects/ecosystem-assets/projects/momee/candidates/m1.0j-construction")
import sheets_j  # noqa: E402
from sheets_j import new_doc, layer, text, badge, frame, checker, COCOA, INK2, TERRA, SAGE  # noqa: E402

sheets_j.KINDS.setdefault("reference", ("REFERENCE ONLY · NOT EXTRACTABLE · NOT ACCEPTED", "#8a8580", True, "#ecebea"))
sheets_j.KINDS.setdefault("failed", ("COMPOSITE TEST · FAILED · NOT A CANDIDATE", TERRA, True, "#fbe7dc"))
CROP = QRectF(240, 150, 340, 330)


def zoom(p, img, src, x, y, s=3):
    p.save()
    p.setRenderHint(QPainter.SmoothPixmapTransform, False)
    p.drawImage(QRectF(x, y, src.width() * s, src.height() * s), img, src)
    p.restore()


def build(F, claims, meas, ready, rec):
    d = new_doc("Momee Mom closed-eye intake v1 review", 2560, 2290)
    master, comp = QImage(F["master"]), QImage(F["composite"])
    layer(d, "Paper", lambda p: p.fillRect(0, 0, 2560, 2290, QColor("#fefaf1")))
    layer(d, "Header", lambda p: (
        text(p, 40, 56, "MOMEE · M1.0l-A3 · CLOSED-EYE ARTWORK VALIDATION — candidate sheet vs accepted Mom v2 and the M1.0l-A1 eye masks", 32, COCOA, True),
        text(p, 40, 90, "candidates/m1.0l-a3/mom-eyes-closed-candidate-v1.png (1536×1024). Result: the closed-eye design is on-model, but the file is REFERENCE ONLY — "
             "the composite test fails (visible skin patches); revision needed.", 17, INK2),
        badge(p, 40, 102, "accepted"), badge(p, 570, 102, "reference"), badge(p, 1110, 102, "failed")))

    def r1(p):
        text(p, 40, 175, "1 · Accepted Mom v2 face (1:1)", 24, COCOA, True)
        frame(p, 40, 190, 380, 400, "extract")
        checker(p, 60, 210, 340, 330)
        p.drawImage(QRectF(60, 210, 340, 330), master, CROP)
        text(p, 60, 568, "master x 240–580, y 150–480 (visual authority)", 13, COCOA, True)
        text(p, 460, 175, "2 · Candidate file (whole sheet, ×0.5) — generated documentation sheet", 24, COCOA, True)
        frame(p, 460, 190, 812, 560, "reference", bg="#f4f3f1")
        checker(p, 482, 210, 768, 512)
        p.drawImage(QRectF(482, 210, 768, 512), QImage(F["sheet"]))
        text(p, 482, 742, "Printed claims are not evidence — each was measured (right).", 13, TERRA, True)
        text(p, 1310, 175, "3 · Printed claims vs measurements", 24, COCOA, True)
        frame(p, 1310, 190, 1210, 560, "extract")
        for i, (claim, verdict, ev) in enumerate(claims):
            y = 228 + i * 64
            text(p, 1334, y, claim, 15, COCOA, True)
            text(p, 1334, y + 24, ev, 13, INK2)
            text(p, 2400, y, verdict, 15, SAGE if verdict == "TRUE" else TERRA, True)
    layer(d, "1–3 — Face, sheet, claims", r1)

    def r2(p):
        text(p, 40, 810, "4 · Closed-eye close-up from the sheet (panel 3) · fitted to master scale · composite test on a master COPY", 24, COCOA, True)
        frame(p, 40, 826, 420, 420, "reference", bg="#f4f3f1")
        p3 = QImage(F["p3"])
        p.drawImage(QRectF(60, 846, p3.width(), p3.height()), p3)
        text(p, 60, 1228, "panel 3, native 379×358 (REFERENCE ONLY)", 13, TERRA, True)
        frame(p, 480, 826, 380, 420, "reference", bg="#f4f3f1")
        checker(p, 500, 846, 340, 330)
        p.drawImage(QRectF(500, 846, 340, 330), QImage(F["p3fit"]), CROP)
        text(p, 500, 1200, "downscaled ×0.81, offset (269, 129)", 13, COCOA, True)
        text(p, 500, 1220, "(no enlargement needed)", 13, SAGE, True)
        frame(p, 880, 826, 380, 420, "failed")
        p.drawImage(QRectF(900, 846, 340, 330), comp, CROP)
        text(p, 900, 1200, "A1 eye masks filled from the fitted panel", 13, TERRA, True)
        text(p, 900, 1220, "lighter skin patches show the mask outlines", 13, TERRA, True)
        text(p, 1300, 810, "5 · Eye close-ups (inspection zoom ×3, display only)", 24, COCOA, True)
        frame(p, 1300, 826, 1220, 420, "extract")
        zoom(p, master, QRectF(330, 240, 96, 90), 1320, 846)
        zoom(p, comp, QRectF(330, 240, 96, 90), 1620, 846)
        zoom(p, master, QRectF(455, 252, 90, 90), 1920, 846)
        zoom(p, comp, QRectF(455, 252, 90, 90), 2220, 846)
        for x, s in ((1320, "near · v2 open"), (1620, "near · composite"), (1920, "far · v2 open"), (2220, "far · composite")):
            text(p, x, 1146, s, 14, COCOA, True)
    layer(d, "4–5 — Close-up, fit, composite", r2)

    def r3(p):
        text(p, 40, 1300, "6 · Alignment and seam findings (composite on a master copy; master and A1 layers untouched)", 24, COCOA, True)
        frame(p, 40, 1316, 1500, 520, "extract")
        for i, (k, v, ok) in enumerate(meas):
            y = 1356 + i * 42
            text(p, 64, y, k, 15, COCOA, True)
            text(p, 470, y, v, 15, SAGE if ok == "ok" else (TERRA if ok == "fail" else INK2))
        text(p, 1580, 1300, "7 · Readiness", 24, COCOA, True)
        frame(p, 1580, 1316, 940, 520, "extract")
        for i, (k, st, why) in enumerate(ready):
            y = 1360 + i * 74
            text(p, 1604, y, k, 17, COCOA, True)
            text(p, 1990, y, st, 17, SAGE if st in ("USABLE", "PASS") else TERRA, True)
            text(p, 1604, y + 26, why, 13, INK2)
    layer(d, "6–7 — Findings and readiness", r3)

    def r4(p):
        text(p, 40, 1930, "8 · Recommendation", 24, COCOA, True)
        frame(p, 40, 1946, 2480, 300, "extract")
        for i, s in enumerate(rec):
            text(p, 64, 1988 + i * 32, s, 16, TERRA if i == 0 else INK2, i == 0)
    layer(d, "8 — Recommendation", r4)
    d.refreshProjection()
    d.waitForDone()
    return d
