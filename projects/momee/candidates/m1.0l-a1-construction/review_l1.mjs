// M1.0l-A1 review data: missing-artwork map panels, difference map and area counts (head crop, 1:1).
// Usage: node review_l1.mjs <master.png> <layersDir> <kritaProjection.png> <outDir>
import { writeFileSync, mkdirSync } from 'node:fs';
const T = await import('/Users/mfm/code/porto-projects/ecosystem-assets/scripts/momee-character-master.mjs');
const [, , masterPath, L, projPath, out] = process.argv;
mkdirSync(out, { recursive: true });
const m = T.readPng(masterPath), W = m.width, H = m.height;
const ld = (n) => T.readPng(`${L}/${n}.png`).data;
const base = ld('base'), neck = ld('body-skin__neck-visible'), head = ld('head-skin__base');
const feats = { 'eye-near': ld('face-eyes__open__eye-near'), 'eye-far': ld('face-eyes__open__eye-far'), 'brow-far': ld('face-brows__neutral__brow-far'), mouth: ld('face-mouth__neutral') };
const CROP = [240, 150, 580, 480], cw = CROP[2] - CROP[0], ch = CROP[3] - CROP[1];
const inPoly = (x, y, P) => { let c = false; for (let i = 0, j = P.length - 1; i < P.length; j = i++) { const [xi, yi] = P[i], [xj, yj] = P[j]; if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c; } return c; };
const NEAR_BROW = [[348, 214], [370, 209], [400, 208], [425, 212], [442, 222], [436, 230], [410, 226], [380, 224], [352, 226]];
const v = (d, o) => Math.max(d[o], d[o + 1], d[o + 2]) / 255;

// category per pixel
const cat = new Uint8Array(W * H); // 0 none, 1 attachment footprint (skin beneath to paint), 2 neck extension to paint, 3 near brow (not separable),
//                                 4 face rim kept in base, 5 hair (front/back not separable), 6 visible neck, 7 head skin, 8 body (out of scope)
const area = { attachmentFootprints: {}, neckExtensionBand: 0, nearBrowRegion: 0, faceRimInBase: 0, hairInHeadArea: 0 };
for (const [n, d] of Object.entries(feats)) { let c = 0; for (let i = 0; i < W * H; i++) if (d[i * 4 + 3]) { cat[i] = 1; c++; } area.attachmentFootprints[n] = c; }
for (let i = 0; i < W * H; i++) if (!cat[i] && head[i * 4 + 3]) cat[i] = 7;
for (let i = 0; i < W * H; i++) if (!cat[i] && neck[i * 4 + 3]) cat[i] = 6;
// neck extension: in each column the neck occupies at its top, the 24 px (6 u) directly above the neck's top pixel
for (let x = 0; x < W; x++) { let top = -1; for (let y = 370; y < 440; y++) if (neck[(y * W + x) * 4 + 3] >= 128) { top = y; break; } if (top < 0 || top > 402) continue;
  for (let y = top - 24; y < top; y++) { const i = y * W + x; if (cat[i] === 7 || base[i * 4 + 3]) { cat[i] = 2; area.neckExtensionBand++; } } }
