import assert from "node:assert/strict";
import { expect, test, type Page } from "@playwright/test";
import { Box3, type BufferAttribute, Euler, Matrix4, PerspectiveCamera, Quaternion, Sphere, Vector3 } from "three";
import { UniverseController } from "../lib/universe-controller";
import { inspectionDistance, universePlanets } from "../lib/universe-config";
import { landmarksForWorld, landmarkProject } from "../lib/universe-landmarks";
import { inspectionCameraBasis } from "../lib/inspection-camera";
import { landmarkCameraPose } from "../lib/landmark-camera";
import { bakeDiorama } from "../components/universe/diorama-primitives";
import { worldRecipe } from "../components/universe/world-recipes";

const finish = (c: UniverseController) => { c.advance(0); for (let i = 0; i < 20; i++) c.advance(.05); };
test("controller defaults to Click Mode, validates focus, locks input and emits only phase changes", () => {
  const c = new UniverseController(universePlanets);
  expect(c.getSnapshot()).toMatchObject({ explorationMode: "click", focusPhase: "planet", landmarkFocusId: null });
  expect(c.focusLandmark("landmark-neuran")).toBe(false);
  c.setFallback(false); c.setReduced(true); c.select("platforms"); c.setReduced(false);
  c.inspection.setOrientation(65, 12);
  const before = { destination: structuredClone(c.destination), orientation: c.inspection.getOrientation(), orbit: c.seconds, travel: c.travelSeconds };
  expect(c.focusLandmark("missing")).toBe(false);
  expect(c.focusLandmark("landmark-tinyverse")).toBe(false);
  let notifications = 0; c.subscribe(() => notifications++);
  expect(c.focusLandmark("landmark-neuran")).toBe(true);
  expect(c.focusLandmark("landmark-neuran")).toBe(false);
  expect(c.inspection.beginDrag(1, 0, 0)).toBe(false);
  expect(c.inspection.key("ArrowRight")).toBe(false);
  c.inspection.setOrientation(0, 0);
  finish(c);
  expect(c.getSnapshot()).toMatchObject({ mode: "inspecting", focusPhase: "focused", landmarkFocusId: "landmark-neuran" });
  expect(notifications).toBe(2);
  expect(c.transitioning).toBe(false);
  expect(c.returnToPlanet()).toBe(true); expect(c.returnToPlanet()).toBe(false);
  expect(c.focusLandmark("landmark-playdeck")).toBe(false);
  finish(c);
  expect(c.getSnapshot()).toMatchObject({ focusPhase: "planet", landmarkFocusId: null });
  expect({ destination: c.destination, orientation: c.inspection.getOrientation(), orbit: c.seconds, travel: c.travelSeconds }).toEqual(before);
  expect(notifications).toBe(4);
  expect(c.inspection.key("ArrowRight")).toBe(true);
});

test("focus cancellation, visibility, reduced motion, fallback and Back cannot leave stale state", () => {
  const c = new UniverseController(universePlanets);
  c.setFallback(false); c.setReduced(true); c.select("games");
  expect(c.focusLandmark("landmark-tinyverse")).toBe(true);
  expect(c.getSnapshot().focusPhase).toBe("focused");
  expect(c.returnToPlanet()).toBe(true); expect(c.getSnapshot().focusPhase).toBe("planet");
  c.setReduced(false); c.focusLandmark("landmark-tinyverse");
  c.advance(0); c.advance(.1); const progress = c.focusProgress;
  c.setVisible(false); finish(c); expect(c.focusProgress).toBe(progress);
  c.setVisible(true); c.returnToPlanet(); finish(c); expect(c.getSnapshot().focusPhase).toBe("planet");
  c.focusLandmark("landmark-tinyverse"); c.setReduced(true); expect(c.getSnapshot().focusPhase).toBe("focused");
  c.back(); expect(c.getSnapshot()).toMatchObject({ mode: "overview", focusPhase: "planet", landmarkFocusId: null });
  c.select("games"); expect(c.getSnapshot().focusPhase).toBe("planet");
  c.focusLandmark("landmark-tinyverse"); c.setFallback(true);
  expect(c.getSnapshot()).toMatchObject({ mode: "overview", selectedId: "games", focusPhase: "planet", landmarkFocusId: null });
  expect(c.focusLandmark("landmark-tinyverse")).toBe(false);
  c.setFallback(false); expect(c.getSnapshot()).toMatchObject({ mode: "inspecting", focusPhase: "planet" });
});

