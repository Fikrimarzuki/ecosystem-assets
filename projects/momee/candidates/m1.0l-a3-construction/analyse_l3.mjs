// M1.0l-A3 closed-eye candidate analysis (read-only on the sheet, the master and the A1 layers).
// Verifies the sheet's printed claims independently:
//  • panel 2 "exact pixels from master" and panel 3 "only eye areas changed": fit each panel to the master by
//    DOWNSCALING THE PANEL ONLY (factor f ≤ 1; never enlarging) plus an integer offset, then measure residuals
//    inside / outside the A1 eye masks and against a resampling-only baseline (master → ×f → back is not done;
//    instead the baseline is panel 2's own fit residual).
//  • panel 3 vs panel 2 directly (same sheet scale): difference outside the eye regions.
// Usage: node analyse_l3.mjs <sheet.png> <master.png> <a1LayersDir> <outDir>
import { writeFileSync, mkdirSync } from 'node:fs';
const T = await import('/Users/mfm/code/porto-projects/ecosystem-assets/scripts/momee-character-master.mjs');
const [, , sheetPath, masterPath, A1, out] = process.argv;
mkdirSync(out, { recursive: true });
const S = T.readPng(sheetPath), M = T.readPng(masterPath), W = M.width;
const PANELS = { 'p2-open-closeup': [365, 43, 745, 400], 'p3-closed-closeup': [774, 43, 1152, 400], 'p4-open-crop': [1182, 43, 1511, 201],
  'p4-closed-crop': [1182, 230, 1511, 401], 'p6-overlay': [993, 498, 1279, 695], 'p9-open-detail': [710, 801, 884, 940], 'p9-closed-detail': [909, 801, 1082, 940] };
const crop = (img, [x0, y0, x1, y1]) => { const w = x1 - x0 + 1, h = y1 - y0 + 1, d = new Uint8Array(w * h * 4); for (let y = 0; y < h; y++) d.set(img.data.subarray(((y + y0) * img.width + x0) * 4, ((y + y0) * img.width + x1 + 1) * 4), y * w * 4); return { width: w, height: h, data: d }; };
const P = Object.fromEntries(Object.entries(PANELS).map(([k, b]) => [k, crop(S, b)]));
for (const [k, c] of Object.entries(P)) T.writePng(`${out}/${k}.png`, c);
// A1 eye masks (alpha > 0 of the extracted open-eye layers) and the union
const near = T.readPng(`${A1}/face-eyes__open__eye-near.png`).data, far = T.readPng(`${A1}/face-eyes__open__eye-far.png`).data;
const inNear = (i) => near[i * 4 + 3] > 0, inFar = (i) => far[i * 4 + 3] > 0;
// fit: downscale panel by f, place at master offset (ox, oy) = master coords of the panel's top-left; residual over the head box
const HEAD = [250, 160, 570, 470];
function placeResid(img, ox, oy, st = 1) {
  let s = 0, n = 0, si = 0, ni = 0;
  for (let y = 0; y < img.height; y += st) for (let x = 0; x < img.width; x += st) {
    const X = x + ox, Y = y + oy; if (X < HEAD[0] || Y < HEAD[1] || X > HEAD[2] || Y > HEAD[3]) continue;
    const i = Y * W + X, o = i * 4, q = (y * img.width + x) * 4; if (M.data[o + 3] < 250 || img.data[q + 3] < 200) continue;
    let e = 0; for (let k = 0; k < 3; k++) e += Math.abs(M.data[o + k] - img.data[q + k]);
    if (inNear(i) || inFar(i)) { si += e; ni += 3; } else { s += e; n += 3; }
  }
  return { outside: n ? s / n : 1e9, inside: ni ? si / ni : null, nOut: n / 3, nIn: ni / 3 };
}
function fit(panel, fMin, fMax) {
  let best = { outside: 1e9 };
  for (let f = fMin; f <= fMax + 1e-9; f += 0.01) {
    const r = T.resample(panel, Math.round(panel.width * f), Math.round(panel.height * f), [0, 0], [0, 0], f);
    for (let oy = 90; oy <= 230; oy += 3) for (let ox = 170; ox <= 340; ox += 3) { const q = placeResid(r, ox, oy, 4); if (q.nOut > 2500 && q.outside < best.outside) best = { f: +f.toFixed(3), ox, oy, ...q }; }
  }
  // refine offset at 1 px around the best
  const r = T.resample(panel, Math.round(panel.width * best.f), Math.round(panel.height * best.f), [0, 0], [0, 0], best.f);
  best.outside = 1e9; for (let oy = best.oy - 3; oy <= best.oy + 3; oy++) for (let ox = best.ox - 3; ox <= best.ox + 3; ox++) { const q = placeResid(r, ox, oy); if (q.nOut > 40000 && q.outside < best.outside) best = { ...best, ox, oy, ...q }; }
  for (const k of ['outside', 'inside']) if (best[k] != null) best[k] = +best[k].toFixed(2);
  return { ...best, placed: r };
}
const R = { panels: PANELS };
const f2 = fit(P['p2-open-closeup'], 0.60, 1.00), f3 = fit(P['p3-closed-closeup'], 0.60, 1.00);
R.fit_p2_open_vs_master = { ...f2, placed: undefined }; R.fit_p3_closed_vs_master = { ...f3, placed: undefined };
// panel 3 vs panel 2, same sheet scale, outside the A1 eye masks projected into panel coordinates (via p2's fit)
{ const a = P['p2-open-closeup'], b = P['p3-closed-closeup']; let s = 0, n = 0, si = 0, ni = 0, changed = 0, changedOut = 0;
  for (let y = 0; y < Math.min(a.height, b.height); y++) for (let x = 0; x < Math.min(a.width, b.width); x++) {
    const X = Math.round(x * f2.f) + f2.ox, Y = Math.round(y * f2.f) + f2.oy, i = Y * W + X, eye = X >= 0 && Y >= 0 && X < W && (inNear(i) || inFar(i));
    const o = (y * a.width + x) * 4, ob = (y * b.width + x) * 4; let e = 0; for (let k = 0; k < 3; k++) e += Math.abs(a.data[o + k] - b.data[ob + k]);
    if (e > 30) { changed++; if (!eye) changedOut++; }
    if (eye) { si += e; ni += 3; } else { s += e; n += 3; } }
  R.p3_vs_p2_sameScale = { outsideEyeMasks: +(s / n).toFixed(2), insideEyeMasks: +(si / ni).toFixed(2), pixelsChangedOver10perChannel: changed, ofWhichOutsideEyeMasks: changedOut }; }