for (let y = CROP[1]; y < CROP[3]; y++) for (let x = CROP[0]; x < CROP[2]; x++) {
  const i = y * W + x, o = i * 4; if (!base[o + 3] || cat[i]) continue;
  if (inPoly(x + 0.5, y + 0.5, NEAR_BROW)) { cat[i] = 3; area.nearBrowRegion++; continue; }
  let nearHead = false; for (let dy = -3; dy <= 3 && !nearHead; dy++) for (let dx = -3; dx <= 3; dx++) { const j = (y + dy) * W + x + dx; if (head[j * 4 + 3] || feats['eye-far'][j * 4 + 3]) { nearHead = true; break; } }
  if (nearHead && v(base, o) >= 0.6) { cat[i] = 4; area.faceRimInBase++; continue; }
  const h = (() => { const r = base[o], g = base[o + 1], b = base[o + 2]; return r > b && r >= g && v(base, o) < 0.85; })();
  const collar = x >= 355 && x <= 470 && y >= 395 && v(base, o) >= 0.4;
  if (h && y < 470 && !collar) { cat[i] = 5; area.hairInHeadArea++; } else cat[i] = 8;
}
const COL = { 1: [214, 58, 58], 2: [214, 58, 58], 3: [240, 150, 40], 4: [240, 220, 60], 5: [140, 90, 200], 6: [110, 180, 110], 7: [250, 215, 185], 8: [205, 205, 205] };
function panel(show, name, hatch = new Set()) {
  const o = new Uint8Array(cw * ch * 4);
  for (let y = 0; y < ch; y++) for (let x = 0; x < cw; x++) {
    const i = (y + CROP[1]) * W + x + CROP[0], c = cat[i], a = m.data[i * 4 + 3];
    // dimmed grey original as context
    const g = Math.round((m.data[i * 4] * 0.3 + m.data[i * 4 + 1] * 0.59 + m.data[i * 4 + 2] * 0.11) * 0.35 + 160);
    let col = a ? [g, g, g] : [255, 255, 255];
    if (show.includes(c)) { col = COL[c]; if (hatch.has(c) && ((x + y) % 6 < 3)) col = [255, 255, 255]; }
    o.set([...col, 255], (y * cw + x) * 4);
  }
  T.writePng(`${out}/${name}.png`, { width: cw, height: ch, data: o });
}
panel([1, 2, 7, 6], 'missing-1-attachment-footprints', new Set([2]));            // red = skin to paint beneath the swappable attachments
panel([2, 7, 6], 'missing-2-neck-extension', new Set([2]));      // hatched red = neck to paint under the chin (≥ 24 px)
panel([3, 4, 5], 'missing-3-not-separable');                     // orange near brow, yellow face rim, purple hair
// difference map (|projection − master| × 64, black = identical) on the head crop and the full canvas count
const p = T.readPng(projPath); let diff = 0, hiddenRgb = 0, alphaDiff = 0;
const dm = new Uint8Array(cw * ch * 4);
for (let i = 0; i < W * H; i++) { const vis = p.data[i * 4 + 3] || m.data[i * 4 + 3]; let e = 0; for (let k = 0; k < 4; k++) e = Math.max(e, Math.abs(p.data[i * 4 + k] - m.data[i * 4 + k])); if (p.data[i * 4 + 3] !== m.data[i * 4 + 3]) alphaDiff++; if (e && vis) diff++; if (e && !vis) { hiddenRgb++; e = 0; }
  const x = i % W, y = (i - x) / W; if (x >= CROP[0] && x < CROP[2] && y >= CROP[1] && y < CROP[3]) dm.set([Math.min(255, e * 64), 0, 0, 255], ((y - CROP[1]) * cw + x - CROP[0]) * 4); }
T.writePng(`${out}/difference-head.png`, { width: cw, height: ch, data: dm });
writeFileSync(`${out}/review-data.json`, JSON.stringify({ crop: CROP, areaPx: area, nearBrowPolygon: NEAR_BROW, projectionVsMasterDifferingPixels: diff, alphaDifferences: alphaDiff, alphaZeroPixelsWithHiddenRgbNotCarried: hiddenRgb,
  legend: { red: 'skin/eyelid to paint beneath swappable attachments', hatchedRed: 'neck extension to paint (hidden under the chin)', orange: 'near brow: inside the hair sweep, not separable',
    yellow: 'face rim and cheek contour pixels kept in base', purple: 'hair: front and back not separable from the flat art', green: 'visible neck (extracted)', peach: 'head skin (extracted)' } }, null, 1));
console.log(JSON.stringify({ area, diff, alphaDiff, hiddenRgb }));
