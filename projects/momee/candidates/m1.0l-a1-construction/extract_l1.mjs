// M1.0l-A1 head-layer extraction from the accepted Mom v2 master (non-destructive).
// Every master pixel is assigned to exactly ONE layer with its original RGBA (no resampling, no recolouring,
// no painting). Empty pixels in a layer are fully transparent. Because the layers partition the image,
// normal-mode compositing reproduces the master exactly; this script verifies it pixel by pixel.
// Boundaries: hand-drawn polygons (in skin areas) for the features, colour + connectivity for head skin and
// neck. Pixels that cannot be separated reliably (near brow inside the hair sweep, all hair, body) stay in `base`.
// Usage: node extract_l1.mjs <master.png> <outDir>
import { writeFileSync, mkdirSync } from 'node:fs';
const T = await import('/Users/mfm/code/porto-projects/ecosystem-assets/scripts/momee-character-master.mjs');
const [, , masterPath, out] = process.argv;
mkdirSync(out, { recursive: true });
const m = T.readPng(masterPath), W = m.width, H = m.height, D = m.data;

// ---- masks (master pixel coordinates; read from gridded crops, documented in masks.json) ----
const POLYS = {
  'face-mouth/neutral': [[398, 339], [457, 339], [457, 367], [398, 367]],
  'face-eyes/open:eye-near': [[332, 282], [333, 266], [340, 261], [352, 257], [366, 253], [380, 249], [394, 245], [413, 247], [425, 266], [425, 300], [411, 321], [376, 327], [345, 319], [334, 301]], // top edge follows the fringe edge
  'face-eyes/open:eye-far': [[461, 296], [465, 276], [478, 260], [505, 256], [528, 260], [536, 274], [531, 292], [527, 300], [522, 308], [517, 318], [510, 328], [503, 334], [478, 335], [464, 319]],
  'face-brows/neutral:brow-far': [[493, 241], [499, 228], [520, 222], [537, 229], [543, 246], [541, 255], [530, 251], [510, 246], [496, 251]],
};
const HEAD_BOX = [255, 150, 560, 400];          // head-skin may only come from this box
const NECK_BOX = [356, 376, 446, 472];          // visible neck and collar-opening skin lie inside this box
const NECK_POLY = [[362, 378], [421, 396], [424, 418], [431, 440], [438, 462], [438, 474], [432, 474], [420, 460], [407, 444], [398, 441], [380, 428], [362, 414], [357, 400]]; // neck + collar opening, inside the collar and lapel edges
const EAR_POLY = [[268, 305], [272, 293], [282, 285], [296, 279], [304, 284], [312, 296], [320, 306], [326, 318], [326, 340], [316, 346], [296, 343], [282, 334], [272, 320]];
const SEEDS = { face: [430, 320], ear: [290, 320], neck: [395, 412] };

const inPoly = (x, y, P) => { let c = false; for (let i = 0, j = P.length - 1; i < P.length; j = i++) { const [xi, yi] = P[i], [xj, yj] = P[j]; if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c; } return c; };
const hsv = (o) => { const r = D[o] / 255, g = D[o + 1] / 255, b = D[o + 2] / 255, mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn; let h = 0; if (d) { h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; h *= 60; if (h < 0) h += 360; } return [h, mx ? d / mx : 0, mx]; };
const inBox = (x, y, B) => x >= B[0] && x <= B[2] && y >= B[1] && y <= B[3];
const skinLike = (o) => { if (D[o + 3] < 200) return false; const [h, s, v] = hsv(o); return v >= 0.8 && s >= 0.06 && s <= 0.5 && (h <= 45 || h >= 345); };
const neckLike = (o) => { if (D[o + 3] < 200) return false; const [h, s, v] = hsv(o); return v >= 0.7 && s >= 0.12 && s <= 0.62 && h >= 13 && h <= 40; };

const NAMES = ['base', 'body-skin/neck-visible', 'head-skin/base', ...Object.keys(POLYS)];
const id = Object.fromEntries(NAMES.map((n, i) => [n, i]));
const label = new Int8Array(W * H).fill(-1);
for (let i = 0; i < W * H; i++) if (D[i * 4 + 3] === 0) label[i] = -2; // empty canvas

