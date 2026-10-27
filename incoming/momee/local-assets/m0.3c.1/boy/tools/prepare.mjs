// M0.3c.1b: deterministic preparation of the Boy candidate.
// Keys the background, applies colour-only refinements, partitions the image
// into cutout layers (full-canvas, aligned), and renders review checks.
// No pixels are invented: every output pixel comes from the candidate.
//
// Usage: node tools/prepare.mjs   (run from assets/.local-assets/m0.3c.1/boy)
import { copyFileSync, mkdirSync, writeFileSync, readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { readPng, writePng, blank } from "./png.mjs";

const SRC = "boy-3quarter-candidate-v1.png";
const OUT = "work";
for (const d of [OUT, `${OUT}/layers`, `${OUT}/checks`, `${OUT}/skin-tone`]) mkdirSync(d, { recursive: true });
copyFileSync(SRC, `${OUT}/boy-3q-v1.original-copy.png`);

const img = readPng(SRC);
const W = img.width, H = img.height, N = W * H;
const P = img.data;
const stats = { source: SRC, size: [W, H] };

// ---------- colour helpers ----------
const hsv = (r, g, b) => {
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  let h = 0;
  if (d) h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return [((h * 60) + 360) % 360, mx ? d / mx : 0, mx / 255];
};
const fromHsv = (h, s, v) => {
  const c = v * s, x = c * (1 - Math.abs(((h / 60) % 2) - 1)), m = v - c;
  const [r, g, b] = h < 60 ? [c, x, 0] : h < 120 ? [x, c, 0] : h < 180 ? [0, c, x] : h < 240 ? [0, x, c] : h < 300 ? [x, 0, c] : [c, 0, x];
  return [(r + m) * 255, (g + m) * 255, (b + m) * 255];
};
const inEllipse = (x, y, [cx, cy, rx, ry]) => ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1;
const inBox = (x, y, [x0, y0, x1, y1]) => x >= x0 && x <= x1 && y >= y0 && y <= y1;
const sha = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");

// ---------- regions (source pixel coordinates, read from gridded crops) ----------
const R = {
  eyeNear: [598, 354, 47, 48],
  eyeFar: [749, 330, 32, 48],
  browFar: [716, 222, 794, 256],
  mouth: [646, 412, 732, 444],
  cheekNear: [590, 412, 58, 34],
  cheekFar: [778, 384, 30, 24],
  nape: [470, 440, 600, 525], // hair behind the jaw/ear → hair-back
  // Chin: the face meets the neck with no outline at the centre, so the split follows
  // the measured chin edge (x → y): neck skin below it becomes body-skin.
  chin: [[560, 490], [590, 494], [640, 497], [690, 496]],
  neckX: [560, 695],
  neckMaxY: 560,
  headMaxY: 530,
};

// ---------- 1. background key ----------
// Background colour from the border; flood fill from the border with a tolerance.
let bs = [0, 0, 0], bn = 0;
for (let x = 0; x < W; x++) for (const y of [0, 1, H - 2, H - 1]) { const o = (y * W + x) * 4; bs[0] += P[o]; bs[1] += P[o + 1]; bs[2] += P[o + 2]; bn++; }
const B = bs.map((v) => v / bn);
const TOL = 10; // per channel (background range measured: 117–123)
const isBgColour = (i) => Math.abs(P[i * 4] - B[0]) <= TOL && Math.abs(P[i * 4 + 1] - B[1]) <= TOL && Math.abs(P[i * 4 + 2] - B[2]) <= TOL;
const bg = new Uint8Array(N);
const stack = [];
for (let x = 0; x < W; x++) { stack.push(x, x + (H - 1) * W); }
for (let y = 0; y < H; y++) { stack.push(y * W, y * W + W - 1); }
while (stack.length) {
  const i = stack.pop();
  if (bg[i] || !isBgColour(i)) continue;
  bg[i] = 1;
  const x = i % W, y = (i / W) | 0;
  if (x > 0) stack.push(i - 1); if (x < W - 1) stack.push(i + 1);
  if (y > 0) stack.push(i - W); if (y < H - 1) stack.push(i + W);
}
// Internal background-coloured pixels that are NOT connected to the border are kept (internal detail).
let internalBgLike = 0;
for (let i = 0; i < N; i++) if (!bg[i] && isBgColour(i)) internalBgLike++;

// Edge band: foreground pixels within 2 px of background.
const near = (i, r, mask) => { const x = i % W, y = (i / W) | 0; for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) { const xx = x + dx, yy = y + dy; if (xx >= 0 && yy >= 0 && xx < W && yy < H && mask[yy * W + xx]) return true; } return false; };
const edge = new Uint8Array(N);
for (let i = 0; i < N; i++) if (!bg[i] && near(i, 2, bg)) edge[i] = 1;

