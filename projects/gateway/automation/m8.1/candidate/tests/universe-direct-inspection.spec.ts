import assert from "node:assert/strict";
import { expect, test, type Page } from "@playwright/test";
import { Euler, Matrix4, PerspectiveCamera, Quaternion, Vector3 } from "three";
import { InspectionController, wrapInspectionYaw } from "../lib/universe-inspection";
import { inspectionCameraBasis } from "../lib/inspection-camera";
import { UniverseController } from "../lib/universe-controller";
import { inspectionDistance, universePlanets } from "../lib/universe-config";
import { bakeDiorama } from "../components/universe/diorama-primitives";
import { worldRecipe } from "../components/universe/world-recipes";

test("direct input wraps, clamps, reverses at limits, and stops precisely", () => {
  const inspection = new InspectionController();
  expect(inspection.beginDrag(1, 0, 0)).toBe(false);
  inspection.setEnabled(true);
  expect(inspection.beginDrag(1, 20, 30)).toBe(true);
  expect(inspection.beginDrag(2, 20, 30)).toBe(false);
  inspection.moveDrag(2, 120, 80);
  expect(inspection.getOrientation()).toEqual({ yaw: 0, pitch: 0 });
  inspection.moveDrag(1, 120, 80);
  expect(inspection.getOrientation()).toEqual({ yaw: 30, pitch: 10 });
  inspection.moveDrag(1, 1220, 1000);
  expect(inspection.getOrientation()).toEqual({ yaw: 0, pitch: 24 });
  inspection.moveDrag(1, 1230, 995);
  expect(inspection.getOrientation()).toEqual({ yaw: 3, pitch: 23 });
  inspection.moveDrag(1, 1230, -1000);
  expect(inspection.getOrientation().pitch).toBe(-12);
  inspection.endDrag(2);
  expect(inspection.dragging).toBe(true);
  inspection.endDrag(1);
  const released = inspection.getOrientation();
  inspection.moveDrag(1, 0, 0);
  expect(inspection.getOrientation()).toBe(released);
  expect(wrapInspectionYaw(181)).toBe(-179);
  expect(wrapInspectionYaw(-181)).toBe(179);
  expect(wrapInspectionYaw(360 * 1000 + 30)).toBe(30);
  inspection.reset();
  for (const key of ["ArrowRight", "ArrowRight", "ArrowUp"]) expect(inspection.key(key)).toBe(true);
  expect(inspection.getOrientation()).toEqual({ yaw: 10, pitch: -5 });
  inspection.key("ArrowLeft"); inspection.key("ArrowDown");
  expect(inspection.getOrientation()).toEqual({ yaw: 5, pitch: 0 });
  expect(inspection.key("PageDown")).toBe(false);
  inspection.beginDrag(3, 0, 0);
  inspection.setEnabled(false);
  expect(inspection.dragging).toBe(false);
  expect(inspection.key("ArrowRight")).toBe(false);
});

test("inspection input does not notify React state or mutate canonical targets", () => {
  const planet = { ...universePlanets[0], focusTarget: [1, 2, 3] as [number, number, number], travelTarget: [4, 5, 6] as [number, number, number], landingTarget: [7, 8, 9] as [number, number, number] };
  const controller = new UniverseController([planet]);
  controller.setFallback(false); controller.setReduced(true); controller.select(planet.id);
  const frozen = structuredClone(controller.destination);
  const canonical = structuredClone(controller.transform(planet.id));
  let renders = 0;
  controller.subscribe(() => renders++);
  controller.inspection.beginDrag(1, 0, 0);
  for (let x = 0; x < 2000; x++) controller.inspection.moveDrag(1, x, x / 10);
  controller.inspection.endDrag();
  expect(renders).toBe(0);
  expect(controller.destination).toEqual(frozen);
  expect(controller.transform(planet.id)).toEqual(canonical);
  controller.inspection.beginDrag(2, 0, 0);
  controller.back();
  expect(controller.inspection.dragging).toBe(false);
  controller.select(planet.id);
  expect(controller.inspection.getOrientation()).toEqual({ yaw: 0, pitch: 0 });
});