// lash colour: darkest 8 % of pixels inside the eye masks (master open lashes vs candidate closed lashes after fit)
function darkest(getPix, idxs) { const v = idxs.map(getPix).filter(Boolean).sort((p, q) => (p[0] + p[1] + p[2]) - (q[0] + q[1] + q[2])); const k = Math.max(1, Math.round(v.length * 0.08)); const m = [0, 0, 0]; for (let j = 0; j < k; j++) for (let c = 0; c < 3; c++) m[c] += v[j][c] / k; return m.map(Math.round); }
const eyeIdx = []; for (let i = 0; i < W * M.height; i++) if (inNear(i) || inFar(i)) eyeIdx.push(i);
R.lashColour = { masterOpenEyes: darkest((i) => [M.data[i * 4], M.data[i * 4 + 1], M.data[i * 4 + 2]], eyeIdx),
  candidateClosedEyes: darkest((i) => { const X = i % W - f3.ox, Y = Math.floor(i / W) - f3.oy, r = f3.placed; if (X < 0 || Y < 0 || X >= r.width || Y >= r.height) return null; const q = (Y * r.width + X) * 4; return [r.data[q], r.data[q + 1], r.data[q + 2]]; }, eyeIdx) };
R.enlargementNeeded = { p3: f3.f <= 1 ? 'none (panel is downscaled ×' + f3.f + ' to reach the master)' : 'yes' };
// write the fitted, downscaled panel 3 on the master canvas (review/inspection only; NOT a candidate layer)
{ const r = f3.placed, o = new Uint8Array(W * M.height * 4); for (let y = 0; y < r.height; y++) for (let x = 0; x < r.width; x++) { const X = x + f3.ox, Y = y + f3.oy; if (X < 0 || Y < 0 || X >= W || Y >= M.height) continue; o.set(r.data.subarray((y * r.width + x) * 4, (y * r.width + x) * 4 + 4), (Y * W + X) * 4); }
  T.writePng(`${out}/p3-fitted-on-master-canvas.png`, { width: W, height: M.height, data: o }); }
{ const r = f2.placed, o = new Uint8Array(W * M.height * 4); for (let y = 0; y < r.height; y++) for (let x = 0; x < r.width; x++) { const X = x + f2.ox, Y = y + f2.oy; if (X < 0 || Y < 0 || X >= W || Y >= M.height) continue; o.set(r.data.subarray((y * r.width + x) * 4, (y * r.width + x) * 4 + 4), (Y * W + X) * 4); }
  T.writePng(`${out}/p2-fitted-on-master-canvas.png`, { width: W, height: M.height, data: o }); }
writeFileSync(`${out}/analysis.json`, JSON.stringify(R, null, 1));
console.log(JSON.stringify(R, null, 1));
