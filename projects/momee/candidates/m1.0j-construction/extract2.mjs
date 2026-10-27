// M1.0j-B non-destructive figure extraction, v2.
// Algorithm = app-momee scripts/assets/key.mjs keyImage (border flood fill, speck removal,
// Chebyshev distance band, 7x7 foreground/background unmix with residual guard), extended with:
//  (a) explicit, reviewed background pockets (enclosed panel colour seen by eye), given as seeds;
//  (b) a ground-shadow flood that may only grow from real background through pixels that are a
//      uniform darkening of the panel colour, inside the bottom band; it is moved to its own layer.
// Reads the sheet, never writes it. Usage: node extract2.mjs <params.json> <outDir>
import { readFileSync } from "node:fs";
const A = "/Users/mfm/code/porto-projects/app-momee/scripts/assets/";
const { readPng, writePng, blank } = await import(A + "png.mjs");
const { crop } = await import(A + "image.mjs");
const [, , paramsPath, out] = process.argv;
const P = JSON.parse(readFileSync(paramsPath, "utf8"));
const [x0, y0, W, H] = P.crop;
const tol = P.tolerance, band = 2, maxResidual = 24, minSpeck = 40;

const sheet = readPng(P.sheet);
const c = crop(sheet, x0, y0, W, H);
const ring = [];
for (let y = 0; y < H; y++) for (let x = 0; x < W; x++)
  if (x < 3 || y < 3 || x >= W - 3 || y >= H - 3) ring.push((y * W + x) * 4);
