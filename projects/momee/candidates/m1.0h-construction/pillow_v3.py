# M1.0h pillow v3 candidate: larger size test. Canvas 160x112 world units
# (320x224 @2x, 160x112 @1x), centre anchor (80, 56). Shapes are the v2 designs
# rescaled by S around the anchor and then refined. Run inside Krita: run(d).
import kpaint2 as K

S = 1.24                      # v2 → v3 size (≈ 131 u wide; ≈ 1.5x the Boy's head)
CX, CY = 80.0, 56.0           # v3 anchor (world units)

LINE = "#9c7d6c"              # warm taupe, a touch deeper than v2 for Boy consistency
LINE_W = 1.0                  # world units (2 px @2x)
BODY, BODY_LOW = "#fcf4e6", "#f2e4d1"
SHADE, CORE = "#c3cde0", "#a8b6cc"   # cool lavender-blue fabric shade (concept boards)
BOUNCE = "#f4d9c0"            # warm light bounced from wood and sheet
LIGHT, SPEC = "#fffaf0", "#fffdf8"
SHADOW = "#59463d"


def T(pts):
    return [(CX + (x - 64) * S, CY + (y - 48) * S) for x, y in pts]


MADE = T([(12, 31), (37, 23.5), (64, 21.5), (91, 23.5), (116, 30.5), (114.5, 48),
          (116.5, 66), (91, 74), (64, 75.5), (37, 74), (11.5, 66), (13.5, 48)])
UNMADE = T([(16, 43), (27, 32), (44, 31), (58, 37.5), (72, 33.5), (93, 27.5), (118, 35),
            (113, 51), (116, 67.5), (93, 72), (66, 70.5), (40, 73), (13, 67), (17, 55)])
FLAP = T([(16, 43), (27, 32), (34, 41), (31, 53), (17, 55)])


def body_group(d, g, body_path, extra_fn=None):
    """Pillow paint group: body, clipped shade/core/bounce/light, weave."""
    E = K.ensure
    names = ["Body — cream", "Soft shade — cool (clipped)", "Core shadow (clipped)",
             "Warm bounce light (clipped)", "Window highlight (clipped)", "Fabric weave (clipped, overlay)"]
    for i, n in enumerate(names):
        E(d, f"{g}Pillow paint/{n}", inherit=i > 0,
          blend="overlay" if "overlay" in n else "normal", opacity=34 if "overlay" in n else 255)
    K.paint(d, f"{g}Pillow paint/Body — cream", lambda p: p.fill(
        body_path, K.lin(CX + 50, CY - 40, CX - 30, CY + 40, [(0, BODY), (0.55, BODY), (1, BODY_LOW)])))
    if extra_fn:
        extra_fn()
    K.paint(d, f"{g}Pillow paint/Fabric weave (clipped, overlay)",
            lambda p: K.texture(p, body_path, K.noise_tile(seed=21, size=160, sigma=16), 0.5))


