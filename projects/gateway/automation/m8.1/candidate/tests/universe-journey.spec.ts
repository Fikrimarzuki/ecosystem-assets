import assert from "node:assert/strict";
import { test, expect } from "@playwright/test";
import { Box3, Euler, Matrix4, PerspectiveCamera, Quaternion, Vector3 } from "three";
import { OBB } from "three/addons/math/OBB.js";
import { UniverseController } from "../lib/universe-controller";
import { gatewayConfig, inspectionDistance, universePlanets, type Coordinates } from "../lib/universe-config";
import { gatewayDockingTransform } from "../lib/universe-transforms";
import { gatewayJourneyOrigin, JourneyPath, JOURNEY_TIMING, rocketPresentation } from "../lib/universe-journey";
import { RocketAttitude } from "../lib/rocket-attitude";
import { createJourneyCameraPose, sampleJourneyCamera } from "../lib/journey-camera";
import { bakeDiorama } from "../components/universe/diorama-primitives";
import { gatewayRecipe } from "../components/universe/gateway";
import { rocketRecipe } from "../components/universe/rocket";
import { worldRecipe } from "../components/universe/world-recipes";

const advance = (c: UniverseController, seconds: number) => { for (let i = 0; i <= Math.ceil(seconds * 60); i++) c.advance(1 / 60); };
function active() { const c = new UniverseController(universePlanets); c.setFallback(false); return c; }
const matrix = (position: Coordinates, rotation: Coordinates, scale: number) => new Matrix4().compose(new Vector3(...position), new Quaternion().setFromEuler(new Euler(...rotation)), new Vector3().setScalar(scale));

test("parked rocket follows the pad transform and clears station structures", () => {
  for (const config of [gatewayConfig, { ...gatewayConfig, position: [8, -4, 3] as Coordinates, rotation: [-0.4, 1.2, 0.6] as Coordinates, scale: 2.3 }]) {
    const expected = new Vector3(...config.dockingPad).applyMatrix4(matrix(config.position, config.rotation, config.scale));
    expect(new Vector3(...gatewayDockingTransform(config).position).distanceTo(expected)).toBeLessThan(1e-12);
  }
  const origin = gatewayJourneyOrigin();
  const rocket = bakeDiorama(rocketRecipe);
  const local = rocket.clone();
  local.translate(gatewayConfig.dockingPad[0], gatewayConfig.dockingPad[1] + 0.73, gatewayConfig.dockingPad[2]);
  local.computeBoundingBox();
  for (const part of gatewayRecipe) {
    const geometry = bakeDiorama([part]); geometry.computeBoundingBox();
    assert(!geometry.boundingBox!.intersectsBox(local.boundingBox!), `parked collision with ${JSON.stringify(part)}`);
    geometry.dispose();
  }
  expect(origin.normal).toEqual(expect.arrayContaining([expect.any(Number)]));
  console.log({ rocketTriangles: rocket.getAttribute("position").count / 3 });
  rocket.dispose(); local.dispose();
});

test("flight is frozen, deterministic, input locked, visibility suspended and hands off canonically", () => {
  const original = JSON.stringify(universePlanets);
  const c = active(); advance(c, 137);
  c.setManualPaused(true);
  const phase = c.seconds, frozen = c.transform("games");
  c.select("games");
  const journey = c.journey;
  expect(c.getSnapshot().mode).toBe("igniting");
  c.select("tools"); c.back(); c.hover("mesh", "tools"); c.focus("tools");
  expect(c.journey).toBe(journey);
  expect(c.getSnapshot().selectedId).toBe("games");
  expect(c.reasons).toEqual(["manual", "destination"]);
  const stages = new Set<string>(); let notifications = 0;
  c.subscribe(() => { notifications++; stages.add(c.getSnapshot().mode); });
  advance(c, 1);
  c.setVisible(false); const time = c.travelSeconds;
  advance(c, 100); expect(c.travelSeconds).toBe(time);
  c.setVisible(true); c.advance(100); c.advance(100);
  expect(c.travelSeconds).toBe(time);
  advance(c, 4);
  expect([...stages]).toEqual(expect.arrayContaining(["launching", "departing", "travelling", "approaching", "arriving", "inspecting"]));
  expect(notifications).toBeLessThan(12);
  expect(c.seconds).toBe(phase);
  expect(c.destination).toEqual(frozen);
  expect(c.travelSeconds).toBe(JOURNEY_TIMING.total);
  expect(c.inspection.getOrientation()).toEqual({ yaw: 0, pitch: 0 });
  c.inspection.setOrientation(175, 20);
  expect(c.inspection.getOrientation()).toEqual({ yaw: 175, pitch: 20 });
  c.back(); advance(c, 2);
  expect(c.getSnapshot().mode).toBe("overview");
  expect(c.journey).toBeNull();
  expect(c.seconds).toBe(phase);
  expect(JSON.stringify(universePlanets)).toEqual(original);
  c.select("tools"); expect(c.journey).not.toBe(journey);
  c.setReduced(true); expect(c.getSnapshot().mode).toBe("inspecting");
  c.back(); c.select("after-hours"); expect(c.getSnapshot().mode).toBe("inspecting");
  expect(c.journey).toBeNull();
});

