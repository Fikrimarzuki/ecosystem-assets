"""M7.5c.2b — validate the animated Explorer GLB in a clean scene and render contact sheets.

Usage:
  blender -b --factory-startup --python scripts/blender/validate_animations.py -- \
      <animated.glb> <reference-rig-v3.glb> <previews_dir> <report.json>

Checks (all against the exported file, reimported):
  * clips present, names, durations and channels (from the raw glTF JSON)
  * geometry / UVs / skin weights / skeleton / textures byte-identical to v3
  * loop seam: first vs last frame vertex positions, and velocity continuity
  * root motion: root never animated, armature static, hips horizontal drift
  * feet: ground penetration, planted-foot sliding relative to the clip's speed
  * joints: elbow / knee / hip angles per frame vs approved limits
  * deformation per frame: flipped / collapsed triangles, new self-intersections,
    and hand-or-forearm vs thigh/hip intersections specifically
  * contact sheets (textured + clay) at gameplay distance
"""
import hashlib
import json
import math
import os
import struct
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_previews import place_camera, render, setup_scene  # noqa: E402
from test_deformation import evaluated, self_intersections, tri_normals_areas  # noqa: E402

FPS = 30
LIMITS = {"elbow": 90.0, "knee": 100.0, "hip": 55.0}
SPEEDS = {"Idle": 0.0}  # filled from the authoring report when available
SHEET_FRAMES = {"Idle": 6, "Walk": 8, "Run": 8}


def read_glb(path):
    with open(path, "rb") as f:
        data = f.read()
    n, _ = struct.unpack_from("<I4s", data, 12)
    doc = json.loads(data[20:20 + n])
    off = 20 + n
    bn, _ = struct.unpack_from("<I4s", data, off)
    binary = data[off + 8: off + 8 + bn]
    return doc, binary


def accessor_bytes(doc, binary, idx):
    acc = doc["accessors"][idx]
    bv = doc["bufferViews"][acc["bufferView"]]
    start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    comp = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}[acc["componentType"]]
    ncomp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[acc["type"]]
    stride = bv.get("byteStride", comp * ncomp)
    if stride == comp * ncomp:
        return binary[start: start + acc["count"] * stride]
    return b"".join(binary[start + i * stride: start + i * stride + comp * ncomp] for i in range(acc["count"]))


def h(b):
    return hashlib.sha256(b).hexdigest()[:16]


