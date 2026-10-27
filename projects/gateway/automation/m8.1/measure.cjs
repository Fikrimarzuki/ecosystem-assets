// Read-only repo-derived geometry/navigation survey; outputs stay outside Gateway.
const fs = require('node:fs'), path = require('node:path'), Module = require('node:module');
const app = 'D:/Code/porto-projects/app-gateway-fe';
const req = Module.createRequire(app + '/package.json'), ts = req('typescript');
const resolve = Module._resolveFilename;
Module._resolveFilename = function(id, p, ...r) { return resolve.call(this, id.startsWith('@/') ? path.join(app, id.slice(2)) : id, p, ...r); };
for (const ext of ['.ts', '.tsx']) require.extensions[ext] = (m, f) => m._compile(ts.transpileModule(fs.readFileSync(f, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true } }).outputText, f);
const { universePlanets } = req('./lib/universe-config.ts');
const { worldRecipe } = req('./components/universe/world-recipes.ts');
const { bakeDiorama } = req('./components/universe/diorama-primitives.tsx');
const { worldNavigation } = req('./components/universe/world-navigation.ts');
const { landmarksForWorld } = req('./lib/universe-landmarks.ts');
const { safePosition, groundHeight, interactionDistance, PLAYER } = req('./lib/first-person.ts');
const { ThirdPersonCamera, thirdPersonSpawnYaw, thirdPersonSpawnPitch } = req('./lib/third-person.ts');
const { INTERACTION_DISTANCE } = req('./lib/first-person-interaction.ts');
const area = p => Math.abs(p.reduce((s, a, i) => { const b = p[(i + 1) % p.length]; return s + a.x * b.z - b.x * a.z; }, 0)) / 2;
class Heap {
  a = [];
  push(v) { let i = this.a.length; this.a.push(v); while (i) { const j = (i - 1) >> 1; if (this.a[j][0] <= v[0]) break; this.a[i] = this.a[j]; i = j; } this.a[i] = v; }
  pop() { const root = this.a[0], last = this.a.pop(); if (this.a.length) { let i = 0; while (2 * i + 1 < this.a.length) { let j = 2 * i + 1; if (j + 1 < this.a.length && this.a[j + 1][0] < this.a[j][0]) j++; if (this.a[j][0] >= last[0]) break; this.a[i] = this.a[j]; i = j; } this.a[i] = last; } return root; }
}
function survey(nav, h, targets) {
  const minX = Math.min(...nav.boundary.map(p => p.x)), minZ = Math.min(...nav.boundary.map(p => p.z));
  const nx = Math.ceil((Math.max(...nav.boundary.map(p => p.x)) - minX) / h), nz = Math.ceil((Math.max(...nav.boundary.map(p => p.z)) - minZ) / h);
  const pos = k => ({ x: minX + (k % nx + .5) * h, z: minZ + (Math.floor(k / nx) + .5) * h });
  const valid = new Uint8Array(nx * nz); let count = 0, nearest = -1, nearestD = Infinity;
  for (let k = 0; k < valid.length; k++) { const p = pos(k); if (safePosition(nav, p.x, p.z)) { valid[k] = 1; count++; const d = Math.hypot(p.x - nav.spawn.x, p.z - nav.spawn.z); if (d < nearestD) { nearestD = d; nearest = k; } } }
  const dist = new Float64Array(valid.length).fill(Infinity), heap = new Heap(); dist[nearest] = nearestD; heap.push([nearestD, nearest]);
  let reached = 0, farthest = 0; const approach = targets.map(() => Infinity);
  while (heap.a.length) {
    const [d, k] = heap.pop(); if (d !== dist[k]) continue;
    reached++; farthest = Math.max(farthest, d); const p = pos(k), x = k % nx, z = Math.floor(k / nx);
    if (targets.length) for (let i = 0; i < targets.length; i++) if (!Number.isFinite(approach[i]) && interactionDistance(nav, { ...p, y: groundHeight(nav, p.x, p.z) }, targets[i].id) <= INTERACTION_DISTANCE) approach[i] = d;
    for (let dz = -1; dz <= 1; dz++) for (let dx = -1; dx <= 1; dx++) {
      if ((!dx && !dz) || x + dx < 0 || x + dx >= nx || z + dz < 0 || z + dz >= nz) continue;
      const next = k + dz * nx + dx; if (!valid[next]) continue;
      const q = pos(next); if (!safePosition(nav, (p.x + q.x) / 2, (p.z + q.z) / 2)) continue;
      const nd = d + Math.hypot(dx, dz) * h; if (nd < dist[next]) { dist[next] = nd; heap.push([nd, next]); }
    }
  }
  return { gridStep: h, safeArea: count * h * h, reachableArea: reached * h * h, farthestShortestRoute: farthest, farthestTravelSeconds: farthest / PLAYER.speed, approach: targets.map((t, i) => ({ projectId: t.projectId, routeLength: approach[i], seconds: approach[i] / PLAYER.speed })) };
}
const results = universePlanets.map(planet => {
  const parts = worldRecipe(planet), nav = worldNavigation(planet), landmarks = landmarksForWorld(planet.id);
  const geometry = bakeDiorama(parts); geometry.computeBoundingBox(); const box = geometry.boundingBox;
  const triangles = geometry.getAttribute('position').count / 3; geometry.dispose();
  const deck = parts.find(p => p.navigationRole === 'ground');
  const yaw = thirdPersonSpawnYaw(nav), pitch = thirdPersonSpawnPitch(nav), cam = new ThirdPersonCamera();
  cam.update({ position: nav.spawn, yaw, pitch }, nav, 0, true, true, 1440 / 900);
  const spacing = landmarks.flatMap((a, i) => landmarks.slice(i + 1).map(b => ({ a: a.projectId, b: b.projectId, xzDistance: Math.hypot(a.anchor[0] - b.anchor[0], a.anchor[2] - b.anchor[2]) })));
  return { id: planet.id, scale: planet.scale, deckSize: deck.size, terrainBounds: { x: Math.max(...nav.boundary.map(p => p.x)) - Math.min(...nav.boundary.map(p => p.x)), z: Math.max(...nav.boundary.map(p => p.z)) - Math.min(...nav.boundary.map(p => p.z)) }, grossArea: area(nav.boundary), groundY: nav.groundY, spawn: nav.spawn, yaw: nav.spawnYaw,
    paths: parts.filter(p => p.navigationRole === 'path').map(p => ({ position: p.position, size: p.size, rotation: p.rotation ?? [0, 0, 0] })), landmarks, spacing, obstacles: nav.obstacles.length, bodyHeightObstaclesAtDeck: nav.obstacles.filter(b => b.max.y > nav.groundY + .0001 && b.min.y - (b.walkingPadding ?? 0) < nav.groundY + PLAYER.height).length,
    recipeParts: parts.length, triangles, dioramaDraws: 1 + landmarks.length, geometryBounds: { min: box.min.toArray(), max: box.max.toArray() },
    spawnTPS: { yaw, pitch, eye: cam.position, target: cam.target, boom: Math.hypot(cam.position.x - cam.target.x, cam.position.y - cam.target.y, cam.position.z - cam.target.z), fov: cam.fov },
    coarse: survey(nav, .01, []), fine: survey(nav, .005, landmarks) };
});
fs.writeFileSync(path.join(__dirname, 'measurements.json'), JSON.stringify({ head: 'e4e6f34', units: 'world-local units before planet transforms', method: 'safePosition raster; 8-neighbor Dijkstra with midpoint clearance; not a native input or camera sweep test', player: PLAYER, results }, null, 2));
for (const r of results) console.log(JSON.stringify({ id: r.id, bounds: r.terrainBounds, gross: r.grossArea, safe: r.fine.safeArea, reachable: r.fine.reachableArea, convergence: r.fine.safeArea - r.coarse.safeArea, time: r.fine.farthestTravelSeconds, approach: r.fine.approach, obstacles: r.obstacles, body: r.bodyHeightObstaclesAtDeck, triangles: r.triangles, parts: r.recipeParts, draws: r.dioramaDraws, boom: r.spawnTPS.boom, pitch: r.spawnTPS.pitch, fov: r.spawnTPS.fov, spacing: r.spacing }));

