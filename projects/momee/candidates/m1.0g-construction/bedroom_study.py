# M1.0g bedroom composition study v1. Run inside Krita: run(d) on a 2560x1440
# RGBA/8 document. World units (1280x720) at 2 px/unit, matching
# app-momee/apps/web/src/adventure/bedroom-layout.ts positions.
import random

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QFont, QImage, QPainter, QPen

import kpaint as K
from kpaint import C, P, rpoly, smooth, rrect, ellipse, poly, lin, rad

E = K.ensure

# ---- palette (bible §7 swatches and their mixes) --------------------------
WALL, WALL_TOP, WALL_LOW = "#f9eddc", "#f1dfc8", "#fbf2e4"
WAINSCOT, RAIL = "#f4e3cd", "#e8cfae"
WOOD, WOOD_FRONT, WOOD_SHADE, WOOD_LIGHT, WOOD_LINE = "#e8c69e", "#dfb98d", "#c99f76", "#f5dfbd", "#a57b5a"
FLOOR_BACK, FLOOR_FRONT, FLOOR_SEAM = "#efd8b6", "#e2c299", "#d4b089"
SHEET, SHEET_FRONT, SHEET_SHADE, CREAM_LINE = "#fbf3e6", "#efe5d7", "#cfd7e1", "#a28c80"
DUVET, DUVET_FRONT, DUVET_SHADE, DUVET_LIGHT, DUVET_LINE = "#9dbbc8", "#8eaebd", "#7393ab", "#c0d6de", "#5f7489"
SAGE, SAGE_DARK, SAGE_LIGHT, SAGE_LINE = "#9eb49f", "#7f977f", "#bccdb8", "#667d67"
BLUSH, BLUSH_SHADE, BLUSH_LINE = "#f3dccd", "#e8c4b0", "#c99a83"
COCOA = "#59463d"

# Calibration rule: line weights in world units (x2 for @2x pixels).
LW_INTERACT, LW_FURNITURE, LW_DECOR = 1.25, 1.0, 0.75
# Window, its shelf and its light sit left of centre so Mom (MOM_SPOT x=840) reads
# against calm wall instead of the curtain.
WINDOW_DX = -60


def obj(d, group, label, base, shade=None, light=None, line=None,
        shade_blur=12, light_blur=10, extra=None):
    """One material stack: base, clipped soft shade, clipped light, line."""
    g = f"{group}/{label}"
    E(d, g, "grouplayer")
    E(d, f"{g}/{label} — base")
    K.paint(d, f"{g}/{label} — base", base)
    if extra:
        for name, fn in extra:
            E(d, f"{g}/{label} — {name}", inherit=True)
            K.paint(d, f"{g}/{label} — {name}", fn)
    if shade:
        E(d, f"{g}/{label} — soft shade (clipped)", inherit=True)
        K.paint(d, f"{g}/{label} — soft shade (clipped)", shade)
        if shade_blur:
            K.blur(d, f"{g}/{label} — soft shade (clipped)", shade_blur)
    if light:
        E(d, f"{g}/{label} — warm light (clipped)", inherit=True)
        K.paint(d, f"{g}/{label} — warm light (clipped)", light)
        if light_blur:
            K.blur(d, f"{g}/{label} — warm light (clipped)", light_blur)
    if line:
        E(d, f"{g}/{label} — line")
        K.paint(d, f"{g}/{label} — line", line)


def text(p, x, y, s, size=9, color=COCOA, bold=False):
    f = QFont("Helvetica")
    f.setPixelSize(max(1, round(size)))
    f.setBold(bold)
    p.p.setFont(f)
    p.p.setPen(C(color) if isinstance(color, str) else color)
    p.p.drawText(QPointF(x, y), s)


