// M1.0l-A2 concept-sheet analysis (read-only on the sheet and the master).
// 1. Crops the expression thumbnails at native resolution (no resampling).
// 2. Frame consistency: aligns each frame to its "existing" partner (integer shift ±5 px) and measures the mean
//    absolute RGB difference OUTSIDE the feature band (should be ≈ noise floor if only the eyes/mouth changed).
// 3. Identity/scale: fits a uniformly DOWNSCALED copy of the accepted master to the "open (existing)" thumbnail
//    (scale and offset search) and reports the residual and the implied enlargement factor needed to reach 4 px/u.
// Usage: node analyse_l2.mjs <sheet.png> <master.png> <outDir>
import { writeFileSync, mkdirSync } from 'node:fs';
const T = await import('/Users/mfm/code/porto-projects/ecosystem-assets/scripts/momee-character-master.mjs');
const [, , sheetPath, masterPath, out] = process.argv;
mkdirSync(out, { recursive: true });
const S = T.readPng(sheetPath), M = T.readPng(masterPath);
const PANELS = { 'eyes-open-a': [348, 836, 432, 938], 'eyes-half-a': [435, 835, 520, 938], 'eyes-closed': [523, 835, 609, 938], 'eyes-half-b': [612, 835, 698, 938],
  'eyes-open-b': [701, 835, 785, 938], 'mouth-neutral': [813, 836, 916, 938], 'mouth-small-open': [919, 836, 1019, 938], 'mouth-wide-open': [1023, 837, 1123, 938], 'brow-raised': [1155, 837, 1266, 938] };
const crop = (img, [x0, y0, x1, y1]) => { const w = x1 - x0 + 1, h = y1 - y0 + 1, d = new Uint8Array(w * h * 4); for (let y = 0; y < h; y++) d.set(img.data.subarray(((y + y0) * img.width + x0) * 4, ((y + y0) * img.width + x1 + 1) * 4), y * w * 4); return { width: w, height: h, data: d }; };
const C = Object.fromEntries(Object.entries(PANELS).map(([k, b]) => [k, crop(S, b)]));
for (const [k, c] of Object.entries(C)) T.writePng(`${out}/thumb-${k}.png`, c);
// mean abs RGB diff of b (shifted by dx,dy) vs a over rows/cols, excluding a band of rows [e0,e1] (relative to a), with an inset margin
function mad(a, b, dx, dy, band, inset = 6) { let s = 0, n = 0; for (let y = inset; y < a.height - inset; y++) { if (band && y >= band[0] && y <= band[1]) continue; for (let x = inset; x < a.width - inset; x++) { const X = x + dx, Y = y + dy; if (X < 0 || Y < 0 || X >= b.width || Y >= b.height) continue; const o = (y * a.width + x) * 4, q = (Y * b.width + X) * 4; for (let k = 0; k < 3; k++) s += Math.abs(a.data[o + k] - b.data[q + k]); n += 3; } } return s / n; }
function best(a, b, band) { let r = { dx: 0, dy: 0, mad: 1e9 }; for (let dy = -5; dy <= 5; dy++) for (let dx = -5; dx <= 5; dx++) { const m = mad(a, b, dx, dy, band); if (m < r.mad) r = { dx, dy, mad: +m.toFixed(2) }; } return r; }
const EYE_BAND = [42, 76], MOUTH_BAND = [78, 100];
const R = { panels: PANELS, consistency: {} };
R.consistency.noiseFloor_openA_vs_openB = { whole: best(C['eyes-open-a'], C['eyes-open-b'], null), outsideEyeBand: best(C['eyes-open-a'], C['eyes-open-b'], EYE_BAND) };
for (const k of ['eyes-half-a', 'eyes-closed', 'eyes-half-b']) R.consistency[`${k}_vs_openA`] = { outsideEyeBand: best(C['eyes-open-a'], C[k], EYE_BAND), insideEyeBandAtThatShift: null };
for (const k of ['mouth-small-open', 'mouth-wide-open']) R.consistency[`${k}_vs_neutral`] = { outsideMouthBand: best(C['mouth-neutral'], C[k], MOUTH_BAND) };
R.consistency['eyes-half-a_vs_eyes-half-b'] = { whole: best(C['eyes-half-a'], C['eyes-half-b'], null) };
R.consistency['mouth-neutral_vs_openA_centre'] = { whole: best(C['eyes-open-a'], crop(S, [823, 836, 907, 938]), null) };
// identity / scale fit: master head region downscaled by s, offset searched, vs eyes-open-a
const A = C['eyes-open-a']; let fit = { mad: 1e9 };
for (let s = 0.24; s <= 0.48 + 1e-9; s += 0.01) {
  const rs = T.resample(M, Math.round(M.width * s), Math.round(M.height * s), [0, 0], [0, 0], s);
  // the thumbnail shows the face; search placement of the master's (x 240..580, y 150..480) region
  for (let oy = Math.round(150 * s) - 20; oy <= Math.round(150 * s) + 90; oy += 1) for (let ox = Math.round(240 * s) - 10; ox <= Math.round(240 * s) + 140; ox += 1) {
    let sum = 0, n = 0; for (let y = 6; y < A.height - 6; y += 2) for (let x = 6; x < A.width - 6; x += 2) { const X = x + ox, Y = y + oy; if (X < 0 || Y < 0 || X >= rs.width || Y >= rs.height) continue; const o = (y * A.width + x) * 4, q = (Y * rs.width + X) * 4; if (rs.data[q + 3] < 200) { sum += 3 * 60; n += 3; continue; } for (let k = 0; k < 3; k++) sum += Math.abs(A.data[o + k] - rs.data[q + k]); n += 3; }
    const m = sum / n; if (m < fit.mad) fit = { scale: +s.toFixed(3), ox, oy, mad: +m.toFixed(2) };
  }
}
fit.enlargementToMaster = +(1 / fit.scale).toFixed(2);
R.identityFit_openA_vs_master = fit;
{ const s = fit.scale, rs = T.resample(M, Math.round(M.width * s), Math.round(M.height * s), [0, 0], [0, 0], s); T.writePng(`${out}/master-at-thumb-scale.png`, crop(rs, [fit.ox, fit.oy, fit.ox + A.width - 1, fit.oy + A.height - 1])); }
writeFileSync(`${out}/analysis.json`, JSON.stringify(R, null, 1));
console.log(JSON.stringify(R, null, 1));
