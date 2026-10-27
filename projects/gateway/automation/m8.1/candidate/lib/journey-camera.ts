import { inspectionDistance, universeCamera, universeView, type Coordinates } from "./universe-config";
import { smoothTransition } from "./universe-orbit";
import { JOURNEY_TIMING, type JourneyPath } from "./universe-journey";
import { worldInspectionExtent } from "./world-dimensions";

export type JourneyCameraPose = { position: Coordinates; target: Coordinates; fov: number };
export function createJourneyCameraPose(): JourneyCameraPose { return { position: [0, 0, 0], target: [0, 0, 0], fov: 40 }; }

/** Camera choreography is derived independently from the rocket path; +Z remains the viewing side. */
function composePose(path: JourneyPath, seconds: number, width: number, height: number,
  rocket: Coordinates, out: JourneyCameraPose) {
  const aspect = width / Math.max(height, 1);
  const view = universeView(width, height);
  const overviewFov = 2 * Math.atan(view.height / (2 * universeCamera.distance)) * 180 / Math.PI;
  const travelled = path.fractionAt(seconds);
  const departureEnd = path.boundaries[1] / path.length;
  const cruiseEnd = path.boundaries[2] / path.length;
  const accompanying = smoothTransition((travelled - 0.07) / Math.max(0.01, departureEnd - 0.07));
  const approach = smoothTransition((travelled - cruiseEnd) / (1 - cruiseEnd));
  const destination = path.destination.focusTarget;
  const destinationWeight = 0.42 + 0.58 * approach;
  const launchDistance = Math.max(16, 12 / aspect);
  const inspection = inspectionDistance(path.destination.scale, aspect, height, path.destination.id);
  for (let axis = 0; axis < 3; axis++) {
    const launchTarget = path.origin.position[axis] + (rocket[axis] - path.origin.position[axis]) * 0.55;
    const followTarget = rocket[axis] + (destination[axis] - rocket[axis]) * destinationWeight;
    out.target[axis] = launchTarget + (followTarget - launchTarget) * accompanying;
  }
  // Fit the rocket and the destination in the shared shot without changing either transform.
  const tangent = Math.tan(Math.PI / 9);
  let followDistance = inspection;
  for (let index = 0; index < 2; index++) {
    const point = index === 0 ? rocket : destination;
    const radius = index === 0 ? 1.12 : path.destination.scale * worldInspectionExtent(path.destination.id);
    const depth = point[2] - out.target[2];
    followDistance = Math.max(followDistance,
      depth + (Math.abs(point[0] - out.target[0]) + radius) / (tangent * aspect * 0.85),
      depth + (Math.abs(point[1] - out.target[1]) + radius) / (tangent * 0.78));
  }
  const arrival = path.arrivalProgress(seconds);
  let distance = launchDistance + (followDistance - launchDistance) * accompanying;
  distance += (inspection - distance) * arrival;
  for (let axis = 0; axis < 3; axis++) out.target[axis] += (destination[axis] - out.target[axis]) * arrival;
  const side = 8 * accompanying * (1 - arrival);
  const above = 2.5 * accompanying * (1 - arrival);
  // Fit in the camera's actual oblique basis, including the near foreground rocket.
  // The small fixed iteration count converges monotonically; it does not move the path.
  for (let iteration = 0; iteration < 8; iteration++) {
    const horizontal = Math.hypot(side, distance), depth = Math.hypot(horizontal, above);
    let required = depth;
    for (let index = 0; index < 2; index++) {
      const point = index === 0 ? rocket : destination;
      const radius = index === 0 ? 1.12 : path.destination.scale * 2;
      const x = point[0] - out.target[0], y = point[1] - out.target[1], z = point[2] - out.target[2];
      const cameraX = (distance * x - side * z) / horizontal;
      const cameraY = (-side * above * x + horizontal * horizontal * y - above * distance * z) / (horizontal * depth);
      const cameraZ = (side * x + above * y + distance * z) / depth;
      required = Math.max(required, cameraZ + (Math.abs(cameraX) + radius) / (tangent * aspect * 0.82),
        cameraZ + (Math.abs(cameraY) + radius) / (tangent * 0.74));
    }
    const fitted = Math.sqrt(Math.max(0, required * required - side * side - above * above));
    distance += Math.max(0, fitted - distance) * accompanying;
  }
  distance += 2 * Math.sin(Math.PI * seconds / JOURNEY_TIMING.total) ** 2;
  distance += (inspection - distance) * arrival;
  const enter = smoothTransition(seconds / 1.05);
  for (let axis = 0; axis < 3; axis++) {
    // Side accompaniment reveals the rocket silhouette and separates it from the world.
    // The final hold settles onto inspection's straight-on viewing axis.
    const offset = axis === 2 ? distance : axis === 0 ? side : above;
    const position = out.target[axis] + offset;
    out.position[axis] = (axis === 2 ? universeCamera.distance : 0) * (1 - enter) + position * enter;
    out.target[axis] *= enter;
  }
  out.fov = overviewFov + (40 - overviewFov) * enter;
}