// Unmix edge pixels: P = a·F + (1−a)·B, with F from nearby core (non-edge) pixels.
const keyed = blank(W, H);
const K = keyed.data;
let edgeCount = 0, alphaZeroed = 0, keptOpaque = 0;
for (let i = 0; i < N; i++) {
  const o = i * 4;
  if (bg[i]) continue;
  if (!edge[i]) { K[o] = P[o]; K[o + 1] = P[o + 1]; K[o + 2] = P[o + 2]; K[o + 3] = 255; continue; }
  edgeCount++;
  const x = i % W, y = (i / W) | 0;
  let best = null, bestErr = Infinity, bestFit = Infinity;
  for (let dy = -5; dy <= 5; dy++) for (let dx = -5; dx <= 5; dx++) {
    const xx = x + dx, yy = y + dy; if (xx < 0 || yy < 0 || xx >= W || yy >= H) continue;
    const j = yy * W + xx; if (bg[j] || edge[j]) continue;
    const F = [P[j * 4], P[j * 4 + 1], P[j * 4 + 2]];
    const d = F.map((v, k) => v - B[k]), p = [P[o] - B[0], P[o + 1] - B[1], P[o + 2] - B[2]];
    const dd = d[0] ** 2 + d[1] ** 2 + d[2] ** 2; if (dd < 400) continue;
    const a = Math.min(1, Math.max(0, (p[0] * d[0] + p[1] * d[1] + p[2] * d[2]) / dd));
    const err = (p[0] - a * d[0]) ** 2 + (p[1] - a * d[1]) ** 2 + (p[2] - a * d[2]) ** 2 + 0.5 * (dx * dx + dy * dy);
    if (err < bestErr) { bestErr = err; bestFit = err - 0.5 * (dx * dx + dy * dy); best = { F, a }; }
  }
  // No plausible unmix (e.g. thin white rims with no white core nearby): keep the pixel opaque, unchanged.
  if (!best || bestFit > 300) { K[o] = P[o]; K[o + 1] = P[o + 1]; K[o + 2] = P[o + 2]; K[o + 3] = 255; keptOpaque++; continue; }
  const { F, a } = best;
  const nearBg = Math.max(Math.abs(P[o] - B[0]), Math.abs(P[o + 1] - B[1]), Math.abs(P[o + 2] - B[2])) <= 2 * TOL;
  if (a < 0.04 && nearBg) { alphaZeroed++; continue; }
  // Exact unmix where alpha is reliable; fall back to the core colour for faint pixels.
  const C = [0, 1, 2].map((k) => (a >= 0.35 ? (P[o + k] - (1 - a) * B[k]) / a : F[k]));
  K[o] = C[0]; K[o + 1] = C[1]; K[o + 2] = C[2]; K[o + 3] = Math.round(a * 255);
}
// Drop tiny detached islands (faint anti-aliasing fragments): ≤ 8 px and alpha ≤ 32.
{
  const seen = new Uint8Array(N); let removed = 0;
  for (let i = 0; i < N; i++) {
    if (!K[i * 4 + 3] || seen[i]) continue;
    const q = [i], members = []; seen[i] = 1; let amax = 0;
    while (q.length) { const j = q.pop(); members.push(j); amax = Math.max(amax, K[j * 4 + 3]); const x = j % W, y = (j / W) | 0;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const xx = x + dx, yy = y + dy; if (xx < 0 || yy < 0 || xx >= W || yy >= H) continue; const k = yy * W + xx; if (K[k * 4 + 3] && !seen[k]) { seen[k] = 1; q.push(k); } } }
    if (members.length <= 8 && amax <= 32) for (const j of members) { K[j * 4 + 3] = 0; removed++; }
  }
  stats.islandsRemovedPx = removed;
}
writePng(`${OUT}/boy-3q-v1.keyed.png`, keyed);

