import { Euler, Vector3, type BufferGeometry } from "three";
import type { UniversePlanet } from "@/lib/universe-config";
import { landmarksForWorld } from "@/lib/universe-landmarks";
import { supportsFirstPerson, validSpawn, type NavigationSurface, type WorldNavigation } from "@/lib/first-person";
import { bakeDiorama, type DioramaPart } from "./diorama-primitives";
import { worldRecipe } from "./world-recipes";

/** A rock's box contains empty corners. Cache its convex projection and actual face planes once. */
function rockBounds(geometry: BufferGeometry, surface: NavigationSurface) {
  const vertices = geometry.getAttribute("position"), unique = new Map<string, { x: number; z: number }>();
  const a = new Vector3(), b = new Vector3(), c = new Vector3(), normal = new Vector3();
  const planes = new Map<string, { x: number; y: number; z: number; constant: number }>();
  for (let i = 0; i < vertices.count; i += 3) {
    a.fromBufferAttribute(vertices, i); b.fromBufferAttribute(vertices, i + 1); c.fromBufferAttribute(vertices, i + 2);
    normal.crossVectors(b.clone().sub(a), c.clone().sub(a)).normalize();
    const plane = { x: normal.x, y: normal.y, z: normal.z, constant: -normal.dot(a) };
    planes.set(Object.values(plane).map(value => value.toFixed(6)).join(":"), plane);
    for (const point of [a, b, c]) unique.set(point.x.toFixed(6) + ":" + point.z.toFixed(6), { x: point.x, z: point.z });
  }
  const points = [...unique.values()].sort((a, b) => a.x - b.x || a.z - b.z);
  const cross = (a: typeof points[number], b: typeof a, c: typeof a) => (b.x - a.x) * (c.z - a.z) - (b.z - a.z) * (c.x - a.x);
  const half = (input: typeof points) => {
    const hull: typeof points = [];
    for (const point of input) { while (hull.length >= 2 && cross(hull[hull.length - 2], hull[hull.length - 1], point) <= 1e-8) hull.pop(); hull.push(point); }
    return hull.slice(0, -1);
  };
  surface.footprint = [...half(points), ...half([...points].reverse())]; surface.planes = [...planes.values()];
}

const navigationCache = new WeakMap<UniversePlanet, WorldNavigation>();

/** Derive a candidate from the existing path, then validate ground/collision in worldNavigation. */
export function navigationSpawnPoint(surface: DioramaPart) {
  const offset = typeof surface.navigationSpawn === "object" ? surface.navigationSpawn : [0, 0];
  if (!Array.isArray(offset) || offset.length !== 2 || !offset.every(value => Number.isFinite(value) && Math.abs(value) <= .5)) throw new Error("World spawn offset is outside its support surface");
  const point = new Vector3(offset[0] * surface.size[0], surface.size[1] / 2, offset[1] * surface.size[2])
    .applyEuler(new Euler(...(surface.rotation ?? [0, 0, 0]))).add(new Vector3(...surface.position));
  return { x: point.x, y: point.y, z: point.z };
}

/** Built once from rendered recipe geometry; conservative height-filtered part bounds. */
export function worldNavigation(planet: UniversePlanet): WorldNavigation {
  if (!supportsFirstPerson(planet.id)) throw new Error("First-person navigation is unavailable for this world");
  const cached = navigationCache.get(planet);
  if (cached) return cached;
  const parts = worldRecipe(planet);
  const deck = parts.find(part => part.navigationRole === "ground");
  const road = parts.find(part => part.navigationRole === "path" && part.navigationSpawn) ?? parts.find(part => part.navigationRole === "path");
  const landmarks = landmarksForWorld(planet.id);
  if (!deck || deck.shape !== "cylinder" || !road || !landmarks.length) throw new Error("World navigation requires ground, path and landmark");
  const groundY = deck.position[1] + deck.size[1] / 2;
  const topPoints = new Map<string, { x: number; z: number }>();
  const bounds = parts.map(part => {
    const geometry = bakeDiorama([part]); geometry.computeBoundingBox();
    const box = geometry.boundingBox!.clone();
    const top = new Map<string, { x: number; z: number }>();
    if (part === deck || part.navigationRole === "path") {
      const vertices = geometry.getAttribute("position");
      for (let i = 0; i < vertices.count; i++) {
        const x = vertices.getX(i), y = vertices.getY(i), z = vertices.getZ(i);
        if (Math.abs(y - box.max.y) < .00001 && Math.hypot(x - part.position[0], z - part.position[2]) > .01) top.set(x.toFixed(6) + ":" + z.toFixed(6), { x, z });
      }
    }
    if (part === deck) for (const [key, point] of top) topPoints.set(key, point);
    const surface: NavigationSurface = { min: { x: box.min.x, y: box.min.y, z: box.min.z }, max: { x: box.max.x, y: box.max.y, z: box.max.z } };
    // Scope refined convex rock bounds to After-Hours; the existing five worlds retain their colliders.
    if (planet.id === "after-hours" && part.shape === "rock") rockBounds(geometry, surface);
    geometry.dispose();
    // Rotated low paths support only their actual top footprint, not empty AABB corners.
    if (part.navigationRole === "path" && part.rotation?.[1]) surface.footprint = [...top.values()].sort((a, b) => Math.atan2(a.z - part.position[2], a.x - part.position[0]) - Math.atan2(b.z - part.position[2], b.x - part.position[0]));
    return surface;
  });
  const boundary = [...topPoints.values()].sort((a, b) => Math.atan2(a.z - deck.position[2], a.x - deck.position[0]) - Math.atan2(b.z - deck.position[2], b.x - deck.position[0]));
  const paths = bounds.filter((_, i) => parts[i].navigationRole === "path");
  const obstacles = bounds.filter((b, i) => !parts[i].navigationRole && b.max.y > groundY);
  // Each building retains its actual per-part vertical/exterior bounds, including elevated parts.
  const interactions = landmarks.map(landmark => ({ landmarkId: landmark.id,
    bounds: bounds.filter((_, i) => parts[i].structureId === landmark.structureId) }));
  if (interactions.some(region => !region.bounds.length)) throw new Error("World landmark has no structure bounds");
  const body = interactions[0].bounds[0], spawn = navigationSpawnPoint(road);
  const nav: WorldNavigation = { worldId: planet.id, boundary, groundY, paths, obstacles,
    spawn,
    // Preserve Tools' west-facing road view; new worlds face their bound building body.
    spawnYaw: planet.id === "tools" ? (road.size[0] >= road.size[2] ? Math.PI / 2 : 0)
      : Math.atan2(spawn.x - (body.min.x + body.max.x) / 2, spawn.z - (body.min.z + body.max.z) / 2),
    interactions };
  if (!validSpawn(nav)) throw new Error("World spawn is obstructed");
  navigationCache.set(planet, nav);
  return nav;
}
