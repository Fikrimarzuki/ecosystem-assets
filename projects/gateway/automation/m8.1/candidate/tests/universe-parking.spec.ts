import assert from "node:assert/strict";
import { expect, test } from "@playwright/test";
import { Euler, Matrix4, PerspectiveCamera, Quaternion, Vector3 } from "three";
import { UniverseController } from "../lib/universe-controller";
import { gatewayConfig, inspectionDistance, universePlanets, type Coordinates } from "../lib/universe-config";
import { DEFAULT_PARKING_TARGET, resolveParkingTarget } from "../lib/universe-transforms";
import { gatewayJourneyOrigin, JourneyPath, rocketPresentation } from "../lib/universe-journey";
import { parkingAttitude, RocketAttitude } from "../lib/rocket-attitude";
import { inspectionCameraBasis } from "../lib/inspection-camera";
import { bakeDiorama } from "../components/universe/diorama-primitives";
import { rocketRecipe } from "../components/universe/rocket";

function advance(c: UniverseController, seconds: number) { c.advance(0); for (let t = 0; t < seconds; t += 1 / 60) c.advance(Math.min(1 / 60, seconds - t)); }

test("parking anchors resolve world-local overrides and the common fallback against frozen transforms", () => {
  const original = JSON.stringify({ universePlanets, gatewayConfig });
  const worlds = universePlanets.map(p => ({ ...p, parkingTarget: p.id === "games" ? [2.4, 1.3, -0.3] as Coordinates : undefined }));
  const c = new UniverseController(worlds); c.setFallback(false); advance(c, 137);
  for (const planet of worlds) {
    const world = c.transform(planet.id);
    const transform = new Matrix4().compose(new Vector3(...world.position), new Quaternion().setFromEuler(new Euler(...world.rotation)), new Vector3().setScalar(world.scale));
    const expected = new Vector3(...(planet.parkingTarget ?? DEFAULT_PARKING_TARGET)).applyMatrix4(transform);
    expect(new Vector3(...world.parkingTarget).distanceTo(expected)).toBeLessThan(1e-12);
    expect(resolveParkingTarget(planet.parkingTarget, world)).toEqual(world.parkingTarget);
    expect(world.parkingTarget).not.toEqual(world.travelTarget);
    expect(world.landingTarget).toBeUndefined();
  }
  expect(JSON.stringify({ universePlanets, gatewayConfig })).toBe(original);
});

test("parking survives inspection and reduced motion; Back resets invisibly and a revisit captures fresh state", () => {
  const c = new UniverseController(universePlanets); c.setFallback(false); c.setManualPaused(true);
  c.select("games"); const first = c.journey!; advance(c, 3.8);
  expect(c.getSnapshot().mode).toBe("inspecting");
  const position: Coordinates = [0, 0, 0]; first.sample(1, position);
  expect(position).toEqual(c.destination?.parkingTarget);
  const frozen = JSON.stringify(c.destination);
  c.inspection.setOrientation(270, 24); advance(c, 10);
  expect(JSON.stringify(c.destination)).toBe(frozen);
  expect(rocketPresentation("inspecting", c.travelSeconds, c.progress)).toEqual({ parked: false, opacity: 1, engine: 0 });
  c.back();
  expect(rocketPresentation("returning", c.travelSeconds, 0)).toEqual({ parked: false, opacity: 1, engine: 0 });
  for (const progress of [0.35, 0.5, 0.649]) expect(rocketPresentation("returning", c.travelSeconds, progress).opacity).toBe(0);
  expect(rocketPresentation("returning", c.travelSeconds, 0.65).parked).toBe(true);
  advance(c, 1.7); expect(c.journey).toBeNull(); expect(c.destination).toBeNull();
  c.select("games"); expect(c.journey).not.toBe(first); expect(c.travelSeconds).toBe(0);
  expect(c.inspection.getOrientation()).toEqual({ yaw: 0, pitch: 0 });
  advance(c, 3.8); expect(c.destination?.parkingTarget).toEqual(position);
  c.setReduced(true); c.back(); c.select("tools");
  expect(c.journey).toBeNull(); expect(c.getSnapshot().mode).toBe("inspecting");
  expect(c.destination?.parkingTarget).toEqual(c.transform("tools").parkingTarget);
});

test("all six parked rockets fit 360-degree inspection at both tilt limits without following the camera", () => {
  const c = new UniverseController(universePlanets), geometry = bakeDiorama(rocketRecipe), vertices = geometry.getAttribute("position");
  const v = new Vector3(), q = new Quaternion(); let worstX = 0, worstY = 0;
  for (const planet of universePlanets) for (const reduced of [false, true]) {
    const world = c.transform(planet.id), path = new JourneyPath(gatewayJourneyOrigin(), world);
    if (reduced) parkingAttitude(world.rotation, q); else new RocketAttitude(path).sample(1, q);
    const position = new Vector3(...world.parkingTarget);
    const parking = new Matrix4().compose(position, q, new Vector3().setScalar(gatewayConfig.scale));
    for (const [width, height] of [[1150, 740], [896, 660], [688, 570], [592, 570]]) for (let yaw = -180; yaw <= 180; yaw += 15) for (const pitch of [-12, 0, 24]) {
      const basis = inspectionCameraBasis(world.rotation, { yaw, pitch });
      const camera = new PerspectiveCamera(40, width / height, 0.1, 80);
      camera.position.copy(basis.offset).multiplyScalar(inspectionDistance(world.scale, width / height, height, world.id)).add(new Vector3(...world.focusTarget));
      camera.up.copy(basis.up); camera.lookAt(new Vector3(...world.focusTarget)); camera.updateMatrixWorld();
      for (let i = 0; i < vertices.count; i++) {
        v.fromBufferAttribute(vertices, i).applyMatrix4(parking).project(camera);
        worstX = Math.max(worstX, Math.abs(v.x)); worstY = Math.max(worstY, Math.abs(v.y));
        assert(Math.abs(v.x) < 0.94 && v.y < 0.80 && v.y > -0.76, `${planet.id} / ${width} / yaw ${yaw} pitch ${pitch}: ${v.toArray()}`);
      }
      expect(position.toArray()).toEqual(world.parkingTarget);
    }
  }
  console.log({ parkedMaximumProjectedX: worstX, parkedMaximumProjectedY: worstY }); geometry.dispose();
});