test("near-side geometry follows the gesture and reset restores the canonical camera", () => {
  for (const planet of universePlanets) {
    const project = (yaw: number, pitch: number) => {
      const basis = inspectionCameraBasis(planet.rotation, { yaw, pitch });
      const camera = new PerspectiveCamera(40, 1.5, 0.1, 80);
      camera.position.copy(basis.offset).multiplyScalar(12);
      camera.up.copy(basis.up); camera.lookAt(0, 0, 0); camera.updateMatrixWorld();
      return new Vector3(0, 0, 1).project(camera);
    };
    expect(project(10, 0).x).toBeGreaterThan(project(0, 0).x);
    expect(project(-10, 0).x).toBeLessThan(project(0, 0).x);
    // NDC Y is upward, opposite to pointer/screen Y.
    expect(project(0, 10).y).toBeLessThan(project(0, 0).y);
    expect(project(0, -10).y).toBeGreaterThan(project(0, 0).y);
    const canonical = inspectionCameraBasis(planet.rotation, { yaw: 0, pitch: 0 });
    expect(canonical.offset.toArray()).toEqual([0, 0, 1]);
    expect(canonical.up.toArray()).toEqual([0, 1, 0]);
  }
});

test("full-circle camera remains above the miniature, centered, and clear of UI", () => {
  const controller = new UniverseController(universePlanets);
  for (const planet of universePlanets) {
    const world = controller.transform(planet.id);
    const geometry = bakeDiorama(worldRecipe(planet));
    const orientation = new Quaternion().setFromEuler(new Euler(...world.rotation));
    geometry.applyMatrix4(new Matrix4().compose(new Vector3(...world.position), orientation, new Vector3().setScalar(world.scale * 1.025)));
    const points = geometry.getAttribute("position");
    const up = new Vector3(0, 1, 0).applyQuaternion(orientation);
    for (const [width, height] of [[1150, 740], [896, 660], [688, 570], [592, 570], [747.5, 740], [582.4, 660], [399.04, 570], [343.36, 570]]) {
      for (let yaw = -180; yaw <= 180; yaw += 15) for (const pitch of [-12, 0, 24]) {
        const basis = inspectionCameraBasis(world.rotation, { yaw, pitch });
        assert(basis.offset.dot(up) > 0.2, `${planet.id}: camera underneath`);
        const camera = new PerspectiveCamera(40, width / height, 0.1, 80);
        camera.position.copy(basis.offset).multiplyScalar(inspectionDistance(world.scale, width / height, height, world.id)).add(new Vector3(...world.focusTarget));
        camera.up.copy(basis.up);
        camera.lookAt(new Vector3(...world.focusTarget));
        camera.updateMatrixWorld();
        const focus = new Vector3(...world.focusTarget).project(camera);
        assert(Math.abs(focus.x) < 1e-8 && Math.abs(focus.y) < 1e-8);
        for (let i = 0; i < points.count; i++) {
          const projected = new Vector3().fromBufferAttribute(points, i).project(camera);
          const x = (projected.x + 1) * width / 2;
          const y = (1 - projected.y) * height / 2;
          assert(x > 20 && x < width - 20 && y > 80 && y < height - 105,
            `${planet.id} ${width}px yaw=${yaw} pitch=${pitch}: x=${x} y=${y}`);
        }
      }
    }
    const before = inspectionCameraBasis(world.rotation, { yaw: 179.999, pitch: 5 });
    const after = inspectionCameraBasis(world.rotation, { yaw: -179.999, pitch: 5 });
    assert(before.offset.distanceTo(after.offset) < 0.0001);
    assert(before.up.distanceTo(after.up) < 0.0001);
    geometry.dispose();
  }
});