// Verify: keyed composited back over the background colour vs the original.
let maxErr = 0, sumErr = 0, over10 = 0; const worst = [];
for (let i = 0; i < N; i++) { const o = i * 4, a = K[o + 3] / 255; let pe = 0; for (let k = 0; k < 3; k++) { const c = K[o + k] * a + B[k] * (1 - a); const e = Math.abs(c - P[o + k]); pe = Math.max(pe, e); sumErr += e; } maxErr = Math.max(maxErr, pe); if (pe > 10) { over10++; worst.push([pe, i % W, (i / W) | 0, K[o + 3]]); } }
worst.sort((a, b) => b[0] - a[0]);
stats.key = { background: B.map((v) => +v.toFixed(1)), tolerance: TOL, backgroundPx: bg.reduce((s, v) => s + v, 0), edgePx: edgeCount, edgeAlphaZeroed: alphaZeroed, edgeKeptOpaque: keptOpaque, internalBackgroundColouredPxKept: internalBgLike, recompositeOverGrey: { maxAbs: +maxErr.toFixed(1), meanAbs: +(sumErr / (N * 3)).toFixed(3), pxOver10: over10, worst: worst.slice(0, 8).map(([e, x, y, a]) => ({ err: +e.toFixed(0), x, y, alpha: a })) } };

// ---------- 2. classification (on keyed colours) ----------
const SL = ["leg-skin", "shoes", "outfit-bottom", "body-skin", "outfit-top", "hair-back", "head-skin", "face-blush", "face-eyes", "face-brows-mouth", "hair-front"];
const id = Object.fromEntries(SL.map((s, i) => [s, i + 1]));
const label = new Uint8Array(N); // 0 = transparent / unassigned
const mat = new Uint8Array(N);   // 1 skin, 2 warm line, 3 hair, 4 yellow, 5 blue, 6 white, 7 other
for (let i = 0; i < N; i++) {
  const o = i * 4; if (!K[o + 3]) continue;
  const [h, s, v] = hsv(K[o], K[o + 1], K[o + 2]);
  const warm = h <= 42 || h >= 340;
  const yy = (i / W) | 0;
  // Skin hue measured at 22–33°; shirt shadows start near 38°, so skin stops at 36°.
  if ((h <= 36 || h >= 340) && v >= 0.86 && s >= 0.25 && s <= 0.72 && yy < 1045) mat[i] = 1;
  else if (warm && s >= 0.6 && v >= 0.35 && v < 0.86) mat[i] = 2;
  else if ((warm && v <= 0.45 && s >= 0.25) || v < 0.18) mat[i] = 3;
  else if (h > 38 && h <= 62 && s >= 0.4 && v >= 0.55) mat[i] = 4;
  else if (h >= 190 && h <= 235 && s >= 0.3) mat[i] = 5;
  else if (s <= (yy >= 1000 ? 0.3 : 0.22) && v >= 0.7) mat[i] = 6;
  else mat[i] = 7;
}