# ---- room shell -------------------------------------------------------------
def room_shell(d):
    G = "Room shell"
    E(d, G, "grouplayer")
    for n in ["Wall — base cream", "Wall — window glow and corners", "Wall — wainscot and rail",
              "Floor — base honey wood", "Floor — planks", "Floor — contact shade at wall",
              "Floor — morning sun patch", "Baseboard"]:
        E(d, f"{G}/{n}")
    K.paint(d, f"{G}/Wall — base cream", lambda p: p.fill(
        rrect(-10, -10, 1300, 500, 0), lin(0, 0, 0, 480, [(0, WALL_TOP), (0.55, WALL), (1, WALL_LOW)])))

    def glow(p):
        p.fill(rrect(-10, -10, 1300, 500, 0), rad(660, 250, 520, [(0, C("#fff7e8", 190)), (1, C("#fff7e8", 0))]))
        p.fill(rrect(-10, -10, 1300, 500, 0), rad(-40, -40, 360, [(0, C("#e6cfb2", 120)), (1, C("#e6cfb2", 0))]))
        p.fill(rrect(-10, -10, 1300, 500, 0), rad(1320, -40, 380, [(0, C("#e6cfb2", 110)), (1, C("#e6cfb2", 0))]))
    K.paint(d, f"{G}/Wall — window glow and corners", glow)

    def wainscot(p):
        p.fill(rrect(-10, 398, 1300, 72, 0), lin(0, 398, 0, 470, [(0, WAINSCOT), (1, "#efdcc3")]))
        p.fill(rrect(-10, 392, 1300, 7, 0), C(RAIL))
        p.line([(-10, 392), (1290, 392)], C("#c9a989", 160), 0.6)
        p.line([(-10, 399), (1290, 399)], C("#d8bd9c", 140), 0.6)
        for x in range(30, 1280, 92):   # soft board joints, background-quiet
            p.line([(x, 404), (x, 466)], C("#e3cdb0", 150), 0.6)
    K.paint(d, f"{G}/Wall — wainscot and rail", wainscot)
    K.paint(d, f"{G}/Floor — base honey wood", lambda p: p.fill(
        rrect(-10, 480, 1300, 250, 0), lin(0, 480, 0, 720, [(0, FLOOR_BACK), (1, FLOOR_FRONT)])))

    def planks(p):
        rnd = random.Random(7)
        ys = [480, 497, 516, 538, 563, 592, 625, 662, 704, 750]
        for i in range(1, len(ys) - 1):
            p.line([(-10, ys[i]), (1290, ys[i])], C(FLOOR_SEAM, 150), 0.7)
        for i in range(len(ys) - 1):
            x = rnd.uniform(0, 160)
            while x < 1280:
                p.line([(x, ys[i] + 1), (x, ys[i + 1] - 1)], C(FLOOR_SEAM, 120), 0.6)
                x += rnd.uniform(220, 340)
            # faint grain streak per board
            gx = rnd.uniform(0, 1100)
            p.line([(gx, (ys[i] + ys[i + 1]) / 2), (gx + rnd.uniform(60, 140), (ys[i] + ys[i + 1]) / 2 + 0.5)],
                   C("#d9b994", 90), 0.6)
    K.paint(d, f"{G}/Floor — planks", planks)
    K.paint(d, f"{G}/Floor — contact shade at wall", lambda p: p.fill(
        rrect(-10, 480, 1300, 12, 0), C("#c7a27a", 110)))
    K.blur(d, f"{G}/Floor — contact shade at wall", 8)
    K.paint(d, f"{G}/Floor — morning sun patch", lambda p: p.fill(
        poly([(452 + WINDOW_DX, 516), (690 + WINDOW_DX, 516), (618 + WINDOW_DX, 612), (338 + WINDOW_DX, 612)]), C("#fff3d8", 120)))
    K.blur(d, f"{G}/Floor — morning sun patch", 26)

    def base(p):
        p.fill(rrect(-10, 468, 1300, 16, 0), lin(0, 468, 0, 484, [(0, "#efd5b1"), (1, "#dcbb92")]))
        p.line([(-10, 468), (1290, 468)], C("#b88f6b", 170), 0.8)
        p.line([(-10, 483.5), (1290, 483.5)], C("#b88f6b", 120), 0.6)
    K.paint(d, f"{G}/Baseboard", base)


# ---- window -----------------------------------------------------------------
GLASS = (572, 120, 176, 232)


