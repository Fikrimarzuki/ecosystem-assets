import assert from "node:assert/strict";
import { expect, test } from "@playwright/test";
import { Box3, Euler, Matrix4, PerspectiveCamera, Quaternion, Vector3 } from "three";
import { universePlanets, universeView, projectUniversePoint, type Coordinates } from "../lib/universe-config";
import { UniverseController } from "../lib/universe-controller";
import { orbitalPosition, ORBIT_PERIOD_SECONDS, frameStep } from "../lib/universe-orbit";
import { gatewayDockingTransform } from "../lib/universe-transforms";
import { bakeDiorama } from "../components/universe/diorama-primitives";
import { worldRecipe } from "../components/universe/world-recipes";
import { gatewayRecipe } from "../components/universe/gateway";
import { gatewayConfig, inspectionDistance, labelPosition } from "../lib/universe-config";

function advance(controller: UniverseController, seconds: number) {
  for (let frame = 0; frame <= Math.ceil(seconds * 60); frame++) controller.advance(1 / 60);
}
function activeController() {
  const controller = new UniverseController(universePlanets);
  controller.setFallback(false);
  return controller;
}

test("orbital positions are deterministic, phase-spaced, periodic and preserve depth", () => {
  for (const planet of universePlanets) {
    expect(orbitalPosition(planet.orbit, 0)).toEqual(planet.position);
    expect(orbitalPosition(planet.orbit, 123)).toEqual(orbitalPosition(planet.orbit, 123));
    for (const [axis, value] of orbitalPosition(planet.orbit, ORBIT_PERIOD_SECONDS).entries()) expect(value).toBeCloseTo(planet.position[axis], 8);
  }
  expect(new Set(universePlanets.map((planet) => planet.position[2])).size).toBe(6);
  expect(frameStep(60)).toBe(0);
  expect(frameStep(Number.NaN)).toBe(0);
});

test("pause reasons compose and never reset the clock or frozen destination", () => {
  const controller = activeController();
  advance(controller, 12);
  const phase = controller.seconds;
  controller.hover("mesh", "games");
  advance(controller, 2);
  expect(controller.seconds).toBe(phase);
  controller.focus("games");
  controller.hover("mesh", null);
  advance(controller, 2);
  expect(controller.reasons).toContain("keyboard-focus");
  expect(controller.seconds).toBe(phase);
  controller.setManualPaused(true);
  controller.focus(null);
  advance(controller, 2);
  expect(controller.seconds).toBe(phase);
  controller.setManualPaused(false);
  advance(controller, 1);
  expect(controller.seconds).toBeGreaterThan(phase);
  const capture = controller.transform("games");
  controller.select("games");
  expect(controller.getSnapshot().mode).toBe("igniting");
  controller.hover("mesh", null);
  const locked = controller.seconds;
  advance(controller, 4);
  expect(controller.getSnapshot().mode).toBe("inspecting");
  expect(controller.seconds).toBe(locked);
  expect(controller.destination).toEqual(capture);
  controller.inspection.setOrientation(460, 100);
  expect(controller.inspection.getOrientation()).toEqual({ yaw: 100, pitch: 24 });
  controller.back();
  expect(controller.getSnapshot().mode).toBe("returning");
  advance(controller, 1);
  expect(controller.seconds).toBe(locked);
  advance(controller, 1);
  expect(controller.getSnapshot().mode).toBe("overview");
  expect(controller.getSnapshot().selectedId).toBeNull();
  expect(controller.seconds).toBeGreaterThan(locked);
});

test("reduced motion, manual pause, hidden state and fallback preserve phase across transitions", () => {
  const controller = activeController();
  advance(controller, 10);
  const phase = controller.seconds;
  controller.setVisible(false);
  advance(controller, 120);
  controller.setVisible(true);
  controller.advance(120);
  expect(controller.seconds).toBe(phase);
  controller.setReduced(true);
  controller.select("tools");
  expect(controller.getSnapshot().mode).toBe("inspecting");
  controller.back();
  expect(controller.getSnapshot().mode).toBe("overview");
  advance(controller, 5);
  expect(controller.seconds).toBe(phase);
  controller.setManualPaused(true);
  controller.setReduced(false);
  controller.select("learning");
  advance(controller, 4);
  controller.back();
  advance(controller, 2);
  expect(controller.seconds).toBe(phase);
  expect(controller.reasons).toContain("manual");
  controller.setFallback(true);
  controller.select("games");
  expect(controller.getSnapshot().mode).toBe("overview");
  expect(controller.getSnapshot().selectedId).toBe("games");
  controller.setFallback(false);
  expect(controller.getSnapshot().mode).toBe("inspecting");
  expect(gatewayDockingTransform().position.every(Number.isFinite)).toBe(true);
});