// Skin components → group by centroid (face/ears = head; neck/arms/hands = torso; shins = legs).
const comp = new Int32Array(N).fill(-1);
const comps = [];
for (let i = 0; i < N; i++) {
  if (mat[i] !== 1 || comp[i] >= 0) continue;
  const c = { n: 0, sy: 0, sx: 0 }; const q = [i]; comp[i] = comps.length;
  while (q.length) {
    const j = q.pop(); c.n++; c.sy += (j / W) | 0; c.sx += j % W;
    const x = j % W, y = (j / W) | 0;
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const xx = x + dx, yy = y + dy; if (xx < 0 || yy < 0 || xx >= W || yy >= H) continue; const k = yy * W + xx; if (mat[k] === 1 && comp[k] < 0) { comp[k] = comps.length; q.push(k); } }
  }
  comps.push(c);
}
// Small warm-light components inside the hair mass are rim highlights, not skin.
const skinSlot = comps.map((c) => { const cy = c.sy / c.n; return cy < 300 && c.n < 5000 ? id["hair-front"] : cy < 470 ? id["head-skin"] : cy < 940 ? id["body-skin"] : id["leg-skin"]; });
const chinY = (x) => { const c = R.chin; if (x <= c[0][0]) return c[0][1]; for (let k = 1; k < c.length; k++) if (x <= c[k][0]) { const [x0, y0] = c[k - 1], [x1, y1] = c[k]; return y0 + ((y1 - y0) * (x - x0)) / (x1 - x0); } return c[c.length - 1][1]; };
stats.skinComponents = comps.filter((c) => c.n > 200).map((c, k) => ({ px: c.n, centroid: [Math.round(c.sx / c.n), Math.round(c.sy / c.n)] }));

for (let i = 0; i < N; i++) {
  if (!K[i * 4 + 3]) continue;
  const x = i % W, y = (i / W) | 0, m = mat[i];
  const inEye = inEllipse(x, y, R.eyeNear) || inEllipse(x, y, R.eyeFar);
  if (inEye && m !== 1) label[i] = id["face-eyes"];
  // M0.3c.2: the far brow touches the hair, so any cut between them crosses solid dark
  // colour and shows a seam after downscaling. The brow stays with hair-front until a
  // separately painted brow exists (expressions).
  else if (inBox(x, y, R.browFar) && (m === 3 || m === 7)) label[i] = id["hair-front"];
  else if (inBox(x, y, R.mouth) && m !== 1) label[i] = id["face-brows-mouth"];
  else if (m === 1) label[i] = skinSlot[comp[i]] === id["head-skin"] && x >= R.neckX[0] && x <= R.neckX[1] && y > chinY(x) && y < R.neckMaxY ? id["body-skin"] : skinSlot[comp[i]];
  else if (m === 3 && y < R.headMaxY) label[i] = inBox(x, y, R.nape) ? id["hair-back"] : id["hair-front"];
  else if (m === 4) label[i] = id["outfit-top"];
  else if (m === 5) label[i] = y >= 1020 ? id.shoes : id["outfit-bottom"];
  else if (m === 6 && y >= 1000) label[i] = id.shoes;
}

// Ambiguous pixels (outlines, anti-aliasing): front-most label within radius 3, by family.
const FRONT = ["hair-front", "face-brows-mouth", "face-eyes", "head-skin", "hair-back", "outfit-top", "body-skin", "outfit-bottom", "shoes", "leg-skin"].map((s) => id[s]);
const WARM_LINE = ["face-brows-mouth", "face-eyes", "head-skin", "outfit-top", "body-skin", "outfit-bottom", "shoes", "leg-skin", "hair-front", "hair-back"].map((s) => id[s]);
let resolvedByNeighbour = 0, resolvedByBfs = 0;
const pending = [];
for (let i = 0; i < N; i++) if (K[i * 4 + 3] && !label[i]) pending.push(i);
const assigned = new Uint8Array(label);
for (const i of pending) {
  const x = i % W, y = (i / W) | 0, present = new Set();
  for (let dy = -3; dy <= 3; dy++) for (let dx = -3; dx <= 3; dx++) { const xx = x + dx, yy = y + dy; if (xx < 0 || yy < 0 || xx >= W || yy >= H) continue; const l = label[yy * W + xx]; if (l) present.add(l); }
  const order = mat[i] === 2 ? WARM_LINE : FRONT;
  const pick = order.find((l) => present.has(l));
  if (pick) { assigned[i] = pick; resolvedByNeighbour++; }
}
// Anything left: nearest labelled pixel (BFS).
let frontier = [];
for (let i = 0; i < N; i++) if (assigned[i]) frontier.push(i);
while (frontier.length) {
  const next = [];
  for (const i of frontier) {
    const x = i % W, y = (i / W) | 0;
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const xx = x + dx, yy = y + dy; if (xx < 0 || yy < 0 || xx >= W || yy >= H) continue; const k = yy * W + xx; if (K[k * 4 + 3] && !assigned[k]) { assigned[k] = assigned[i]; resolvedByBfs++; next.push(k); } }
  }
  frontier = next;
}
label.set(assigned);
stats.classification = { pendingAfterColour: pending.length, resolvedByNeighbour, resolvedByBfs };

