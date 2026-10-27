// M1.0k-A2 pre-intake for an already-transparent generated figure (derivative only; the original is
// never written). Steps, all alpha-only (RGB of kept pixels is never changed):
//  1. glow trim  — alpha ≤ maxGlowAlpha AND ≥ minDist px (8-connected) from the solid figure (alpha ≥ 128) → 0
//  2. strays     — detached components (alpha > 0) of ≤ maxStray px → 0
//  3. opacity    — the generator left the body ≈ 1% translucent (interior alpha ≈ 253 ± 4). Pixels ≥ 4 px inside the
//                  figure (from any alpha < 128) with alpha ≥ 240 → 255; all others a' = min(255, round(a · 255 / cap)), cap = 253,
//                  preserving the 1–4 px edge falloff.
// Usage: node deglow.mjs <in.png> <out.png> [maxGlowAlpha=4] [minDist=3] [maxStray=64] [cap=auto]
const T = await import('/Users/mfm/code/porto-projects/ecosystem-assets/scripts/momee-character-master.mjs');
const [, , inPath, outPath, g = '4', md = '3', ms = '64', capArg] = process.argv;
const maxGlow = Number(g), minDist = Number(md), maxStray = Number(ms);
const im = T.readPng(inPath), W = im.width, H = im.height, D = new Uint8Array(im.data);
const cap = capArg ? Number(capArg) : 253;
const dist = new Int16Array(W * H).fill(-1); let fr = [];
for (let i = 0; i < W * H; i++) if (D[i * 4 + 3] >= 128) { dist[i] = 0; fr.push(i); }
for (let d = 1; d < minDist && fr.length; d++) {
  const nx = [];
  for (const i of fr) { const x = i % W, y = (i - x) / W; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const X = x + dx, Y = y + dy; if (X < 0 || Y < 0 || X >= W || Y >= H) continue; const j = Y * W + X; if (dist[j] < 0) { dist[j] = d; nx.push(j); } } }
  fr = nx;
}
let glow = 0;
for (let i = 0; i < W * H; i++) { const a = D[i * 4 + 3]; if (a > 0 && a <= maxGlow && dist[i] < 0) { D.fill(0, i * 4, i * 4 + 4); glow++; } }
// strays
const lab = new Int32Array(W * H).fill(-1), comps = [];
for (let i = 0; i < W * H; i++) {
  if (lab[i] >= 0 || !D[i * 4 + 3]) continue;
  const id = comps.length, m = [i]; lab[i] = id;
  for (let k = 0; k < m.length; k++) { const j = m[k], x = j % W, y = (j - x) / W; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const X = x + dx, Y = y + dy; if (X < 0 || Y < 0 || X >= W || Y >= H) continue; const q = Y * W + X; if (lab[q] < 0 && D[q * 4 + 3]) { lab[q] = id; m.push(q); } } }
  comps.push(m);
}
comps.sort((a, b) => b.length - a.length);
let strays = 0, strayComps = 0, keptSmall = 0;
for (const m of comps.slice(1)) { if (m.length <= maxStray) { strayComps++; for (const j of m) { D.fill(0, j * 4, j * 4 + 4); strays++; } } else keptSmall++; }
const inner = new Int16Array(W * H).fill(-1); let f2 = [];
for (let i = 0; i < W * H; i++) if (D[i * 4 + 3] < 128) { inner[i] = 0; f2.push(i); }
for (let d = 1; d < 4 && f2.length; d++) {
  const nx = [];
  for (const i of f2) { const x = i % W, y = (i - x) / W; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const X = x + dx, Y = y + dy; if (X < 0 || Y < 0 || X >= W || Y >= H) continue; const j = Y * W + X; if (inner[j] < 0) { inner[j] = d; nx.push(j); } } }
  f2 = nx;
}
let opaque = 0, interiorSet = 0;
for (let i = 0; i < W * H; i++) {
  const a = D[i * 4 + 3]; if (!a) continue;
  if (inner[i] < 0 && a >= 240) { D[i * 4 + 3] = 255; interiorSet++; } else D[i * 4 + 3] = Math.min(255, Math.round((a * 255) / cap));
  if (D[i * 4 + 3] === 255) opaque++;
}
let rgbChanged = 0;
for (let i = 0; i < D.length; i += 4) if (D[i + 3] && [0, 1, 2].some((k) => D[i + k] !== im.data[i + k])) rgbChanged++;
T.writePng(outPath, { width: W, height: H, data: D });
const box = T.figureBox({ width: W, height: H, data: D }), box128 = T.figureBox({ width: W, height: H, data: D }, 128);
console.log(JSON.stringify({ in: inPath.split('/').pop(), cap, glowPixelsCleared: glow, interiorMadeOpaque: interiorSet, strayComponentsRemoved: strayComps, strayPixels: strays,
  largeSecondaryComponentsKept: keptSmall, opaquePixelsAfter: opaque, rgbChangedOnKeptPixels: rgbChanged, boundsAlphaGt0: box, boundsAlpha128: box128 }));
