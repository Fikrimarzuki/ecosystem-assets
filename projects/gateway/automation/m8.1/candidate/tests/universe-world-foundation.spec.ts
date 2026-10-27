import { test, expect, type Locator, type Page } from "@playwright/test";
import type { Mesh, Scene, PerspectiveCamera } from "three";
import { DEFAULT_WORLD_DIMENSIONS, worldDimensions, worldInspectionExtent } from "../lib/world-dimensions";
import { universePlanets } from "../lib/universe-config";
import { projectLocations, projectLandmarks, validateProjectLocations, landmarksFromLocations, type ProjectLocation } from "../lib/universe-landmarks";
import { featuredProjects } from "../lib/site-config";
import { worldRecipe } from "../components/universe/world-recipes";
import { worldNavigation } from "../components/universe/world-navigation";
import { bakeDiorama } from "../components/universe/diorama-primitives";
import { PLAYER, FirstPersonPlayer, safePosition, validSpawn, groundHeight } from "../lib/first-person";
import { ThirdPersonCamera, thirdPersonSpawnYaw, thirdPersonSpawnPitch, cameraBoomFraction } from "../lib/third-person";
import { walkingExplorationEnabled } from "../lib/universe-exploration";
import type { UniverseController } from "../lib/universe-controller";

const tools = universePlanets.find(p => p.id === "tools")!;

test("M8.1 dimensions migrate only Tools and keep other recipes at the original defaults", () => {
  expect(worldDimensions("tools")).toEqual({ width: 5.2, depth: 4.4 });
  for (const world of universePlanets) {
    const parts = worldRecipe(world), deck = parts.find(p => p.navigationRole === "ground")!;
    expect(deck.size).toEqual([worldDimensions(world.id).width, .1, worldDimensions(world.id).depth]);
    if (world.id !== "tools") {
      expect(worldDimensions(world.id)).toBe(DEFAULT_WORLD_DIMENSIONS);
      expect(parts[0].size).toEqual([2.65, .5, 2.25]); expect(parts[1].size).toEqual([2.5, .85, 2.05]);
      expect(worldInspectionExtent(world.id)).toBe(2);
    }
  }
  expect(worldDimensions("__proto__")).toBe(DEFAULT_WORLD_DIMENSIONS);
  expect(tools.scale).toBe(1.5); expect(PLAYER).toMatchObject({ height: .3, speed: .42, radius: .05 });
});

test("M8.1 rendered deck vertices are the navigation boundary and new land is supported", () => {
  const nav = worldNavigation(tools), deck = worldRecipe(tools).find(p => p.navigationRole === "ground")!;
  const geometry = bakeDiorama([deck]), positions = geometry.getAttribute("position");
  for (const point of nav.boundary) {
    let match = false;
    for (let i = 0; i < positions.count; i++) if (Math.abs(positions.getX(i) - point.x) < 1e-6 && Math.abs(positions.getZ(i) - point.z) < 1e-6 && Math.abs(positions.getY(i) - nav.groundY) < 1e-6) match = true;
    expect(match).toBe(true);
  }
  expect(nav.boundary).toHaveLength(10); expect(validSpawn(nav)).toBe(true);
  expect(nav.spawn).toEqual({ x: 0, y: .1805, z: .35 });
  expect(safePosition(nav, 2, .35)).toBe(true); expect(groundHeight(nav, 2, .35)).toBe(.18);
  expect(safePosition(nav, 3, 0)).toBe(false); expect(safePosition(nav, -.4, -.25)).toBe(false);
  expect(worldNavigation(tools)).toBe(nav); geometry.dispose();
});

test("M8.1 movement crosses the old edge, stops at the new inset, and still reaches CareerLens", () => {
  const nav = worldNavigation(tools), player = new FirstPersonPlayer();
  player.enter(nav); player.setActive(true); player.key("KeyS", true);
  for (let i = 0; i < 600; i++) player.advance(1 / 60);
  expect(player.position.x).toBeGreaterThan(2); expect(player.position.x).toBeLessThan(2.6);
  expect(safePosition(nav, player.position.x, player.position.z)).toBe(true);
  expect(player.position.y).toBe(.18);
  player.enter(nav); player.setActive(true); player.yaw = thirdPersonSpawnYaw(nav); player.key("KeyW", true);
  for (let i = 0; i < 90; i++) player.advance(1 / 60);
  expect(player.canInteract("landmark-careerlens")).toBe(true);
});

test("M8.1 terrain expansion adds no triangles, batches, obstacles or changed building dimensions", () => {
  const parts = worldRecipe(tools), nav = worldNavigation(tools), geometry = bakeDiorama(parts);
  expect(parts.find(p => p.structureId === "workshop-hall")?.size).toEqual([.96, .64, .8]);
  expect(parts.find(p => p.walkingPadding === .048)?.size).toEqual([.65, .26, .38]);
  expect(geometry.getAttribute("position").count / 3).toBe(898);
  expect(nav.obstacles).toHaveLength(24); expect(nav.paths).toHaveLength(1);
  expect(parts).toHaveLength(30);
  expect(projectLandmarks.filter(l => l.worldId === "tools")).toHaveLength(1); geometry.dispose();
});