test("all authored anchors fit their full structures and approach outside world bounds at desktop/tablet sizes", () => {
  const controller = new UniverseController(universePlanets);
  for (const planet of universePlanets) {
    const world = controller.transform(planet.id), parts = worldRecipe(planet);
    const matrix = new Matrix4().compose(new Vector3(...world.position), new Quaternion().setFromEuler(new Euler(...world.rotation)), new Vector3().setScalar(world.scale * 1.025));
    const geometry = bakeDiorama(parts).applyMatrix4(matrix);
    const worldBounds = new Box3().setFromBufferAttribute(geometry.getAttribute("position") as BufferAttribute).getBoundingSphere(new Sphere());
    for (const landmark of landmarksForWorld(planet.id)) {
      const structure = bakeDiorama(parts.filter(part => part.structureId === landmark.structureId)).applyMatrix4(matrix);
      const points = structure.getAttribute("position");
      const bounds = new Box3().setFromBufferAttribute(points as BufferAttribute);
      const anchor = new Vector3(...landmark.anchor).applyMatrix4(matrix);
      for (const [width, height] of [[747.5, 740], [582.4, 660], [399.04, 570], [343.36, 570]]) for (const orientation of [{ yaw: 0, pitch: 0 }, { yaw: 75, pitch: 24 }, { yaw: -140, pitch: -12 }]) {
        const basis = inspectionCameraBasis(world.rotation, orientation);
        const from = { position: basis.offset.multiplyScalar(inspectionDistance(world.scale, width / height, height, world.id)).add(new Vector3(...world.focusTarget)), target: new Vector3(...world.focusTarget), up: basis.up, fov: 40 };
        const vertices: Vector3[] = [];
        for (let i = 0; i < points.count; i++) vertices.push(new Vector3().fromBufferAttribute(points, i));
        const pose = landmarkCameraPose(anchor, bounds, worldBounds, from, width, height, vertices);
        expect(pose.position.distanceTo(anchor), landmark.id + " approaches its anchor").toBeLessThan(from.position.distanceTo(anchor));
        for (let i = 0; i <= 10; i++) expect(new Vector3().lerpVectors(from.position, pose.position, i / 10).distanceTo(worldBounds.center)).toBeGreaterThan(worldBounds.radius);
        const camera = new PerspectiveCamera(pose.fov, width / height, .1, 80);
        camera.position.copy(pose.position); camera.up.copy(pose.up); camera.lookAt(pose.target); camera.updateMatrixWorld();
        expect(pose.target.clone().project(camera).x).toBeCloseTo(0, 8); expect(pose.target.clone().project(camera).y).toBeCloseTo(0, 8);
        for (let i = 0; i < points.count; i++) {
          const p = new Vector3().fromBufferAttribute(points, i).project(camera);
          const y = (1 - p.y) * height / 2;
          assert(Math.abs(p.x) < .85 && y > 90 && y < height - 120 && p.z > -1 && p.z < 1, landmark.id + " frame at " + width + "px yaw=" + orientation.yaw + " pitch=" + orientation.pitch);
        }
      }
      structure.dispose();
    }
    geometry.dispose();
  }
});

