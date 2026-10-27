"""Construction helper for mom-head-v1.svg (M1.1b-1), second approach.

The hair silhouette, wave troughs and sheen glints are hand-placed point lists that are smoothed into
cubic Beziers (Catmull-Rom). Everything else (face, eyes, brows, mouth, fringe) is hand-written path
data in the template. The generated SVG is plain, editable Inkscape-compatible paths; this script is a
drafting aid and is not needed to edit the SVG. Usage: python3 build_mom_head_v2.py template.svg out.svg
"""
import sys

def smooth(pts, closed=False, tension=1.0):
    P = pts + pts[:3] if closed else pts
    n = len(pts)
    segs = n if closed else n - 1
    d = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for i in range(segs):
        p0 = P[i - 1] if (i > 0 or closed) else P[i]
        p1, p2 = P[i], P[i + 1]
        p3 = P[i + 2] if (i + 2 < len(P)) else p2
        k = tension / 6
        c1 = (p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k)
        c2 = (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k)
        d.append(f"C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}")
    return " ".join(d) + (" Z" if closed else "")

AX = 774  # mirror axis: twice the face centre (x = 387)

def mirror(pts, dy=0, squeeze=1.0):
    return [(AX - (387 + (x - 387) * squeeze), y + dy * min(1.0, max(0.0, (y - 120) / 600))) for x, y in pts][::-1]

# Left half of the hair silhouette, crown -> outer waves -> notched tips -> inner edge up to the neck.
LEFT_OUT = [(388, 42), (312, 50), (248, 80), (208, 124), (182, 182), (168, 248), (158, 312), (138, 362), (126, 414),
            (138, 462), (116, 510), (98, 558), (96, 606), (110, 648), (90, 690), (78, 734), (86, 772), (106, 798)]
LEFT_TIPS = [(126, 806), (152, 794), (162, 770)]
LEFT_IN = [(178, 740), (200, 700), (220, 660), (238, 620), (258, 586), (282, 558), (312, 536), (348, 522), (388, 516)]

def silhouette():
    left = LEFT_OUT + LEFT_TIPS + LEFT_IN
    right = mirror(left[1:-1], dy=6, squeeze=0.97)
    return smooth(left + right, closed=True)

def tapered(spine, w, tip=0.15):
    """Closed crescent-like glint/trough along a spine: widest in the middle, pointed at both ends."""
    import math
    n = len(spine)
    a, b = [], []
    for i, (x, y) in enumerate(spine):
        t = i / (n - 1)
        hw = w * math.sin(math.pi * t) ** 0.8 + tip
        xa, ya = spine[max(i - 1, 0)]
        xb, yb = spine[min(i + 1, n - 1)]
        tx, ty = xb - xa, yb - ya
        L = math.hypot(tx, ty) or 1
        nx, ny = -ty / L, tx / L
        a.append((x + nx * hw, y + ny * hw))
        b.append((x - nx * hw, y - ny * hw))
    return smooth(a + b[::-1], closed=True, tension=0.9)

TROUGHS_L = [[(138, 462), (162, 476), (188, 494), (214, 516)],
             [(110, 648), (136, 660), (164, 676), (194, 700)],
             [(190, 214), (194, 276), (196, 336), (200, 392)]]
GLINTS_L = [[(150, 384), (142, 412), (144, 442)],
            [(116, 566), (110, 594), (114, 624)],
            [(100, 714), (96, 740), (102, 764)],
            [(194, 236), (186, 272), (184, 308)],
            [(196, 560), (188, 596), (186, 632)]]
STRANDS_L = [[(236, 104), (200, 180), (184, 270), (172, 350), (152, 430), (140, 510), (124, 600), (118, 690), (124, 770)],
             [(250, 280), (232, 360), (222, 440), (212, 520), (204, 600), (196, 680)]]

def mirror_spine(spine, dy=6, squeeze=0.97):
    return [(AX - (387 + (x - 387) * squeeze), y + dy * min(1.0, max(0.0, (y - 120) / 600))) for x, y in spine]

def build(template, out):
    troughs = [tapered(s, 7) for s in TROUGHS_L] + [tapered(mirror_spine(s), 7) for s in TROUGHS_L]
    glints = [tapered(s, 3.2) for s in GLINTS_L] + [tapered(mirror_spine(s), 3.2) for s in GLINTS_L]
    strands = [smooth(s) for s in STRANDS_L] + [smooth(mirror_spine(s)) for s in STRANDS_L]
    rep = {
        "<!--SILHOUETTE-->": silhouette(),
        "<!--TROUGHS-->": "\n      ".join(f'<path id="hair-back-trough-{i+1}" d="{d}"/>' for i, d in enumerate(troughs)),
        "<!--GLINTS-->": "\n      ".join(f'<path id="hair-back-glint-{i+1}" d="{d}"/>' for i, d in enumerate(glints)),
        "<!--STRANDS-->": "\n      ".join(f'<path id="hair-back-strand-{i+1}" d="{d}"/>' for i, d in enumerate(strands)),
    }
    s = open(template).read()
    for k, v in rep.items():
        s = s.replace(k, v)
    open(out, "w").write(s)

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