const region = (page: Page) => page.getByRole("region", { name: "Project Universe" });
const scene = (page: Page) => region(page).locator('[data-ready="true"]');
const surface = (page: Page) => region(page).getByRole("group", { name: /^Inspect / });
async function openWorld(page: Page, name = "Games") {
  await page.goto("/");
  await expect(scene(page)).toBeVisible();
  await scene(page).scrollIntoViewIfNeeded();
  await region(page).getByRole("button", { name, exact: true }).click();
  await expect(scene(page)).toHaveAttribute("data-state", "inspecting");
}
async function orientation(page: Page) {
  return scene(page).evaluate((element) => {
    const controller = (element as HTMLElement & { __universeController: UniverseController }).__universeController;
    return { ...controller.inspection.getOrientation(), dragging: controller.inspection.dragging,
      seconds: controller.seconds, destination: controller.destination };
  });
}
async function drag(page: Page, dx: number, dy: number, release = true) {
  await expect(surface(page)).toHaveAttribute("data-enabled", "true");
  await surface(page).scrollIntoViewIfNeeded();
  const box = (await surface(page).boundingBox())!;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2 + dx, box.y + box.height / 2 + dy, { steps: 5 });
  if (release) await page.mouse.up();
}

test("pointer capture, direct direction, cursor, release, cancel and keyboard work", async ({ page }) => {
  await openWorld(page);
  await expect(surface(page)).toHaveCSS("cursor", "grab");
  const canonical = (await orientation(page)).destination;
  await drag(page, 100, 50, false);
  await expect(surface(page)).toHaveCSS("cursor", "grabbing");
  const moved = await orientation(page);
  expect(moved.yaw).toBe(30); expect(moved.pitch).toBe(10);
  expect(moved.destination).toEqual(canonical);
  expect(await surface(page).evaluate((element) => element.hasPointerCapture(1))).toBe(true);
  // Capture keeps the gesture alive outside the original surface.
  await page.mouse.move(5, 5);
  expect((await orientation(page)).yaw).not.toBe(30);
  await page.mouse.up();
  const released = await orientation(page);
  await page.mouse.move(20, 20);
  expect(await orientation(page)).toEqual(released);
  await expect(surface(page)).toHaveCSS("cursor", "grab");
  expect(await surface(page).evaluate((element) => element.hasPointerCapture(1))).toBe(false);
  await region(page).getByRole("button", { name: "Reset view" }).click();
  await drag(page, 40, -20, false);
  await surface(page).dispatchEvent("pointercancel", { pointerId: 1 });
  await expect(surface(page)).toHaveAttribute("data-dragging", "false");
  expect(await surface(page).evaluate((element) => element.hasPointerCapture(1))).toBe(false);
  await page.mouse.up();
  await region(page).getByRole("button", { name: "Reset view" }).click();
  await surface(page).focus();
  for (const key of ["ArrowRight", "ArrowRight", "ArrowDown"]) await page.keyboard.press(key);
  expect(await orientation(page)).toMatchObject({ yaw: 10, pitch: 5 });
  await page.keyboard.press("ArrowLeft"); await page.keyboard.press("ArrowUp");
  expect(await orientation(page)).toMatchObject({ yaw: 5, pitch: 0 });
  const slider = region(page).getByRole("slider");
  await expect(slider).toHaveValue("5");
  await slider.focus(); await page.keyboard.press("End");
  expect(await orientation(page)).toMatchObject({ yaw: 180, pitch: 0 });
  await region(page).getByRole("button", { name: "Reset view" }).click();
  expect(await orientation(page)).toMatchObject({ yaw: 0, pitch: 0 });
  await page.keyboard.press("ArrowRight"); // Reset remains focused: no global shortcut.
  expect(await orientation(page)).toMatchObject({ yaw: 0, pitch: 0 });
});