/** A bounded, precomputed C2 track replaces per-frame active-constraint switching.
 * Positive cubic B-spline weights keep the camera inside its planned control hull.
 * Repeated endpoint controls give zero velocity/acceleration at overview and inspection.
 */
export class JourneyCameraTrack {
  private readonly count = 14;
  private readonly values = new Float64Array(15 * 7);
  constructor(path: JourneyPath, width: number, height: number) {
    const point: Coordinates = [0, 0, 0], pose = createJourneyCameraPose();
    for (let i = 0; i <= this.count; i++) {
      const seconds = i <= 1 ? 0 : i >= this.count - 1 ? JOURNEY_TIMING.total : i / this.count * JOURNEY_TIMING.total;
      path.sample(path.fractionAt(seconds), point);
      composePose(path, seconds, width, height, point, pose);
      for (let axis = 0; axis < 3; axis++) {
        this.values[i * 7 + axis] = pose.position[axis];
        this.values[i * 7 + axis + 3] = pose.target[axis];
      }
      this.values[i * 7 + 6] = pose.fov;
    }
  }
  sample(seconds: number, out: JourneyCameraPose) {
    const sample = Math.max(0, Math.min(1, seconds / JOURNEY_TIMING.total)) * this.count;
    const index = Math.floor(sample), t = sample - index, s = 1 - t;
    const a = Math.max(0, index - 1) * 7, b = index * 7, c = Math.min(this.count, index + 1) * 7, d = Math.min(this.count, index + 2) * 7;
    for (let axis = 0; axis < 7; axis++) {
      const value = (s ** 3 * this.values[a + axis] + (3 * t ** 3 - 6 * t * t + 4) * this.values[b + axis]
        + (-3 * t ** 3 + 3 * t * t + 3 * t + 1) * this.values[c + axis] + t ** 3 * this.values[d + axis]) / 6;
      if (axis < 3) out.position[axis] = value;
      else if (axis < 6) out.target[axis - 3] = value;
      else out.fov = value;
    }
    // Preserve bit-exact canonical endpoint poses (rather than summation roundoff).
    if (sample === 0 || sample === this.count) {
      for (let axis = 0; axis < 3; axis++) { out.position[axis] = this.values[index * 7 + axis]; out.target[axis] = this.values[index * 7 + axis + 3]; }
      out.fov = this.values[index * 7 + 6];
    }
  }
}

const tracks = new WeakMap<JourneyPath, { width: number; height: number; track: JourneyCameraTrack }>();
export function sampleJourneyCamera(path: JourneyPath, seconds: number, width: number, height: number, out: JourneyCameraPose) {
  let cached = tracks.get(path);
  if (!cached || cached.width !== width || cached.height !== height) {
    cached = { width, height, track: new JourneyCameraTrack(path, width, height) };
    tracks.set(path, cached);
  }
  cached.track.sample(seconds, out);
}
