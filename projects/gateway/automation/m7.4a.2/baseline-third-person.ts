import { groundHeight, PLAYER, type FirstPersonPlayer, type GroundPoint, type NavigationBounds, type WorldNavigation } from "./first-person";

export const THIRD_PERSON = { distance: .68, targetHeight: .35, radius: .035, pitchMin: -.65, pitchMax: .10, pitch: -.22, followRate: 12, followSpeed: 2, fov: 65, closeFov: 75, fovSpeed: 20, stride: .17 };
// Camera presentation only; Latest’s rear beam and Platforms’ facing roofs need a higher aim; FPS spawns stay unchanged.
const worldTargetHeight: Partial<Record<WorldNavigation["worldId"], number>> = { latest: .47, platforms: .435 };
export const thirdPersonTargetHeight = (nav: WorldNavigation) => worldTargetHeight[nav.worldId] ?? THIRD_PERSON.targetHeight;
const turn = (angle: number) => Math.atan2(Math.sin(angle), Math.cos(angle));
const axes = ["x", "y", "z"] as const;

export type ThirdPersonPose = { leftLeg: number; rightLeg: number; leftArm: number; rightArm: number; breath: number; leftFootZ: number; rightFootZ: number; leftFootY: number; rightFootY: number };
const poseKeys = ["leftLeg", "rightLeg", "leftArm", "rightArm", "breath", "leftFootZ", "rightFootZ", "leftFootY", "rightFootY"] as const;
const emptyPose = (): ThirdPersonPose => ({ leftLeg: 0, rightLeg: 0, leftArm: 0, rightArm: 0, breath: 0, leftFootZ: 0, rightFootZ: 0, leftFootY: 0, rightFootY: 0 });

function footPose(out: ThirdPersonPose, phase: number, moving: boolean, reduced: boolean, side: "left" | "right") {
  const cycle = phase % (Math.PI * 2), extent = THIRD_PERSON.stride / 4;
  const travel = !moving || reduced ? 0 : cycle < Math.PI ? -extent + 2 * extent * cycle / Math.PI : extent * Math.cos(cycle - Math.PI);
  const lift = !moving || reduced || cycle < Math.PI ? 0 : Math.sin(cycle - Math.PI) * .015;
  out[side === "left" ? "leftFootZ" : "rightFootZ"] = travel;
  out[side === "left" ? "leftFootY" : "rightFootY"] = lift;
}

/** Continuous presentation only: gait follows displacement, never held keys against a wall. */
export class ThirdPersonCharacter {
  yaw = 0; phase = 0; idle = 0; speed = 0;
  reset(yaw: number) { this.yaw = yaw; this.phase = 0; this.idle = 0; this.speed = 0; }
  advance(dx: number, dz: number, delta: number, reduced: boolean) {
    const dt = Number.isFinite(delta) ? Math.max(0, Math.min(delta, .1)) : 0, distance = Math.hypot(dx, dz);
    this.speed = dt > 0 ? distance / dt : 0;
    if (distance > 1e-7) {
      const facing = Math.atan2(-dx, -dz);
      this.yaw += turn(facing - this.yaw) * (reduced ? 1 : 1 - Math.exp(-18 * dt));
      this.phase = (this.phase + distance / THIRD_PERSON.stride * Math.PI * 2) % (Math.PI * 2);
    } else if (!reduced) this.idle += dt;
  }
  pose(reduced: boolean, out: ThirdPersonPose = emptyPose()) {
    const moving = this.speed > .0001, swing = moving ? Math.cos(this.phase) * (reduced ? .10 : .48) : reduced ? 0 : Math.sin(this.idle * 1.5) * .025;
    out.leftLeg = moving ? swing : 0; out.rightLeg = -out.leftLeg;
    out.leftArm = -swing; out.rightArm = swing;
    out.breath = reduced ? 0 : moving ? Math.abs(Math.sin(this.phase)) * .001 : Math.sin(this.idle * 1.8) * .0015;
    // A half-cycle stance counters half a stride of root travel. The other half
    // returns the foot gently above the floor; the mesh compensates its short leg's rotation.
    footPose(out, this.phase, moving, reduced, "left"); footPose(out, this.phase + Math.PI, moving, reduced, "right");
    return out;
  }
}

