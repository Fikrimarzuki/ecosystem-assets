"""Measure limb centre-lines and widths of a character mesh by planar cross-sections.

Usage:
  blender -b --factory-startup --python scripts/blender/measure_landmarks.py -- <in.glb> <out.json>

Read-only. Welds seam-split vertices in memory, then intersects the mesh with
planes (numpy, no extra dependency):
  legs — horizontal planes, one contour cluster per side
  arms — planes perpendicular to the arm axis; the axis is re-fitted from the
         section centres a few times, because A-pose arms run diagonally
Writes per-section centre (bounding-box centre of the contour) and width.
Joint placement is decided from this data in build_rig.py, and checked visually.
"""
import json
import sys

import bmesh
import bpy
import numpy as np


def load_welded(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    obj = next(o for o in bpy.context.scene.objects if o.type == "MESH")
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    mw = obj.matrix_world
    verts = np.array([tuple(mw @ v.co) for v in bm.verts])
    edges = np.array([(e.verts[0].index, e.verts[1].index) for e in bm.edges])
    bm.free()
    return verts, edges


def section(verts, edges, co, no):
    d = (verts - co) @ no
    d0, d1 = d[edges[:, 0]], d[edges[:, 1]]
    cross = (d0 * d1) < 0
    a, b = verts[edges[cross, 0]], verts[edges[cross, 1]]
    t = (d0[cross] / (d0[cross] - d1[cross]))[:, None]
    return a + (b - a) * t


def clusters(points, link=0.025):
    """Single-linkage clustering (contours of separate limbs are > link apart)."""
    n = len(points)
    if n == 0:
        return []
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    dist = np.linalg.norm(points[:, None, :] - points[None, :, :], axis=-1)
    ii, jj = np.nonzero(np.triu(dist < link, 1))
    for i, j in zip(ii, jj):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return [points[g] for g in groups.values()]


def box_centre(pts):
    return (pts.min(0) + pts.max(0)) / 2


def legs(verts, edges, side):
    out = []
    for z in np.arange(-0.94, 0.30, 0.01):
        pts = section(verts, edges, np.array([0, 0, z]), np.array([0, 0, 1.0]))
        pts = pts[(np.sign(pts[:, 0]) == side) & (np.abs(pts[:, 0]) < 0.37)]
        cs = [c for c in clusters(pts) if len(c) >= 6]
        if not cs:
            continue
        # The leg is the cluster nearest the previous centre (or the most medial one at the bottom).
        if out:
            prev = np.array(out[-1]["centre"])
            c = min(cs, key=lambda c: np.linalg.norm(box_centre(c)[:2] - prev[:2]))
        else:
            c = max(cs, key=len)
        ctr = box_centre(c)
        span = c.max(0) - c.min(0)
        out.append({"z": round(float(z), 3), "centre": [round(float(x), 4) for x in ctr],
                    "widthX": round(float(span[0]), 4), "depthY": round(float(span[1]), 4),
                    "clustersOnSide": len(cs)})
    return out


def arm(verts, edges, side, shoulder_guess, tip_guess, iterations=3):
    s = np.array(shoulder_guess, dtype=float)
    h = np.array(tip_guess, dtype=float)
    samples = []
    for _ in range(iterations):
        axis = h - s
        length = np.linalg.norm(axis)
        d = axis / length
        samples = []
        for t in np.arange(0.15, 1.0, 0.025):
            p = s + d * length * t
            pts = section(verts, edges, p, d)
            pts = pts[np.linalg.norm(pts - p, axis=1) < 0.12]
            cs = [c for c in clusters(pts) if len(c) >= 5]
            if not cs:
                continue
            c = min(cs, key=lambda c: np.linalg.norm(box_centre(c) - p))
            ctr = box_centre(c)
            # Width measured across the arm in the frontal plane and front-to-back.
            side_axis = np.cross(d, [0, 1.0, 0])
            side_axis /= np.linalg.norm(side_axis)
            w = float((c @ side_axis).max() - (c @ side_axis).min())
            dep = float(c[:, 1].max() - c[:, 1].min())
            samples.append({"t": round(float(t), 3), "centre": [round(float(x), 4) for x in ctr],
                            "width": round(w, 4), "depthY": round(dep, 4), "points": int(len(c))})
        # Re-fit the axis through the section centres (principal direction).
        ctrs = np.array([x["centre"] for x in samples if 0.25 <= x["t"] <= 0.9])
        mean = ctrs.mean(0)
        _, _, vt = np.linalg.svd(ctrs - mean)
        dirn = vt[0] if np.dot(vt[0], h - s) > 0 else -vt[0]
        s = mean - dirn * np.dot(mean - s, dirn)
        h = s + dirn * np.dot(h - s, dirn)
    return {"axisStart": [round(float(x), 4) for x in s], "axisEnd": [round(float(x), 4) for x in h],
            "axisDir": [round(float(x), 4) for x in (h - s) / np.linalg.norm(h - s)], "sections": samples}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    src, out = argv
    verts, edges = load_welded(src)
    tip = {s: verts[np.argmax(verts[:, 0] * s)] for s in (1, -1)}
    result = {
        "bounds": {"min": verts.min(0).round(4).tolist(), "max": verts.max(0).round(4).tolist()},
        "handTip": {"L": tip[1].round(4).tolist(), "R": tip[-1].round(4).tolist()},
        "legs": {"L": legs(verts, edges, 1), "R": legs(verts, edges, -1)},
        "arms": {
            "L": arm(verts, edges, 1, (0.20, 0.0, 0.45), tip[1]),
            "R": arm(verts, edges, -1, (-0.20, 0.0, 0.45), tip[-1]),
        },
    }
    # Torso / neck / head widths on the midline.
    mid = []
    for z in np.arange(0.10, 0.95, 0.02):
        pts = section(verts, edges, np.array([0, 0, z]), np.array([0, 0, 1.0]))
        pts = pts[np.abs(pts[:, 0]) < 0.30]
        cs = [c for c in clusters(pts) if len(c) >= 6]
        if not cs:
            continue
        c = min(cs, key=lambda c: abs(box_centre(c)[0]))
        span = c.max(0) - c.min(0)
        mid.append({"z": round(float(z), 3), "centre": box_centre(c).round(4).tolist(),
                    "widthX": round(float(span[0]), 4), "depthY": round(float(span[1]), 4)})
    result["midline"] = mid
    with open(out, "w") as f:
        json.dump(result, f, indent=1)
    print("LANDMARKS_OK")


main()