// ---------- 3. colour-only refinements ----------
const refined = { width: W, height: H, data: new Uint8ClampedArray(K) };
const F = refined.data;
let hairPx = 0, irisPx = 0;
for (let i = 0; i < N; i++) {
  const o = i * 4; if (!F[o + 3]) continue;
  const l = label[i], [h, s, v] = hsv(F[o], F[o + 1], F[o + 2]);
  const warm = h <= 45 || h >= 330;
  // Hair and brows: cooler, darker cocoa (reference #3c2c2d–#413131). Weight fades for lighter transition pixels.
  if ((l === id["hair-front"] || l === id["hair-back"] || l === id["face-brows-mouth"] && inBox(i % W, (i / W) | 0, R.browFar)) && warm && s < 0.78) {
    const w = v <= 0.42 ? 1 : v >= 0.72 ? 0 : (0.72 - v) / 0.3;
    if (w > 0) {
      const t = fromHsv((h - 14 + 360) % 360, s * 0.55, v * 0.88);
      for (let k = 0; k < 3; k++) F[o + k] = F[o + k] * (1 - w) + t[k] * w;
      hairPx++;
    }
  }
  // Eyes: darken brown iris toward near-black; keep pupils, highlights and sclera unchanged.
  if (l === id["face-eyes"] && warm && s >= 0.3 && v >= 0.15 && v <= 0.75) {
    const t = fromHsv(h, s * 0.75, v * 0.42);
    for (let k = 0; k < 3; k++) F[o + k] = t[k];
    irisPx++;
  }
}
stats.refinement = { hairAndBrowPxRecoloured: hairPx, irisPxDarkened: irisPx, hairTransform: "hue −14°, saturation ×0.55, value ×0.88 (weighted; transitions fade out above value 0.42)", irisTransform: "saturation ×0.75, value ×0.42 for brown iris pixels (value 0.15–0.75)" };

// ---------- 4. blush unmixing (head-skin inside cheek ellipses) ----------
const SB = [254, 204, 150];            // base face skin (#fecc96, measured on the forehead/cheek)
const BC = [253, 142, 106];            // blush colour (extrapolated from the deepest cheek sample #fca775)
const dir = SB.map((v, k) => BC[k] - v), dd = dir.reduce((s, v) => s + v * v, 0);
const blush = blank(W, H), BL = blush.data;
let blushPx = 0, blushMaxErr = 0;
for (let i = 0; i < N; i++) {
  const o = i * 4, x = i % W, y = (i / W) | 0;
  if (label[i] !== id["head-skin"] || mat[i] !== 1) continue;
  const ell = [R.cheekNear, R.cheekFar].find((e) => inEllipse(x, y, e)); if (!ell) continue;
  const d = [F[o] - SB[0], F[o + 1] - SB[1], F[o + 2] - SB[2]];
  let a = (d[0] * dir[0] + d[1] * dir[1] + d[2] * dir[2]) / dd;
  const r2 = ((x - ell[0]) / ell[2]) ** 2 + ((y - ell[1]) / ell[3]) ** 2;
  a = Math.min(0.9, Math.max(0, a)) * Math.min(1, (1 - r2) / 0.35); // feather toward the ellipse edge
  // Cap so the unmixed skin stays within 0..255 (keeps the split exact).
  for (let k = 0; k < 3; k++) { a = Math.min(a, F[o + k] / BC[k]); if (BC[k] < 255) a = Math.min(a, (255 - F[o + k]) / (255 - BC[k])); }
  const A = Math.round(a * 255) / 255; if (A <= 0) continue;
  // Exact unmix: skin' = (P − A·BC) / (1 − A), so skin' ⊕ blush = P.
  const S = [0, 1, 2].map((k) => (F[o + k] - A * BC[k]) / (1 - A));
  const Sq = S.map((v) => Math.round(Math.min(255, Math.max(0, v))));
  for (let k = 0; k < 3; k++) { const back = Sq[k] * (1 - A) + BC[k] * A; blushMaxErr = Math.max(blushMaxErr, Math.abs(back - F[o + k])); }
  F[o] = Sq[0]; F[o + 1] = Sq[1]; F[o + 2] = Sq[2];
  BL[o] = BC[0]; BL[o + 1] = BC[1]; BL[o + 2] = BC[2]; BL[o + 3] = Math.round(A * F[o + 3]);
  blushPx++;
}
stats.blush = { px: blushPx, colour: "#fd8e6a", recompositeMaxAbs: +blushMaxErr.toFixed(2) };