/** Rendered pose only: ease to the neutral goal without advancing a blocked gait. */
export class ThirdPersonAnimation {
  readonly pose = emptyPose();
  private readonly target = emptyPose();
  reset() { for (const key of poseKeys) this.pose[key] = 0; }
  update(character: ThirdPersonCharacter, delta: number, reduced: boolean) {
    const dt = Number.isFinite(delta) ? Math.max(0, Math.min(delta, .1)) : 0;
    character.pose(reduced, this.target);
    const blend = reduced ? 1 : 1 - Math.exp(-20 * dt);
    for (const key of poseKeys) this.pose[key] += (this.target[key] - this.pose[key]) * blend;
    return this.pose;
  }
}

/** Conservative sphere clearance along the whole boom, including near-plane padding. */
export function cameraBoomFraction(from: GroundPoint, to: GroundPoint, obstacles: NavigationBounds[], radius = THIRD_PERSON.radius) {
  let fraction = 1;
  for (const box of obstacles) {
    let start = 0, end = 1;
    if (box.planes) {
      // Cached unit face normals retain the rock's empty corners; offset each plane
      // by the camera sphere radius, matching the existing convex sight boundary.
      for (const plane of box.planes) {
        const origin = plane.x * from.x + plane.y * from.y + plane.z * from.z + plane.constant - radius;
        const delta = plane.x * (to.x - from.x) + plane.y * (to.y - from.y) + plane.z * (to.z - from.z);
        if (Math.abs(delta) < 1e-10) { if (origin > 1e-8) { end = -1; break; } }
        else if (delta < 0) start = Math.max(start, -origin / delta);
        else end = Math.min(end, -origin / delta);
        if (start > end) break;
      }
    } else for (const axis of axes) {
      const delta = to[axis] - from[axis], min = box.min[axis] - radius, max = box.max[axis] + radius;
      if (Math.abs(delta) < 1e-10) { if (from[axis] < min || from[axis] > max) { end = -1; break; } }
      else { const a = (min - from[axis]) / delta, b = (max - from[axis]) / delta;
        start = Math.max(start, Math.min(a, b)); end = Math.min(end, Math.max(a, b)); }
      if (start > end) break;
    }
    if (start <= end && end >= 0) fraction = Math.min(fraction, Math.max(0, start - .01));
  }
  return fraction;
}
const ceilingCache = new WeakMap<WorldNavigation, NavigationBounds[]>();
function walkableCeilings(nav: WorldNavigation) {
  let ceilings = ceilingCache.get(nav);
  if (!ceilings) {
    // Roofs entirely covered by a player's padded building body cannot be walked under.
    // Anticipate only true overhead passages, without suppressing front-facade views.
    ceilings = nav.obstacles.filter(box => !nav.obstacles.some(base => base !== box
      && base.min.y < nav.groundY + PLAYER.height && base.max.y > nav.groundY + PLAYER.step
      && base.min.x - PLAYER.radius <= box.min.x && base.max.x + PLAYER.radius >= box.max.x
      && base.min.z - PLAYER.radius <= box.min.z && base.max.z + PLAYER.radius >= box.max.z));
    ceilingCache.set(nav, ceilings);
  }
  return ceilings;
}
const length = (a: GroundPoint, b: GroundPoint) => Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);

// Camera presentation only. Five low envelope probes cover the imported boots'
// width/depth; two torso probes prioritize a readable body when a boot intersects
// a prop. Reuse cached navigation bounds, never skin or raycast the whole scene.
const visibilityProbes = [[-.065, -.05, .01], [.065, -.05, .01], [-.065, .05, .01], [.065, .05, .01], [0, 0, .01], [0, 0, .15], [0, 0, .25]] as const;
const visibilityViews = [
  [0, -.16, THIRD_PERSON.distance], [-.25, 0, THIRD_PERSON.distance], [.25, 0, THIRD_PERSON.distance],
  [-.50, 0, THIRD_PERSON.distance], [.50, 0, THIRD_PERSON.distance], [0, -.32, THIRD_PERSON.distance],
  [0, -.16, .55], [-.50, -.16, THIRD_PERSON.distance], [.50, -.16, THIRD_PERSON.distance],
] as const;

