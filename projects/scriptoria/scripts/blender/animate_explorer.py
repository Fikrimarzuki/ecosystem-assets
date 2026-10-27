"""M7.5c.2b — author Idle / Walk / Run for the Explorer v3 rig and export an animated GLB.

Usage:
  blender -b --factory-startup --python scripts/blender/animate_explorer.py -- \
      <rig-v3.blend> <out.glb> <out.blend> <report.json>

How the clips are made
  * Every clip is a periodic function of phase p in [0, 1). One key per frame
    for frames 0..N with p = f / N, so frame N is identical to frame 0 and the
    loop is seamless by construction (no hand-matched end keys).
  * Poses are built as world-space bone matrices, then converted to local
    rotation keys (plus hips translation) — no constraints, drivers or helper
    bones, so the GLB only contains plain TRS channels Babylon can play.
  * Legs: analytic two-bone IK. Each ankle follows a planned path; a planted
    foot moves backwards along the ground at the clip's constant ground speed
    (in-place locomotion), which is what keeps feet from sliding once the game
    moves the character at that speed. Heel strike pivots on the heel, heel-off
    pivots on the toe joint with the toe bone kept flat.
  * Arms, spine and head: forward kinematics within the approved ranges
    (elbow <= 90 deg, knee <= 100 deg, hip <= 55 deg). The generator measures
    the angles it produced and fails loudly if a limit is exceeded.
  * In place: the root bone is never keyed; hips only move vertically and a
    few centimetres sideways for weight shift (no forward travel, no yaw drift).
Mesh, UVs, materials, textures, skeleton and weights are not touched.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

FPS = 30
FORWARD = Vector((0, -1, 0))
UP = Vector((0, 0, 1))
LIMITS = {"elbow": 90.0, "knee": 100.0, "hip": 55.0}
REACH_MARGIN = 0.995

CLIPS = {
    "Idle": {"frames": 105},  # 3.50 s
    "Walk": {"frames": 30},   # 1.00 s
    "Run": {"frames": 22},    # 0.733 s
}

# Gait parameters (metres / degrees). Forward is −Y.
WALK = dict(duty=0.62, y_front=-0.30, y_back=0.32, foot_x=0.12, lift=0.075, heel_strike=12.0, heel_off=22.0,
            hips_z=-0.012, bob=0.020, sway=0.018, pelvis_yaw=5.0, pelvis_roll=2.5, lean=5.0, chest_yaw=-7.0,
            arm_down=34.0, arm_out=3.0, arm_swing=17.0, elbow=16.0, elbow_swing=8.0)
RUN = dict(duty=0.36, y_front=-0.25, y_back=0.38, foot_x=0.11, lift=0.19, heel_strike=4.0, heel_off=28.0,
           hips_z=-0.085, bob=0.030, sway=0.012, pelvis_yaw=8.0, pelvis_roll=3.0, lean=15.0, chest_yaw=-11.0,
           arm_down=28.0, arm_out=6.0, arm_swing=34.0, elbow=74.0, elbow_swing=10.0)
IDLE = dict(foot_x=0.16, foot_y=0.02, hips_z=0.004, sway=0.012, pelvis_roll=1.4, breathe=1.3,
            arm_down=36.0, arm_out=5.0, elbow=13.0, head_yaw=2.5)


def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def hermite(p0, p1, m0, m1, t):
    t2, t3 = t * t, t * t * t
    return (2 * t3 - 3 * t2 + 1) * p0 + (t3 - 2 * t2 + t) * m0 + (-2 * t3 + 3 * t2) * p1 + (t3 - t2) * m1


def rot_about(axis, degrees):
    return Matrix.Rotation(math.radians(degrees), 4, axis.normalized())


class Pose:
    """World-space pose of every bone, built from the rest matrices."""

    def __init__(self, rig):
        self.rig = rig
        self.m = {n: rig.rest[n].copy() for n in rig.rest}

    def head(self, n):
        return self.m[n].translation.copy()

    def tail(self, n):
        return self.m[n] @ Vector((0, self.rig.length[n], 0))

    def direction(self, n):
        return (self.tail(n) - self.head(n)).normalized()

    def transform_subtree(self, n, mat):
        for b in self.rig.subtree[n]:
            self.m[b] = mat @ self.m[b]

    def rotate(self, n, axis, degrees, pivot=None):
        c = self.head(n) if pivot is None else pivot
        self.transform_subtree(n, Matrix.Translation(c) @ rot_about(axis, degrees) @ Matrix.Translation(-c))

    def rotate_expect(self, n, axis, degrees, expect):
        """Rotate so the bone tip moves the expected way (sign chosen by test, independent of side)."""
        before = self.tail(n)
        saved = {b: self.m[b].copy() for b in self.rig.subtree[n]}
        for sign in (1, -1):
            self.rotate(n, axis, sign * degrees)
            d = self.tail(n) - before
            ok = {"fwd": d.y < 0, "back": d.y > 0, "down": d.z < 0, "up": d.z > 0,
                  "out": abs(self.tail(n).x) > abs(before.x)}[expect]
            if ok or degrees == 0:
                return
            for b, mm in saved.items():
                self.m[b] = mm.copy()

    def set_bone(self, n, head, rot3):
        self.m[n] = Matrix.Translation(head) @ rot3.to_4x4()


class Rig:
    def __init__(self, arm):
        self.arm = arm
        self.rest = {b.name: arm.matrix_world @ b.matrix_local for b in arm.data.bones}
        self.length = {b.name: b.length for b in arm.data.bones}
        self.parent = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}
        self.subtree = {b.name: [b.name] + [c.name for c in b.children_recursive] for b in arm.data.bones}
        self.order = [b.name for b in arm.data.bones]  # parents before children


def leg_ik(pose, side, ankle, foot_pitch_down, toe_flat=True):
    """Place thigh/shin/foot/toe so the ankle reaches `ankle`; knee bends forward. Returns (reached, ankle_error_m)."""
    rig = pose.rig
    th, sh, ft, to = f"thigh.{side}", f"shin.{side}", f"foot.{side}", f"toe.{side}"
    hip = pose.head(th)
    l1, l2 = rig.length[th], rig.length[sh]
    to_ankle = ankle - hip
    d = to_ankle.length
    reach = REACH_MARGIN * (l1 + l2)
    reached = d <= reach
    d = min(d, reach)
    u = to_ankle.normalized()
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    fwd = (FORWARD - u * FORWARD.dot(u)).normalized()
    knee = hip + u * a + fwd * h
    ank = hip + u * d

    def oriented(name, new_dir):
        rest = rig.rest[name].to_3x3()
        rest_dir = rest.col[1].normalized()
        return rest_dir.rotation_difference(new_dir).to_matrix() @ rest

    pose.set_bone(th, hip, oriented(th, (knee - hip).normalized()))
    pose.set_bone(sh, knee, oriented(sh, (ank - knee).normalized()))
    foot_rot = rot_about(Vector((1, 0, 0)), foot_pitch_down).to_3x3() @ rig.rest[ft].to_3x3()
    pose.set_bone(ft, ank, foot_rot)
    toe_rot = rig.rest[to].to_3x3() if toe_flat else foot_rot @ (rig.rest[ft].to_3x3().inverted() @ rig.rest[to].to_3x3())
    pose.set_bone(to, pose.tail(ft), toe_rot)
    return reached, (ankle - ank).length


class FootGeo:
    """Rest-pose pivots of one foot: heel (bottom-back of the boot) and toe joint."""

    def __init__(self, rig, mesh, side):
        self.ankle = rig.rest[f"foot.{side}"].translation.copy()
        self.toe_joint = rig.rest[f"toe.{side}"].translation.copy()
        names = {g.index: g.name for g in mesh.vertex_groups}
        pts = []
        for v in mesh.data.vertices:
            if v.groups and names[max(v.groups, key=lambda g: g.weight).group] in (f"foot.{side}", f"toe.{side}"):
                pts.append(mesh.matrix_world @ v.co)
        self.ground = min(p.z for p in pts)
        low = [p for p in pts if p.z < self.ground + 0.012]
        heel_y = max(p.y for p in low)
        self.heel = Vector((self.ankle.x, heel_y, self.ground))

    def ankle_for(self, contact_y, x, pitch_down):
        """Ankle position for a planted foot whose pivot sits at `contact_y` on the ground."""
        r = rot_about(Vector((1, 0, 0)), pitch_down).to_3x3()
        if pitch_down >= 0:  # heel off: pivot on the toe joint, which stays put
            pivot_rest = self.toe_joint
        else:                # heel strike (toes up): pivot on the heel
            pivot_rest = self.heel
        off = self.ankle - pivot_rest
        pivot = Vector((x, contact_y + (pivot_rest.y - self.ankle.y), pivot_rest.z))
        return pivot + r @ off


def gait_foot(fg, g, phase, x, period_s):
    """Ankle target + pitch for a locomotion foot at its own phase (0 = heel strike)."""
    duty = g["duty"]
    yF, yB = g["y_front"], g["y_back"]
    if phase < duty:
        s = phase / duty
        y = yF + (yB - yF) * s
        pitch = -g["heel_strike"] * (1 - smoothstep(0.0, 0.18, s)) + g["heel_off"] * smoothstep(0.68, 1.0, s)
        return fg.ankle_for(y, x, pitch), pitch, True
    s = (phase - duty) / (1 - duty)
    start = fg.ankle_for(yB, x, g["heel_off"])
    end = fg.ankle_for(yF, x, -g["heel_strike"])
    # Leave and arrive at the stance foot's ground speed (per unit s), so velocity is continuous at toe-off/heel-strike.
    v = (yB - yF) / duty * (1 - duty)
    y = hermite(start.y, end.y, v * 0.5, v * 0.5, s)
    z = start.z + (end.z - start.z) * smoothstep(0, 1, s) + g["lift"] * math.sin(math.pi * s) ** 1.2
    pitch = g["heel_off"] + (-g["heel_strike"] - g["heel_off"]) * smoothstep(0.0, 1.0, s)
    pitch -= 10.0 * math.sin(math.pi * s)  # toes up through mid-swing for clearance
    return Vector((x, y, z)), pitch, False


def build_arms(pose, side, down, out, swing, elbow, wrist=0.0):
    ua, fa, hd = f"upper_arm.{side}", f"forearm.{side}", f"hand.{side}"
    pose.rotate_expect(ua, FORWARD, down, "down")
    pose.rotate_expect(ua, FORWARD, -out if out else 0, "out") if out else None
    swing_axis = pose.direction(ua).cross(FORWARD)
    pose.rotate_expect(ua, swing_axis, abs(swing), "fwd" if swing >= 0 else "back")
    pose.rotate_expect(fa, pose.direction(fa).cross(FORWARD), elbow, "fwd")
    if wrist:
        pose.rotate_expect(hd, pose.direction(hd).cross(FORWARD), abs(wrist), "fwd" if wrist >= 0 else "back")


def torso(pose, hips_offset, pelvis_yaw, pelvis_roll, lean, chest_yaw, chest_pitch=0.0, head_yaw=0.0, head_pitch=0.0):
    pose.transform_subtree("hips", Matrix.Translation(hips_offset))
    pose.rotate("hips", UP, pelvis_yaw)
    pose.rotate("hips", FORWARD, pelvis_roll)
    pose.rotate("spine", Vector((1, 0, 0)), lean * 0.6)
    pose.rotate("chest", Vector((1, 0, 0)), lean * 0.4 + chest_pitch)
    pose.rotate("spine", UP, chest_yaw * 0.4)
    pose.rotate("chest", UP, chest_yaw * 0.6)
    # Keep the head level and looking ahead: undo accumulated pitch/yaw, then add the clip's own.
    pose.rotate("neck", Vector((1, 0, 0)), -(lean + chest_pitch) * 0.5)
    pose.rotate("head", Vector((1, 0, 0)), -(lean + chest_pitch) * 0.5 + head_pitch)
    pose.rotate("neck", UP, -(pelvis_yaw + chest_yaw) * 0.5)
    pose.rotate("head", UP, -(pelvis_yaw + chest_yaw) * 0.5 + head_yaw)
    pose.rotate("chest", FORWARD, -pelvis_roll * 0.8)


def pose_idle(rig, feet, p):
    g = IDLE
    w = 2 * math.pi * p
    pose = Pose(rig)
    breathe = math.sin(w * 1.0)  # one breath per 3.5 s loop
    shift = math.sin(w)          # one weight shift per loop
    torso(pose, Vector((g["sway"] * shift, 0, g["hips_z"] + 0.004 * breathe)), 0.0, g["pelvis_roll"] * shift,
          1.5, 0.0, chest_pitch=-g["breathe"] * breathe, head_yaw=g["head_yaw"] * math.sin(w + 1.0))
    for side, sx in (("L", 1), ("R", -1)):
        pose.rotate_expect(f"shoulder.{side}", FORWARD, 1.0 + 0.8 * breathe, "up")
        build_arms(pose, side, g["arm_down"], g["arm_out"], 2.0 * shift * sx, g["elbow"] + 2.0 * breathe)
    stats = []
    for side, sx in (("L", 1), ("R", -1)):
        fg = feet[side]
        ankle = fg.ankle_for(g["foot_y"], sx * g["foot_x"], 0.0)
        stats.append(leg_ik(pose, side, ankle, 0.0))
    return pose, stats


def pose_gait(rig, feet, p, g, period_s):
    w = 2 * math.pi * p
    pose = Pose(rig)
    bob = -math.cos(2 * w) if g is WALK else math.cos(2 * w - 2 * math.pi * 2 * 0.43)
    torso(pose, Vector((g["sway"] * math.sin(w), 0, g["hips_z"] + g["bob"] * bob)),
          g["pelvis_yaw"] * math.cos(w), -g["pelvis_roll"] * math.sin(w), g["lean"], g["chest_yaw"] * math.cos(w))
    stats = []
    for side, sx, off in (("L", 1, 0.0), ("R", -1, 0.5)):
        phase = (p + off) % 1.0
        ankle, pitch, _ = gait_foot(feet[side], g, phase, sx * g["foot_x"], period_s)
        stats.append(leg_ik(pose, side, ankle, pitch))
    # Arms swing opposite to the legs: right arm forward while the left foot is forward (p = 0).
    for side, sgn in (("R", 1), ("L", -1)):
        swing = g["arm_swing"] * sgn * math.cos(w)
        elbow = g["elbow"] + g["elbow_swing"] * max(0.0, sgn * math.cos(w))
        build_arms(pose, side, g["arm_down"], g["arm_out"], swing, elbow)
    return pose, stats


def angle(a, b):
    return math.degrees(a.angle(b))


def joint_angles(pose, rest_pose):
    out = {}
    for side in "LR":
        out[f"elbow.{side}"] = angle(pose.direction(f"upper_arm.{side}"), pose.direction(f"forearm.{side}")) - \
            angle(rest_pose.direction(f"upper_arm.{side}"), rest_pose.direction(f"forearm.{side}"))
        out[f"knee.{side}"] = angle(pose.direction(f"thigh.{side}"), pose.direction(f"shin.{side}")) - \
            angle(rest_pose.direction(f"thigh.{side}"), rest_pose.direction(f"shin.{side}"))
        # Hip flexion: thigh angle from the pelvis' down axis, measured in the pelvis' sagittal plane.
        pelvis = pose.m["hips"].to_3x3()
        down = -(pelvis @ Vector((0, 1, 0)))  # hips bone points up (local Y)
        side_axis = (pelvis @ Vector((1, 0, 0))).normalized()
        t = pose.direction(f"thigh.{side}")
        t_s = (t - side_axis * t.dot(side_axis)).normalized()
        fwd = side_axis.cross(down).normalized()
        sign = 1 if t_s.dot(fwd) * fwd.dot(FORWARD) >= 0 else -1
        out[f"hip.{side}"] = sign * angle(down, t_s)
    return out


def key_pose(rig, pose, frame, prev_q):
    arm = rig.arm
    for n in rig.order:
        pb = arm.pose.bones[n]
        rest = rig.rest[n]
        par = rig.parent[n]
        if par is None:
            basis = rest.inverted() @ pose.m[n]
        else:
            basis = (rig.rest[par].inverted() @ rest).inverted() @ pose.m[par].inverted() @ pose.m[n]
        q = basis.to_quaternion()
        if n in prev_q and prev_q[n].dot(q) < 0:
            q.negate()
        prev_q[n] = q
        if n == "root":
            continue  # root is never animated: no root motion
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = q
        pb.keyframe_insert("rotation_quaternion", frame=frame)
        if n == "hips":
            pb.location = basis.translation
            pb.keyframe_insert("location", frame=frame)
        else:
            pb.location = (0, 0, 0)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    src_blend, out_glb, out_blend, report_path = argv
    bpy.ops.wm.open_mainfile(filepath=src_blend)
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    mesh = next(o for o in bpy.data.objects if o.type == "MESH")
    rig = Rig(arm)
    feet = {s: FootGeo(rig, mesh, s) for s in "LR"}
    rest_pose = Pose(rig)
    arm.animation_data_create()
    report = {"fps": FPS, "groundZ": round(feet["L"].ground, 4), "clips": {}}

    for name, spec in CLIPS.items():
        n = spec["frames"]
        action = bpy.data.actions.new(name)
        action.use_fake_user = True
        arm.animation_data.action = action
        prev_q = {}
        maxima = {}
        unreached = 0
        max_err = 0.0
        for f in range(n + 1):
            p = (f % n) / n  # frame n == frame 0 exactly
            if name == "Idle":
                pose, stats = pose_idle(rig, feet, p)
            else:
                pose, stats = pose_gait(rig, feet, p, WALK if name == "Walk" else RUN, n / FPS)
            for reached, err in stats:
                unreached += not reached
                max_err = max(max_err, err)
            for k, v in joint_angles(pose, rest_pose).items():
                lo, hi = maxima.get(k, (v, v))
                maxima[k] = (min(lo, v), max(hi, v))
            key_pose(rig, pose, f, prev_q)
        for fc in getattr(action, "fcurves", []):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
        arm.animation_data.action = None
        track = arm.animation_data.nla_tracks.new()
        track.name = name
        strip = track.strips.new(name, 0, action)
        strip.name = name
        track.mute = False

        g = WALK if name == "Walk" else RUN if name == "Run" else None
        speed = None
        if g:
            speed = (g["y_back"] - g["y_front"]) / (g["duty"] * n / FPS)
        report["clips"][name] = {
            "frames": n, "durationS": round(n / FPS, 4), "groundSpeedMps": round(speed, 3) if speed else 0.0,
            "stepLengthM": round(speed * n / FPS / 2, 3) if speed else 0.0,
            "jointRangeDeg": {k: [round(lo, 1), round(hi, 1)] for k, (lo, hi) in sorted(maxima.items())},
            "ikTargetsOutOfReach": unreached, "maxAnkleTargetErrorM": round(max_err, 4),
        }
        over = []
        for k, (lo, hi) in maxima.items():
            kind = k.split(".")[0]
            if hi > LIMITS[kind] + 0.05:
                over.append(f"{name}:{k}={hi:.1f}")
        if over:
            print("RANGES", json.dumps(report["clips"]))
            raise RuntimeError("joint limit exceeded: " + ", ".join(over))

    scene.frame_start, scene.frame_end = 0, max(s["frames"] for s in CLIPS.values())
    for pb in arm.pose.bones:
        pb.rotation_quaternion = Quaternion()
        pb.location = (0, 0, 0)

    os.makedirs(os.path.dirname(out_glb), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    arm.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=out_glb, export_format="GLB", use_selection=True, export_yup=True,
        export_apply=False, export_texcoords=True, export_normals=True, export_tangents=False,
        export_materials="EXPORT", export_image_format="AUTO", export_skins=True, export_morph=False,
        export_draco_mesh_compression_enable=False,
        export_animations=True, export_animation_mode="NLA_TRACKS", export_anim_slide_to_zero=True,
        export_optimize_animation_size=False, export_bake_animation=False,
    )
    bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=True)
    report["glb"] = out_glb
    report["glbSizeBytes"] = os.path.getsize(out_glb)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=1)
    print("ANIMATE_OK", json.dumps(report["clips"]))


main()