type View = { anchor: number[]; projectedAnchor: number[]; projectedFocusTarget: number[]; projectedMin: number[]; projectedMax: number[]; distance: number; matrix: number[] };
type Harness = HTMLElement & { __universeController: UniverseController; __landmarkView: (id: string) => View; __universeRender: () => { camera: number[]; cameraQuaternion: number[]; cameraUp: number[] } };
const region = (page: Page) => page.getByRole("region", { name: "Project Universe" });
const scene = (page: Page) => region(page).locator('[data-ready="true"]');
const detail = (page: Page) => region(page).getByRole("article", { name: / project details$/ });
const view = (page: Page, id: string) => scene(page).evaluate((e, id) => (e as Harness).__landmarkView(id), id);
const camera = (page: Page) => scene(page).evaluate(e => {
  const r = (e as Harness).__universeRender();
  return { position: r.camera, quaternion: r.cameraQuaternion, up: r.cameraUp, orientation: (e as Harness).__universeController.inspection.getOrientation() };
});
async function expectRestored(page: Page, before: Awaited<ReturnType<typeof camera>>) {
  await expect.poll(async () => { const now = await camera(page); return Math.max(...now.position.map((v, i) => Math.abs(v - before.position[i]))); }).toBeLessThan(1e-8);
  const now = await camera(page); expect(now.orientation).toEqual(before.orientation);
  for (const key of ["quaternion", "up"] as const) for (let i = 0; i < now[key].length; i++) expect(now[key][i]).toBeCloseTo(before[key][i], 8);
}

test("all 12 selections focus the real anchor, retain details, and restore the previous inspection view", async ({ page }) => {
  test.setTimeout(120000); await page.goto("/"); await expect(scene(page)).toBeVisible();
  await expect(region(page)).toHaveAttribute("data-exploration-mode", "click");
  await expect(region(page).getByRole("button", { name: /First.Person|Third.Person/i })).toHaveCount(0);
  await expect(region(page).getByRole("button", { name: "Focus Landmark" })).toHaveCount(0);
  for (const planet of universePlanets) {
    await region(page).getByRole("button", { name: planet.name, exact: true }).click();
    await expect(scene(page)).toHaveAttribute("data-focus-phase", "planet");
    await expect(region(page).getByRole("button", { name: "Focus Landmark" })).toHaveCount(0);
    await scene(page).scrollIntoViewIfNeeded();
    await region(page).getByRole("group", { name: "Inspect " + planet.name }).focus(); await page.keyboard.press("ArrowRight");
    for (const landmark of landmarksForWorld(planet.id)) {
      const project = landmarkProject(landmark.id)!;
      await region(page).getByRole("button", { name: "Discover " + project.title, exact: true }).click();
      const before = await camera(page), world = await view(page, landmark.id), scroll = await page.evaluate(() => scrollY);
      await detail(page).getByRole("button", { name: "Focus Landmark" }).click();
      await expect(scene(page)).toHaveAttribute("data-focus-phase", "focused");
      await expect.poll(async () => (await view(page, landmark.id)).projectedFocusTarget.slice(0, 2).reduce((sum, v) => sum + Math.abs(v), 0)).toBeLessThan(1e-6);
      const focused = await view(page, landmark.id);
      expect(focused.matrix).toEqual(world.matrix); expect(focused.distance).toBeLessThan(world.distance);
      expect(focused.projectedMin[0]).toBeGreaterThan(-1); expect(focused.projectedMax[0]).toBeLessThan(1);
      expect(focused.projectedMin[1]).toBeGreaterThan(-1); expect(focused.projectedMax[1]).toBeLessThan(1);
      await expect(detail(page)).toHaveAccessibleName(project.title + " project details");
      await expect(scene(page)).toHaveAttribute("data-active-landmarks", new RegExp(landmark.id));
      await expect(region(page).getByRole("slider")).toBeDisabled();
      await expect(detail(page).getByRole("button", { name: "← All Projects" })).toBeDisabled();
      expect(await page.evaluate(() => scrollY)).toBe(scroll);
      await region(page).screenshot({ path: "test-results/m5-1-" + landmark.projectId + ".png" });
      await detail(page).getByRole("button", { name: "Return to Planet" }).click();
      await expect(scene(page)).toHaveAttribute("data-focus-phase", "planet"); await expectRestored(page, before);
      await expect(detail(page)).toHaveAccessibleName(project.title + " project details");
      await page.keyboard.press("Escape"); await expect(detail(page)).toHaveCount(0);
    }
    await region(page).getByRole("button", { name: "Back to Universe" }).click();
  }
});