def made(d):
    g = "Made — plump and tidy/"
    body = K.smooth(MADE, t=0.55)
    K.paint(d, g + "Contact shadow", lambda p: (
        p.fill(K.ellipse(CX - 70, CY + 8, 140, 30), K.rad(CX, CY + 22, 72, [(0, K.C(SHADOW, 70)), (1, K.C(SHADOW, 0))])),
        p.fill(K.ellipse(CX - 58, CY + 24, 116, 12), K.C(SHADOW, 60))))
    K.blur(d, g + "Contact shadow", 6)
    body_group(d, g, body)

    def shade(p):
        p.fill(K.smooth(T([(2, 54), (40, 59), (90, 60), (126, 55), (126, 92), (2, 92)])), K.C(SHADE))
        p.fill(K.smooth(T([(0, 24), (16, 32), (22, 56), (10, 80), (0, 60)])), K.C(SHADE))
        p.fill(K.ellipse(CX - 34, CY - 12, 68, 22), K.C(SHADE, 55))   # gentle centre dip
    K.paint(d, g + "Pillow paint/Soft shade — cool (clipped)", shade)
    K.blur(d, g + "Pillow paint/Soft shade — cool (clipped)", 11)
    K.paint(d, g + "Pillow paint/Core shadow (clipped)", lambda p: p.fill(
        K.smooth(T([(8, 67), (40, 69.5), (90, 70), (122, 66), (122, 80), (8, 80)])), K.C(CORE, 140)))
    K.blur(d, g + "Pillow paint/Core shadow (clipped)", 8)
    K.paint(d, g + "Pillow paint/Warm bounce light (clipped)", lambda p: p.fill(
        K.smooth(T([(20, 73), (64, 76.5), (108, 73), (108, 80), (20, 80)])), K.C(BOUNCE, 170)))
    K.blur(d, g + "Pillow paint/Warm bounce light (clipped)", 3)

    def light(p):
        p.fill(K.smooth(T([(52, 29), (82, 26), (108, 31), (108, 44), (80, 46), (56, 41)])), K.C(LIGHT))
        p.fill(K.ellipse(*[v for v in (CX + 32, CY - 26, 16, 8)]), K.C(SPEC))
        p.fill(K.ellipse(*[v for v in (CX - 66, CY - 26, 18, 10)]), K.C(LIGHT, 170))   # puffed corner
    K.paint(d, g + "Pillow paint/Window highlight (clipped)", light)
    K.blur(d, g + "Pillow paint/Window highlight (clipped)", 7)
    K.ensure(d, g + "Pillow paint/Seam piping (clipped)", inherit=True)
    seam = T([(16, 34), (38, 27.5), (64, 25.5), (90, 27.5), (112, 33.5), (110.5, 48), (112.5, 63),
              (90, 70), (64, 71.5), (38, 70), (15.5, 63), (17.5, 48)])
    K.paint(d, g + "Pillow paint/Seam piping (clipped)", lambda p: (
        p.stroke(K.smooth(seam, t=0.55), K.C("#d8c4b1", 220), 0.7),
        p.p.translate(0.4, 0.5), p.stroke(K.smooth(seam, t=0.55), K.C("#fffaf2", 160), 0.5)))
    K.paint(d, g + "Line art — warm taupe", lambda p: K.wline(p, body, LINE, LINE_W))