// 1. features by polygon (only non-empty pixels)
for (const [name, P] of Object.entries(POLYS)) {
  const xs = P.map((p) => p[0]), ys = P.map((p) => p[1]);
  for (let y = Math.min(...ys); y <= Math.max(...ys); y++) for (let x = Math.min(...xs); x <= Math.max(...xs); x++) {
    const i = y * W + x; if (label[i] === -1 && inPoly(x + 0.5, y + 0.5, P)) label[i] = id[name];
  }
}
// 2. flood helper (8-connected)
function flood(seed, ok) { const [sx, sy] = seed, q = [sy * W + sx], got = new Set(q); for (let k = 0; k < q.length; k++) { const j = q[k], x = j % W, y = (j - x) / W; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const X = x + dx, Y = y + dy; if (X < 0 || Y < 0 || X >= W || Y >= H) continue; const n = Y * W + X; if (!got.has(n) && ok(n, X, Y)) { got.add(n); q.push(n); } } } return got; }
// 3. head skin: skin-coloured pixels connected to the face or ear seed, inside HEAD_BOX, outside NECK_BOX rows below the chin
const featureIds = new Set(Object.keys(POLYS).map((n) => id[n]));
const headOk = (n, X, Y) => inBox(X, Y, HEAD_BOX) && !inBox(X, Y, [NECK_BOX[0], 398, NECK_BOX[2], NECK_BOX[3]]) && (featureIds.has(label[n]) || (label[n] === -1 && skinLike(n * 4)));
const head = new Set([...flood(SEEDS.face, headOk), ...flood(SEEDS.ear, headOk)]);
for (const n of head) if (label[n] === -1) label[n] = id['head-skin/base'];
// 3a. ear: every non-dark pixel inside the ear outline (its inner shading is too saturated for skinLike; the dark hair wedge stays in base)
let ear = 0;
for (let y = 279; y <= 346; y++) for (let x = 268; x <= 326; x++) { const n = y * W + x; if (label[n] === -1 && inPoly(x + 0.5, y + 0.5, EAR_POLY) && D[n * 4 + 3] >= 128 && hsv(n * 4)[2] >= 0.45) { label[n] = id['head-skin/base']; ear++; } }
// 3b. enclosed holes in the head region (nose mark, inner lines) join head skin: anything unlabelled inside HEAD_BOX
//     that cannot reach the HEAD_BOX border through unlabelled/non-head pixels
const outside = new Set(); { const q = []; for (let x = HEAD_BOX[0]; x <= HEAD_BOX[2]; x++) for (const y of [HEAD_BOX[1], HEAD_BOX[3]]) q.push(y * W + x); for (let y = HEAD_BOX[1]; y <= HEAD_BOX[3]; y++) for (const x of [HEAD_BOX[0], HEAD_BOX[2]]) q.push(y * W + x);
  for (const s of q) if (label[s] < 0 || label[s] === id.base) outside.add(s);
  const arr = [...outside]; for (let k = 0; k < arr.length; k++) { const j = arr[k], x = j % W, y = (j - x) / W; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const X = x + dx, Y = y + dy; if (!inBox(X, Y, HEAD_BOX)) continue; const n = Y * W + X; if (!outside.has(n) && (label[n] === -1 || label[n] === -2)) { outside.add(n); arr.push(n); } } } }
let holes = 0;
for (let y = HEAD_BOX[1]; y <= HEAD_BOX[3]; y++) for (let x = HEAD_BOX[0]; x <= HEAD_BOX[2]; x++) { const n = y * W + x; if (label[n] === -1 && !outside.has(n)) { label[n] = id['head-skin/base']; holes++; } }
// 4. neck: neck-coloured pixels connected to the neck seed inside NECK_BOX
const neck = flood(SEEDS.neck, (n, X, Y) => inBox(X, Y, NECK_BOX) && inPoly(X + 0.5, Y + 0.5, NECK_POLY) && label[n] === -1 && neckLike(n * 4));
for (const n of neck) label[n] = id['body-skin/neck-visible'];
// 4b. chin outline: unlabelled pixels in NECK_BOX with head skin ≤ 4 px above and neck ≤ 4 px below (same column) belong to the head
let chin = 0;
for (let y = NECK_BOX[1]; y <= NECK_BOX[3]; y++) for (let x = NECK_BOX[0]; x <= NECK_BOX[2]; x++) {
  const n = y * W + x; if (label[n] !== -1) continue;
  let up = false, dn = false; for (let k = 1; k <= 4; k++) { if (label[(y - k) * W + x] === id['head-skin/base']) up = true; if (label[(y + k) * W + x] === id['body-skin/neck-visible']) dn = true; }
  if (up && dn) { label[n] = id['head-skin/base']; chin++; }
}
// 5. everything else → base
for (let i = 0; i < W * H; i++) if (label[i] === -1) label[i] = id.base;