def window(d):
    G = "Window — morning light source"
    E(d, G, "grouplayer")
    E(d, f"{G}/Garden view (calm, no line)")

    def view(p):
        x, y, w, h = GLASS
        p.p.setClipPath(rrect(x, y, w, h, 6))
        p.fill(rrect(x, y, w, h, 0), lin(0, y, 0, y + h, [(0, "#c9dfe8"), (0.7, "#e6efe8"), (1, "#eef0e2")]))
        p.fill(ellipse(690, 120, 90, 70), rad(735, 150, 60, [(0, C("#fff6dc", 230)), (1, C("#fff6dc", 0))]))
        for cx, cy, rx, ry in [(610, 168, 26, 9), (628, 162, 18, 9), (700, 196, 22, 7)]:
            p.fill(ellipse(cx - rx, cy - ry, rx * 2, ry * 2), C("#fbf6ec", 210))
        p.fill(smooth([(560, 330), (610, 296), (660, 306), (720, 286), (760, 300), (760, 360), (560, 360)]), C("#c8d8c2"))
        for cx, cy, r in [(590, 312, 20), (612, 300, 16), (726, 300, 18), (744, 312, 16)]:
            p.fill(ellipse(cx - r, cy - r, 2 * r, 2 * r), C("#b3c9ab"))
        p.fill(smooth([(560, 344), (640, 326), (700, 334), (760, 322), (760, 360), (560, 360)]), C("#b8cdb0"))
    K.paint(d, f"{G}/Garden view (calm, no line)", view)
    K.blur(d, f"{G}/Garden view (calm, no line)", 2)

    outer = rrect(556, 104, 208, 264, 16)
    inner = rrect(*GLASS, 6)
    frame = outer.subtracted(inner)
    frame = frame.united(rrect(657, 120, 6, 232, 2)).united(rrect(572, 231, 176, 6, 2))
    sill = rrect(542, 362, 236, 14, 5).united(rrect(546, 374, 228, 9, 4))
    obj(d, G, "Window frame and sill",
        base=lambda p: (p.fill(frame, C("#eed8b8")), p.fill(sill, C(WOOD))),
        shade=lambda p: (p.fill(rrect(540, 374, 240, 12, 0), C(WOOD_SHADE)),
                         p.fill(rrect(556, 104, 18, 264, 0), C("#dcc09c", 180))),
        light=lambda p: p.fill(rrect(740, 104, 30, 160, 0), C("#fbeedb", 220)),
        line=lambda p: (p.stroke(outer, WOOD_LINE, LW_FURNITURE), p.stroke(inner, C(WOOD_LINE, 200), 0.8),
                        p.stroke(rrect(542, 362, 236, 14, 5), WOOD_LINE, LW_FURNITURE)),
        shade_blur=6, light_blur=10)

    pot = rrect(588, 344, 26, 20, 6)
    leaves = [smooth([(601, 346), (590, 332), (588, 318), (597, 324), (603, 340)]),
              smooth([(601, 346), (606, 326), (614, 314), (616, 326), (606, 342)]),
              smooth([(601, 346), (598, 322), (602, 304), (608, 318), (604, 340)])]

    def plant_base(p):
        for lf in leaves:
            p.fill(lf, C(SAGE))
        p.fill(pot, C("#f2e5d5"))
    obj(d, G, "Sill plant", base=plant_base,
        shade=lambda p: (p.fill(rrect(586, 352, 14, 16, 0), C("#dccfc0")), p.fill(rrect(586, 326, 12, 24, 0), C(SAGE_DARK))),
        light=lambda p: p.fill(ellipse(606, 312, 12, 16), C(SAGE_LIGHT)),
        line=lambda p: ([p.stroke(lf, SAGE_LINE, LW_DECOR) for lf in leaves], p.stroke(pot, "#b39a86", LW_DECOR)),
        shade_blur=4, light_blur=4)

    left = smooth([(514, 90), (576, 90), (568, 210), (556, 300), (566, 380), (574, 424),
                   (540, 428), (510, 424), (520, 360), (522, 300), (514, 200)], t=0.4)
    right = smooth([(1320 - x, y) for x, y in [(514, 90), (576, 90), (568, 210), (556, 300), (566, 380),
                                               (574, 424), (540, 428), (510, 424), (520, 360), (522, 300),
                                               (514, 200)]], t=0.4)

    def folds(p):
        for x0 in (528, 546, 562):
            p.fill(smooth([(x0, 96), (x0 + 6, 96), (x0 + 2, 300), (x0 + 6, 420), (x0, 420), (x0 - 4, 300)], t=0.4), C(BLUSH_SHADE))
            p.fill(smooth([(1320 - x0, 96), (1314 - x0, 96), (1318 - x0, 300), (1314 - x0, 420), (1320 - x0, 420), (1324 - x0, 300)], t=0.4), C(BLUSH_SHADE))
        p.fill(ellipse(500, 280, 80, 30), C("#e2bba5", 160))  # tie-back shade
        p.fill(ellipse(740, 280, 80, 30), C("#e2bba5", 160))

    def tieback(p):
        p.fill(rrect(519, 294, 42, 7, 3), C("#d9a98f"))
        p.fill(rrect(759, 294, 42, 7, 3), C("#d9a98f"))
    obj(d, G, "Curtains — soft blush", base=lambda p: (p.fill(left, C(BLUSH)), p.fill(right, C(BLUSH))),
        shade=folds, light=lambda p: (p.fill(rrect(560, 90, 16, 330, 0), C("#fbede2")),
                                      p.fill(rrect(744, 90, 16, 330, 0), C("#fbede2"))),
        line=lambda p: (p.stroke(left, BLUSH_LINE, 0.9), p.stroke(right, BLUSH_LINE, 0.9), tieback(p)),
        shade_blur=7, light_blur=7)
    E(d, f"{G}/Curtain rod")
    K.paint(d, f"{G}/Curtain rod", lambda p: (
        p.fill(rrect(504, 86, 312, 6, 3), C("#d8b48d")),
        p.fill(ellipse(498, 83, 12, 12), C("#d8b48d")), p.fill(ellipse(810, 83, 12, 12), C("#d8b48d")),
        p.stroke(rrect(504, 86, 312, 6, 3), WOOD_LINE, 0.7)))


