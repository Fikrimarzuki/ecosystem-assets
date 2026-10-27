const fs = require('node:fs'), path = require('node:path'), Module = require('node:module');
const app = 'D:/Code/porto-projects/app-gateway-fe', req = Module.createRequire(app + '/package.json'), ts = req('typescript');
const resolve = Module._resolveFilename;
Module._resolveFilename = function(id, p, ...r) { return resolve.call(this, id.startsWith('@/') ? path.join(app, id.slice(2)) : id, p, ...r); };
for (const ext of ['.ts', '.tsx']) require.extensions[ext] = (m, f) => m._compile(ts.transpileModule(fs.readFileSync(f, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true } }).outputText, f);
const { universePlanets, universeView, projectUniversePoint } = req('./lib/universe-config.ts');
const { orbitalPosition } = req('./lib/universe-orbit.ts');
const { bakeDiorama } = req('./components/universe/diorama-primitives.tsx');
const { worldRecipe } = req('./components/universe/world-recipes.ts');
const { Matrix4, Vector3, Quaternion, Euler } = req('three');
const output = [];
for (const enlarged of [false, true]) {
  const vertices = universePlanets.map(p => {
    const parts = worldRecipe(p).map((part, i) => {
      if (!enlarged || p.id !== 'tools' || ![0, 1, 2].includes(i)) return part;
      const size = p.id === 'platforms' ? [6.4, 5.2] : [5.2, 4.4];
      return { ...part, size: [part.size[0] * size[0] / 2.72, part.size[1], part.size[2] * size[1] / 2.32] };
    });
    const g = bakeDiorama(parts), positions = g.getAttribute('position'), v = [];
    const matrix = new Matrix4().compose(new Vector3(), new Quaternion().setFromEuler(new Euler(...p.rotation)), new Vector3().setScalar(p.scale * 1.025));
    for (let i = 0; i < positions.count; i++) v.push(new Vector3().fromBufferAttribute(positions, i).applyMatrix4(matrix));
    g.dispose(); return v;
  });
  for (const [width, height] of [[1440, 900], [768, 700]]) {
    const view = universeView(width, height); let maxOverlap = 0, clippedWorldSamples = 0, pair = '', worstTime = 0;
    for (let time = 0; time < 600; time += 5) {
      const rectangles = universePlanets.map((p, i) => {
        const at = orbitalPosition(p.orbit, time), points = vertices[i].map(v => projectUniversePoint([v.x + at[0], v.y + at[1], v.z + at[2]], view));
        const rect = { l: Math.min(...points.map(p => p.x)), r: Math.max(...points.map(p => p.x)), t: Math.min(...points.map(p => p.y)), b: Math.max(...points.map(p => p.y)) };
        if (rect.l < 0 || rect.r > 1 || rect.t < 0 || rect.b > 1) clippedWorldSamples++;
        return rect;
      });
      for (let i = 0; i < rectangles.length; i++) for (let j = i + 1; j < rectangles.length; j++) {
        const a = rectangles[i], b = rectangles[j], overlap = Math.max(0, Math.min(a.r, b.r) - Math.max(a.l, b.l)) * Math.max(0, Math.min(a.b, b.b) - Math.max(a.t, b.t));
        const ratio = overlap / Math.min((a.r-a.l)*(a.b-a.t), (b.r-b.l)*(b.b-b.t));
        if (ratio > maxOverlap) { maxOverlap = ratio; pair = universePlanets[i].id + '/' + universePlanets[j].id; worstTime = time; }
      }
    }
    output.push({ enlarged, width, height, maxProjectedAABBOverlapFraction: maxOverlap, pair, worstTime, clippedWorldSamples, worldSamples: 720 });
  }
}
fs.writeFileSync(path.join(__dirname, 'tools-overview-probe.json'), JSON.stringify({ method: 'Hypothetical enlargement of the three island-base parts only; existing transforms, buildings and overview projection. 5-second orbit samples, fixed authored rotation; no bob/yaw, labels, station or rendered occlusion. Projected AABB risk estimate, not production layout validation.', output }, null, 2));
console.log(JSON.stringify(output, null, 2));