// ---- write layers, verify the partition and the composite ----
const layers = NAMES.map(() => new Uint8Array(W * H * 4));
for (let i = 0; i < W * H; i++) if (label[i] >= 0) layers[label[i]].set(D.subarray(i * 4, i * 4 + 4), i * 4);
const report = { master: masterPath, canvas: [W, H], layers: {}, chinOutlinePixelsToHead: chin, enclosedPixelsToHead: holes, earPolygonPixelsToHead: ear };
const file = (n) => n.replace(/[/:]/g, '__') + '.png';
NAMES.forEach((n, k) => {
  const img = { width: W, height: H, data: layers[k] }; T.writePng(`${out}/${file(n)}`, img);
  let c = 0, x0 = W, y0 = H, x1 = -1, y1 = -1; for (let i = 0; i < W * H; i++) if (layers[k][i * 4 + 3]) { c++; const x = i % W, y = (i - x) / W; x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  report.layers[n] = { file: file(n), pixels: c, bbox: c ? [x0, y0, x1, y1] : null };
});
// composite: straight-alpha "over" in drawing order (base first). Because no two layers share a pixel, the result must equal D.
const comp = new Uint8Array(W * H * 4); let overlaps = 0;
for (const L of layers) for (let i = 0; i < W * H; i++) { const a = L[i * 4 + 3]; if (!a) continue; if (comp[i * 4 + 3]) overlaps++; comp.set(L.subarray(i * 4, i * 4 + 4), i * 4); }
let diff = 0; for (let i = 0; i < D.length; i++) if (comp[i] !== D[i] && (D[i - (i % 4) + 3] || comp[i - (i % 4) + 3])) diff++;
report.verification = { overlappingPixels: overlaps, differingChannelValues: diff, identical: overlaps === 0 && diff === 0 };
T.writePng(`${out}/composite.png`, { width: W, height: H, data: comp });
// label map for review (one flat colour per layer)
const COL = [[200, 200, 200], [120, 190, 120], [250, 205, 170], [200, 60, 60], [60, 110, 220], [40, 170, 220], [150, 80, 200]];
const lm = new Uint8Array(W * H * 4); for (let i = 0; i < W * H; i++) if (label[i] >= 0) lm.set([...COL[label[i]], 255], i * 4);
T.writePng(`${out}/label-map.png`, { width: W, height: H, data: lm });
writeFileSync(`${out}/masks.json`, JSON.stringify({ polygons: POLYS, earPolygon: EAR_POLY, neckPolygon: NECK_POLY, headBox: HEAD_BOX, neckBox: NECK_BOX, seeds: SEEDS,
  rules: { skinLike: 'alpha ≥ 200, V ≥ 0.80, 0.06 ≤ S ≤ 0.50, hue ≤ 45° or ≥ 345°', neckLike: 'alpha ≥ 200, V ≥ 0.70, 0.12 ≤ S ≤ 0.62, 13° ≤ hue ≤ 40°',
    order: 'features (polygons) → head skin (flood from face and ear seeds; ear outline polygon, non-dark pixels; enclosed pixels) → neck (flood) → chin outline to head → base' }, labelColours: Object.fromEntries(NAMES.map((n, k) => [n, COL[k]])) }, null, 1));
writeFileSync(`${out}/extract-report.json`, JSON.stringify(report, null, 1));
console.log(JSON.stringify(report, null, 1));