# ---- door -----------------------------------------------------------------
def door(d):
    G = "Door — interactable"
    E(d, G, "grouplayer")
    trim = rrect(992, 178, 176, 306, 22)
    leaf = rrect(1004, 190, 152, 292, 16)
    panels = [rrect(1048, 208, 92, 112, 10), rrect(1048, 342, 92, 120, 10)]
    obj(d, G, "Door trim", base=lambda p: p.fill(trim, C("#ead0ab")),
        shade=lambda p: p.fill(rrect(990, 178, 16, 306, 0), C("#d8b892")),
        line=lambda p: p.stroke(trim, WOOD_LINE, LW_FURNITURE), shade_blur=6)

    def panel_detail(p):
        for pn in panels:
            p.fill(pn, C("#e8cba3"))
            p.stroke(pn, C("#c9a37c", 200), 0.8)
    obj(d, G, "Door leaf", base=lambda p: p.fill(leaf, lin(1004, 190, 1156, 480, [(0, "#f2dbbb"), (1, "#e8c9a1")])),
        extra=[("raised panels (clipped)", panel_detail)],
        shade=lambda p: (p.fill(rrect(1000, 186, 22, 300, 0), C(WOOD_SHADE, 170)),
                         p.fill(rrect(1000, 456, 170, 30, 0), C(WOOD_SHADE, 140))),
        light=lambda p: p.fill(rrect(1130, 190, 26, 260, 0), C("#fbecd6", 200)),
        line=lambda p: (p.stroke(leaf, WOOD_LINE, LW_INTERACT),
                        p.fill(ellipse(1023, 336, 18, 18), C("#cf9f68")), p.fill(ellipse(1028, 339, 6, 5), C("#f3d7ae")),
                        p.stroke(ellipse(1023, 336, 18, 18), "#8f6544", 0.9)),
        shade_blur=10, light_blur=10)
    E(d, f"{G}/Door contact shade")
    K.paint(d, f"{G}/Door contact shade", lambda p: p.fill(rrect(996, 478, 168, 8, 4), C("#b48d66", 120)))
    K.blur(d, f"{G}/Door contact shade", 5)


