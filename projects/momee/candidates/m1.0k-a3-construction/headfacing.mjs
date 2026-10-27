// Supplementary facing / identity test (M1.0k-A2 method, saved as a script in M1.0k-A3).
// Scales the candidate master so its head (hair top → chin) matches the accepted Mom v1.2 extraction's head (156 px; downscale
// only), then compares the head-and-shoulders region (1.6 heads tall, 200 px wide) and the face band (0.35–1.0 head) as drawn
// and mirrored: IoU of alpha ≥ 128 masks and mean absolute RGB difference where both are solid.
// Usage: node headfacing.mjs <candidate-master.png> <chinRow>
const T = await import('/Users/mfm/code/porto-projects/ecosystem-assets/scripts/momee-character-master.mjs');
const [, , candPath, chinArg] = process.argv;
const acc = T.readPng('/Users/mfm/code/porto-projects/ecosystem-assets/projects/momee/source/characters/mom/mom-three-quarter-accepted-clean.v1.native.png');
const cand = T.readPng(candPath);
const accTop = 16, accChin = 172, candTop = T.figureBox(cand, 128)[1], candChin = Number(chinArg);
const s = (accChin - accTop) / (candChin - candTop);
const c = T.resample(cand, Math.round(cand.width * s), Math.round(cand.height * s), [0, 0], [0, 0], s);
const cb = T.figureBox(c, 128), ab = T.figureBox(acc, 128);
function diff(a, ax, ay, b, bx, by, w, h, mir) { let s = 0, n = 0, i = 0, u = 0; for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const xa = ax + x, ya = ay + y; const xb = mir ? bx + w - 1 - x : bx + x, yb = by + y; if (xa < 0 || ya < 0 || xa >= a.width || ya >= a.height || xb < 0 || yb < 0 || xb >= b.width || yb >= b.height) continue; const oa = (ya * a.width + xa) * 4, ob = (yb * b.width + xb) * 4; const pa = a.data[oa + 3] >= 128, pb = b.data[ob + 3] >= 128; if (pa && pb) { i++; for (let k = 0; k < 3; k++) s += Math.abs(a.data[oa + k] - b.data[ob + k]); n += 3; } if (pa || pb) u++; } return { iou: +(i / u).toFixed(3), meanAbs: +(s / n).toFixed(1) }; }
const com = (img, top, h) => { let sx = 0, n = 0; for (let y = top; y < top + h; y++) for (let x = 0; x < img.width; x++) if (img.data[(y * img.width + x) * 4 + 3] >= 128) { sx += x; n++; } return sx / n; };
const H = Math.round(156 * 1.6), W = 200, ac = com(acc, ab[1], H), cc = com(c, cb[1], H);
const hs = [false, true].map((m) => diff(acc, Math.round(ac - W / 2), ab[1], c, Math.round(cc - W / 2), cb[1], W, H, m));
const fT = Math.round(156 * 0.35), fH = Math.round(156 * 0.65), FW = 120;
const fb = [false, true].map((m) => diff(acc, Math.round(ac - FW / 2), ab[1] + fT, c, Math.round(cc - FW / 2), cb[1] + fT, FW, fH, m));
console.log(JSON.stringify({ scale: +s.toFixed(4), headAndShoulders: { asDrawn: hs[0], mirrored: hs[1] }, faceBand: { asDrawn: fb[0], mirrored: fb[1] } }));
