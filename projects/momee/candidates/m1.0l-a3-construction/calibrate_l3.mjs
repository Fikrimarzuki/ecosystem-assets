// Calibration only (in memory; nothing saved as an asset): what residual would the panel-2 fit show if the panel
// really were master pixels enlarged ×1/f and re-encoded? Enlarges the master head crop bilinearly by 1/f, then
// runs the same downscale-and-place fit, and also adds the JPEG-free 8-bit rounding only.
const T = await import('/Users/mfm/code/porto-projects/ecosystem-assets/scripts/momee-character-master.mjs');
const [, , masterPath, A1, fArg, oxArg, oyArg, wArg, hArg] = process.argv;
const M = T.readPng(masterPath), W = M.width, f = Number(fArg), ox = Number(oxArg), oy = Number(oyArg), pw = Number(wArg), ph = Number(hArg);
const near = T.readPng(`${A1}/face-eyes__open__eye-near.png`).data, far = T.readPng(`${A1}/face-eyes__open__eye-far.png`).data;
// synthetic panel: bilinear enlargement of the master region that panel 2 covers
const pan = { width: pw, height: ph, data: new Uint8Array(pw * ph * 4) };
for (let y = 0; y < ph; y++) for (let x = 0; x < pw; x++) { const sx = ox + (x + 0.5) * f - 0.5, sy = oy + (y + 0.5) * f - 0.5, x0 = Math.floor(sx), y0 = Math.floor(sy), fx = sx - x0, fy = sy - y0;
  for (let k = 0; k < 4; k++) { const g = (X, Y) => M.data[(Y * W + X) * 4 + k]; pan.data[(y * pw + x) * 4 + k] = Math.round(g(x0, y0) * (1 - fx) * (1 - fy) + g(x0 + 1, y0) * fx * (1 - fy) + g(x0, y0 + 1) * (1 - fx) * fy + g(x0 + 1, y0 + 1) * fx * fy); } }
const r = T.resample(pan, Math.round(pw * f), Math.round(ph * f), [0, 0], [0, 0], f);
let best = 1e9;
for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) { let s = 0, n = 0; for (let y = 0; y < r.height; y++) for (let x = 0; x < r.width; x++) { const X = x + ox + dx, Y = y + oy + dy; if (X < 250 || Y < 160 || X > 570 || Y > 470) continue; const i = Y * W + X, o = i * 4, q = (y * r.width + x) * 4; if (M.data[o + 3] < 250 || r.data[q + 3] < 200 || near[o + 3] || far[o + 3]) continue; for (let k = 0; k < 3; k++) s += Math.abs(M.data[o + k] - r.data[q + k]); n += 3; } best = Math.min(best, s / n); }
console.log(JSON.stringify({ calibration: 'master enlarged ×' + (1 / f).toFixed(3) + ' bilinear then refit', residualOutsideEyeMasks: +best.toFixed(2) }));