# ---- decor -----------------------------------------------------------------
def decor(d):
    G = "Decor — restrained, low contrast"
    E(d, G, "grouplayer")
    frame1 = rrect(200, 150, 100, 78, 7)
    mat1 = rrect(207, 157, 86, 64, 4)

    def pic1(p):
        p.fill(frame1, C("#e8cba4"))
        p.fill(mat1, C("#dbe8ea"))
        p.p.setClipPath(mat1)
        p.fill(ellipse(262, 166, 18, 18), C("#f5dfae"))
        p.fill(smooth([(200, 214), (230, 196), (258, 204), (300, 190), (300, 230), (200, 230)]), C("#c3d4bd"))
        p.fill(smooth([(200, 222), (250, 208), (300, 214), (300, 230), (200, 230)]), C("#aec5a7"))
        p.p.setClipping(False)
    frame2 = ellipse(318, 192, 46, 46)

    def pic2(p):
        p.fill(frame2, C("#e8cba4"))
        p.fill(ellipse(323, 197, 36, 36), C("#f7e7da"))
        p.line([(341, 228), (341, 214)], SAGE_DARK, 1.0)
        for ang in range(5):
            import math
            a = ang * 2 * math.pi / 5 - math.pi / 2
            cx, cy = 341 + 5 * math.cos(a), 210 + 5 * math.sin(a)
            p.fill(ellipse(cx - 3.5, cy - 3.5, 7, 7), C("#edb293"))
        p.fill(ellipse(338.5, 207.5, 5, 5), C("#f3dcb1"))
    obj(d, G, "Wall pictures (no text)", base=lambda p: (pic1(p), pic2(p)),
        shade=lambda p: p.fill(rrect(196, 216, 170, 16, 0), C("#d8bc98", 150)),
        line=lambda p: (p.stroke(frame1, C(WOOD_LINE, 210), LW_DECOR), p.stroke(frame2, C(WOOD_LINE, 210), LW_DECOR)),
        shade_blur=5)

    # rug: an oval on the floor in front of the window (perspective-flattened)
    rug = ellipse(468, 592, 364, 78)
    rug_in = ellipse(486, 600, 328, 62)
    obj(d, G, "Rug — soft blush oval", base=lambda p: (p.fill(rug, C("#efd2bf")), p.fill(rug_in, C("#f6e2d3"))),
        shade=lambda p: p.fill(ellipse(460, 630, 380, 50), C("#e3bea8", 170)),
        light=lambda p: p.fill(ellipse(520, 596, 220, 30), C("#fbefe4", 200)),
        line=lambda p: (p.stroke(rug, BLUSH_LINE, LW_FURNITURE), p.stroke(rug_in, C("#e4b9a1", 200), 0.7)),
        shade_blur=14, light_blur=12)

    # low toy shelf under the window, against the wall
    K.OFFSET = WINDOW_DX
    y0, h, x0, x1 = 500, 68, 590, 734
    top = poly([P(x0, h, 0, y0), P(x1, h, 0, y0), P(x1, h, 26, y0), P(x0, h, 26, y0)])
    front = rrect(x0, y0 - h, x1 - x0, h, 6)
    cub = [rrect(600, 442, 58, 50, 5), rrect(666, 442, 58, 50, 5)]
    books = [(606, 452, 10, 40, SAGE), (617, 456, 9, 36, "#f1d9a8"), (627, 450, 11, 42, "#9fb4c7"),
             (639, 458, 9, 34, "#edb293")]

    def shelf_base(p):
        p.fill(top, C(WOOD_LIGHT))
        p.fill(front, C(WOOD_FRONT))
        for c in cub:
            p.fill(c, C("#cfa57b"))
        for bx, by, bw, bh, col in books:
            p.fill(rrect(bx, by, bw, bh, 2), C(col))
        p.fill(ellipse(684, 470, 22, 22), C("#d48658"))          # soft ball
        p.fill(rrect(706, 474, 14, 18, 3), C("#f3dcb1"))         # small block
    obj(d, G, "Toy shelf with books and ball", base=shelf_base,
        shade=lambda p: (p.fill(rrect(588, 440, 70, 56, 0), C("#a98360", 120)), p.fill(rrect(588, 440, 20, 70, 0), C(WOOD_SHADE, 160))),
        light=lambda p: p.fill(ellipse(688, 472, 8, 6), C("#f6c6a3")),
        line=lambda p: (p.stroke(front, WOOD_LINE, LW_FURNITURE), p.stroke(top, C(WOOD_LINE, 200), 0.8),
                        [p.stroke(c, C("#a77f5d", 200), 0.7) for c in cub],
                        [p.stroke(rrect(bx, by, bw, bh, 2), C("#8b7468", 160), 0.6) for bx, by, bw, bh, _ in books],
                        p.stroke(ellipse(684, 470, 22, 22), "#a3613d", 0.8)),
        shade_blur=8, light_blur=3)

    # teddy bear sitting on the shelf (a familiar concept-board prop)
    bear_parts = [ellipse(692, 396, 34, 30), ellipse(696, 372, 28, 26), ellipse(694, 368, 10, 10),
                  ellipse(716, 368, 10, 10), ellipse(688, 412, 14, 10), ellipse(712, 413, 14, 10)]

    def bear_base(p):
        for part in bear_parts:
            p.fill(part, C("#cf9f76"))
        p.fill(ellipse(704, 384, 12, 9), C("#f1dcc4"))
        p.fill(ellipse(697, 401, 20, 16), C("#e7c4a0"))
    obj(d, G, "Teddy bear", base=bear_base,
        shade=lambda p: p.fill(ellipse(684, 392, 22, 40), C("#a97b57", 170)),
        light=lambda p: p.fill(ellipse(712, 374, 10, 8), C("#ebc39b")),
        line=lambda p: ([p.stroke(part, "#8f664b", LW_DECOR) for part in bear_parts],
                        p.fill(ellipse(702, 380, 3, 3.4), C(COCOA)), p.fill(ellipse(712, 380, 3, 3.4), C(COCOA)),
                        p.fill(ellipse(708, 386, 3, 2), C(COCOA))),
        shade_blur=5, light_blur=4)
    E(d, f"{G}/Shelf contact shade")
    K.paint(d, f"{G}/Shelf contact shade", lambda p: p.fill(rrect(584, 494, 156, 10, 5), C("#a9835f", 110)))
    K.blur(d, f"{G}/Shelf contact shade", 6)
    K.OFFSET = 0

    # floor plant beside the door
    pot = rpoly([(1188, 470), (1232, 470), (1228, 520), (1192, 520)], 6)
    leaves = []
    for (bx, by, tx, ty, w) in [(1210, 470, 1170, 400, 20), (1210, 470, 1250, 396, 20), (1210, 470, 1206, 370, 18),
                                (1210, 470, 1182, 430, 16), (1210, 470, 1242, 432, 16), (1210, 470, 1226, 380, 16)]:
        mx, my = (bx + tx) / 2, (by + ty) / 2
        dx, dy = ty - by, bx - tx
        n = (dx * dx + dy * dy) ** 0.5
        ox, oy = dx / n * w / 2, dy / n * w / 2
        leaves.append(smooth([(bx, by), (mx + ox, my + oy), (tx, ty), (mx - ox, my - oy)], t=0.6))
    obj(d, G, "Floor plant", base=lambda p: ([p.fill(lf, C(SAGE)) for lf in leaves], p.fill(pot, C("#f2e5d5")),
                                             p.fill(rrect(1189, 482, 42, 8, 2), C("#cfdccb"))),
        shade=lambda p: (p.fill(rrect(1160, 380, 46, 100, 0), C(SAGE_DARK, 200)), p.fill(rrect(1186, 470, 18, 52, 0), C("#dccfc0"))),
        light=lambda p: p.fill(ellipse(1222, 380, 30, 50), C(SAGE_LIGHT, 220)),
        line=lambda p: ([p.stroke(lf, SAGE_LINE, LW_FURNITURE) for lf in leaves], p.stroke(pot, "#b39a86", LW_FURNITURE)),
        shade_blur=10, light_blur=10)
    E(d, f"{G}/Plant contact shade")
    K.paint(d, f"{G}/Plant contact shade", lambda p: p.fill(ellipse(1182, 514, 56, 12), C("#a9835f", 120)))
    K.blur(d, f"{G}/Plant contact shade", 6)