test("normal motion approaches, cancels safely, stays stationary, and Escape/Back/revisit preserve priorities", async ({ page }) => {
  await page.goto("/"); await expect(scene(page)).toBeVisible();
  await region(page).getByRole("button", { name: "Platforms / Suites", exact: true }).click();
  await region(page).getByRole("group", { name: "Inspect Platforms / Suites" }).focus();
  await page.keyboard.press("ArrowRight"); await page.keyboard.press("ArrowUp");
  await region(page).getByRole("button", { name: "Discover Neuran", exact: true }).click();
  await scene(page).scrollIntoViewIfNeeded(); await page.emulateMedia({ reducedMotion: "no-preference" });
  const before = await camera(page);
  await detail(page).getByRole("button", { name: "Focus Landmark" }).click();
  await expect(scene(page)).toHaveAttribute("data-focus-phase", "approaching");
  await expect(region(page).getByRole("group", { name: "Inspect Platforms / Suites" })).toHaveAttribute("data-enabled", "false");
  expect(await scene(page).evaluate(e => (e as Harness).__universeController.focusLandmark("landmark-playdeck"))).toBe(false);
  await page.keyboard.press("Escape");
  await expect(scene(page)).toHaveAttribute("data-focus-phase", "returning");
  await page.keyboard.press("Escape"); await expect(detail(page)).toHaveAccessibleName("Neuran project details");
  await expect(scene(page)).toHaveAttribute("data-focus-phase", "planet"); await expectRestored(page, before);
  for (let i = 0; i < 2; i++) {
    await detail(page).getByRole("button", { name: "Focus Landmark" }).click();
    await expect(scene(page)).toHaveAttribute("data-focus-phase", "focused");
    const stationary = await camera(page); await page.waitForTimeout(160); expect(await camera(page)).toEqual(stationary);
    await expect(detail(page).getByRole("link")).toHaveCount(5);
    await detail(page).getByRole("button", { name: "Return to Planet" }).click();
    await expect(scene(page)).toHaveAttribute("data-focus-phase", "planet"); await expectRestored(page, before);
  }
  await detail(page).getByRole("button", { name: "Focus Landmark" }).click();
  await region(page).getByRole("button", { name: "Back to Universe" }).click();
  await expect(scene(page)).toHaveAttribute("data-state", /overview/);
  await expect(scene(page)).toHaveAttribute("data-focus-phase", "planet"); await expect(detail(page)).toHaveCount(0);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await region(page).getByRole("button", { name: "Platforms / Suites", exact: true }).click();
  await expect(scene(page)).toHaveAttribute("data-focused-landmark", "");
  await expect(region(page).getByRole("button", { name: "Discover Neuran", exact: true })).toBeVisible();
});

test("fallback and resize remove 3D focus while retaining project access and selection", async ({ page }) => {
  await page.goto("/"); await expect(scene(page)).toBeVisible();
  await region(page).getByRole("button", { name: "Platforms / Suites", exact: true }).click();
  await region(page).getByRole("button", { name: "Discover Neuran", exact: true }).click();
  await detail(page).getByRole("button", { name: "Focus Landmark" }).click();
  await expect(scene(page)).toHaveAttribute("data-focus-phase", "focused");
  await page.setViewportSize({ width: 768, height: 1000 });
  await expect.poll(async () => Math.abs((await view(page, "landmark-neuran")).projectedFocusTarget[0])).toBeLessThan(1e-6);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(region(page).locator("canvas")).toHaveCount(0);
  await expect(detail(page)).toHaveAccessibleName("Neuran project details"); await expect(detail(page).getByRole("link")).toHaveCount(5);
  await expect(detail(page).getByRole("button", { name: /Focus Landmark|Return to Planet/ })).toHaveCount(0);
  await page.keyboard.press("Escape"); await expect(detail(page)).toHaveCount(0);
  await region(page).getByRole("button", { name: "Discover Playdeck", exact: true }).click();
  await expect(detail(page)).toHaveAccessibleName("Playdeck project details");
  await page.setViewportSize({ width: 1440, height: 1000 }); await expect(scene(page)).toBeVisible();
  await expect(scene(page)).toHaveAttribute("data-focus-phase", "planet");
  await expect(detail(page).getByRole("button", { name: "Focus Landmark" })).toBeVisible();
});