/** Local follow adapter owned by the existing sole UniverseCamera writer. */
export class ThirdPersonCamera {
  position: GroundPoint = { x: 0, y: 0, z: 0 };
  target: GroundPoint = { x: 0, y: 0, z: 0 };
  settled = true;
  fov = THIRD_PERSON.fov;
  private initialized = false;
  private visibilityView = -1;
  private clearSeconds = 0;
  private readonly probes = visibilityProbes.map(() => ({ x: 0, y: 0, z: 0 }));
  private readonly candidate: GroundPoint = { x: 0, y: 0, z: 0 };
  reset() { this.initialized = false; this.settled = true; this.fov = THIRD_PERSON.fov; this.visibilityView = -1; this.clearSeconds = 0; }
  update(player: Pick<FirstPersonPlayer, "position" | "yaw" | "pitch">, nav: WorldNavigation, delta: number, reduced: boolean, checkVisibility = true) {
    const dt = Number.isFinite(delta) ? Math.max(0, Math.min(delta, .1)) : 0;
    const pivot = { x: player.position.x, y: player.position.y + thirdPersonTargetHeight(nav), z: player.position.z };
    // A player may fit beneath a roof overhang while the usual above-helmet aim does not.
    // Lower only the camera pivot below that ceiling; player height/support never changes.
    for (const box of nav.obstacles) {
      if (box.min.y < player.position.y + PLAYER.height - .0001) continue;
      if (pivot.x >= box.min.x - THIRD_PERSON.radius && pivot.x <= box.max.x + THIRD_PERSON.radius
        && pivot.z >= box.min.z - THIRD_PERSON.radius && pivot.z <= box.max.z + THIRD_PERSON.radius
        && pivot.y >= box.min.y - THIRD_PERSON.radius) pivot.y = box.min.y - THIRD_PERSON.radius - .002;
    }
    const pitch = Math.max(THIRD_PERSON.pitchMin, Math.min(THIRD_PERSON.pitchMax, player.pitch));
    const rear = { x: pivot.x + Math.sin(player.yaw) * Math.cos(pitch) * THIRD_PERSON.distance,
      y: pivot.y - Math.sin(pitch) * THIRD_PERSON.distance,
      z: pivot.z + Math.cos(player.yaw) * Math.cos(pitch) * THIRD_PERSON.distance };
    rear.y = Math.max(rear.y, groundHeight(nav, rear.x, rear.z) + THIRD_PERSON.radius);
    const clearRear = cameraBoomFraction(pivot, rear, nav.obstacles) === 1
      && [.5, .8].some(height => cameraBoomFraction(rear, { ...player.position, y: player.position.y + PLAYER.height * height }, nav.obstacles, 0) === 1);
    // Anticipate an overhead edge before the boom enters its footprint. A radial
    // projection alone would collapse an above-roof view in one frame at that edge.
    let ceiling = Infinity;
    for (const box of walkableCeilings(nav)) {
      if (box.min.y < player.position.y + PLAYER.height - .0001) continue;
      const dx = Math.max(box.min.x - THIRD_PERSON.radius - pivot.x, 0, pivot.x - box.max.x - THIRD_PERSON.radius);
      const dz = Math.max(box.min.z - THIRD_PERSON.radius - pivot.z, 0, pivot.z - box.max.z - THIRD_PERSON.radius);
      // Prepare the smoothed camera throughout a nearby overhead passage, including turns.
      // Immediate entry/reduced placement keeps a clear outside-footprint rear view.
      if (Math.hypot(dx, dz) > 0 && (!this.initialized || reduced || clearRear)) continue;
      const proximity = Math.min(1, Math.hypot(dx, dz) / .36), ease = proximity * proximity * (3 - 2 * proximity);
      if (proximity < 1) {
        const safe = box.min.y - THIRD_PERSON.radius - .012;
        ceiling = Math.min(ceiling, safe + (Math.max(pivot.y + .50, this.position.y) - safe) * ease);
      }
    }
    let desired = rear;
    const clear = (point: GroundPoint, limitCeiling = true) => {
      if (limitCeiling) point = { ...point, y: Math.min(point.y, ceiling) };
      const t = cameraBoomFraction(pivot, point, nav.obstacles);
      return { x: pivot.x + (point.x - pivot.x) * t, y: pivot.y + (point.y - pivot.y) * t, z: pivot.z + (point.z - pivot.z) * t };
    };
    desired = clear(desired);
    // Ease toward the clear overhead/level view before a rear obstruction crowds the helmet.
    // A continuous blend avoids switching camera destinations abruptly at a single distance.
    const rearLength = length(pivot, desired);
    if (rearLength < .45) {
      let alternate = desired;
      const overhead = clear({ x: pivot.x, y: pivot.y + .50, z: pivot.z });
      if (length(pivot, overhead) > rearLength) alternate = overhead;
      const level = clear({ x: pivot.x + Math.sin(player.yaw) * THIRD_PERSON.distance,
        y: pivot.y, z: pivot.z + Math.cos(player.yaw) * THIRD_PERSON.distance });
      if (length(pivot, alternate) < .30 && length(pivot, level) > length(pivot, alternate)) alternate = level;
      const weight = Math.min(1, (.45 - rearLength) / .15), blend = weight * weight * (3 - 2 * weight);
      desired = clear({ x: desired.x + (alternate.x - desired.x) * blend,
        y: desired.y + (alternate.y - desired.y) * blend, z: desired.z + (alternate.z - desired.z) * blend });
    }

    if (checkVisibility) {
      let active = 0, total = 0;
      const sin = Math.sin(player.yaw), cos = Math.cos(player.yaw);
      for (let i = 0; i < this.probes.length; i++) {
        const [side, depth, height] = visibilityProbes[i], probe = this.probes[i];
        probe.x = player.position.x + cos * side + sin * depth;
        probe.y = player.position.y + height;
        probe.z = player.position.z - sin * side + cos * depth;
        // Camera changes cannot reveal vertices inside a solid without seeing
        // through it. Ignore impossible envelope points, retaining torso checks.
        if (cameraBoomFraction(probe, probe, nav.obstacles, 0) === 1) { active |= 1 << i; total += i < 5 ? 1 : 2; }
      }
      const score = (point: GroundPoint) => {
        let visible = 0;
        for (let i = 0; i < this.probes.length; i++) if ((active & (1 << i)) && cameraBoomFraction(point, this.probes[i], nav.obstacles, 0) === 1) visible += i < 5 ? 1 : 2;
        return visible;
      };
      const view = (index: number) => {
        const [yawOffset, pitchOffset, distance] = visibilityViews[index];
        const angle = Math.max(THIRD_PERSON.pitchMin, pitch + pitchOffset), yaw = player.yaw + yawOffset;
        this.candidate.x = pivot.x + Math.sin(yaw) * Math.cos(angle) * distance;
        this.candidate.z = pivot.z + Math.cos(yaw) * Math.cos(angle) * distance;
        this.candidate.y = Math.max(pivot.y - Math.sin(angle) * distance, groundHeight(nav, this.candidate.x, this.candidate.z) + THIRD_PERSON.radius);
        return clear(this.candidate);
      };
      const preferredScore = score(desired);
      if (preferredScore === total) {
        this.clearSeconds += dt;
        if (this.visibilityView >= 0 && this.initialized && !reduced && this.clearSeconds < .30) {
          const held = view(this.visibilityView);
          if (length(pivot, held) >= .48 && score(held) === total) desired = held;
          else this.visibilityView = -1;
        } else this.visibilityView = -1;
      } else {
        this.clearSeconds = 0;
        let best = preferredScore, selected = -1;
        if (this.visibilityView >= 0) {
          const held = view(this.visibilityView), visible = score(held);
          if (length(pivot, held) >= .48 && visible >= best) { best = visible; selected = this.visibilityView; desired = held; }
        }
        for (let i = 0; i < visibilityViews.length && best < total; i++) {
          if (i === selected) continue;
          const candidate = view(i);
          if (length(pivot, candidate) < .48) continue; // Never trade obstruction for a crowded/unsafe zoom.
          const visible = score(candidate);
          if (visible > best) { best = visible; selected = i; desired = candidate; }
        }
        this.visibilityView = selected;
      }
    }

    // Bound presentation travel as well as exponential following when an obstacle changes the desired view.
    const blend = !this.initialized || reduced ? 1 : Math.min(1 - Math.exp(-THIRD_PERSON.followRate * dt),
      THIRD_PERSON.followSpeed * dt / Math.max(length(this.position, desired), 1e-9));
    const project = (amount: number) => {
      const candidate = { x: this.position.x + (desired.x - this.position.x) * amount,
        y: this.position.y + (desired.y - this.position.y) * amount, z: this.position.z + (desired.z - this.position.z) * amount };
      candidate.y = Math.max(candidate.y, groundHeight(nav, candidate.x, candidate.z) + THIRD_PERSON.radius);
      return clear(candidate, false);
    };
    let next = project(blend);
    // Retract along the current clear boom before changing sides at a roof/wall corner.
    // This avoids a large radial projection when a tiny interpolated step grazes a new face.
    if (this.initialized && !reduced && length(this.position, next) > THIRD_PERSON.followSpeed * dt + .0001) {
      const inward = Math.min(1, THIRD_PERSON.followSpeed * dt / Math.max(length(this.position, pivot), 1e-9));
      next = clear({ x: this.position.x + (pivot.x - this.position.x) * inward,
        y: this.position.y + (pivot.y - this.position.y) * inward, z: this.position.z + (pivot.z - this.position.z) * inward }, false);
    }
    this.position = next;
    // Collision projects each smoothed step; do not jump directly to an overhead/level fallback.
    // Widen only a close retracted view: the position, aim and central interaction ray stay unchanged.
    const close = Math.max(0, Math.min(1, (.55 - length(pivot, this.position)) / .35));
    const desiredFov = THIRD_PERSON.fov + (THIRD_PERSON.closeFov - THIRD_PERSON.fov) * close * close * (3 - 2 * close);
    const fovStep = (desiredFov - this.fov) * (1 - Math.exp(-10 * dt));
    this.fov += !this.initialized || reduced ? desiredFov - this.fov : Math.max(-THIRD_PERSON.fovSpeed * dt, Math.min(THIRD_PERSON.fovSpeed * dt, fovStep));
    this.target = pivot; this.initialized = true;
    this.settled = length(this.position, desired) < .0001 && Math.abs(this.fov - desiredFov) < .005
      && !(this.visibilityView >= 0 && this.clearSeconds > 0 && this.clearSeconds < .30);
  }
}