# ---- bed (interactable) --------------------------------------------------
Y0 = 578  # bed's front floor line


def arch_panel(x, h0, h_front, z1, h_back, rise, z0=0):
    """A board perpendicular to the picture plane at x: straight sides, arched top."""
    from PyQt5.QtGui import QPainterPath
    path = QPainterPath(QPointF(*P(x, h0, z0, Y0)))
    path.lineTo(QPointF(*P(x, h_front, z0, Y0)))
    zm1, zm2 = z0 + (z1 - z0) * 0.3, z0 + (z1 - z0) * 0.7
    path.cubicTo(QPointF(*P(x, h_front + rise, zm1, Y0)), QPointF(*P(x, h_back + rise, zm2, Y0)),
                 QPointF(*P(x, h_back, z1, Y0)))
    path.lineTo(QPointF(*P(x, h0, z1, Y0)))
    path.closeSubpath()
    return path


def bed(d, pillow_made, pillow_unmade):
    G = "Bed — interactable"
    E(d, G, "grouplayer")
    E(d, f"{G}/Bed contact shadow")
    K.paint(d, f"{G}/Bed contact shadow", lambda p: p.fill(
        poly([(80, 572), (470, 572), (490, 520), (170, 520)]), C("#a57d58", 120)))
    K.blur(d, f"{G}/Bed contact shadow", 12)

    # headboard inner face (seen from the room's centre) with an arched top
    hb = arch_panel(96, 50, 196, 98, 210, 30)  # below the rail is hidden
    hb_inset = arch_panel(96, 70, 176, 84, 186, 22, z0=14)
    back_post = None
    rail = rrect(96, Y0 - 60, 362, 46, 10)
    legs = [rrect(102, Y0 - 16, 14, 18, 4), rrect(438, Y0 - 16, 14, 18, 4)]
    obj(d, G, "Bed frame — headboard, rail and legs (honey wood)",
        base=lambda p: (p.fill(hb, C(WOOD)), p.fill(hb_inset, C("#efd2ab")),
                        p.fill(rail, C(WOOD_FRONT)), [p.fill(l, C(WOOD_SHADE)) for l in legs]),
        shade=lambda p: (p.fill(poly([P(96, 0, 0, Y0), P(96, 120, 0, Y0), P(96, 120, 98, Y0), P(96, 0, 98, Y0)]), C(WOOD_SHADE, 200)),
                         p.fill(rrect(96, Y0 - 30, 362, 18, 0), C(WOOD_SHADE, 170))),
        light=lambda p: (p.fill(ellipse(140, 322, 40, 30), C(WOOD_LIGHT)), p.fill(rrect(300, Y0 - 60, 160, 8, 0), C(WOOD_LIGHT, 200))),
        line=lambda p: (p.stroke(hb, WOOD_LINE, LW_INTERACT), p.stroke(hb_inset, C(WOOD_LINE, 150), 0.8),
                        p.stroke(rail, WOOD_LINE, LW_INTERACT),
                        [p.stroke(l, WOOD_LINE, 1.0) for l in legs]),
        shade_blur=16, light_blur=12)

    # mattress + fitted sheet: front face and top surface
    top = rpoly([P(100, 92, 0, Y0), P(456, 92, 0, Y0), P(456, 92, 96, Y0), P(100, 92, 96, Y0)], 10)
    front = rrect(100, Y0 - 92, 356, 34, 12)
    obj(d, G, "Mattress and sheet — cream",
        base=lambda p: (p.fill(front, C(SHEET_FRONT)), p.fill(top, C(SHEET))),
        shade=lambda p: (p.fill(rrect(96, Y0 - 76, 370, 22, 0), C(SHEET_SHADE)),
                         p.fill(ellipse(110, 440, 120, 60), C(SHEET_SHADE, 170))),
        light=lambda p: p.fill(ellipse(280, 440, 200, 34), C("#fffaf1")),
        line=lambda p: (p.stroke(top.united(front), CREAM_LINE, LW_INTERACT),
                        p.line([(106, Y0 - 92), (450, Y0 - 92)], C(CREAM_LINE, 160), 0.7)),
        shade_blur=12, light_blur=14)

    # placed pillow sprites (v2 candidate exports, scale 1: 128x96 units)
    for name, f, vis in [("Pillow — unmade (v2 candidate, placed)", pillow_unmade, False),
                         ("Pillow — made (v2 candidate, placed)", pillow_made, True)]:
        E(d, f"{G}/{name}", visible=vis)
        K.place_image(d, f"{G}/{name}", f, 170 - 64, 463 - 48, 128, 96)

    # duvet: lies on the top from x≈236 to the foot, drapes over the front
    duv_top = rpoly([P(236, 98, 2, Y0), P(458, 98, 2, Y0), P(458, 98, 96, Y0), P(236, 98, 96, Y0)], 12)
    drape = smooth([P(232, 98, 4, Y0), (300, Y0 - 101), (400, Y0 - 101), P(460, 98, 4, Y0), (462, Y0 - 52),
                    (430, Y0 - 40), (390, Y0 - 44), (350, Y0 - 38), (300, Y0 - 44), (262, Y0 - 38), (234, Y0 - 46)], t=0.45)
    cuff = rpoly([P(236, 99, 2, Y0), P(262, 99, 2, Y0), P(262, 99, 96, Y0), P(236, 99, 96, Y0)], 8)
    duvet_body = duv_top.united(drape)

    def duvet_base(p):
        p.fill(duv_top, C(DUVET))
        p.fill(drape, lin(0, Y0 - 98, 0, Y0 - 38, [(0, DUVET_FRONT), (1, "#86a6b6")]))

    def cuff_fn(p):
        p.fill(cuff, C("#dde8ec"))
        p.fill(rrect(226, Y0 - 100, 37, 70, 0), C("#d3e0e6"))
    obj(d, G, "Duvet — smooth, sky mist", base=duvet_base, extra=[("turned-down cuff (clipped)", cuff_fn)],
        shade=lambda p: (p.fill(rrect(228, Y0 - 70, 240, 40, 0), C(DUVET_SHADE, 200)),
                         p.fill(ellipse(220, 430, 60, 140), C(DUVET_SHADE, 170)),
                         [p.fill(smooth([(x, Y0 - 90), (x + 14, Y0 - 90), (x + 8, Y0 - 44), (x - 6, Y0 - 44)]), C(DUVET_SHADE, 90))
                          for x in (318, 398)]),
        light=lambda p: (p.fill(ellipse(330, 432, 150, 30), C(DUVET_LIGHT)), p.fill(rrect(240, 432, 18, 50, 0), C("#f0f5f6", 200))),
        line=lambda p: (p.stroke(duvet_body, DUVET_LINE, LW_INTERACT),
                        p.line([P(262, 99, 94, Y0), P(262, 99, 2, Y0), (263, Y0 - 40)], C(DUVET_LINE, 170), 0.8, t=0.2)),
        shade_blur=14, light_blur=14)

    # footboard outer face + front posts (closest to the viewer)
    fb = arch_panel(458, 0, 118, 98, 124, 14)
    fpost = rrect(446, Y0 - 132, 16, 134, 8)
    hpost = rrect(82, Y0 - 206, 18, 208, 9)
    obj(d, G, "Bed frame — footboard and front posts",
        base=lambda p: (p.fill(fb, C("#ddb68a")), p.fill(fpost, C(WOOD)), p.fill(hpost, C(WOOD))),
        shade=lambda p: (p.fill(rrect(440, Y0 - 60, 60, 70, 0), C(WOOD_SHADE, 190)), p.fill(rrect(78, Y0 - 120, 10, 130, 0), C(WOOD_SHADE, 200))),
        light=lambda p: (p.fill(ellipse(456, Y0 - 140, 30, 50), C(WOOD_LIGHT)), p.fill(ellipse(88, Y0 - 212, 14, 40), C(WOOD_LIGHT))),
        line=lambda p: (p.stroke(fb, WOOD_LINE, LW_INTERACT), p.stroke(fpost, WOOD_LINE, LW_INTERACT), p.stroke(hpost, WOOD_LINE, LW_INTERACT)),
        shade_blur=10, light_blur=8)