// ---------- 5. write layers (full canvas, original alignment) ----------
// Recompose the refined image from the layers so the checks use exactly what the layers contain.
const layerFiles = [];
const composite = blank(W, H), CO = composite.data;
const over = (dst, o, r, g, b, a) => { const A = a / 255, da = dst[o + 3] / 255, oa = A + da * (1 - A); if (oa <= 0) return; for (const [k, c] of [[0, r], [1, g], [2, b]]) dst[o + k] = (c * A + dst[o + k] * da * (1 - A)) / oa; dst[o + 3] = oa * 255; };
SL.forEach((slot, n) => {
  const layer = blank(W, H), L = layer.data;
  let count = 0, x0 = W, y0 = H, x1 = -1, y1 = -1;
  for (let i = 0; i < N; i++) {
    const o = i * 4;
    if (slot === "face-blush") { if (!BL[o + 3]) continue; L.set(BL.subarray(o, o + 4), o); }
    else { if (label[i] !== id[slot]) continue; L.set(F.subarray(o, o + 4), o); }
    count++; const x = i % W, y = (i / W) | 0; x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y);
    over(CO, o, L[o], L[o + 1], L[o + 2], L[o + 3]);
  }
  const file = `${OUT}/layers/${String(n + 1).padStart(2, "0")}-${slot}.png`;
  writePng(file, layer);
  layerFiles.push({ order: n + 1, slot, file: file.replace(`${OUT}/`, ""), px: count, bbox: count ? [x0, y0, x1, y1] : null, sha256: sha(file) });
});
writePng(`${OUT}/boy-3q-v1.refined.png`, composite);
stats.layers = layerFiles;

// Layers recompose to keyed+refined (before blush unmix) within rounding?
const refinedReference = new Uint8ClampedArray(K); // rebuild refined-without-blush-split for comparison
// (refinement applied to K earlier lives in F; blush split rewrote F's cheek pixels, so compare composite vs pre-split values)
writeFileSync(`${OUT}/stats.json`, JSON.stringify(stats, null, 2));

// ---------- 6. checks ----------
function flat(rgb, src) { const out = blank(W, H), D = out.data; for (let i = 0; i < N; i++) { const o = i * 4, a = src[o + 3] / 255; for (let k = 0; k < 3; k++) D[o + k] = src[o + k] * a + rgb[k] * (1 - a); D[o + 3] = 255; } return out; }
const bgs = { white: [255, 255, 255], cream: [249, 237, 220], black: [20, 18, 20], magenta: [255, 0, 255] };
for (const [name, c] of Object.entries(bgs)) writePng(`${OUT}/checks/refined-on-${name}.png`, flat(c, CO));
writePng(`${OUT}/checks/keyed-on-white.png`, flat(bgs.white, K));

