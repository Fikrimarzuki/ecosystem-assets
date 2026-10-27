"""Assemble side-by-side comparison sheets (default: source | 40k | 25k | 20k), one per view.

Usage:
  blender -b --factory-startup --python scripts/blender/make_contact_sheets.py -- <previews_dir> [labels,comma,separated] [sheet-suffix]

Uses Blender's own image API + numpy (bundled with Blender) — no extra dependency.
"""
import os
import sys

import bpy
import numpy as np

DEFAULT_LABELS = ["source", "40k", "25k", "20k"]


def load(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    return px


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    root = os.path.abspath(args[0])
    labels = args[1].split(",") if len(args) > 1 else DEFAULT_LABELS
    suffix = f"_{args[2]}" if len(args) > 2 else ""
    out_dir = os.path.join(root, "comparison")
    os.makedirs(out_dir, exist_ok=True)
    for look in ("textured", "clay"):
        views = sorted({f.split("_", 1)[1] for f in os.listdir(os.path.join(root, look)) if f.startswith("source_")})
        for view in views:
            tiles = [load(os.path.join(root, look, f"{label}_{view}")) for label in labels]
            gap = np.ones((tiles[0].shape[0], 8, 4), dtype=np.float32)
            row = np.concatenate([t if i == 0 else np.concatenate([gap, t], axis=1) for i, t in enumerate(tiles)], axis=1)
            h, w = row.shape[:2]
            out = bpy.data.images.new(f"sheet_{look}_{view}{suffix}", w, h, alpha=True)
            out.pixels = row.ravel()
            out.filepath_raw = os.path.join(out_dir, f"{look}_{view.replace('.png', '')}{suffix}.png")
            out.file_format = "PNG"
            out.save()
            print("SHEET", out.filepath_raw)


main()
