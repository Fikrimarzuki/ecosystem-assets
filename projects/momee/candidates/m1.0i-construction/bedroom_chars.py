# M1.0i bedroom character integration study (2560x1440, 2 px/u): the M1.0h room
# render with the v1 Boy and Mom candidates at the bedroom-layout.ts positions.
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QFont, QImage, QPainter, QTransform

import kpaint2 as K
from kpaint2 import C, ellipse, rrect, lin, rad

E = K.ensure
CHILD_START, MOM_SPOT = (520, 630), (840, 560)
WIN_X = 600          # M1.0h window centre (world x): the room's light source


def place(p, img, anchor_px, feet, scale, mirror=False):
    """Draw a 4 px/u master render so its feet anchor lands on `feet` (world units)."""
    ax, ay = anchor_px
    p.p.save()
    p.p.translate(*feet)
    if mirror:
        p.p.scale(-1, 1)
    p.p.drawImage(QRectF(-ax * scale, -ay * scale, img.width() * scale, img.height() * scale), img)
    p.p.restore()


def run(d, room_png, boy_png, mom_png, boy_anchor, mom_anchor):
    room = QImage(room_png)
    boy, mom = QImage(boy_png), QImage(mom_png)
    s = 0.25   # 4 px/u master render → world units (painter is at 2 px/u)
    E(d, "Room — M1.0h bedroom study v2 (room-only render)")
    K.paint(d, "Room — M1.0h bedroom study v2 (room-only render)", lambda p: p.p.drawImage(QRectF(0, 0, 1280, 720), room))
    E(d, "Contact shadows (study)")
    K.paint(d, "Contact shadows (study)", lambda p: (
        p.fill(ellipse(CHILD_START[0] - 36, CHILD_START[1] - 7, 72, 14), C("#6e4a30", 95)),
        p.fill(ellipse(CHILD_START[0] - 22, CHILD_START[1] - 4, 44, 7), C("#6e4a30", 95)),
        p.fill(ellipse(MOM_SPOT[0] - 42, MOM_SPOT[1] - 7, 84, 14), C("#6e4a30", 85)),
        p.fill(ellipse(MOM_SPOT[0] - 26, MOM_SPOT[1] - 4, 52, 7), C("#6e4a30", 85))))
    K.blur(d, "Contact shadows (study)", 5)
    for who, img, anchor, feet, mirror, rim_side in (
            ("Boy", boy, boy_anchor, CHILD_START, False, 1), ("Mom", mom, mom_anchor, MOM_SPOT, True, -1)):
        g = f"{who} — candidate v1, ¾ neutral" + (" (mirrored to face the child)" if mirror else "")
        E(d, g, "grouplayer")
        E(d, f"{g}/{who} — character render (unmodified export source)")
        K.paint(d, f"{g}/{who} — character render (unmodified export source)",
                lambda p, img=img, anchor=anchor, feet=feet, mirror=mirror: place(p, img, anchor, feet, s, mirror))
        # study-only lighting adaptation: warm rim on the window side, cool falloff away from it
        h = 200 if who == "Boy" else 290
        x0 = feet[0]
        E(d, f"{g}/window rim light (clipped, study only)", inherit=True, blend="screen", opacity=150)
        K.paint(d, f"{g}/window rim light (clipped, study only)", lambda p, x0=x0, h=h, rs=rim_side, f=feet: p.fill(
            rrect(x0 - 80, f[1] - h - 20, 160, h + 30, 0),
            lin(x0 + rs * 60, 0, x0 - rs * 10, 0, [(0, C("#ffe2b0", 200)), (1, C("#ffe2b0", 0))])))
        E(d, f"{g}/away-from-window falloff (clipped, study only)", inherit=True, blend="multiply", opacity=90)
        K.paint(d, f"{g}/away-from-window falloff (clipped, study only)", lambda p, x0=x0, h=h, rs=rim_side, f=feet: p.fill(
            rrect(x0 - 80, f[1] - h - 20, 160, h + 30, 0),
            lin(x0 - rs * 60, 0, x0 + rs * 5, 0, [(0, C("#c9b8c8", 200)), (1, C("#c9b8c8", 0))])))
    E(d, "Labels (study)")

    def labels(p):
        f = QFont("Helvetica")
        f.setPixelSize(8)
        p.p.setFont(f)
        p.p.setPen(C("#59463d"))
        p.p.drawText(QPointF(CHILD_START[0] - 70, CHILD_START[1] + 22), "BOY — M1.0i candidate v1 (not approved) · 200 u")
        p.p.drawText(QPointF(MOM_SPOT[0] - 64, MOM_SPOT[1] + 22), "MOM — M1.0i candidate v1 (not approved) · 290 u")
    K.paint(d, "Labels (study)", labels)
    K.refresh(d)
