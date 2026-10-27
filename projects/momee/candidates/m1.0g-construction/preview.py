# Review helpers: export each pillow state and build a side-by-side sheet.
from krita import Krita, InfoObject
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QColor, QImage, QPainter
import kpaint as K

STATES = {"unmade": "Unmade — rumpled", "made": "Made — plump and tidy"}


def export_state(d, state, path):
    for s, g in STATES.items():
        K.find(d, g).setVisible(s == state)
    K.find(d, "Guides — anchor and bounds (hidden)").setVisible(False)
    K.refresh(d)
    d.setBatchmode(True)
    info = InfoObject()
    info.setProperty("alpha", True)
    info.setProperty("compression", 9)
    info.setProperty("forceSRGB", False)
    info.setProperty("saveSRGBProfile", False)
    ok = d.exportImage(path, info)
    d.setBatchmode(False)
    return ok


def sheet(files, out, bgs=("#f9eddc", "#96b5c3", "#59463d"), zoom=2):
    imgs = [QImage(f) for f in files]
    w, h = imgs[0].width(), imgs[0].height()
    W = len(imgs) * w * zoom // 2 + 0
    sheet = QImage(len(imgs) * w, len(bgs) * h, QImage.Format_ARGB32)
    sheet.fill(QColor("#fefaf1"))
    p = QPainter(sheet)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)
    for r, bg in enumerate(bgs):
        for c, im in enumerate(imgs):
            p.fillRect(c * w, r * h, w, h, QColor(bg))
            p.drawImage(c * w, r * h, im)
    p.end()
    sheet.save(out)