test("M8.1 location validation rejects malformed, duplicate, unknown and nonoccupied project bindings", () => {
  const sample: ProjectLocation[] = [
    { id: "reserve", worldId: "tools", position: [1, .18, 1], state: "reserved" },
    { id: "decor", worldId: "tools", position: [1, .18, -1], rotation: [0, .2, 0], state: "decorative" },
    { id: "build", worldId: "tools", position: [-1, .18, 1], state: "construction" },
  ];
  expect(() => validateProjectLocations(sample)).not.toThrow();
  const invalid = (value: unknown) => expect(() => validateProjectLocations(value as ProjectLocation[])).toThrow();
  invalid([sample[0], sample[0]]);
  invalid([{ ...sample[0], projectId: "careerLens" }]);
  invalid([{ ...sample[0], state: "mystery" }]);
  invalid([{ ...sample[0], worldId: "missing" }]);
  invalid([{ ...sample[0], position: [NaN, 0, 0] }]);
  invalid([{ ...sample[0], rotation: [0, 0] }]);
  invalid([{ id: "unknown", worldId: "tools", state: "occupied", projectId: "missing-project", structureId: "hall", position: [0, 0, 0] }]);
  const occupied = projectLocations.find(l => l.id === "landmark-careerlens")!;
  invalid([{ ...occupied, worldId: "latest" }]);
  invalid([occupied, { ...occupied, id: "duplicate-binding" }]);
});

test("M8.1 locations retain all project identities and filter reserves and ineligible listings", () => {
  expect(projectLandmarks).toHaveLength(12);
  expect(projectLandmarks.map(l => l.projectId)).toEqual(["pageLayr", "tinyverse", "javascriptia", "kodeStep", "careerLens", "foodieMap", "tcgHub", "playdeck", "neuran", "nikahyuk", "nikahyukPrototype", "nikahkuy"]);
  expect(projectLandmarks.find(l => l.projectId === "careerLens")).toEqual({ id: "landmark-careerlens", projectId: "careerLens", worldId: "tools", anchor: [-.4, .8, -.25], structureId: "workshop-hall" });
  expect(projectLocations.find(l => l.state === "reserved")?.id).toBe("tools-reserve-east");
  expect(projectLandmarks.some(l => l.id === "tools-reserve-east")).toBe(false);
  const eligible = featuredProjects.filter(p => p.projectId !== "careerLens");
  expect(landmarksFromLocations(projectLocations, eligible).some(l => l.projectId === "careerLens")).toBe(false);
});

test("M8.1 Tools TPS stays collision-clear on the entry, bench frontage and expanded open ground", () => {
  const nav = worldNavigation(tools);
  for (const reduced of [false, true]) {
    const camera = new ThirdPersonCamera(), player = { position: { ...nav.spawn }, yaw: thirdPersonSpawnYaw(nav), pitch: thirdPersonSpawnPitch(nav) };
    for (const [x, z] of [[0, .35], [.4, .35], [.9, .35], [1.4, .35], [1.8, .35], [1.8, .8], [1.2, 1.2]]) {
      expect(safePosition(nav, x, z)).toBe(true);
      player.position = { x, z, y: groundHeight(nav, x, z) };
      for (let frame = 0; frame < 90; frame++) {
        camera.update(player, nav, 1 / 60, reduced, true, 1440 / 900);
        expect(cameraBoomFraction(camera.target, camera.position, nav.obstacles)).toBe(1);
        expect(camera.position.y).toBeGreaterThanOrEqual(groundHeight(nav, camera.position.x, camera.position.z) + .035 - 1e-8);
      }
    }
  }
});

type Harness = HTMLElement & { __universeController: UniverseController; __landmarkPoint: (id: string) => { x: number; y: number } | null; __universeRender: () => { calls: number; triangles: number; astronaut: { visible: boolean; assetState: string } | null } };
async function clickNative(page: Page, control: Locator) {
  await control.scrollIntoViewIfNeeded();
  expect(await control.evaluate(e => { const b = e.getBoundingClientRect(); return e.contains(document.elementFromPoint(b.x + b.width / 2, b.y + b.height / 2)); })).toBe(true);
  const b = (await control.boundingBox())!; await page.mouse.click(b.x + b.width / 2, b.y + b.height / 2);
}