export function thirdPersonSpawnYaw(nav: WorldNavigation) {
  const body = nav.interactions[0].bounds[0];
  // Aim at Playdeck's near left facade: the opposite suite blocks a center-facing rear boom.
  const x = nav.worldId === "platforms" ? body.min.x + (body.max.x - body.min.x) * .25 : (body.min.x + body.max.x) / 2;
  const z = nav.worldId === "platforms" ? body.max.z : (body.min.z + body.max.z) / 2;
  return Math.atan2(nav.spawn.x - x, nav.spawn.z - z);
}

/** Choose entry framing through the same camera adapter, without a second spawn/navigation table. */
export function thirdPersonSpawnPitch(nav: WorldNavigation) {
  const yaw = thirdPersonSpawnYaw(nav), camera = new ThirdPersonCamera();
  const pitches = Array.from({ length: Math.ceil((THIRD_PERSON.pitch - THIRD_PERSON.pitchMin) / .10) + 1 },
    (_, i) => Math.max(THIRD_PERSON.pitchMin, THIRD_PERSON.pitch - i * .10));
  for (const pitch of pitches) {
    // Preserve entry mouse-look yaw/pitch; the adapter corrects the visual
    // envelope afterwards without rewriting the player's input orientation.
    camera.update({ position: nav.spawn, yaw, pitch }, nav, 0, true, false);
    const rear = (camera.position.x - nav.spawn.x) * Math.sin(yaw) + (camera.position.z - nav.spawn.z) * Math.cos(yaw);
    const visible = [0, PLAYER.height / 2, PLAYER.height].every(height => cameraBoomFraction(camera.position,
      { ...nav.spawn, y: nav.spawn.y + height }, nav.obstacles, 0) === 1);
    if (rear >= Math.cos(pitch) * THIRD_PERSON.distance * .90 && visible) return pitch;
  }
  // If all initial angles are obstructed, the normal collision-aware adapter retains its safe retraction.
  return THIRD_PERSON.pitch;
}