test("one rocket has explicit ignition, arrival, inspection and late return visibility", () => {
  expect(rocketPresentation("overview", 0, 0)).toEqual({ parked: true, opacity: 1, engine: 0 });
  expect(rocketPresentation("igniting", 0.2, 0).engine).toBeGreaterThan(0);
  expect(rocketPresentation("travelling", 2, 0)).toEqual({ parked: false, opacity: 1, engine: 1 });
  expect(rocketPresentation("arriving", 3.5, 0).opacity).toBeGreaterThan(0);
  expect(rocketPresentation("arriving", 3.75, 0).opacity).toBe(1);
  expect(rocketPresentation("inspecting", 3.75, 1)).toEqual({ parked: false, opacity: 1, engine: 0 });
  expect(rocketPresentation("returning", 3.75, 0.64).opacity).toBe(0);
  expect(rocketPresentation("returning", 3.75, 0.85).opacity).toBeGreaterThan(0);
  expect(rocketPresentation("returning", 3.75, 1)).toEqual({ parked: true, opacity: 1, engine: 0 });
});

test("all routes clear frozen world bounds across the orbit and keep continuous tangent attitude", () => {
  const c = active(), point: Coordinates = [0, 0, 0], tangent: Coordinates = [0, 0, 0];
  const q = new Quaternion(), previous = new Quaternion(), direction = new Vector3();
  const geometries = universePlanets.map((p) => bakeDiorama(worldRecipe(p)));
  const localBounds = geometries.map((g) => { g.computeBoundingBox(); return g.boundingBox!.clone(); });
  const partBounds = universePlanets.map(p => worldRecipe(p).map(part => {
    const g = bakeDiorama([part]); g.computeBoundingBox(); const b = g.boundingBox!.clone(); g.dispose(); return b;
  }));
  const stationParts = gatewayRecipe.map((part) => {
    const g = bakeDiorama([part]); g.computeBoundingBox();
    const b = g.boundingBox!.clone(); g.dispose(); return b;
  });
  const rocket = bakeDiorama(rocketRecipe), vertices = rocket.getAttribute("position");
  const rocketParts = rocketRecipe.map(part => { const g = bakeDiorama([part]); g.computeBoundingBox(); const b = new OBB().fromBox3(g.boundingBox!); g.dispose(); return b; });
  const partBox = new OBB(), rocketMatrix = new Matrix4(), localMatrix = new Matrix4();
  const rocketBounds = new Box3(), v = new Vector3();
  const stationInverse = matrix(gatewayConfig.position, gatewayConfig.rotation, gatewayConfig.scale).invert();
  const rocketPosition = new Vector3();
  let minimumWorldClearance = Infinity, largestTurn = 0, turnLocation = "";
  for (let phase = 0; phase < 600; phase += 10) {
    const worlds = universePlanets.map((p) => c.transform(p.id));
    const inverseWorlds = worlds.map((w) => matrix(w.position, w.rotation, w.scale * 1.025).invert());
    const bounds = worlds.map((world, i) => {
      const g = geometries[i].clone().applyMatrix4(matrix(world.position, world.rotation, world.scale * 1.025));
      g.computeBoundingBox(); const b = g.boundingBox!.clone(); g.dispose(); return b;
    });
    for (const destination of worlds) {
      const path = new JourneyPath(gatewayJourneyOrigin(), destination), attitude = new RocketAttitude(path);
      const duplicate = new JourneyPath(gatewayJourneyOrigin(), destination);
      expect(path.curves).toEqual(duplicate.curves);
      path.sample(0, point); expect(point).toEqual(path.origin.position);
      path.sample(1, point); expect(point).toEqual(destination.parkingTarget);
      for (let i = 0; i <= 512; i++) {
        path.sample(i / 512, point, tangent); attitude.sample(i / 512, q);
        assert(direction.set(0, 1, 0).applyQuaternion(q).dot(v.fromArray(tangent)) > 0.9999);
        if (i && previous.angleTo(q) > largestTurn) { largestTurn = previous.angleTo(q); turnLocation = `${destination.id}/${phase}/${i}`; }
        previous.copy(q);
        // A 1.12-unit sphere encloses the complete scaled rocket in every attitude.
        for (const [j, b] of bounds.entries()) {
          const distance = b.distanceToPoint(v.fromArray(point)) - 1.12;
          minimumWorldClearance = Math.min(minimumWorldClearance, distance);
          if (distance <= 0) {
            // The persistent holding pose is closer than a nose-sized sphere permits.
            // Narrow phase still conservatively encloses every actual rocket vertex.
            rocketBounds.makeEmpty(); rocketPosition.fromArray(point);
            for (let k = 0; k < vertices.count; k++) rocketBounds.expandByPoint(v.fromBufferAttribute(vertices, k).multiplyScalar(path.origin.scale).applyQuaternion(q).add(rocketPosition).applyMatrix4(inverseWorlds[j]));
            if (rocketBounds.intersectsBox(localBounds[j])) for (const [part, box] of partBounds[j].entries()) {
              if (!rocketBounds.intersectsBox(box)) continue;
              rocketMatrix.compose(rocketPosition, q, new Vector3().setScalar(path.origin.scale));
              localMatrix.multiplyMatrices(inverseWorlds[j], rocketMatrix);
              for (const rocketPart of rocketParts) assert(!partBox.copy(rocketPart).applyMatrix4(localMatrix).intersectsBox3(box), `${destination.id} at ${phase}s, path ${i}/512 intersects ${worlds[j].id} part ${part}`);
            }
          }
        }
        if (i < 100) {
          rocketBounds.makeEmpty();
          rocketPosition.fromArray(point);
          for (let k = 0; k < vertices.count; k++) rocketBounds.expandByPoint(v.fromBufferAttribute(vertices, k).multiplyScalar(path.origin.scale).applyQuaternion(q).add(rocketPosition).applyMatrix4(stationInverse));
          for (const b of stationParts) assert(!rocketBounds.intersectsBox(b), `${destination.id} at ${phase}s launch intersects Gateway at ${i}`);
        }
      }
    }
    advance(c, 10);
  }
  console.log({ turnLocation, largestTurn });
  expect(largestTurn).toBeLessThan(0.3);
  console.log({ minimumWorldClearance, largestTurnDegrees: largestTurn * 180 / Math.PI });
  geometries.forEach((g) => g.dispose()); rocket.dispose();
});