# ---- light, characters, annotations, texture ---------------------------
def light(d):
    G = "Light — morning window light"
    E(d, G, "grouplayer", passthrough=True)
    E(d, f"{G}/Light shafts (screen)", blend="screen", opacity=120)
    K.paint(d, f"{G}/Light shafts (screen)", lambda p: (
        p.fill(poly([(600, 124), (650, 124), (520, 612), (420, 612)]), C("#fff0d0", 90)),
        p.fill(poly([(668, 124), (744, 124), (640, 612), (540, 612)]), C("#fff0d0", 70))))
    K.blur(d, f"{G}/Light shafts (screen)", 30)


def characters(d, boy_png):
    G = "Characters — position study (not room art)"
    E(d, G, "grouplayer")
    E(d, f"{G}/Character contact shadows")
    K.paint(d, f"{G}/Character contact shadows", lambda p: (
        p.fill(ellipse(484, 622, 76, 16), C(COCOA, 70)), p.fill(ellipse(796, 552, 92, 18), C(COCOA, 60))))
    K.blur(d, f"{G}/Character contact shadows", 6)
    # Boy: existing refined cutout, unmodified, alpha bbox 330..864 x 28..1206 of 1254 px.
    s = 200.0 / (1206 - 28)
    E(d, f"{G}/Boy — existing candidate, unmodified (reference)")
    K.place_image(d, f"{G}/Boy — existing candidate, unmodified (reference)", boy_png,
                  520 - 597 * s, 630 - 1206 * s, 1254 * s, 1254 * s)
    E(d, f"{G}/Mom — PLACEHOLDER silhouette (not character art)")

    def mom(p):
        # 290 units, feet at MOM_SPOT (840, 560); ≈3.1 heads, facing the child
        sil = (ellipse(796, 270, 88, 94)                                             # head
               .united(smooth([(792, 300), (788, 360), (800, 404), (872, 404), (884, 360), (880, 300)]))  # hair
               .united(rpoly([(806, 362), (868, 362), (874, 452), (800, 452)], 14))  # blouse
               .united(rpoly([(800, 448), (874, 448), (886, 548), (848, 548), (838, 470), (828, 548), (792, 548)], 10))
               .united(ellipse(786, 542, 44, 18)).united(ellipse(842, 542, 46, 18))
               .united(rpoly([(800, 370), (788, 372), (778, 446), (792, 450)], 8)))
        p.fill(sil, C("#e9d3c6", 190))
        pen = QPen(C("#b07f6a"), 1.2, Qt.DashLine, Qt.RoundCap, Qt.RoundJoin)
        p.p.strokePath(sil, pen)
    K.paint(d, f"{G}/Mom — PLACEHOLDER silhouette (not character art)", mom)
    E(d, f"{G}/Labels")
    K.paint(d, f"{G}/Labels", lambda p: (
        text(p, 446, 656, "BOY — existing candidate, unmodified · 200 u", 8.5),
        text(p, 772, 584, "MOM — PLACEHOLDER (not art) · 290 u", 8.5)))


