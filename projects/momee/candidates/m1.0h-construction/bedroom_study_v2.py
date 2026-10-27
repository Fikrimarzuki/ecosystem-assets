# M1.0h bedroom composition study v2: a rendering refinement of v1 (M1.0g).
# Same room layout, window position, door, character zones and every
# bedroom-layout.ts coordinate. 2560x1440 RGBA/8 at 2 px per world unit.
import math

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QFont, QImage, QPainterPath, QPen

import kpaint2 as K
from kpaint2 import C, P, rpoly, smooth, rrect, ellipse, poly, lin, rad

E = K.ensure

# ---- palette: v1 families, slightly richer saturation and value range --------
WALL, WALL_TOP, WALL_LOW = "#f8e6cf", "#eed2b2", "#fbefdf"
WAINSCOT, WAINSCOT_LOW, RAIL = "#f3dcc1", "#eacdab", "#e2bf93"
WOOD, WOOD_FRONT, WOOD_SHADE, WOOD_DEEP, WOOD_LIGHT = "#e6b983", "#dba873", "#bf8a5b", "#a5714a", "#f8dcad"
WOOD_LINE = "#8e5c38"
FLOOR_BACK, FLOOR_FRONT, FLOOR_ALT, FLOOR_SEAM = "#efd1a3", "#dcb07c", "#e5c08d", "#c4955f"
SHEET, SHEET_FRONT, SHEET_SHADE, CREAM_LINE = "#fcf3e4", "#f0e2cf", "#c3cbe0", "#9c7d6c"
DUVET, DUVET_LIGHT, DUVET_FRONT, DUVET_SHADE, DUVET_DEEP, DUVET_LINE = (
    "#8db3cc", "#bcd6e5", "#7ea4c0", "#5c80a2", "#4b6d90", "#46617e")
SAGE, SAGE_DARK, SAGE_LIGHT, SAGE_LINE = "#92b393", "#6c9070", "#bad3b5", "#53715a"
BLUSH, BLUSH_SHADE, BLUSH_LIGHT, BLUSH_LINE = "#f5d4bf", "#e6b59b", "#fde9dc", "#bd8a70"
COCOA, AO = "#59463d", "#6e4a30"

# Line weights in world units (M1.0h: lighter than M1.0g, closer to the Boy)
LW_INTERACT, LW_FURNITURE, LW_DECOR = 1.0, 0.85, 0.6

WINDOW_DX = -60
GLASS = (512, 120, 176, 232)                    # after the shift
WIN_C = (600.0, 236.0)                          # window centre: the room's light source
Y0 = 578                                        # bed's front floor line

LEFT_OF_WINDOW, RIGHT_OF_WINDOW = (-0.3, 0.35), (0.3, 0.35)   # shadow-side line offsets


def obj(d, group, label, base, shade=None, light=None, line=None, extra=(),
        shade_blur=12, light_blur=10, tex=None):
    """Material stack: base, clipped extras, soft shade, light, optional texture, line."""
    g = f"{group}/{label}"
    E(d, g, "grouplayer")
    E(d, f"{g}/{label} — base")
    K.paint(d, f"{g}/{label} — base", base)
    for name, fn, blur in extra:
        E(d, f"{g}/{label} — {name}", inherit=True)
        K.paint(d, f"{g}/{label} — {name}", fn)
        if blur:
            K.blur(d, f"{g}/{label} — {name}", blur)
    if shade:
        E(d, f"{g}/{label} — soft shade (clipped)", inherit=True)
        K.paint(d, f"{g}/{label} — soft shade (clipped)", shade)
        if shade_blur:
            K.blur(d, f"{g}/{label} — soft shade (clipped)", shade_blur)
    if light:
        E(d, f"{g}/{label} — window light (clipped)", inherit=True)
        K.paint(d, f"{g}/{label} — window light (clipped)", light)
        if light_blur:
            K.blur(d, f"{g}/{label} — window light (clipped)", light_blur)
    if tex:
        name, fn, blend, op = tex
        E(d, f"{g}/{label} — {name} (clipped)", inherit=True, blend=blend, opacity=op)
        K.paint(d, f"{g}/{label} — {name} (clipped)", fn)
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