def static_compare(anim_path, ref_path):
    a, ab = read_glb(anim_path)
    r, rb = read_glb(ref_path)
    out = {}
    pa, pr = a["meshes"][0]["primitives"][0], r["meshes"][0]["primitives"][0]
    for key in sorted(pr["attributes"]):
        out[key] = h(accessor_bytes(a, ab, pa["attributes"][key])) == h(accessor_bytes(r, rb, pr["attributes"][key]))
    out["indices"] = h(accessor_bytes(a, ab, pa["indices"])) == h(accessor_bytes(r, rb, pr["indices"]))
    out["inverseBindMatrices"] = h(accessor_bytes(a, ab, a["skins"][0]["inverseBindMatrices"])) == \
        h(accessor_bytes(r, rb, r["skins"][0]["inverseBindMatrices"]))
    names_a = [a["nodes"][j]["name"] for j in a["skins"][0]["joints"]]
    names_r = [r["nodes"][j]["name"] for j in r["skins"][0]["joints"]]
    out["jointNames"] = names_a == names_r
    rest_a = {a["nodes"][j]["name"]: (a["nodes"][j].get("translation"), a["nodes"][j].get("rotation")) for j in a["skins"][0]["joints"]}
    rest_r = {r["nodes"][j]["name"]: (r["nodes"][j].get("translation"), r["nodes"][j].get("rotation")) for j in r["skins"][0]["joints"]}
    out["jointRestTRS"] = rest_a == rest_r

    def img_hashes(doc, binary):
        return [h(binary[doc["bufferViews"][i["bufferView"]].get("byteOffset", 0):
                         doc["bufferViews"][i["bufferView"]].get("byteOffset", 0) + doc["bufferViews"][i["bufferView"]]["byteLength"]])
                for i in doc["images"]]
    out["images"] = img_hashes(a, ab) == img_hashes(r, rb)
    out["materials"] = json.dumps(a["materials"], sort_keys=True) == json.dumps(r["materials"], sort_keys=True)

    clips = {}
    root_index = next(i for i, n in enumerate(a["nodes"]) if n.get("name") == "root")
    for anim in a.get("animations", []):
        times = []
        targets = {}
        for ch in anim["channels"]:
            smp = anim["samplers"][ch["sampler"]]
            acc = a["accessors"][smp["input"]]
            times.append(acc["max"][0])
            node = a["nodes"][ch["target"]["node"]].get("name")
            targets.setdefault(node, []).append(ch["target"]["path"])
        clips[anim["name"]] = {
            "durationS": round(max(times), 4),
            "channels": len(anim["channels"]),
            "animatedNodes": len(targets),
            "translationChannels": sorted(n for n, p in targets.items() if "translation" in p),
            "rootAnimated": "root" in targets,
            "interpolations": sorted({s.get("interpolation", "LINEAR") for s in anim["samplers"]}),
        }
    tris = sum(a["accessors"][p["indices"]]["count"] // 3 for m in a["meshes"] for p in m["primitives"])
    return out, clips, tris, root_index


def assign(arm, action):
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = action
    if hasattr(ad, "action_slot") and getattr(action, "slots", None):
        ad.action_slot = action.slots[0]


def joint_angles(arm, rest_dirs):
    def d(n):
        pb = arm.pose.bones[n]
        return (pb.tail - pb.head).normalized()
    out = {}
    for s in "LR":
        out[f"elbow.{s}"] = math.degrees(d(f"upper_arm.{s}").angle(d(f"forearm.{s}"))) - rest_dirs[f"elbow.{s}"]
        out[f"knee.{s}"] = math.degrees(d(f"thigh.{s}").angle(d(f"shin.{s}"))) - rest_dirs[f"knee.{s}"]
        hips = arm.pose.bones["hips"].matrix.to_3x3()
        down = -(hips @ Vector((0, 1, 0)))
        side = (hips @ Vector((1, 0, 0))).normalized()
        t = d(f"thigh.{s}")
        t_s = (t - side * t.dot(side)).normalized()
        out[f"hip.{s}"] = math.degrees(down.angle(t_s)) * (1 if t_s.y <= down.y + 1e-9 or t_s.dot(Vector((0, -1, 0))) > 0 else -1)
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    anim_path, ref_path, out_dir, report_path = argv
    out_dir = os.path.abspath(out_dir)
    authoring = os.path.join(os.path.dirname(report_path), "animate-report.json")
    if os.path.exists(authoring):
        for k, v in json.load(open(authoring))["clips"].items():
            SPEEDS[k] = v["groundSpeedMps"]

    static, raw_clips, tris, _ = static_compare(anim_path, ref_path)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = FPS
    bpy.ops.import_scene.gltf(filepath=anim_path)
    arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
    mesh = next(o for o in bpy.context.scene.objects if o.type == "MESH" and o.find_armature() == arm)
    for o in [o for o in bpy.context.scene.objects if o.type == "MESH" and o is not mesh]:
        o.hide_render = True  # importer's bone-display shape
    scene, cam = setup_scene()
    actions = {a.name: a for a in bpy.data.actions}

    # Rest baseline (no action).
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    rest_co, rest_tris = evaluated(mesh)
    names = {g.index: g.name for g in mesh.vertex_groups}
    dom = np.array([max(v.groups, key=lambda g: g.weight).group if v.groups else 0 for v in mesh.data.vertices])
    dom_name = np.array([names[i] for i in dom])
    _, inv = np.unique(np.round(rest_co, 5), axis=0, return_inverse=True)
    keys = inv.reshape(-1)
    rest_pairs = set(self_intersections(rest_co, rest_tris, keys))
    n0, a0 = tri_normals_areas(rest_co, rest_tris)
    ground = float(rest_co[:, 2].min())
    rest_dirs = {}
    for s in "LR":
        def rd(n):
            b = arm.data.bones[n]
            return (b.tail_local - b.head_local).normalized()
        rest_dirs[f"elbow.{s}"] = math.degrees(rd(f"upper_arm.{s}").angle(rd(f"forearm.{s}")))
        rest_dirs[f"knee.{s}"] = math.degrees(rd(f"thigh.{s}").angle(rd(f"shin.{s}")))
    feet = {s: np.where(np.isin(dom_name, [f"foot.{s}", f"toe.{s}"]))[0] for s in "LR"}
    arms_ = np.isin(dom_name, ["hand.L", "hand.R", "forearm.L", "forearm.R"])
    legs_ = np.isin(dom_name, ["thigh.L", "thigh.R", "hips", "shin.L", "shin.R"])
    tri_dom = dom_name[rest_tris[:, 0]]

    report = {"file": os.path.abspath(anim_path), "fileSizeBytes": os.path.getsize(anim_path), "triangles": tris,
              "staticIdenticalToV3": static, "rawClips": raw_clips, "groundZ": round(ground, 4), "clips": {}}

    for name in ("Idle", "Walk", "Run"):
        if name not in actions:
            report["clips"][name] = {"present": False}
            continue
        act = actions[name]
        assign(arm, act)
        f0, f1 = (int(round(x)) for x in act.frame_range)
        frames = list(range(f0, f1 + 1))
        cos, root_dev, hips_xy, angles = [], 0.0, [], {}
        flipped_max = collapsed_max = clip_max = hand_leg_max = 0
        pen = {"L": 0.0, "R": 0.0}
        contacts = {"L": [], "R": []}
        for f in frames:
            scene.frame_set(f)
            co, tris_ = evaluated(mesh)
            cos.append(co)
            root_dev = max(root_dev, (arm.pose.bones["root"].matrix_basis - Matrix.Identity(4)).to_3x3().to_quaternion().angle,
                           arm.pose.bones["root"].matrix_basis.translation.length)
            hp = arm.pose.bones["hips"].head
            hips_xy.append((hp.x, hp.y, hp.z))
            for k, v in joint_angles(arm, rest_dirs).items():
                lo, hi = angles.get(k, (v, v))
                angles[k] = (min(lo, v), max(hi, v))
            n1, a1 = tri_normals_areas(co, tris_)
            ratio = a1 / np.maximum(a0, 1e-12)
            collapsed_max = max(collapsed_max, int((ratio < 0.25).sum()))
            # Flip test: compare with rest normal rotated by the triangle's dominant bone.
            rots = {pb.name: np.array((pb.matrix.to_3x3() @ pb.bone.matrix_local.to_3x3().inverted())) for pb in arm.pose.bones}
            expected = np.einsum("nij,nj->ni", np.array([rots[b] for b in tri_dom]), n0)
            flipped_max = max(flipped_max, int(((np.einsum("ij,ij->i", expected, n1) < 0) & (a0 > 1e-9)).sum()))
            if (f - f0) % 2 == 0:
                pairs = set(self_intersections(co, tris_, keys)) - rest_pairs
                clip_max = max(clip_max, len(pairs))
                hl = 0
                for i, j in pairs:
                    vi, vj = rest_tris[i, 0], rest_tris[j, 0]
                    if (arms_[vi] and legs_[vj]) or (arms_[vj] and legs_[vi]):
                        hl += 1
                hand_leg_max = max(hand_leg_max, hl)
            for s in "LR":
                z = co[feet[s], 2]
                zmin = float(z.min())
                pen[s] = max(pen[s], ground - zmin)
                contacts[s].append(co[feet[s]].copy())

        cos = np.array(cos)
        seam = float(np.abs(cos[-1] - cos[0]).max())
        v_end = cos[-1] - cos[-2]
        v_start = cos[1] - cos[0]
        accel_seam = float(np.linalg.norm(v_start - v_end, axis=1).max())
        accel_typ = float(max(np.linalg.norm((cos[i + 1] - cos[i]) - (cos[i] - cos[i - 1]), axis=1).max()
                              for i in range(1, len(cos) - 1)))
        speed = SPEEDS.get(name, 0.0)
        slide = {}
        for s in "LR":
            # Per-vertex: a sole vertex touching the ground (within 3 mm) in two consecutive frames should
            # move backwards (+Y) by exactly speed/FPS and not sideways. Tracking the same vertices avoids
            # the heel-to-toe jump a "lowest points" centroid would show while the foot rolls.
            errs, lat, planted = [], [], 0
            expected_dy = speed / FPS
            for i in range(len(contacts[s]) - 1):
                a, b = contacts[s][i], contacts[s][i + 1]
                on = (a[:, 2] < ground + 0.003) & (b[:, 2] < ground + 0.003)
                if not on.any():
                    continue
                planted += 1
                d = b[on] - a[on]
                errs.extend(np.abs(d[:, 1] - expected_dy).tolist())
                lat.extend(np.abs(d[:, 0]).tolist())
            slide[s] = {
                "plantedFramePairs": planted, "framesTotal": len(frames),
                "expectedBackwardMmPerFrame": round(1000 * expected_dy, 2),
                "slideErrMeanMmPerFrame": round(1000 * float(np.mean(errs)), 2) if errs else None,
                "slideErrMaxMmPerFrame": round(1000 * float(np.max(errs)), 2) if errs else None,
                "lateralMaxMmPerFrame": round(1000 * float(np.max(lat)), 2) if lat else None,
                "groundPenetrationMm": round(1000 * pen[s], 1),
            }
        hx = np.array(hips_xy)
        over = {k: hi for k, (lo, hi) in angles.items() if hi > LIMITS[k.split(".")[0]] + 0.1}
        report["clips"][name] = {
            "present": True, "frames": f"{f0}-{f1}", "durationS": round((f1 - f0) / FPS, 4),
            "loopSeamMaxVertexGapMm": round(1000 * seam, 3),
            "loopSeamVelocityJumpMm": round(1000 * accel_seam, 2), "typicalMaxPerFrameAccelMm": round(1000 * accel_typ, 2),
            "rootMaxDeviation": round(root_dev, 6),
            "hipsDriftXmm": round(1000 * float(np.ptp(hx[:, 0])), 1), "hipsDriftYmm": round(1000 * float(np.ptp(hx[:, 1])), 1),
            "hipsBobZmm": round(1000 * float(np.ptp(hx[:, 2])), 1),
            "jointRangeDeg": {k: [round(lo, 1), round(hi, 1)] for k, (lo, hi) in sorted(angles.items())},
            "jointLimitViolations": over,
            "maxFlippedTris": flipped_max, "maxCollapsedTris": collapsed_max,
            "maxNewSelfIntersections": clip_max, "maxHandOrForearmVsLegIntersections": hand_leg_max,
            "feet": slide, "groundSpeedMps": speed,
        }
        print("CLIP", name, json.dumps({k: v for k, v in report["clips"][name].items() if k not in ("jointRangeDeg", "feet")}))

        # Contact sheets at gameplay distance.
        n_shots = SHEET_FRAMES[name]
        picks = [f0 + round(i * (f1 - f0) / n_shots) for i in range(n_shots)]
        for look in ("textured", "clay"):
            if look == "textured":
                scene.render.engine = "BLENDER_EEVEE"
            else:
                scene.render.engine = "BLENDER_WORKBENCH"
                sh = scene.display.shading
                sh.light, sh.color_type, sh.single_color, sh.show_cavity = "STUDIO", "SINGLE", (0.7, 0.7, 0.7), True
            for f in picks:
                scene.frame_set(f)
                for view, az in (("side", 0.0), ("three-quarter", 315.0), ("front", 270.0)):
                    place_camera(cam, Vector((0, 0, 0)), 4.2, az, 5.0)
                    render(scene, os.path.join(out_dir, look, f"{name}_f{f:03d}_{view}.png"), (420, 560))

    with open(report_path, "w") as f:
        json.dump(report, f, indent=1)
    print("STATIC", json.dumps(static))
    print("RAW", json.dumps(raw_clips))
    print("VALIDATE_OK")


if __name__ == "__main__":
    main()
