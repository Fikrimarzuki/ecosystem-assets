# M1.0g pillow v2 candidate. Run inside Krita with kpaint imported as K and the
# document as d. World units (1 unit = 2 px @2x). Canvas 128x96 units, anchor (64,48).
import kpaint as K

LINE = "#a28c80"      # warm taupe: darker than the cream fill, never black
LINE_W = 1.25         # world units -> 2.5 px @2x (calibration rule for interactables)
BODY = "#fbf3e6"      # cream fabric
BODY_LOW = "#f1e6d8"  # lower body of the gradient
SHADE = "#c9d2de"     # one soft cool shadow tone (cream + dusty blue)
SHADE_CORE = "#b4bfcd"
LIGHT = "#fffaf1"     # gentle highlight, not pure white
SEAM = "#dccbbb"
SHADOW = "#59463d"    # cocoa, used at low alpha only

MADE = [(12, 31), (37, 24), (64, 22.5), (91, 24), (116, 30.5), (115, 48),
        (116.5, 66), (91, 73.5), (64, 75), (37, 73.5), (11.5, 66), (13, 48)]
UNMADE = [(16, 43), (27, 32), (44, 31), (58, 37.5), (72, 33.5), (93, 27.5),
          (118, 35), (113, 51), (116, 67.5), (93, 72), (66, 70.5), (40, 73),
          (13, 67), (17, 55)]
FLAP = [(16, 43), (27, 32), (33, 41), (30, 52), (17, 55)]


def made(d):
    g = "Made — plump and tidy/"
    body = K.smooth(MADE, t=0.55)
    K.paint(d, g + "Contact shadow", lambda p: p.fill(
        K.ellipse(14, 60, 102, 20), K.rad(64, 70, 52, [(0, K.C(SHADOW, 60)), (1, K.C(SHADOW, 0))])))
    K.blur(d, g + "Contact shadow", 6)
    K.paint(d, g + "Pillow paint/Body — cream", lambda p: p.fill(
        body, K.lin(80, 22, 50, 76, [(0, BODY), (0.6, BODY), (1, BODY_LOW)])))

    def shade(p):
        # light from the upper right: shade the lower left and the underside
        p.fill(K.smooth([(2, 54), (40, 60), (90, 61), (126, 56), (126, 92), (2, 92)]), K.C(SHADE))
        p.fill(K.smooth([(0, 26), (18, 34), (24, 56), (10, 78), (0, 60)]), K.C(SHADE))
        p.fill(K.ellipse(18, 66, 76, 12), K.C(SHADE_CORE, 200))
    K.paint(d, g + "Pillow paint/Soft shade — cool (clipped)", shade)
    K.blur(d, g + "Pillow paint/Soft shade — cool (clipped)", 9)

    def light(p):
        p.fill(K.smooth([(50, 30), (80, 27), (104, 33), (102, 44), (78, 46), (56, 42)]), K.C(LIGHT))
        p.fill(K.ellipse(96, 30, 12, 6), K.C("#fffdf8"))
    K.paint(d, g + "Pillow paint/Warm light (clipped)", light)
    K.blur(d, g + "Pillow paint/Warm light (clipped)", 7)

    def seam(p):
        inner = [(16, 34), (38, 28), (64, 26.5), (90, 28), (112, 33.5), (111, 48),
                 (112.5, 63), (90, 70), (64, 71.5), (38, 70), (15.5, 63), (17, 48)]
        p.stroke(K.smooth(inner, t=0.55), K.C(SEAM, 210), 0.8)
    K.paint(d, g + "Pillow paint/Seam piping (clipped)", seam)
    K.paint(d, g + "Line art — warm taupe", lambda p: p.stroke(body, LINE, LINE_W))


def unmade(d):
    g = "Unmade — rumpled/"
    body = K.smooth(UNMADE, t=0.5)
    K.paint(d, g + "Contact shadow", lambda p: p.fill(
        K.ellipse(14, 60, 102, 18), K.rad(66, 69, 52, [(0, K.C(SHADOW, 55)), (1, K.C(SHADOW, 0))])))
    K.blur(d, g + "Contact shadow", 6)
    K.paint(d, g + "Pillow paint/Body — cream", lambda p: p.fill(
        body, K.lin(84, 26, 50, 74, [(0, BODY), (0.55, BODY), (1, BODY_LOW)])))
    K.paint(d, g + "Pillow paint/Folded corner", lambda p: p.fill(
        K.smooth(FLAP, t=0.45), K.lin(18, 36, 30, 52, [(0, "#e9e3df"), (1, "#d6dbe3")])))

    def shade(p):
        p.fill(K.smooth([(2, 57), (40, 60), (90, 60), (126, 57), (126, 92), (2, 92)]), K.C(SHADE))
        p.fill(K.ellipse(20, 64, 74, 10), K.C(SHADE_CORE, 190))
        p.fill(K.ellipse(46, 36, 30, 16), K.C(SHADE, 190))           # head dent
        p.fill(K.smooth([(30, 40), (36, 50), (32, 60), (22, 58)]), K.C(SHADE_CORE, 170))  # under the fold
        p.fill(K.smooth([(76, 44), (84, 56), (78, 64), (70, 54)]), K.C(SHADE, 170))
    K.paint(d, g + "Pillow paint/Soft shade — cool (clipped)", shade)
    K.blur(d, g + "Pillow paint/Soft shade — cool (clipped)", 8)

    def light(p):
        p.fill(K.smooth([(76, 33), (96, 29), (112, 36), (104, 44), (86, 44)]), K.C(LIGHT))
        p.fill(K.ellipse(36, 52, 20, 7), K.C(LIGHT, 170))
    K.paint(d, g + "Pillow paint/Warm light (clipped)", light)
    K.blur(d, g + "Pillow paint/Warm light (clipped)", 6)

    def creases(p):
        # soft rumple lines radiating from the head dent
        for pts in ([(58, 40), (60, 47), (57, 55)],
                    [(66, 40), (73, 47), (76, 56)],
                    [(48, 47), (42, 56), (43, 64)],
                    [(88, 33), (92, 42), (98, 50)],
                    [(96, 60), (103, 62), (108, 59)]):
            p.line(pts, K.C("#b8a99f", 230), 0.85)
    K.paint(d, g + "Pillow paint/Creases (clipped)", creases)

    def lines(p):
        p.stroke(body, LINE, LINE_W)
        p.line([(27, 32), (33, 41), (30, 52), (17, 55)], LINE, 1.0)   # folded corner edge
    K.paint(d, g + "Line art — warm taupe", lines)


def guides(d):
    def g1(p):
        p.stroke(K.rrect(0.5, 0.5, 127, 95, 0), "#d48658", 0.5)
        p.line([(64, 40), (64, 56)], "#d48658", 0.5)
        p.line([(56, 48), (72, 48)], "#d48658", 0.5)
    K.paint(d, "Guides — anchor and bounds (hidden)/Canvas 256x192, anchor (128,96)", g1)
    # v1 visible bounds: made 28..233 x 48..143 px, unmade 28..233 x 58..141 px (@2x)
    K.paint(d, "Guides — anchor and bounds (hidden)/v1 silhouette bounds for comparison", lambda p: (
        p.stroke(K.rrect(14, 24, 102.5, 47.5, 0), "#6986a2", 0.5),
        p.stroke(K.rrect(14, 29, 102.5, 41.5, 0), "#9eb49f", 0.5)))


def run(d):
    guides(d)
    made(d)
    unmade(d)
    K.refresh(d)