def wood_grain(p, path, rect, seed, angle=0.0, n=40, length=60):
    K.streaks(p, path, rect, C("#9a6a42", 50), n, length, angle, seed, 0.45)
    K.streaks(p, path, rect, C("#fbe2b8", 55), n // 2, length * 0.7, angle, seed + 1, 0.4)


def weave(p, path, seed=31):
    K.texture(p, path, K.noise_tile(seed=seed, size=192, sigma=13), 0.5)


# ---- room shell ----------------------------------------------------------------
def floor_patch_quads():
    """Sunlight through the four window panes, projected onto the floor (the sun
    is high and to the right, so the patch falls in front of and left of the window)."""
    kx, kz = 0.45, 0.55

    def F(x, y):
        h = 480 - y
        return (x - kx * h, 480 + kz * h)
    gx, gy, gw, gh = GLASS
    panes = [(gx, gy, gx + gw / 2 - 3, gy + gh / 2 - 3), (gx + gw / 2 + 3, gy, gx + gw, gy + gh / 2 - 3),
             (gx, gy + gh / 2 + 3, gx + gw / 2 - 3, gy + gh), (gx + gw / 2 + 3, gy + gh / 2 + 3, gx + gw, gy + gh)]
    return [poly([F(x0, y1), F(x1, y1), F(x1, y0), F(x0, y0)]) for x0, y0, x1, y1 in panes]


def room_shell(d):
    G = "Room shell"
    E(d, G, "grouplayer")
    for n in ["Wall — base cream", "Wall — window glow and corner falloff", "Wall — wainscot, rail and joints",
              "Floor — base honey wood", "Floor — plank tones", "Floor — seams and grain (selective texture)",
              "Floor — ambient occlusion at the wall", "Floor — sunlight through the panes", "Baseboard"]:
        E(d, f"{G}/{n}")
    K.paint(d, f"{G}/Wall — base cream", lambda p: p.fill(
        rrect(-10, -10, 1300, 500, 0), lin(0, 0, 0, 480, [(0, WALL_TOP), (0.5, WALL), (1, WALL_LOW)])))

    def glow(p):
        wall = rrect(-10, -10, 1300, 500, 0)
        p.fill(wall, rad(WIN_C[0], WIN_C[1], 560, [(0, C("#fff3da", 220)), (0.5, C("#fff3da", 90)), (1, C("#fff3da", 0))]))
        p.fill(wall, rad(-60, -60, 420, [(0, C("#d9b48d", 150)), (1, C("#d9b48d", 0))]))
        p.fill(wall, rad(1340, -60, 460, [(0, C("#d9b48d", 150)), (1, C("#d9b48d", 0))]))
    K.paint(d, f"{G}/Wall — window glow and corner falloff", glow)

    def wainscot(p):
        p.fill(rrect(-10, 398, 1300, 72, 0), lin(0, 398, 0, 470, [(0, WAINSCOT), (1, WAINSCOT_LOW)]))
        p.fill(rrect(-10, 391, 1300, 8, 0), lin(0, 391, 0, 399, [(0, "#efd2a9"), (1, RAIL)]))
        p.line([(-10, 391), (1290, 391)], C("#b9895d", 170), 0.6)
        p.line([(-10, 399), (1290, 399)], C("#c79c6f", 150), 0.6)
        p.line([(-10, 400.5), (1290, 400.5)], C("#c79c6f", 70), 1.2)       # rail shadow on boards
        for x in range(30, 1280, 92):
            lit = x < WIN_C[0]
            p.line([(x, 404), (x, 466)], C("#d9b892", 170), 0.6)
            p.line([(x + (0.8 if lit else -0.8), 404), (x + (0.8 if lit else -0.8), 466)], C("#fbebd6", 150), 0.5)
    K.paint(d, f"{G}/Wall — wainscot, rail and joints", wainscot)
    K.paint(d, f"{G}/Floor — base honey wood", lambda p: p.fill(
        rrect(-10, 480, 1300, 250, 0), lin(0, 480, 0, 720, [(0, FLOOR_BACK), (1, FLOOR_FRONT)])))
    ys = [480, 497, 516, 538, 563, 592, 625, 662, 704, 750]

    def tones(p):
        for i in range(len(ys) - 1):
            if i % 2:
                p.fill(rrect(-10, ys[i], 1300, ys[i + 1] - ys[i], 0), C(FLOOR_ALT, 70))
    K.paint(d, f"{G}/Floor — plank tones", tones)

    def planks(p):
        import random
        rnd = random.Random(7)
        for i in range(1, len(ys) - 1):
            p.line([(-10, ys[i]), (1290, ys[i])], C(FLOOR_SEAM, 170), 0.7)
            p.line([(-10, ys[i] + 0.9), (1290, ys[i] + 0.9)], C("#f8e0b8", 120), 0.5)
        floor = rrect(-10, 480, 1300, 250, 0)
        for i in range(len(ys) - 1):
            x = rnd.uniform(0, 160)
            while x < 1280:
                p.line([(x, ys[i] + 1), (x, ys[i + 1] - 1)], C(FLOOR_SEAM, 140), 0.6)
                x += rnd.uniform(220, 340)
        K.streaks(p, floor, (-10, 482, 1300, 240), C("#b98a58", 60), 140, 90, 0, 41, 0.45)
        K.streaks(p, floor, (-10, 482, 1300, 240), C("#fbe5c0", 70), 80, 70, 0, 43, 0.4)
    K.paint(d, f"{G}/Floor — seams and grain (selective texture)", planks)
    K.paint(d, f"{G}/Floor — ambient occlusion at the wall", lambda p: p.fill(
        rrect(-10, 480, 1300, 14, 0), C(AO, 120)))
    K.blur(d, f"{G}/Floor — ambient occlusion at the wall", 8)

    def sun(p):
        for q in floor_patch_quads():
            p.fill(q, C("#fff1cf", 165))
    K.paint(d, f"{G}/Floor — sunlight through the panes", sun)
    K.blur(d, f"{G}/Floor — sunlight through the panes", 7)

    def base(p):
        p.fill(rrect(-10, 467, 1300, 17, 0), lin(0, 467, 0, 484, [(0, "#f1d3a8"), (1, "#d3a978")]))
        p.line([(-10, 467), (1290, 467)], C("#9f6f47", 190), 0.7)
        p.line([(-10, 468.2), (1290, 468.2)], C("#fbe6c4", 170), 0.5)
        p.line([(-10, 483.6), (1290, 483.6)], C("#9f6f47", 140), 0.6)
    K.paint(d, f"{G}/Baseboard", base)


# ---- window ------------------------------------------------------------------------
def window(d):
    G = "Window — morning light source"
    E(d, G, "grouplayer")
    gx, gy, gw, gh = GLASS
    E(d, f"{G}/Garden view (calm, no line)")

    def view(p):
        p.p.setClipPath(rrect(gx, gy, gw, gh, 6))
        p.fill(rrect(gx, gy, gw, gh, 0), lin(0, gy, 0, gy + gh, [(0, "#b7d6ea"), (0.65, "#dcecee"), (1, "#eef0dc")]))
        p.fill(ellipse(gx + 110, gy - 10, 110, 90), rad(gx + 160, gy + 26, 80, [(0, C("#fff6d6", 245)), (1, C("#fff6d6", 0))]))
        for cx, cy, rx, ry in [(gx + 40, 166, 28, 9), (gx + 58, 160, 18, 9), (gx + 128, 196, 22, 7)]:
            p.fill(ellipse(cx - rx, cy - ry, rx * 2, ry * 2), C("#fdfaf2", 225))
        p.fill(smooth([(gx - 12, 330), (gx + 38, 296), (gx + 88, 306), (gx + 148, 286), (gx + 188, 300), (gx + 188, 360), (gx - 12, 360)]), C("#b9d2ad"))
        for cx, cy, r in [(gx + 18, 312, 20), (gx + 40, 300, 16), (gx + 154, 300, 18), (gx + 172, 312, 16)]:
            p.fill(ellipse(cx - r, cy - r, 2 * r, 2 * r), C("#9ec293"))
            p.fill(ellipse(cx - r * 0.5, cy - r * 0.9, r, r * 0.8), C("#b8d6a9"))
        p.fill(smooth([(gx - 12, 344), (gx + 68, 326), (gx + 128, 334), (gx + 188, 322), (gx + 188, 360), (gx - 12, 360)]), C("#a8c99b"))
    K.paint(d, f"{G}/Garden view (calm, no line)", view)
    K.blur(d, f"{G}/Garden view (calm, no line)", 2)

    outer = rrect(gx - 16, gy - 16, gw + 32, gh + 32, 16)
    inner = rrect(gx, gy, gw, gh, 6)
    frame = outer.subtracted(inner)
    mull = rrect(gx + gw / 2 - 3, gy, 6, gh, 2).united(rrect(gx, gy + gh / 2 - 3, gw, 6, 2))
    sill = rrect(gx - 30, 362, gw + 60, 14, 5)
    sill_front = rrect(gx - 26, 374, gw + 52, 10, 4)
    obj(d, G, "Window frame, reveal and sill",
        base=lambda p: (p.fill(frame.united(mull), C("#f0d6b0")), p.fill(sill, C(WOOD_LIGHT)), p.fill(sill_front, C(WOOD_FRONT))),
        extra=[("reveal depth (clipped)", lambda p: (p.stroke(inner, C("#d2a87c", 230), 5),), 2)],
        shade=lambda p: (p.fill(sill_front, C(WOOD_SHADE)), p.fill(rrect(gx - 16, gy - 16, 16, gh + 32, 0), C("#dcb98f", 170))),
        light=lambda p: (p.fill(rrect(gx + gw, gy - 16, 16, gh + 32, 0), C("#fff0d8", 210)),
                         p.fill(rrect(gx - 30, 362, gw + 60, 4, 0), C("#fff1d6", 220))),
        line=lambda p: (K.wline(p, outer, WOOD_LINE, LW_FURNITURE, LEFT_OF_WINDOW), p.stroke(inner, C(WOOD_LINE, 190), 0.6),
                        p.stroke(mull, C(WOOD_LINE, 150), 0.5), K.wline(p, sill.united(sill_front), WOOD_LINE, LW_FURNITURE)),
        shade_blur=6, light_blur=6)

    pot = rrect(gx + 16, 344, 26, 20, 6)
    leaves = [smooth([(gx + 29, 346), (gx + 18, 332), (gx + 16, 318), (gx + 25, 324), (gx + 31, 340)]),
              smooth([(gx + 29, 346), (gx + 34, 326), (gx + 42, 314), (gx + 44, 326), (gx + 34, 342)]),
              smooth([(gx + 29, 346), (gx + 26, 322), (gx + 30, 304), (gx + 36, 318), (gx + 32, 340)])]
    obj(d, G, "Sill plant", base=lambda p: ([p.fill(lf, C(SAGE)) for lf in leaves], p.fill(pot, C("#f4e6d4"))),
        shade=lambda p: (p.fill(rrect(gx + 14, 352, 12, 16, 0), C("#d8c4ad")), p.fill(rrect(gx + 12, 320, 14, 30, 0), C(SAGE_DARK))),
        light=lambda p: (p.fill(ellipse(gx + 32, 308, 14, 22), C(SAGE_LIGHT)), p.fill(rrect(gx + 34, 346, 8, 16, 0), C("#fff7ea"))),
        line=lambda p: ([p.stroke(lf, SAGE_LINE, LW_DECOR) for lf in leaves], p.stroke(pot, "#a98b74", LW_DECOR)),
        shade_blur=4, light_blur=4)

    L = [(454, 90), (516, 90), (508, 210), (496, 300), (506, 380), (514, 424), (480, 428), (450, 424),
         (460, 360), (462, 300), (454, 200)]
    left = smooth(L, t=0.4)
    right = smooth([(1200 - x, y) for x, y in L], t=0.4)     # mirrored about the window centre (x 600)

    def folds(p):
        for x0 in (468, 486, 502):
            for xs in (x0, 1200 - x0 - 6):
                p.fill(smooth([(xs, 96), (xs + 6, 96), (xs + 2, 300), (xs + 7, 420), (xs, 420), (xs - 4, 300)], t=0.4), C(BLUSH_SHADE))
        p.fill(ellipse(440, 280, 80, 30), C("#d9a68b", 170))
        p.fill(ellipse(680, 280, 80, 30), C("#d9a68b", 170))

    def glow_through(p):   # sunlight through the inner edges of the curtains
        p.fill(rrect(500, 90, 18, 336, 0), C(BLUSH_LIGHT, 240))
        p.fill(rrect(682, 90, 18, 336, 0), C(BLUSH_LIGHT, 240))

    def ties(p):
        p.fill(rrect(459, 294, 42, 7, 3), C("#d29a7c"))
        p.fill(rrect(699, 294, 42, 7, 3), C("#d29a7c"))
    obj(d, G, "Curtains — soft blush", base=lambda p: (p.fill(left, C(BLUSH)), p.fill(right, C(BLUSH))),
        shade=folds, light=glow_through,
        tex=("fabric weave", lambda p: (weave(p, left, 33), weave(p, right, 34)), "overlay", 34),
        line=lambda p: (K.wline(p, left, BLUSH_LINE, 0.8, LEFT_OF_WINDOW), K.wline(p, right, BLUSH_LINE, 0.8, RIGHT_OF_WINDOW), ties(p)),
        shade_blur=7, light_blur=8)
    E(d, f"{G}/Curtain rod")
    K.paint(d, f"{G}/Curtain rod", lambda p: (
        p.fill(rrect(444, 86, 312, 6, 3), lin(0, 86, 0, 92, [(0, "#efcf9f"), (1, "#c79466")])),
        p.fill(ellipse(438, 83, 12, 12), C("#d6a676")), p.fill(ellipse(750, 83, 12, 12), C("#d6a676")),
        p.stroke(rrect(444, 86, 312, 6, 3), WOOD_LINE, 0.6)))


# ---- door with depth ------------------------------------------------------------------
def door(d):
    G = "Door — interactable"
    E(d, G, "grouplayer")
    E(d, f"{G}/Trim cast shadow on wall")
    K.paint(d, f"{G}/Trim cast shadow on wall", lambda p: p.fill(
        rpoly([(1166, 186), (1178, 196), (1178, 484), (1166, 484)], 4), C(AO, 90)))
    K.blur(d, f"{G}/Trim cast shadow on wall", 8)
    trim = rrect(992, 178, 176, 306, 22)
    opening = rrect(1004, 190, 152, 294, 16)
    leaf = rrect(1004, 192, 144, 292, 15)          # recessed: the right jamb shows
    panels = [rrect(1040, 210, 92, 110, 10), rrect(1040, 342, 92, 118, 10)]
    obj(d, G, "Door trim and jamb",
        base=lambda p: (p.fill(trim, C("#ebca9c")), p.fill(opening, C("#c9996a"))),
        extra=[("lit right jamb (clipped)", lambda p: p.fill(rrect(1146, 192, 12, 292, 0), lin(1146, 0, 1158, 0, [(0, "#eac08c"), (1, "#f6d8ab")])), 0)],
        shade=lambda p: (p.fill(rrect(1150, 178, 20, 306, 0), C(WOOD_SHADE, 200)),),
        light=lambda p: (p.fill(rrect(992, 178, 12, 306, 0), C("#fbe4bf", 230)), p.fill(rrect(992, 178, 176, 8, 0), C("#fbe4bf", 160))),
        line=lambda p: (K.wline(p, trim, WOOD_LINE, LW_FURNITURE, RIGHT_OF_WINDOW), p.stroke(opening, C(WOOD_LINE, 170), 0.6)),
        shade_blur=6, light_blur=5)

    def panel_bevels(p):
        for pn in panels:
            p.fill(pn, C("#efcd9e"))
            p.p.save()
            p.p.translate(-0.9, -0.9)
            p.stroke(pn, C("#fbe6c4", 230), 1.1)        # lit upper-left bevel
            p.p.restore()
            p.p.save()
            p.p.translate(0.9, 0.9)
            p.stroke(pn, C("#b8875a", 200), 1.0)        # shaded lower-right bevel
            p.p.restore()
    obj(d, G, "Door leaf (recessed)",
        base=lambda p: p.fill(leaf, lin(1004, 192, 1148, 484, [(0, "#f2d3a6"), (1, "#e2b583")])),
        extra=[("raised panels with bevels (clipped)", panel_bevels, 0)],
        shade=lambda p: (p.fill(rrect(1000, 188, 152, 12, 0), C(AO, 120)), p.fill(rrect(1000, 188, 10, 300, 0), C(AO, 100)),
                         p.fill(rrect(1000, 452, 152, 34, 0), C(WOOD_SHADE, 140))),
        light=lambda p: p.fill(rrect(1004, 192, 30, 292, 0), C("#fde7c4", 150)),
        tex=("wood grain", lambda p: wood_grain(p, leaf, (1004, 192, 144, 292), 61, 90, 60, 70), "normal", 255),
        line=lambda p: (K.wline(p, leaf, WOOD_LINE, LW_INTERACT, RIGHT_OF_WINDOW),
                        p.fill(ellipse(1022, 341, 6, 4), C(AO, 90)),
                        p.fill(ellipse(1023, 336, 18, 18), rad(1029, 341, 11, [(0, "#f2cf98"), (1, "#bf8d55")])),
                        p.fill(ellipse(1026, 339, 6, 5), C("#fff0d4")),
                        p.stroke(ellipse(1023, 336, 18, 18), "#7f5534", 0.8)),
        shade_blur=7, light_blur=14)
    E(d, f"{G}/Door contact shadow")
    K.paint(d, f"{G}/Door contact shadow", lambda p: p.fill(rrect(994, 478, 172, 10, 5), C(AO, 140)))
    K.blur(d, f"{G}/Door contact shadow", 5)


# ---- decor ----------------------------------------------------------------------------
def decor(d):
    G = "Decor — restrained"
    E(d, G, "grouplayer")
    frame1, mat1 = rrect(200, 150, 100, 78, 7), rrect(207, 157, 86, 64, 4)
    frame2 = ellipse(318, 192, 46, 46)
    E(d, f"{G}/Picture shadows on wall")
    K.paint(d, f"{G}/Picture shadows on wall", lambda p: (
        p.fill(rrect(197, 154, 100, 78, 7), C(AO, 80)), p.fill(ellipse(315, 196, 46, 46), C(AO, 80))))
    K.blur(d, f"{G}/Picture shadows on wall", 5)

    def pics(p):
        p.fill(frame1, C("#e7c08f"))
        p.fill(mat1, C("#d5e7ee"))
        p.p.save()
        p.p.setClipPath(mat1)
        p.fill(ellipse(262, 166, 18, 18), C("#f6dca2"))
        p.fill(smooth([(200, 214), (230, 196), (258, 204), (300, 190), (300, 230), (200, 230)]), C("#b9d1b1"))
        p.fill(smooth([(200, 222), (250, 208), (300, 214), (300, 230), (200, 230)]), C("#a1c197"))
        p.p.restore()
        p.fill(frame2, C("#e7c08f"))
        p.fill(ellipse(323, 197, 36, 36), C("#f8e4d6"))
        p.line([(341, 228), (341, 214)], SAGE_DARK, 1.0)
        for i in range(5):
            a = i * 2 * math.pi / 5 - math.pi / 2
            p.fill(ellipse(341 + 5 * math.cos(a) - 3.5, 210 + 5 * math.sin(a) - 3.5, 7, 7), C("#e9a585"))
        p.fill(ellipse(338.5, 207.5, 5, 5), C("#f3d6a0"))
    obj(d, G, "Wall pictures (no text)", base=pics,
        light=lambda p: (p.fill(rrect(292, 150, 8, 78, 0), C("#fbe6c4", 200)), p.fill(ellipse(352, 196, 12, 36), C("#fbe6c4", 200))),
        line=lambda p: (p.stroke(frame1, C(WOOD_LINE, 220), LW_DECOR), p.stroke(frame2, C(WOOD_LINE, 220), LW_DECOR),
                        p.stroke(mat1, C(WOOD_LINE, 120), 0.4)),
        light_blur=3)

    rug, rug_in = ellipse(468, 592, 364, 78), ellipse(486, 600, 328, 62)
    obj(d, G, "Rug — soft blush oval", base=lambda p: (p.fill(rug, C("#efc6ad")), p.fill(rug_in, C("#f7dccb"))),
        shade=lambda p: p.fill(ellipse(456, 632, 380, 48), C("#d9a88d", 170)),
        light=lambda p: p.fill(ellipse(480, 596, 240, 34), C("#fff0e2", 220)),
        tex=("fabric weave", lambda p: weave(p, rug, 35), "overlay", 44),
        line=lambda p: (K.wline(p, rug, BLUSH_LINE, LW_FURNITURE), p.stroke(rug_in, C("#dca88c", 200), 0.6)),
        shade_blur=14, light_blur=12)

    # low toy shelf under the window
    K.OFFSET = WINDOW_DX
    y0, h, x0, x1 = 500, 68, 590, 734
    top = poly([P(x0, h, 0, y0), P(x1, h, 0, y0), P(x1, h, 26, y0), P(x0, h, 26, y0)])
    front = rrect(x0, y0 - h, x1 - x0, h, 6)
    cub = [rrect(600, 442, 58, 50, 5), rrect(666, 442, 58, 50, 5)]
    books = [(606, 452, 10, 40, SAGE), (617, 456, 9, 36, "#f2d49c"), (627, 450, 11, 42, "#93aec7"), (639, 458, 9, 34, "#e9a585")]
    E(d, f"{G}/Shelf contact shadow")
    K.paint(d, f"{G}/Shelf contact shadow", lambda p: p.fill(rrect(582, 494, 160, 12, 6), C(AO, 150)))
    K.blur(d, f"{G}/Shelf contact shadow", 6)

    def shelf_base(p):
        p.fill(top, C(WOOD_LIGHT))
        p.fill(front, lin(x0, 0, x1, 0, [(0, WOOD_SHADE), (0.3, WOOD_FRONT), (1, WOOD_FRONT)]))
        for c in cub:
            p.fill(c, C("#b98657"))
        for bx, by, bw, bh, col in books:
            p.fill(rrect(bx, by, bw, bh, 2), C(col))
        p.fill(ellipse(684, 470, 22, 22), rad(690, 476, 14, [(0, "#eaa173"), (1, "#c96f43")]))
        p.fill(rrect(706, 474, 14, 18, 3), C("#f2d49c"))
    obj(d, G, "Toy shelf with books and ball", base=shelf_base,
        shade=lambda p: ([p.fill(rrect(c_x, 442, 58, 12, 0), C(AO, 120)) for c_x in (600, 666)],
                         [p.fill(rrect(c_x, 442, 8, 50, 0), C(AO, 90)) for c_x in (600, 666)]),
        light=lambda p: (p.fill(rrect(x0, y0 - h - 14, x1 - x0, 16, 0), C("#fff0d0", 200)), p.fill(ellipse(688, 472, 8, 6), C("#ffd9bb"))),
        tex=("wood grain", lambda p: wood_grain(p, front, (x0, y0 - h, x1 - x0, h), 71, 0, 26, 50), "normal", 255),
        line=lambda p: (K.wline(p, front, WOOD_LINE, LW_FURNITURE), p.stroke(top, C(WOOD_LINE, 200), 0.6),
                        [p.stroke(c, C("#8e5c38", 190), 0.6) for c in cub],
                        [p.stroke(rrect(bx, by, bw, bh, 2), C("#7d6458", 170), 0.5) for bx, by, bw, bh, _ in books],
                        p.stroke(ellipse(684, 470, 22, 22), "#94502d", 0.7)),
        shade_blur=4, light_blur=4)
    bear = [ellipse(692, 396, 34, 30), ellipse(696, 372, 28, 26), ellipse(694, 368, 10, 10),
            ellipse(716, 368, 10, 10), ellipse(688, 412, 14, 10), ellipse(712, 413, 14, 10)]
    E(d, f"{G}/Teddy contact shadow")
    K.paint(d, f"{G}/Teddy contact shadow", lambda p: p.fill(ellipse(688, 418, 44, 8), C(AO, 140)))
    K.blur(d, f"{G}/Teddy contact shadow", 3)

    def bear_base(p):
        for part in bear:
            p.fill(part, C("#cf9a6c"))
        p.fill(ellipse(704, 384, 12, 9), C("#f2dcc2"))
        p.fill(ellipse(697, 401, 20, 16), C("#e8c29b"))
    obj(d, G, "Teddy bear", base=bear_base,
        shade=lambda p: p.fill(ellipse(686, 390, 22, 42), C("#a2704b", 190)),
        light=lambda p: (p.fill(ellipse(704, 372, 14, 10), C("#efc79c")), p.fill(ellipse(708, 398, 12, 10), C("#efc79c"))),
        line=lambda p: ([p.stroke(part, "#87593a", LW_DECOR) for part in bear],
                        p.fill(ellipse(702, 380, 3, 3.4), C(COCOA)), p.fill(ellipse(712, 380, 3, 3.4), C(COCOA)),
                        p.fill(ellipse(702.6, 380.4, 1, 1), C("#fff6ea")), p.fill(ellipse(712.6, 380.4, 1, 1), C("#fff6ea")),
                        p.fill(ellipse(708, 386, 3, 2), C(COCOA))),
        shade_blur=5, light_blur=4)
    K.OFFSET = 0

    # floor plant beside the door, lit from the window side (left)
    pot = rpoly([(1188, 470), (1232, 470), (1228, 520), (1192, 520)], 6)
    leaves, ribs = [], []
    for (bx, by, tx, ty, w) in [(1210, 470, 1170, 400, 20), (1210, 470, 1250, 396, 20), (1210, 470, 1206, 370, 18),
                                (1210, 470, 1182, 430, 16), (1210, 470, 1242, 432, 16), (1210, 470, 1226, 380, 16)]:
        mx, my = (bx + tx) / 2, (by + ty) / 2
        dx, dy = ty - by, bx - tx
        n = (dx * dx + dy * dy) ** 0.5
        ox, oy = dx / n * w / 2, dy / n * w / 2
        leaves.append(smooth([(bx, by), (mx + ox, my + oy), (tx, ty), (mx - ox, my - oy)], t=0.6))
        ribs.append([(bx, by), ((bx + tx) / 2, (by + ty) / 2), (tx, ty)])
    E(d, f"{G}/Plant contact shadow")
    K.paint(d, f"{G}/Plant contact shadow", lambda p: p.fill(ellipse(1182, 512, 60, 14), C(AO, 150)))
    K.blur(d, f"{G}/Plant contact shadow", 5)
    obj(d, G, "Floor plant", base=lambda p: ([p.fill(lf, C(SAGE)) for lf in leaves], p.fill(pot, C("#f4e6d4")),
                                             p.fill(rrect(1189, 482, 42, 8, 2), C("#c4d8c0"))),
        shade=lambda p: (p.fill(rrect(1214, 370, 50, 110, 0), C(SAGE_DARK, 210)), p.fill(rrect(1214, 470, 20, 52, 0), C("#d6c1a8"))),
        light=lambda p: (p.fill(ellipse(1162, 380, 40, 60), C(SAGE_LIGHT, 230)), p.fill(rrect(1188, 470, 8, 50, 0), C("#fff8ec"))),
        line=lambda p: ([p.stroke(lf, SAGE_LINE, LW_FURNITURE) for lf in leaves], [p.line(r, C(SAGE_LINE, 140), 0.45) for r in ribs],
                        K.wline(p, pot, "#a98b74", LW_FURNITURE, RIGHT_OF_WINDOW)),
        shade_blur=10, light_blur=10)


# ---- bed --------------------------------------------------------------------------------
def arch_panel(x, h0, h_front, z1, h_back, rise, z0=0):
    path = QPainterPath(QPointF(*P(x, h0, z0, Y0)))
    path.lineTo(QPointF(*P(x, h_front, z0, Y0)))
    zm1, zm2 = z0 + (z1 - z0) * 0.3, z0 + (z1 - z0) * 0.7
    path.cubicTo(QPointF(*P(x, h_front + rise, zm1, Y0)), QPointF(*P(x, h_back + rise, zm2, Y0)),
                 QPointF(*P(x, h_back, z1, Y0)))
    path.lineTo(QPointF(*P(x, h0, z1, Y0)))
    path.closeSubpath()
    return path


MAT_LO, MAT_HI = 44, 80        # M1.0h: mattress top lowered from 92 u to 80 u; 36 u thick


def bed(d, pillow_made, pillow_unmade, pillow_size):
    G = "Bed — interactable"
    E(d, G, "grouplayer")
    E(d, f"{G}/Bed contact shadow — floor")
    K.paint(d, f"{G}/Bed contact shadow — floor", lambda p: (
        p.fill(poly([(78, 580), (474, 580), (494, 524), (166, 524)]), C(AO, 150)),
        p.fill(rrect(88, 566, 378, 16, 8), C(AO, 170))))
    K.blur(d, f"{G}/Bed contact shadow — floor", 9)

    hb = arch_panel(96, MAT_LO, 186, 98, 196, 30)
    hb_inset = arch_panel(96, MAT_HI + 6, 166, 84, 174, 20, z0=16)
    rail = rrect(96, Y0 - MAT_LO, 362, MAT_LO - 12, 9)
    legs = [rrect(104, Y0 - 14, 14, 16, 4), rrect(436, Y0 - 14, 14, 16, 4)]

    def frame_base(p):
        p.fill(hb, lin(*P(96, 120, 0, Y0), *P(96, 120, 98, Y0), [(0, WOOD_FRONT), (1, WOOD)]))
        p.fill(hb_inset, C("#efcb98"))
        p.fill(rrect(98, Y0 - 12, 358, 12, 4), C("#7a5236"))            # dark gap under the rail
        for l in legs:
            p.fill(l, C(WOOD_SHADE))
        p.fill(rail, lin(0, Y0 - MAT_LO, 0, Y0 - 12, [(0, "#efc993"), (0.25, WOOD_FRONT), (1, "#c99363")]))

    def frame_bevels(p):
        p.p.save(); p.p.translate(0.9, 0.2); p.stroke(hb_inset, C("#fde4bc", 230), 1.2); p.p.restore()   # lit edge (window side)
        p.p.save(); p.p.translate(-0.9, 0.4); p.stroke(hb_inset, C("#b47e50", 200), 1.0); p.p.restore()
        p.line([(100, Y0 - MAT_LO + 1.2), (454, Y0 - MAT_LO + 1.2)], C("#fde4bc", 220), 1.0)              # rail top lip
        p.line([(100, Y0 - 26), (454, Y0 - 26)], C("#b07a4c", 150), 0.6)                                 # rail groove
        p.line([(100, Y0 - 25.2), (454, Y0 - 25.2)], C("#f7d6a6", 140), 0.5)
    obj(d, G, "Bed frame — headboard, rail and legs (honey wood)", base=frame_base,
        extra=[("carved bevels (clipped)", frame_bevels, 0)],
        shade=lambda p: (p.fill(poly([P(96, MAT_LO, 0, Y0), P(96, 130, 0, Y0), P(96, 130, 98, Y0), P(96, MAT_LO, 98, Y0)]), C(WOOD_SHADE, 210)),
                         p.fill(rrect(96, Y0 - MAT_LO, 70, MAT_LO, 0), C(WOOD_DEEP, 120))),
        light=lambda p: (p.fill(ellipse(118, 318, 56, 70), C(WOOD_LIGHT, 230)), p.fill(rrect(330, Y0 - MAT_LO, 130, 10, 0), C(WOOD_LIGHT, 200))),
        tex=("wood grain", lambda p: (wood_grain(p, rail, (96, Y0 - MAT_LO, 362, 32), 81, 0, 30, 80),
                                      wood_grain(p, hb, (96, 300, 80, 240), 82, -60, 16, 60)), "normal", 255),
        line=lambda p: (K.wline(p, hb, WOOD_LINE, LW_INTERACT), p.stroke(hb_inset, C(WOOD_LINE, 140), 0.6),
                        K.wline(p, rail, WOOD_LINE, LW_INTERACT), [K.wline(p, l, WOOD_LINE, 0.8) for l in legs]),
        shade_blur=16, light_blur=12)

    # mattress: thicker (36 u), lower, soft rounded edge between top and front
    top = rpoly([P(100, MAT_HI, 0, Y0), P(456, MAT_HI, 0, Y0), P(456, MAT_HI, 96, Y0), P(100, MAT_HI, 96, Y0)], 10)
    front = rrect(100, Y0 - MAT_HI, 356, MAT_HI - MAT_LO + 2, 14)
    mattress = top.united(front)

    def mat_details(p):
        y = Y0 - MAT_HI + 9
        p.line([(110, y), (448, y)], C("#d9cdbf", 220), 0.7)                     # piping seam
        p.line([(110, y + 0.9), (448, y + 0.9)], C("#fffaf0", 200), 0.5)
        p.fill(rrect(100, Y0 - MAT_HI - 1, 356, 5, 3), C("#fffaf2", 230))      # rounded top edge catching light
    obj(d, G, "Mattress and sheet — cream", base=lambda p: (p.fill(front, lin(0, Y0 - MAT_HI, 0, Y0 - MAT_LO, [(0, SHEET_FRONT), (1, "#e3d4c2")])),
                                                          p.fill(top, lin(*P(100, MAT_HI, 0, Y0), *P(456, MAT_HI, 96, Y0), [(0, "#f6ead8"), (1, SHEET)]))),
        extra=[("piping and rounded edge (clipped)", mat_details, 0)],
        shade=lambda p: (p.fill(rrect(96, Y0 - MAT_LO - 12, 370, 14, 0), C(SHEET_SHADE)),
                         p.fill(rrect(96, Y0 - MAT_HI, 60, 40, 0), C(SHEET_SHADE, 170)),
                         p.fill(ellipse(110, 446, 120, 54), C(SHEET_SHADE, 150))),
        light=lambda p: p.fill(ellipse(300, 446, 200, 30), C("#fffbf2")),
        line=lambda p: (K.wline(p, mattress, CREAM_LINE, LW_INTERACT),),
        shade_blur=18, light_blur=12)

    # pillow cast shadow on the sheet (beneath the sprite's own contact shadow)
    E(d, f"{G}/Pillow cast shadow on sheet")
    K.paint(d, f"{G}/Pillow cast shadow on sheet", lambda p: p.fill(ellipse(104, 470, 124, 26), C("#7d86a8", 90)))
    K.blur(d, f"{G}/Pillow cast shadow on sheet", 6)
    pw, ph = pillow_size
    for name, f, vis in [("Pillow — unmade (v3 candidate, placed)", pillow_unmade, False),
                         ("Pillow — made (v3 candidate, placed)", pillow_made, True)]:
        E(d, f"{G}/{name}", visible=vis)
        K.place_image(d, f"{G}/{name}", f, 170 - pw / 2, 463 - ph / 2, pw, ph)

    # duvet cast shadow onto the rail below its hem
    E(d, f"{G}/Duvet cast shadow on rail")
    K.paint(d, f"{G}/Duvet cast shadow on rail", lambda p: p.fill(
        smooth([(236, Y0 - 40), (300, Y0 - 34), (360, Y0 - 31), (420, Y0 - 34), (462, Y0 - 38), (462, Y0 - 26), (236, Y0 - 26)], t=0.4), C(AO, 120)))
    K.blur(d, f"{G}/Duvet cast shadow on rail", 6)

    H = MAT_HI + 6
    duv_top = rpoly([P(236, H, 2, Y0), P(460, H, 2, Y0), P(460, H, 96, Y0), P(236, H, 96, Y0)], 14)
    hem = [(462, Y0 - 44), (440, Y0 - 34), (418, Y0 - 38), (392, Y0 - 31), (364, Y0 - 36), (334, Y0 - 30),
           (304, Y0 - 36), (276, Y0 - 31), (250, Y0 - 37), (234, Y0 - 44)]
    drape = smooth([P(232, H, 4, Y0), (300, Y0 - H - 3), (400, Y0 - H - 3), P(462, H, 4, Y0)] + hem, t=0.45)
    cuff = rpoly([P(236, H + 1, 2, Y0), P(266, H + 1, 2, Y0), P(266, H + 1, 96, Y0), P(236, H + 1, 96, Y0)], 9)
    body = duv_top.united(drape)

    def duvet_base(p):
        p.fill(duv_top, lin(*P(236, H, 0, Y0), *P(460, H, 96, Y0), [(0, "#86acc6"), (1, DUVET_LIGHT)]))
        p.fill(drape, lin(0, Y0 - H, 0, Y0 - 32, [(0, DUVET_FRONT), (1, "#7097b4")]))

    def cuff_fn(p):
        p.fill(cuff, C("#dce9f0"))
        p.fill(rrect(226, Y0 - H - 2, 41, 70, 0), lin(0, Y0 - H, 0, Y0 - 32, [(0, "#d4e3ec"), (1, "#bcd0de")]))
        p.p.save(); p.p.translate(2.2, 0.6)                                   # cuff's soft shadow onto the duvet
        p.stroke(rrect(232, Y0 - H - 50, 34, 120, 0), C(DUVET_DEEP, 120), 1.6)
        p.p.restore()

    def folds(p):
        # three soft fold ridges on the drape: a shadow groove and a lit ridge on the window side
        for x in (318, 372, 424):
            groove = [(x, Y0 - H + 4), (x - 3, Y0 - 62), (x + 2, Y0 - 36)]
            p.line(groove, C(DUVET_DEEP, 170), 4.5)
            p.line([(gx + 5, gy) for gx, gy in groove], C(DUVET_LIGHT, 190), 3.5)
        p.fill(rrect(228, Y0 - 44, 240, 16, 0), C(DUVET_SHADE, 170))              # hem underside

    def duvet_shade(p):
        p.fill(rrect(226, Y0 - 70, 244, 40, 0), C(DUVET_SHADE, 170))
        p.fill(ellipse(214, 420, 70, 150), C(DUVET_SHADE, 170))

    def duvet_light(p):
        p.fill(rrect(240, Y0 - H - 4, 222, 7, 3), C("#d8eaf3", 235))            # rounded front edge, lit
        p.fill(ellipse(330, 438, 150, 26), C(DUVET_LIGHT, 230))
    obj(d, G, "Duvet — smooth, sky mist", base=duvet_base,
        extra=[("fold ridges (clipped)", folds, 7), ("turned-down cuff (clipped)", cuff_fn, 0)],
        shade=duvet_shade, light=duvet_light,
        tex=("fabric weave", lambda p: weave(p, body, 37), "overlay", 34),
        line=lambda p: (K.wline(p, body, DUVET_LINE, LW_INTERACT),
                        p.line([P(266, H + 1, 94, Y0), P(266, H + 1, 2, Y0), (267, Y0 - 44)], C(DUVET_LINE, 170), 0.7, t=0.2)),
        shade_blur=14, light_blur=10)

    fb = arch_panel(458, 0, 108, 98, 114, 12)
    fpost = rrect(446, Y0 - 120, 16, 122, 8)
    hpost = rrect(82, Y0 - 200, 18, 202, 9)
    obj(d, G, "Bed frame — footboard and front posts",
        base=lambda p: (p.fill(fb, lin(*P(458, 60, 0, Y0), *P(458, 60, 98, Y0), [(0, "#e9bd85"), (1, "#f4d3a1")])),
                        p.fill(fpost, lin(446, 0, 462, 0, [(0, WOOD_SHADE), (0.45, WOOD), (1, WOOD_LIGHT)])),
                        p.fill(hpost, lin(82, 0, 100, 0, [(0, WOOD_SHADE), (0.45, WOOD), (1, WOOD_LIGHT)]))),
        shade=lambda p: (p.fill(rrect(440, Y0 - 50, 60, 60, 0), C(WOOD_SHADE, 180)), p.fill(rrect(78, Y0 - 90, 12, 96, 0), C(WOOD_DEEP, 150))),
        light=lambda p: (p.fill(ellipse(462, Y0 - 150, 32, 70), C(WOOD_LIGHT, 240)), p.fill(ellipse(92, Y0 - 210, 10, 60), C("#fde8c5", 230))),
        tex=("wood grain", lambda p: wood_grain(p, fb, (458, 400, 30, 180), 91, -80, 12, 60), "normal", 255),
        line=lambda p: (K.wline(p, fb, WOOD_LINE, LW_INTERACT), K.wline(p, fpost, WOOD_LINE, LW_INTERACT), K.wline(p, hpost, WOOD_LINE, LW_INTERACT)),
        shade_blur=10, light_blur=8)


# ---- light, characters, annotations ------------------------------------------------
def light(d):
    G = "Light — morning window light"
    E(d, G, "grouplayer", passthrough=True)
    gx, gy, gw, gh = GLASS
    kx, kz = 0.45, 0.55
    E(d, f"{G}/Light shafts through the panes (screen)", blend="screen", opacity=140)

    def shafts(p):
        for x0, x1 in ((gx + 4, gx + gw / 2 - 4), (gx + gw / 2 + 4, gx + gw - 4)):
            top_l, top_r = (x0, gy + 6), (x1, gy + 6)
            bot_l = (x0 - kx * (480 - gy), 480 + kz * (480 - gy))
            bot_r = (x1 - kx * (480 - (gy + gh)), 480 + kz * (480 - (gy + gh)))
            p.fill(poly([top_l, top_r, bot_r, bot_l]), C("#ffefc8", 70))
    K.paint(d, f"{G}/Light shafts through the panes (screen)", shafts)
    K.blur(d, f"{G}/Light shafts through the panes (screen)", 22)
    E(d, f"{G}/Warm ambient bounce (soft light)", blend="soft_light", opacity=90)
    K.paint(d, f"{G}/Warm ambient bounce (soft light)", lambda p: p.fill(
        rrect(-10, -10, 1300, 740, 0), rad(WIN_C[0], 420, 720, [(0, C("#ffd9a0", 160)), (1, C("#ffd9a0", 0))])))


def characters(d, boy_png):
    G = "Characters — position study (not room art)"
    E(d, G, "grouplayer")
    E(d, f"{G}/Character contact shadows")
    K.paint(d, f"{G}/Character contact shadows", lambda p: (
        p.fill(ellipse(482, 621, 80, 18), C(AO, 90)), p.fill(ellipse(496, 625, 50, 9), C(AO, 90)),
        p.fill(ellipse(794, 551, 96, 20), C(AO, 80)), p.fill(ellipse(808, 555, 66, 10), C(AO, 80))))
    K.blur(d, f"{G}/Character contact shadows", 5)
    s = 200.0 / (1206 - 28)
    E(d, f"{G}/Boy — existing candidate, unmodified (reference)")
    K.place_image(d, f"{G}/Boy — existing candidate, unmodified (reference)", boy_png,
                  520 - 597 * s, 630 - 1206 * s, 1254 * s, 1254 * s)
    E(d, f"{G}/Mom — PLACEHOLDER silhouette (not character art)")

    def mom(p):
        sil = (ellipse(796, 270, 88, 94)
               .united(smooth([(792, 300), (788, 360), (800, 404), (872, 404), (884, 360), (880, 300)]))
               .united(rpoly([(806, 362), (868, 362), (874, 452), (800, 452)], 14))
               .united(rpoly([(800, 448), (874, 448), (886, 548), (848, 548), (838, 470), (828, 548), (792, 548)], 10))
               .united(ellipse(786, 542, 44, 18)).united(ellipse(842, 542, 46, 18))
               .united(rpoly([(800, 370), (788, 372), (778, 446), (792, 450)], 8)))
        p.fill(sil, C("#e9d3c6", 190))
        p.p.strokePath(sil, QPen(C("#b07f6a"), 1.2, Qt.DashLine, Qt.RoundCap, Qt.RoundJoin))
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


def run(d, pillow_made, pillow_unmade, pillow_size, boy_png,
        parts=("shell", "window", "door", "decor", "bed", "light", "chars", "notes")):
    if "shell" in parts:
        room_shell(d)
    if "window" in parts:
        window(d)
    if "door" in parts:
        door(d)
    if "decor" in parts:
        decor(d)
    if "bed" in parts:
        bed(d, pillow_made, pillow_unmade, pillow_size)
    if "light" in parts:
        light(d)
    if "chars" in parts:
        characters(d, boy_png)
    if "notes" in parts:
        annotations(d)
    K.refresh(d)