// Slot map: each layer in a flat colour, for reviewing the partition.
const COLORS = { "leg-skin": [255, 170, 120], shoes: [40, 90, 200], "outfit-bottom": [120, 170, 255], "body-skin": [255, 120, 60], "outfit-top": [255, 220, 0], "hair-back": [120, 60, 20], "head-skin": [255, 200, 160], "face-eyes": [0, 200, 120], "face-brows-mouth": [200, 0, 200], "hair-front": [60, 30, 10] };
const map = blank(W, H);
for (let i = 0; i < N; i++) { const o = i * 4; if (!label[i]) { map.data.set([230, 230, 230, 255], o); continue; } const c = COLORS[SL[label[i] - 1]]; map.data.set([...c, 255], o); }
writePng(`${OUT}/checks/slot-map.png`, map);

// Motion preview: head group up 8 px, torso group up 4 px, on magenta (reveals missing hidden artwork).
const GROUP = { "leg-skin": "legs", shoes: "legs", "outfit-bottom": "legs", "body-skin": "torso", "outfit-top": "torso", "hair-back": "head", "head-skin": "head", "face-blush": "head", "face-eyes": "head", "face-brows-mouth": "head", "hair-front": "head" };
const OFFSET = { legs: [0, 0], torso: [0, -4], head: [0, -8] };
const motion = blank(W, H), MD = motion.data;
for (let i = 0; i < N; i++) MD.set([255, 0, 255, 255], i * 4);
SL.forEach((slot) => {
  const [dx, dy] = OFFSET[GROUP[slot]];
  for (let i = 0; i < N; i++) {
    const o = i * 4; let r, g, b, a;
    if (slot === "face-blush") { a = BL[o + 3]; if (!a) continue; [r, g, b] = BC; }
    else { if (label[i] !== id[slot]) continue; r = F[o]; g = F[o + 1]; b = F[o + 2]; a = F[o + 3]; }
    const x = (i % W) + dx, y = ((i / W) | 0) + dy; if (x < 0 || y < 0 || x >= W || y >= H) continue;
    over(MD, (y * W + x) * 4, r, g, b, a);
  }
});
writePng(`${OUT}/checks/motion-preview-head-up8-torso-up4.png`, motion);

// Blink feasibility: eyes layer removed (shows the missing eyelid skin).
const noEyes = flat([255, 0, 255], CO).data;
for (let i = 0; i < N; i++) if (label[i] === id["face-eyes"]) noEyes.set([255, 0, 255, 255], i * 4);
writePng(`${OUT}/checks/blink-eyes-removed.png`, { width: W, height: H, data: noEyes });

// ---------- 7. skin-tone previews (evaluation only, not approved tones) ----------
const SKIN_SLOTS = new Set([id["leg-skin"], id["body-skin"], id["head-skin"]]);
const lum = (r, g, b) => 0.2126 * r + 0.7152 * g + 0.0722 * b;
const BASE_L = lum(...SB);
const TONES = { "tone-a-light": [254, 204, 150], "tone-b-medium": [214, 154, 108], "tone-c-deep": [141, 90, 61] };
for (const method of ["tint", "transfer"]) {
  for (const [tname, T] of Object.entries(TONES)) {
    const out = blank(W, H), D = out.data;
    for (let i = 0; i < N; i++) {
      const o = i * 4; D[o + 3] = 255;
      let r = F[o], g = F[o + 1], b = F[o + 2]; const a = F[o + 3] / 255;
      if (SKIN_SLOTS.has(label[i])) {
        if (method === "tint") { const n = lum(r, g, b) / BASE_L; [r, g, b] = T.map((c) => c * n); } // greyscale base × tone (MULTIPLY tint)
        else { [r, g, b] = [r * T[0] / SB[0], g * T[1] / SB[1], b * T[2] / SB[2]]; }                      // per-channel colour transfer
      }
      // blush on top
      const ba = BL[o + 3] / 255; if (ba) { r = r * (1 - ba) + BC[0] * ba; g = g * (1 - ba) + BC[1] * ba; b = b * (1 - ba) + BC[2] * ba; }
      for (const [k, c] of [[0, r], [1, g], [2, b]]) D[o + k] = c * a + 249 * [1, 0.95, 0.88][k] * (1 - a); // cream page
    }
    writePng(`${OUT}/skin-tone/${method}-${tname}.png`, out);
  }
}
console.log(JSON.stringify(stats, null, 1));