def annotations(d):
    from bedroom_layout_data import INTERACTABLES, FLOOR, CAMERA_TARGETS
    G = "Annotations — interaction areas and camera (guide)"
    E(d, G, "grouplayer", visible=False)
    E(d, f"{G}/Floor band (walkable)")
    K.paint(d, f"{G}/Floor band (walkable)", lambda p: (
        p.fill(rrect(*FLOOR, 0), C("#9eb49f", 50)), p.stroke(rrect(*FLOOR, 0), C("#667d67", 200), 0.8),
        text(p, FLOOR[0] + 4, FLOOR[1] + FLOOR[3] - 4, "FLOOR band 90–1190 × 500–680", 8, "#4f6650")))

    def inter(p):
        pen = QPen(C("#4f6a84"), 1.0, Qt.DashLine)
        for iid, (x, y, w, h), appr in INTERACTABLES:
            p.p.strokePath(rrect(x, y, w, h, 0), pen)
            text(p, x + 3, y + 10, iid, 8, "#4f6a84", True)
            if appr:
                p.fill(ellipse(appr[0] - 4, appr[1] - 4, 8, 8), C("#4f6a84"))
    E(d, f"{G}/Interactable bounds and approach points")
    K.paint(d, f"{G}/Interactable bounds and approach points", inter)

    def cams(p):
        pen = QPen(C("#94502d", 220), 1.0, Qt.DotLine)
        for cid, (x, y, w, h) in CAMERA_TARGETS:
            p.p.strokePath(rrect(x, y, w, h, 0), pen)
            text(p, x + 3, y + h - 3, "camera: " + cid, 7.5, "#94502d")
    E(d, f"{G}/Camera mustSee targets")
    K.paint(d, f"{G}/Camera mustSee targets", cams)


def texture(d):
    G = "Texture — painterly paper grain"
    E(d, G, "grouplayer", passthrough=True)
    for name, cell, op in [("Grain — broad mottling (soft light)", 16, 80), ("Grain — fine tooth (overlay)", 3, 40)]:
        E(d, f"{G}/{name}", blend="soft_light" if "soft" in name else "overlay", opacity=op)
        rnd = random.Random(11 + cell)
        w, h = (d.width() // cell) + 2, (d.height() // cell) + 2
        small = QImage(w, h, QImage.Format_ARGB32)
        for y in range(h):
            for x in range(w):
                v = int(128 + rnd.gauss(0, 30 if cell > 4 else 40))
                v = max(0, min(255, v))
                small.setPixel(x, y, (255 << 24) | (v << 16) | (v << 8) | v)

        def fn(p, small=small, cell=cell):
            p.p.setRenderHint(QPainter.SmoothPixmapTransform, True)
            p.p.drawImage(QRectF(-cell / 2, -cell / 2, small.width() * cell / 2, small.height() * cell / 2), small)
        K.paint(d, f"{G}/{name}", fn)


def run(d, pillow_made, pillow_unmade, boy_png, parts=("shell", "window", "door", "decor", "bed", "light", "texture", "chars", "notes")):
    if "shell" in parts: room_shell(d)
    if "window" in parts:
        K.OFFSET = WINDOW_DX
        window(d)
        K.OFFSET = 0
    if "door" in parts: door(d)
    if "decor" in parts: decor(d)
    if "bed" in parts: bed(d, pillow_made, pillow_unmade)
    if "light" in parts:
        K.OFFSET = WINDOW_DX
        light(d)
        K.OFFSET = 0
    if "texture" in parts: texture(d)
    if "chars" in parts: characters(d, boy_png)
    if "notes" in parts: annotations(d)
    K.refresh(d)