test("cinematic camera moves independently and converges continuously to canonical inspection", () => {
  const c = active(), point: Coordinates = [0, 0, 0], pose = createJourneyCameraPose();
  for (const p of universePlanets) {
    const destination = c.transform(p.id), path = new JourneyPath(gatewayJourneyOrigin(), destination);
    for (const [width, height] of [[1150, 740], [896, 660], [688, 570], [592, 570]]) {
      path.sample(0, point); sampleJourneyCamera(path, 0, width, height, pose);
      expect(pose.position).toEqual([0, 0, 28]); expect(pose.target).toEqual([0, 0, 0]);
      path.sample(1, point); sampleJourneyCamera(path, 3.75, width, height, pose);
      expect(pose.target).toEqual(destination.focusTarget);
      const distance = inspectionDistance(destination.scale, width / height, height, destination.id);
      expect(pose.position).toEqual([destination.focusTarget[0], destination.focusTarget[1], destination.focusTarget[2] + distance]);
      const final = [...pose.position];
      sampleJourneyCamera(path, 3.749, width, height, pose);
      expect(new Vector3(...pose.position).distanceTo(new Vector3(...final))).toBeLessThan(0.001);
    }
  }
});

test("rocket and approached destination stay inside the cinematic frame at representative phases and widths", () => {
  const c = active(), pose = createJourneyCameraPose(), point: Coordinates = [0, 0, 0];
  const rocket = bakeDiorama(rocketRecipe), vertices = rocket.getAttribute("position");
  const q = new Quaternion(), v = new Vector3(), offset = new Vector3();
  for (const phase of [0, 150, 300, 450]) {
    for (const planet of universePlanets) {
      const destination = c.transform(planet.id), path = new JourneyPath(gatewayJourneyOrigin(), destination), attitude = new RocketAttitude(path);
      const world = bakeDiorama(worldRecipe(planet)).applyMatrix4(matrix(destination.position, destination.rotation, destination.scale));
      const worldVertices = world.getAttribute("position");
      for (const [width, height] of [[1150, 740], [896, 660], [688, 570], [592, 570]]) {
        const camera = new PerspectiveCamera(40, width / height, 0.1, 80);
        for (let time = 0; time <= 3.75; time += 0.125) {
          path.sample(path.fractionAt(time), point); attitude.sample(path.fractionAt(time), q); offset.fromArray(point);
          sampleJourneyCamera(path, time, width, height, pose);
          camera.position.fromArray(pose.position); camera.fov = pose.fov; camera.lookAt(new Vector3(...pose.target)); camera.updateProjectionMatrix(); camera.updateMatrixWorld();
          for (let i = 0; i < vertices.count; i++) {
            v.fromBufferAttribute(vertices, i).multiplyScalar(path.origin.scale).applyQuaternion(q).add(offset).project(camera);
            assert(Math.abs(v.x) < 0.94 && v.y > -0.76 && v.y < 0.80 && v.z < 1, `${planet.id} phase ${phase} width ${width} time ${time} rocket ${v.toArray()}`);
          }
          if (time >= 1.75) for (let i = 0; i < worldVertices.count; i++) {
            v.fromBufferAttribute(worldVertices, i).project(camera);
            assert(Math.abs(v.x) < 0.94 && v.y > -0.76 && v.y < 0.80 && v.z < 1, `${planet.id} phase ${phase} width ${width} time ${time} world ${v.toArray()}`);
          }
        }
      }
      world.dispose();
    }
    advance(c, 150);
  }
  rocket.dispose();
});