test("pause and reduced motion permit drag; Back cancels capture and revisit resets", async ({ page }) => {
  await openWorld(page);
  await drag(page, 200, 100);
  expect(await orientation(page)).toMatchObject({ yaw: 60, pitch: 20 });
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await region(page).getByRole("button", { name: "Pause motion" }).click();
  const before = await orientation(page);
  await drag(page, 100, -50, false);
  expect(await orientation(page)).toMatchObject({ yaw: 90, pitch: 10, seconds: before.seconds });
  // Keyboard activation of Back while the pointer is still held.
  await region(page).getByRole("button", { name: "Back to Universe" }).focus();
  await page.keyboard.press("Enter");
  await expect(scene(page)).toHaveAttribute("data-state", "returning");
  expect((await orientation(page)).dragging).toBe(false);
  expect(await surface(page).evaluate((element) => element.hasPointerCapture(1))).toBe(false);
  await page.mouse.up();
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(scene(page)).toHaveAttribute("data-state", "overview-paused");
  await region(page).getByRole("button", { name: "Games", exact: true }).click();
  expect(await orientation(page)).toMatchObject({ yaw: 0, pitch: 0, seconds: before.seconds });
  await drag(page, -100, 300);
  expect(await orientation(page)).toMatchObject({ yaw: -30, pitch: 24 });
  await region(page).getByRole("button", { name: "Reset view" }).click();
  expect(await orientation(page)).toMatchObject({ yaw: 0, pitch: 0 });
});

test("back-side views and tablet touch gestures preserve framing and outside scroll", async ({ page, context }) => {
  test.setTimeout(120_000);
  await openWorld(page);
  for (const name of ["Games", "Tools", "After-Hours", "Learning"]) {
    if (name !== "Games") await region(page).getByRole("button", { name, exact: true }).click();
    for (const [view, yaw, pitch] of [["rear", 180, 0], ["tilted", 120, 24]] as const) {
      await scene(page).evaluate((element, angles) => {
        (element as HTMLElement & { __universeController: UniverseController }).__universeController.inspection.setOrientation(angles.yaw, angles.pitch);
      }, { yaw, pitch });
      await region(page).screenshot({ path: `test-results/m2-1-${name.toLowerCase()}-${view}.png` });
    }
    await region(page).getByRole("button", { name: "Back to Universe" }).click();
  }
  for (const width of [1366, 768, 640]) {
    await page.setViewportSize({ width, height: 1000 });
    await region(page).getByRole("button", { name: "Learning", exact: true }).click();
    await drag(page, 200, 100);
    await region(page).screenshot({ path: `test-results/m2-1-${width}-inspection.png` });
    await region(page).getByRole("button", { name: "Back to Universe" }).click();
  }
  const cdp = await context.newCDPSession(page);
  await cdp.send("Emulation.setTouchEmulationEnabled", { enabled: true, maxTouchPoints: 1 });
  await region(page).getByRole("button", { name: "Games", exact: true }).click();
  await surface(page).scrollIntoViewIfNeeded();
  const box = (await surface(page).boundingBox())!;
  const x = box.x + box.width / 2, y = box.y + box.height / 2;
  const scrollBefore = await page.evaluate(() => scrollY);
  await cdp.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x, y }] });
  await cdp.send("Input.dispatchTouchEvent", { type: "touchMove", touchPoints: [{ x: x + 100, y: y + 50 }] });
  await cdp.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
  expect(await orientation(page)).toMatchObject({ yaw: 30, pitch: 10, dragging: false });
  expect(await page.evaluate(() => scrollY)).toBe(scrollBefore);
  const canvas = (await region(page).locator("canvas").boundingBox())!;
  const edgeX = canvas.x + 8;
  await cdp.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: edgeX, y }] });
  await cdp.send("Input.dispatchTouchEvent", { type: "touchMove", touchPoints: [{ x: edgeX, y: y - 120 }] });
  await cdp.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
  await expect.poll(() => page.evaluate(() => scrollY)).toBeGreaterThan(scrollBefore);
  await cdp.detach();
});
