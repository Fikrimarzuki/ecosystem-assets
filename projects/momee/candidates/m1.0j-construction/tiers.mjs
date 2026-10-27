// M1.0j-B: place an extracted figure on stable canvases (native, @1x, @2x) by its feet anchor.
// Native = the extracted pixels unresampled (only translated by whole pixels).
// Tiers = premultiplied area-average downscale at one uniform scale (never enlarges).
// Usage: node tiers.mjs <extract.json> <extracted.png> <outDir> <name> <heightU> <canvasU W,H> <anchorU X,Y>
const A = "/Users/mfm/code/porto-projects/app-momee/scripts/assets/";
const { readPng, writePng, blank } = await import(A + "png.mjs");
const [, , infoJson, figPath, out, name, hU, canvasU, anchorU] = process.argv;
const info = JSON.parse(infoJson);
const fig = readPng(figPath);
const [bx0, by0, bx1, by1] = info.figureBounds;
const [ax, ay] = info.feetAnchorPx;              // sole row = by1
const figH = by1 - by0 + 1;
const [cw, ch] = canvasU.split(",").map(Number);
const [aux, auy] = anchorU.split(",").map(Number);
const res = { name, figureHeightPx: figH, nativePxPerUnit: +(figH / Number(hU)).toFixed(4), files: [] };

// native canvas: 16 px padding left/right/top, 8 px below the soles, anchor centred
const half = Math.max(ax - bx0, bx1 - ax) + 16;
const nW = 2 * half, nH = 16 + figH + 8, nAx = half, nAy = 16 + figH - 1;
const native = blank(nW, nH);
for (let y = by0; y <= by1; y++) for (let x = bx0; x <= bx1; x++) {
  const s = (y * fig.width + x) * 4, dx = x - ax + nAx, dy = y - ay + nAy;
  native.data.set(fig.data.subarray(s, s + 4), (dy * nW + dx) * 4);
}
writePng(`${out}/${name}.native.png`, native);
res.files.push({ tier: "native", width: nW, height: nH, anchorPx: [nAx, nAy], scale: 1 });

function place(tier) {
  const ppu = tier === "@1x" ? 1 : 2;
  const W = cw * ppu, H = ch * ppu, tx = aux * ppu, ty = auy * ppu;
  const s = (Number(hU) * ppu) / figH;            // uniform
  if (s > 1) return null;                          // would enlarge: not produced
  const img = blank(W, H);
  // output pixel (x,y) covers source area [(x - tx)/s + nAx, ...] in native coords; the sole row's
  // bottom edge (nAy + 1) maps to ty (the anchor row's bottom edge is the ground line).
  for (let y = 0; y < H; y++) {
    const y0 = (y - ty) / s + nAy + 1, y1 = (y + 1 - ty) / s + nAy + 1;
    if (y1 <= 0 || y0 >= nH) continue;
    for (let x = 0; x < W; x++) {
      const x0 = (x - tx) / s + nAx + 0.5, x1 = (x + 1 - tx) / s + nAx + 0.5;
      if (x1 <= 0 || x0 >= nW) continue;
      let r = 0, g = 0, b = 0, a = 0, w = 0;
      for (let yy = Math.max(0, Math.floor(y0)); yy < Math.min(nH, Math.ceil(y1)); yy++) {
        const wy = Math.min(yy + 1, y1) - Math.max(yy, y0);
        for (let xx = Math.max(0, Math.floor(x0)); xx < Math.min(nW, Math.ceil(x1)); xx++) {
          const wt = wy * (Math.min(xx + 1, x1) - Math.max(xx, x0));
          const o = (yy * nW + xx) * 4, pa = native.data[o + 3] / 255;
          r += native.data[o] * pa * wt; g += native.data[o + 1] * pa * wt; b += native.data[o + 2] * pa * wt;
          a += pa * wt; w += wt;
        }
      }
      const area = (x1 - x0) * (y1 - y0);
      const o = (y * W + x) * 4;
      if (a > 0) img.data.set([Math.round(r / a), Math.round(g / a), Math.round(b / a)], o);
      img.data[o + 3] = Math.round((a / area) * 255);
    }
  }
  writePng(`${out}/${name}.${tier}.png`, img);
  return { tier, width: W, height: H, anchorPx: [tx, ty], scale: +s.toFixed(5), pxPerUnit: ppu };
}
for (const t of ["@1x", "@2x"]) {
  const r = place(t);
  res.files.push(r ?? { tier: t, skipped: `would need ${((Number(hU) * (t === "@1x" ? 1 : 2)) / figH).toFixed(3)}× enlargement` });
}
console.log(JSON.stringify(res));
