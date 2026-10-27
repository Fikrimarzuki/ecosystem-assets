// M1.0l-A3 composite test (working copy only; the master and A1 layers are never written).
// Takes the panel-3 close-up DOWNSCALED to master scale by the fitted factor (analysis.json) and placed at the fitted
// offset, cuts it with each A1 open-eye mask (eye-near, eye-far) and composites it over a COPY of the master.
// Measures: pixels changed outside the masks (must be 0 by construction), the seam (mask-edge pixels vs their
// outside neighbours, compared with the master's own edge contrast), skin colour inside the mask vs the ring outside,
// eye alignment (centroid of dark lash pixels vs the A1 open-eye centroid) and fringe overlap.
// Usage: node composite_l3.mjs <master.png> <a1LayersDir> <fittedP3OnCanvas.png> <outDir>
import { writeFileSync } from 'node:fs';
const T = await import('/Users/mfm/code/porto-projects/ecosystem-assets/scripts/momee-character-master.mjs');
const [, , masterPath, A1, p3Path, out] = process.argv;
const M = T.readPng(masterPath), C = T.readPng(p3Path), W = M.width, H = M.height;
const masks = { 'eye-near': T.readPng(`${A1}/face-eyes__open__eye-near.png`).data, 'eye-far': T.readPng(`${A1}/face-eyes__open__eye-far.png`).data };
const comp = new Uint8Array(M.data);
const R = {};
const lum = (d, o) => 0.2126 * d[o] + 0.7152 * d[o + 1] + 0.0722 * d[o + 2];
for (const [name, m] of Object.entries(masks)) {
  let n = 0, x0 = W, y0 = H, x1 = 0, y1 = 0; for (let i = 0; i < W * H; i++) if (m[i * 4 + 3]) { n++; comp.set(C.data.subarray(i * 4, i * 4 + 3), i * 4); comp[i * 4 + 3] = M.data[i * 4 + 3]; const x = i % W, y = (i - x) / W; x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
  // seam: for mask pixels with a 4-neighbour outside the mask: |comp(in) − master(out)| vs |master(in) − master(out)|
  let sc = 0, sm = 0, k = 0, big = 0;
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) { const i = y * W + x; if (!m[i * 4 + 3]) continue;
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const j = (y + dy) * W + x + dx; if (m[j * 4 + 3]) continue;
      let ec = 0, em = 0; for (let c = 0; c < 3; c++) { ec += Math.abs(comp[i * 4 + c] - M.data[j * 4 + c]); em += Math.abs(M.data[i * 4 + c] - M.data[j * 4 + c]); }
      sc += ec / 3; sm += em / 3; k++; if (ec / 3 > 25) big++; } }
  // skin inside the mask (light pixels, luma ≥ 170) vs skin in a 6 px ring outside
  const ring = []; for (let y = y0 - 6; y <= y1 + 6; y++) for (let x = x0 - 6; x <= x1 + 6; x++) { const i = y * W + x; if (m[i * 4 + 3]) continue; let near = false; for (let dy = -6; dy <= 6 && !near; dy++) for (let dx = -6; dx <= 6; dx++) if (m[((y + dy) * W + x + dx) * 4 + 3]) { near = true; break; } if (near && lum(M.data, i * 4) >= 170 && M.data[i * 4 + 3] === 255) ring.push(i); }
  const mean = (d, idx) => { const s = [0, 0, 0]; for (const i of idx) for (let c = 0; c < 3; c++) s[c] += d[i * 4 + c] / idx.length; return s.map((v) => Math.round(v)); };
  const inSkin = []; for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) { const i = y * W + x; if (m[i * 4 + 3] && lum(comp, i * 4) >= 170) inSkin.push(i); }
  // alignment: centroid of dark (luma < 90) pixels in the mask — open eye (master) vs closed eye (candidate); closed lashes sit at the lid line
  const cen = (d) => { let sx = 0, sy = 0, c = 0; for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) { const i = y * W + x; if (m[i * 4 + 3] && lum(d, i * 4) < 90) { sx += x; sy += y; c++; } } return c ? [Math.round(sx / c), Math.round(sy / c), c] : null; };
  R[name] = { maskPixels: n, bbox: [x0, y0, x1, y1], seam: { edgePairs: k, compositeMeanAbs: +(sc / k).toFixed(1), masterOwnEdgeMeanAbs: +(sm / k).toFixed(1), pairsOver25: big },
    skin: { candidateInsideMask: mean(comp, inSkin), masterRingOutside: mean(M.data, ring), insideSkinPixels: inSkin.length }, darkCentroid: { masterOpen: cen(M.data), candidateClosed: cen(comp) } };
}
let outside = 0; for (let i = 0; i < W * H; i++) { if (masks['eye-near'][i * 4 + 3] || masks['eye-far'][i * 4 + 3]) continue; for (let c = 0; c < 4; c++) if (comp[i * 4 + c] !== M.data[i * 4 + c]) { outside++; break; } }
R.pixelsChangedOutsideMasks = outside;
T.writePng(`${out}/composite-closed-on-master-copy.png`, { width: W, height: H, data: comp });
writeFileSync(`${out}/composite.json`, JSON.stringify(R, null, 1));
console.log(JSON.stringify(R, null, 1));