async function toolsBounds(canvas: Locator) {
  return canvas.evaluate(element => {
    type State = { scene: Scene; camera: PerspectiveCamera };
    type Hook = { memoizedState?: { current?: State }; next?: Hook };
    type Fiber = { return?: Fiber; memoizedState?: Hook };
    const e = element as unknown as Record<string, Fiber>; let fiber: Fiber | undefined = e[Object.keys(e).find(k => k.startsWith("__reactFiber"))!], state: State | undefined;
    for (; fiber && !state; fiber = fiber.return) for (let h = fiber.memoizedState; h; h = h.next) if (h.memoizedState?.current?.scene && h.memoizedState.current.camera) { state = h.memoizedState.current; break; }
    if (!state) throw new Error("R3F inspection unavailable");
    state.scene.updateMatrixWorld(true); state.camera.updateMatrixWorld();
    const point = state.camera.position.clone(), bounds = { x: 0, y: 0, minDepth: Infinity, maxDepth: -Infinity };
    for (const name of ["tools-background", "landmark-careerlens", "gateway-rocket"]) {
      const root = state.scene.getObjectByName(name);
      if (!root) throw new Error("Missing rendered object: " + name);
      root?.traverse(node => {
        const mesh = node as Mesh; if (!mesh.isMesh) return;
        const vertices = mesh.geometry.getAttribute("position");
        for (let i = 0; i < vertices.count; i++) {
          point.fromBufferAttribute(vertices, i).applyMatrix4(mesh.matrixWorld).project(state!.camera);
          bounds.x = Math.max(bounds.x, Math.abs(point.x)); bounds.y = Math.max(bounds.y, Math.abs(point.y));
          bounds.minDepth = Math.min(bounds.minDepth, point.z); bounds.maxDepth = Math.max(bounds.maxDepth, point.z);
        }
      });
    }
    return bounds;
  });
}

for (const [width, height, motion] of [[1440, 900, "no-preference"], [768, 700, "reduce"]] as const) {
  test(`M8.1 native Tools/overview smoke ${width}px`, async ({ page }) => {
    test.skip(!walkingExplorationEnabled, "Requires a walking opt-in test server"); test.setTimeout(120_000);
    const errors: string[] = []; page.on("pageerror", error => errors.push(error.message));
    await page.setViewportSize({ width, height }); await page.emulateMedia({ reducedMotion: motion });
    await page.goto("/"); const universe = page.getByRole("region", { name: "Project Universe" }), scene = universe.locator('[data-ready="true"]');
    await expect(scene).toBeVisible(); await scene.scrollIntoViewIfNeeded();
    const canvas = universe.locator("canvas"), initialCanvas = await canvas.elementHandle();
    await scene.screenshot({ path: test.info().outputPath(`overview-${width}.png`) });
    await clickNative(page, universe.getByRole("button", { name: "Tools", exact: true }));
    await expect(scene).toHaveAttribute("data-state", "inspecting");
    await expect(universe.locator('[data-revealed="true"]')).toBeVisible(); await scene.scrollIntoViewIfNeeded();
    const bounds = await toolsBounds(canvas); expect(bounds.x).toBeLessThan(.96); expect(bounds.y).toBeLessThan(.96); expect(bounds.minDepth).toBeGreaterThan(-1); expect(bounds.maxDepth).toBeLessThan(1);
    console.log(`M8.1 rendered bounds ${width}: ${JSON.stringify(bounds)}`);
    await scene.screenshot({ path: test.info().outputPath(`tools-${width}.png`) });
    const point = await scene.evaluate(e => (e as Harness).__landmarkPoint("landmark-careerlens")); expect(point).not.toBeNull();
    await page.mouse.click(point!.x, point!.y);
    await expect(universe.getByRole("article", { name: "CareerLens project details" })).toBeVisible();
    await universe.getByRole("button", { name: "← All Projects", exact: true }).click();
    for (const [name, mode] of [["Explore in First Person", "first-person"], ["Explore in Third Person", "third-person"]]) {
      await clickNative(page, universe.getByRole("button", { name, exact: true }));
      await expect(universe).toHaveAttribute("data-exploration-mode", mode);
      await expect.poll(() => page.evaluate(() => !!document.pointerLockElement)).toBe(true);
      if (mode === "third-person") await expect.poll(() => scene.evaluate(e => (e as Harness).__universeRender().astronaut?.assetState)).toBe("ready");
      const before = await scene.evaluate(e => ({ ...(e as Harness).__universeController.player.position }));
      await page.keyboard.down("KeyS"); await expect.poll(async () => scene.evaluate((e, p) => { const next = (e as Harness).__universeController.player.position; return Math.hypot(next.x - p.x, next.z - p.z); }, before)).toBeGreaterThan(.025); await page.keyboard.up("KeyS");
      if (mode === "third-person") await scene.screenshot({ path: test.info().outputPath(`tps-${width}.png`) });
      else expect(await scene.evaluate(e => (e as Harness).__universeRender().astronaut?.visible ?? false)).toBe(false);
      await page.keyboard.press("Escape"); await clickNative(page, universe.getByRole("button", { name: "Return to Planet", exact: true }).first());
      await expect(universe).toHaveAttribute("data-exploration-mode", "click");
      await expect(universe.getByRole("group", { name: "Inspect Tools", exact: true })).toBeFocused();
    }
    await clickNative(page, universe.getByRole("button", { name: "Back to Universe", exact: true }));
    await expect(scene).toHaveAttribute("data-state", /overview/);
    expect(await initialCanvas!.evaluate(e => e === e.closest("section")?.querySelector("canvas"))).toBe(true);
    expect(errors).toEqual([]);
  });
}