def unmade(d):
    g = "Unmade — rumpled/"
    body = K.smooth(UNMADE, t=0.5)
    K.paint(d, g + "Contact shadow", lambda p: (
        p.fill(K.ellipse(CX - 70, CY + 6, 140, 28), K.rad(CX + 2, CY + 20, 72, [(0, K.C(SHADOW, 66)), (1, K.C(SHADOW, 0))])),
        p.fill(K.ellipse(CX - 58, CY + 20, 116, 11), K.C(SHADOW, 55))))
    K.blur(d, g + "Contact shadow", 6)
    K.ensure(d, g + "Pillow paint/Body — cream")
    body_group(d, g, body)
    K.ensure(d, g + "Pillow paint/Folded corner (clipped)", inherit=True)
    K.paint(d, g + "Pillow paint/Folded corner (clipped)", lambda p: p.fill(
        K.smooth(FLAP, t=0.45), K.lin(*T([(18, 36)])[0], *T([(30, 52)])[0], [(0, "#e8e1e2"), (1, "#cdd5e3")])))

    def shade(p):
        p.fill(K.smooth(T([(2, 57), (40, 60), (90, 60), (126, 57), (126, 92), (2, 92)])), K.C(SHADE))
        p.fill(K.ellipse(*T([(44, 34)])[0], 34 * S, 18 * S), K.C(SHADE, 200))          # head dent
        p.fill(K.smooth(T([(30, 40), (37, 51), (33, 61), (22, 58)])), K.C(CORE, 170))  # under the fold
        p.fill(K.smooth(T([(76, 44), (84, 56), (78, 64), (70, 54)])), K.C(SHADE, 170))
    K.paint(d, g + "Pillow paint/Soft shade — cool (clipped)", shade)
    K.blur(d, g + "Pillow paint/Soft shade — cool (clipped)", 10)
    K.paint(d, g + "Pillow paint/Core shadow (clipped)", lambda p: p.fill(
        K.smooth(T([(10, 67), (40, 68.5), (90, 68), (122, 65), (122, 80), (10, 80)])), K.C(CORE, 135)))
    K.blur(d, g + "Pillow paint/Core shadow (clipped)", 8)
    K.paint(d, g + "Pillow paint/Warm bounce light (clipped)", lambda p: p.fill(
        K.smooth(T([(22, 70), (66, 72.5), (110, 69.5), (110, 78), (22, 78)])), K.C(BOUNCE, 160)))
    K.blur(d, g + "Pillow paint/Warm bounce light (clipped)", 3)
    K.paint(d, g + "Pillow paint/Window highlight (clipped)", lambda p: (
        p.fill(K.smooth(T([(76, 32), (96, 28.5), (113, 36), (104, 45), (86, 45)])), K.C(LIGHT)),
        p.fill(K.ellipse(*T([(36, 51)])[0], 22 * S, 8 * S), K.C(LIGHT, 180))))
    K.blur(d, g + "Pillow paint/Window highlight (clipped)", 6)
    K.ensure(d, g + "Pillow paint/Fold ridges (clipped)", inherit=True)

    def ridges(p):
        # each soft fold: a shadow groove and a lit ridge just above-right of it
        for pts in ([(58, 40), (60, 47), (57, 55)], [(66, 40), (73, 47), (76, 56)], [(48, 47), (42, 56), (43, 64)],
                    [(88, 33), (92, 42), (98, 50)], [(96, 60), (103, 62), (108, 59)], [(24, 61), (30, 64), (36, 63)]):
            q = T(pts)
            p.line(q, K.C("#ad9f9c", 200), 0.8)
            p.line([(x + 0.9, y - 0.7) for x, y in q], K.C("#fffaf1", 200), 0.7)
    K.paint(d, g + "Pillow paint/Fold ridges (clipped)", ridges)
    K.paint(d, g + "Line art — warm taupe", lambda p: (
        K.wline(p, body, LINE, LINE_W),
        p.line(T([(27, 32), (34, 41), (31, 53), (17, 55)]), LINE, 0.85)))


def guides(d):
    def g1(p):
        p.stroke(K.rrect(0.5, 0.5, 159, 111, 0), "#d48658", 0.5)
        p.line([(CX, CY - 8), (CX, CY + 8)], "#d48658", 0.5)
        p.line([(CX - 8, CY), (CX + 8, CY)], "#d48658", 0.5)
    K.paint(d, "Guides — anchor and bounds (hidden)/Canvas 320x224, anchor (160,112)", g1)
    # v2 visible extent (@2x 18..237 x 43..164 on a 256x192 canvas), re-centred on the v3 anchor
    K.paint(d, "Guides — anchor and bounds (hidden)/v2 extent re-centred for comparison", lambda p: p.stroke(
        K.rrect(CX - 64 + 9, CY - 48 + 21.5, 109.5, 60.5, 0), "#6986a2", 0.5))


def build(d):
    E = K.ensure
    for n in list(d.rootNode().childNodes()):
        n.remove()
    E(d, "Guides — anchor and bounds (hidden)", "grouplayer", visible=False)
    E(d, "Guides — anchor and bounds (hidden)/Canvas 320x224, anchor (160,112)")
    E(d, "Guides — anchor and bounds (hidden)/v2 extent re-centred for comparison")
    for st in ["Unmade — rumpled", "Made — plump and tidy"]:
        E(d, st, "grouplayer")
        E(d, st + "/Contact shadow")
        E(d, st + "/Pillow paint", "grouplayer")
        E(d, st + "/Line art — warm taupe")
    guides(d)
    made(d)
    unmade(d)
    K.refresh(d)