const med = (k) => { const v = ring.map((o) => c.data[o + k]).sort((a, b) => a - b); return v[v.length >> 1]; };
const B = [med(0), med(1), med(2)];
// flatten a sheet-wide alpha veil over the panel colour (what a viewer sees on the sheet)
const flat = blank(W, H);
let veil = 0;
for (let i = 0; i < c.data.length; i += 4) {
  const a = c.data[i + 3] / 255; if (c.data[i + 3] < 255) veil++;
  for (let k = 0; k < 3; k++) flat.data[i + k] = Math.round(c.data[i + k] * a + B[k] * (1 - a));
  flat.data[i + 3] = 255;
}
const D = flat.data;
const near = (i) => Math.abs(D[i * 4] - B[0]) <= tol && Math.abs(D[i * 4 + 1] - B[1]) <= tol && Math.abs(D[i * 4 + 2] - B[2]) <= tol;
const bg = new Uint8Array(W * H);
const flood = (seeds, test) => {
  const st = [];
  for (const i of seeds) if (!bg[i] && test(i)) { bg[i] = 1; st.push(i); }
  let n = 0;
  while (st.length) {
    const i = st.pop(); n++;
    const x = i % W, y = (i - x) / W;
    for (const [nx, ny] of [[x - 1, y], [x + 1, y], [x, y - 1], [x, y + 1]]) {
      if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
      const j = ny * W + nx;
      if (!bg[j] && test(j)) { bg[j] = 1; st.push(j); }
    }
  }
  return n;
};
// 1. border flood (as keyImage)
const border = [];
for (let x = 0; x < W; x++) border.push(x, (H - 1) * W + x);
for (let y = 0; y < H; y++) border.push(y * W, y * W + W - 1);
const borderPx = flood(border, near);
const outerBg = bg.slice();          // shadow may grow only from the outer background, never from reviewed gaps
// (a) reviewed pockets
const nearT = (t) => (i) => Math.abs(D[i * 4] - B[0]) <= t && Math.abs(D[i * 4 + 1] - B[1]) <= t && Math.abs(D[i * 4 + 2] - B[2]) <= t;
const pocketPx = P.pockets.map(([sx, sy, t]) => flood([sy * W + sx], t ? nearT(t) : near));   // optional per-pocket tolerance
// (b) ground shadow: from background into uniformly darkened panel colour, bottom band only
let top = H, bottom = -1;
for (let i = 0; i < W * H; i++) if (!bg[i]) { const y = (i - (i % W)) / W; top = Math.min(top, y); bottom = Math.max(bottom, y); }
const bandTop = bottom - Math.round((bottom - top) * P.shadowBand);
const S = [160, 135, 125];   // warm shadow tone observed under the shoes
const shadowA = new Float32Array(W * H);
const keep = (P.keepRects ?? []);   // reviewed artwork regions the shadow flood may not enter
const isShadow = (i) => {
  const x = i % W, y = (i - x) / W;
  if (y < bandTop) return false;
  if (keep.some(([kx, ky, kw, kh]) => x >= kx && x < kx + kw && y >= ky && y < ky + kh)) return false;
  const d = [0, 1, 2].map((k) => B[k] - D[i * 4 + k]);
  if (Math.min(...d) < -2) return false;
  const sum = d[0] + d[1] + d[2];
  if (sum < 6 || sum > 230) return false;            // darker than this is drawn outline, kept
  const gb = (d[1] + d[2]) / 2;
  if (d[0] > 1.15 * gb + 2 || d[0] < 0.4 * gb - 2) return false;          // near-neutral warm darkening
  if (Math.abs(d[1] - d[2]) > Math.max(6, 0.15 * gb)) return false;        // green and blue drop together (beige cloth fails)
  shadowA[i] = Math.max(0, Math.min(1, [0, 1, 2].reduce((t, k) => t + d[k] / (B[k] - S[k]), 0) / 3));
  return true;
};
const before = bg.slice();
const shadowSeeds = [];
for (let i = 0; i < W * H; i++) if (outerBg[i] && (i - (i % W)) / W >= bandTop - 2) {
  const x = i % W, y = (i - x) / W;
  for (const [nx, ny] of [[x - 1, y], [x + 1, y], [x, y - 1], [x, y + 1]]) if (nx >= 0 && ny >= 0 && nx < W && ny < H) shadowSeeds.push(ny * W + nx);
}
const shadowPx = flood(shadowSeeds, isShadow);
const shadowMask = new Uint8Array(W * H);
for (let i = 0; i < W * H; i++) if (bg[i] && !before[i]) shadowMask[i] = 1;
// 2. specks (as keyImage, 8-connected)
const comp = new Int32Array(W * H).fill(-1);
let specks = 0;
for (let i = 0; i < W * H; i++) {
  if (bg[i] || comp[i] >= 0) continue;
  const m = [i]; comp[i] = i;
  for (let k = 0; k < m.length; k++) {
    const j = m[k], x = j % W, y = (j - x) / W;
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
      const nx = x + dx, ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
      const n = ny * W + nx;
      if (!bg[n] && comp[n] < 0) { comp[n] = i; m.push(n); }
    }
  }
  if (m.length < minSpeck) { specks++; for (const j of m) bg[j] = 1; }
}
// 3. distance band (as keyImage)
const dist = new Uint8Array(W * H).fill(255);
let fr = [];
for (let i = 0; i < W * H; i++) if (bg[i]) { dist[i] = 0; fr.push(i); }
for (let d = 1; d <= band + 3 && fr.length; d++) {
  const nx2 = [];
  for (const i of fr) {
    const x = i % W, y = (i - x) / W;
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
      const nx = x + dx, ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
      const n = ny * W + nx;
      if (dist[n] === 255) { dist[n] = d; nx2.push(n); }
    }
  }
  fr = nx2;
}
// 4. unmix (as keyImage)
const fig = blank(W, H);
const st = { unmixed: 0, fallbackOpaque: 0, unexplainedOpaque: 0, cleared: 0 };
for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
  const i = y * W + x, o = i * 4;
  if (bg[i]) continue;
  const Pc = [D[o], D[o + 1], D[o + 2]];
  if (dist[i] > band) { fig.data.set([...Pc, 255], o); continue; }
  const pd = [Pc[0] - B[0], Pc[1] - B[1], Pc[2] - B[2]];
  let best = null;
  for (let dy = -3; dy <= 3; dy++) for (let dx = -3; dx <= 3; dx++) {
    const nx = x + dx, ny = y + dy;
    if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
    const j = ny * W + nx;
    if (bg[j] || dist[j] <= dist[i]) continue;
    const fd = [D[j * 4] - B[0], D[j * 4 + 1] - B[1], D[j * 4 + 2] - B[2]];
    const len2 = fd[0] ** 2 + fd[1] ** 2 + fd[2] ** 2;
    if (len2 < 400) continue;
    const a = Math.min(1, Math.max(0, (pd[0] * fd[0] + pd[1] * fd[1] + pd[2] * fd[2]) / len2));
    const residual = Math.max(...[0, 1, 2].map((k) => Math.abs(a * fd[k] - pd[k])));
    if (!best || residual < best.residual) best = { a, residual };
  }
  if (!best) { fig.data.set([...Pc, 255], o); st.fallbackOpaque++; continue; }
  if (best.residual > maxResidual) { fig.data.set([...Pc, 255], o); st.unexplainedOpaque++; continue; }
  if (best.a < 0.04) { st.cleared++; continue; }
  const col = [0, 1, 2].map((k) => Math.min(255, Math.max(0, (Pc[k] - (1 - best.a) * B[k]) / best.a)));
  fig.data.set([...col, Math.round(best.a * 255)], o); st.unmixed++;
}
const shadow = blank(W, H);
for (let i = 0; i < W * H; i++) if (shadowMask[i]) shadow.data.set([...S, Math.round(shadowA[i] * 255)], i * 4);
// integrity and measurements
let opaque = 0, changed = 0, partial = 0, bx = [W, H, -1, -1];
for (let i = 0; i < W * H; i++) {
  const a = fig.data[i * 4 + 3]; if (!a) continue;
  const x = i % W, y = (i - x) / W;
  bx = [Math.min(bx[0], x), Math.min(bx[1], y), Math.max(bx[2], x), Math.max(bx[3], y)];
  if (a === 255) { opaque++; if ([0, 1, 2].some((k) => fig.data[i * 4 + k] !== D[i * 4 + k])) changed++; } else partial++;
}
let sx = 0, sn = 0;
for (let y = bx[3] - Math.round((bx[3] - bx[1]) * 0.03); y <= bx[3]; y++) for (let x = 0; x < W; x++) if (fig.data[(y * W + x) * 4 + 3] > 128) { sx += x; sn++; }
writePng(`${out}/${P.name}.source-crop.png`, flat);
writePng(`${out}/${P.name}.extracted.png`, fig);
writePng(`${out}/${P.name}.ground-shadow.png`, shadow);
const mask = blank(W, H);
for (let i = 0; i < W * H; i++) { const a = fig.data[i * 4 + 3]; mask.data.set([a, a, a, 255], i * 4); }
writePng(`${out}/${P.name}.alpha-mask.png`, mask);
console.log(JSON.stringify({ name: P.name, crop: P.crop, background: B, veilPixels: veil, tolerance: tol, borderPx, pocketPx, shadowPx, specks,
  ...st, figureBounds: bx, figureHeightPx: bx[3] - bx[1] + 1, figureWidthPx: bx[2] - bx[0] + 1, feetAnchorPx: [Math.round(sx / sn), bx[3]],
  opaquePixels: opaque, opaqueChanged: changed, edgePartialPixels: partial }));