test("every phase keeps projected geometry and labels separated and within the overview", () => {
  const localBounds = universePlanets.map((planet) => {
    const geometry = bakeDiorama(worldRecipe(planet));
    const bounds = new Box3();
    for (const yaw of [-0.035, 0.035]) {
      const transformed = geometry.clone().applyMatrix4(new Matrix4().compose(new Vector3(),
        new Quaternion().setFromEuler(new Euler(planet.rotation[0], planet.rotation[1] + yaw, planet.rotation[2])),
        new Vector3().setScalar(planet.scale * 1.025)));
      transformed.computeBoundingBox();
      bounds.union(transformed.boundingBox!);
      transformed.dispose();
    }
    geometry.dispose();
    bounds.expandByScalar(0.025);
    return bounds;
  });
  let minimumDistance = Infinity;
  let maximumOverlap = 0;
  const station = bakeDiorama(gatewayRecipe);
  station.applyMatrix4(new Matrix4().compose(new Vector3(...gatewayConfig.position), new Quaternion().setFromEuler(new Euler(...gatewayConfig.rotation)), new Vector3().setScalar(gatewayConfig.scale)));
  station.computeBoundingBox();
  const stationBounds = station.boundingBox!.clone();
  station.dispose();
  for (const [width, height] of [[1150, 740], [896, 660], [688, 570], [592, 570]]) {
    const view = universeView(width, height);
    const homeAnchor = projectUniversePoint(labelPosition(gatewayConfig), view);
    const homeOffset = width < 700 ? -16 : 0;
    const homeLabel = { left: homeAnchor.x * width - 70, right: homeAnchor.x * width + 70, top: homeAnchor.y * height + homeOffset, bottom: homeAnchor.y * height + 36 + homeOffset };
    for (let seconds = 0; seconds < ORBIT_PERIOD_SECONDS; seconds += 1) {
      const positions = universePlanets.map((planet) => orbitalPosition(planet.orbit, seconds));
      const rectangles = positions.map((position, index) => {
        const b = localBounds[index];
        const points = [];
        for (const x of [b.min.x, b.max.x]) for (const y of [b.min.y, b.max.y]) for (const z of [b.min.z, b.max.z]) points.push(projectUniversePoint([x + position[0], y + position[1], z + position[2]], view));
        return { left: Math.min(...points.map((p) => p.x)) * width, right: Math.max(...points.map((p) => p.x)) * width,
          top: Math.min(...points.map((p) => p.y)) * height, bottom: Math.max(...points.map((p) => p.y)) * height };
      });
      const labels = positions.map((position, index) => {
        const planet = universePlanets[index];
        const point: Coordinates = [position[0], position[1] + planet.labelTop, position[2]];
        const projected = projectUniversePoint(point, view);
        const labelWidth = planet.name.length * (width < 700 ? 6.2 : 6.7) + 40;
        return { left: projected.x * width - labelWidth / 2, right: projected.x * width + labelWidth / 2, top: projected.y * height - 34, bottom: projected.y * height };
      });
      const overlap = (a: typeof labels[number], b: typeof labels[number]) => Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
      for (let i = 0; i < positions.length; i++) {
        const tag = `${universePlanets[i].id} at ${seconds}s / ${width}px`;
        const rect = rectangles[i];
        assert(rect.left > 0, tag);
        assert(rect.right < width, tag);
        assert(rect.top > 0, tag);
        assert(rect.bottom < height, tag);
        assert(labels[i].left > 0, tag);
        assert(labels[i].right < width, tag);
        assert(labels[i].top > 0, tag);
        assert(labels[i].bottom < height, tag);
        assert(!localBounds[i].clone().translate(new Vector3(...positions[i])).intersectsBox(stationBounds), `${tag} intersects Gateway`);
        assert.equal(overlap(labels[i], homeLabel), 0, `${tag} label / Gateway label`);
        for (let j = i + 1; j < positions.length; j++) {
          assert(!localBounds[i].clone().translate(new Vector3(...positions[i])).intersectsBox(localBounds[j].clone().translate(new Vector3(...positions[j]))), `${tag} intersects ${universePlanets[j].id}`);
          const distance = new Vector3(...positions[i]).distanceTo(new Vector3(...positions[j]));
          minimumDistance = Math.min(minimumDistance, distance);
          assert(distance > 5.5, tag);
          assert.equal(overlap(labels[i], labels[j]), 0, `${tag} label / ${universePlanets[j].id}`);
          const area = overlap(rect, rectangles[j]);
          const smaller = Math.min((rect.right - rect.left) * (rect.bottom - rect.top), (rectangles[j].right - rectangles[j].left) * (rectangles[j].bottom - rectangles[j].top));
          maximumOverlap = Math.max(maximumOverlap, area / smaller);
          assert(area / smaller < 0.12, `${tag} geometry / ${universePlanets[j].id}`);
        }
      }
    }
  }
  console.log({ minimumDistance, maximumOverlap });
});


test("all inspection silhouettes fit at both rotation limits with UI clearance", () => {
  const controller = activeController();
  for (const planet of universePlanets) {
    const world = controller.transform(planet.id);
    const geometry = bakeDiorama(worldRecipe(planet));
    geometry.applyMatrix4(new Matrix4().compose(new Vector3(...world.position), new Quaternion().setFromEuler(new Euler(...world.rotation)), new Vector3().setScalar(world.scale * 1.025)));
    const points = geometry.getAttribute("position");
    for (const [width, height] of [[1150, 740], [896, 660], [688, 570], [592, 570]]) {
      for (const degrees of [-20, 0, 20]) {
        const camera = new PerspectiveCamera(40, width / height, 0.1, 80);
        const distance = inspectionDistance(world.scale, width / height, height, world.id);
        const yaw = degrees * Math.PI / 180;
        camera.position.set(Math.sin(yaw) * distance, 0, Math.cos(yaw) * distance).add(new Vector3(...world.focusTarget));
        camera.lookAt(new Vector3(...world.focusTarget));
        camera.updateMatrixWorld();
        for (let i = 0; i < points.count; i++) {
          const projected = new Vector3().fromBufferAttribute(points, i).project(camera);
          const x = (projected.x + 1) * width / 2;
          const y = (1 - projected.y) * height / 2;
          const tag = `${planet.id} / ${width}px / ${degrees}deg`;
          assert(x > 20 && x < width - 20, tag);
          assert(y > 80 && y < height - 105, `${tag}: y=${y}`);
        }
      }
    }
    geometry.dispose();
  }
});
