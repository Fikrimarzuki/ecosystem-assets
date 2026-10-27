// M1.0j-C scale verification renders. Characters are only ever DOWNscaled (or shown 1:1);
// every view is rendered twice — composited, and as a character-only mask — so on-screen
// heights are measured, not assumed.
// Usage: node scale_renders.mjs <config.json>
import { readFileSync, writeFileSync } from "node:fs";
const A = "/Users/mfm/code/porto-projects/app-momee/scripts/assets/";
const { readPng, writePng, blank } = await import(A + "png.mjs");
const cfg = JSON.parse(readFileSync(process.argv[2], "utf8"));
const out = cfg.outDir;

// premultiplied area-average draw of src (anchor sa) into dst so the anchor lands on (tx, ty), uniform scale s ≤ 1
function drawScaled(dst, src, [sax, say], [tx, ty], s, { mask = false } = {}) {
  if (s > 1 + 1e-9) throw new Error("enlargement refused");
  const x0 = Math.floor(tx - (sax + 1) * s) - 1, x1 = Math.ceil(tx + (src.width - sax) * s) + 1;
  const y0 = Math.floor(ty - (say + 1) * s) - 1, y1 = Math.ceil(ty + (src.height - say) * s) + 1;
  for (let y = Math.max(0, y0); y < Math.min(dst.height, y1); y++) {
    const sy0 = (y - ty) / s + say + 1, sy1 = (y + 1 - ty) / s + say + 1;
    for (let x = Math.max(0, x0); x < Math.min(dst.width, x1); x++) {
      const sx0 = (x - tx) / s + sax + 0.5, sx1 = (x + 1 - tx) / s + sax + 0.5;
      let r = 0, g = 0, b = 0, a = 0;
      for (let yy = Math.max(0, Math.floor(sy0)); yy < Math.min(src.height, Math.ceil(sy1)); yy++) {
        const wy = Math.min(yy + 1, sy1) - Math.max(yy, sy0);
        for (let xx = Math.max(0, Math.floor(sx0)); xx < Math.min(src.width, Math.ceil(sx1)); xx++) {
          const w = wy * (Math.min(xx + 1, sx1) - Math.max(xx, sx0));
          const o = (yy * src.width + xx) * 4, pa = src.data[o + 3] / 255;
          r += src.data[o] * pa * w; g += src.data[o + 1] * pa * w; b += src.data[o + 2] * pa * w; a += pa * w;
        }
      }
      const area = (sx1 - sx0) * (sy1 - sy0);
      const A_ = Math.min(1, a / area);
      if (A_ <= 0) continue;
      const o = (y * dst.width + x) * 4;
      if (mask) { dst.data[o + 3] = Math.max(dst.data[o + 3], Math.round(A_ * 255)); dst.data.fill(255, o, o + 3); continue; }
      const c = [r / a, g / a, b / a];
      const da = dst.data[o + 3] / 255, oa = A_ + da * (1 - A_);
      for (let k = 0; k < 3; k++) dst.data[o + k] = Math.round((c[k] * A_ + dst.data[o + k] * da * (1 - A_)) / oa);
      dst.data[o + 3] = Math.round(oa * 255);
    }
  }
}
function bounds128(img) {
  let b = [img.width, img.height, -1, -1];
  for (let y = 0; y < img.height; y++) for (let x = 0; x < img.width; x++)
    if (img.data[(y * img.width + x) * 4 + 3] >= 128) b = [Math.min(b[0], x), Math.min(b[1], y), Math.max(b[2], x), Math.max(b[3], y)];
  return b;
}
// world image (1 px/u) with edge-replicated bleed, so camera frames beyond 1280×720 show wall/floor (as the Phaser scene does)
function worldCrop(room, wx, wy, ww, wh) {
  const o = blank(ww, wh);
  for (let y = 0; y < wh; y++) for (let x = 0; x < ww; x++) {
    const sx = Math.min(room.width - 1, Math.max(0, wx + x)), sy = Math.min(room.height - 1, Math.max(0, wy + y));
    o.data.set(room.data.subarray((sy * room.width + sx) * 4, (sy * room.width + sx) * 4 + 4), (y * ww + x) * 4);
  }
  return o;
}
function downscale(img, s) { // whole image, uniform s ≤ 1
  const W = Math.round(img.width * s), H = Math.round(img.height * s), o = blank(W, H);
  drawScaled(o, img, [0, -1], [0, 0], s);
  return o;
}

const room = readPng(cfg.room);
const chars = Object.fromEntries(Object.entries(cfg.characters).map(([k, c]) => [k, { ...c, img: readPng(c.native), shadow: readPng(c.shadowNative) }]));
const report = { views: [], lineup: null };

// 1. full scene at 1 px/u, characters placed in world units on separate layers
function scene(placements) {
  const comp = { width: room.width, height: room.height, data: new Uint8Array(room.data) };
  const masks = {};
  for (const [k, feet] of Object.entries(placements)) {
    const c = chars[k], s = c.heightU / c.figureHeightPx;
    drawScaled(comp, c.shadow, c.anchor, feet, s);
    const m = blank(room.width, room.height);
    drawScaled(m, c.img, c.anchor, feet, s, { mask: true });
    masks[k] = m;
  }
  // depth: sorted by feet y (asset-pipeline §4 rig contract) — nearer characters draw last
  for (const [k, feet] of Object.entries(placements).sort((p, q) => p[1][1] - q[1][1])) { const c = chars[k]; drawScaled(comp, c.img, c.anchor, feet, c.heightU / c.figureHeightPx); }
  return { comp, masks };
}
const base = scene(cfg.placements.default);
writePng(`${out}/bedroom-full.@1x.png`, base.comp);
for (const [k, m] of Object.entries(base.masks)) {
  const b = bounds128(m);
  report.views.push({ view: "full bedroom @1x (1 px/u)", character: k, expectedPx: chars[k].heightU, measuredPx: b[3] - b[1] + 1, soleRow: b[3], feetY: cfg.placements.default[k][1] });
}
// 2. camera frames: crop world, then downscale to CSS px (zoom ≤ 1) or show 1:1 (zoom > 1, labelled)
for (const v of cfg.views) {
  const sc = v.placements ? scene(v.placements) : base;
  const wx = Math.round(v.cx - v.visW / 2), wy = Math.round(v.cy - v.visH / 2);
  const bg = worldCrop(sc.comp, wx, wy, v.visW, v.visH);
  // re-place characters on the cropped frame so out-of-room bleed doesn't clip them
  const z = Math.min(1, v.zoom);
  const img = z < 1 ? downscale(bg, z) : bg;
  writePng(`${out}/${v.name}.png`, img);
  for (const [k, m] of Object.entries(sc.masks)) {
    const mc = worldCrop(m, wx, wy, v.visW, v.visH);
    const md = z < 1 ? downscale(mc, z) : mc;
    const b = bounds128(md);
    const visible = b[3] >= 0;
    report.views.push({ view: v.name, character: k, cameraZoom: v.zoom, renderScale: z, visible,
      expectedPx: visible ? +(chars[k].heightU * z).toFixed(1) : null, measuredPx: visible ? b[3] - b[1] + 1 : null,
      deviceCssPx: +(chars[k].heightU * v.zoom).toFixed(1),
      clippedByFrame: visible ? [b[0] === 0 && 'left', b[1] === 0 && 'top', b[2] === md.width - 1 && 'right', b[3] === md.height - 1 && 'bottom'].filter(Boolean) : [] });
  }
}
// 3. line-up on a common ground line at 1 px/u (tier @1x images, unscaled)
{
  const W = 560, H = 360, gy = 330, L = blank(W, H);
  L.data.fill(255);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) L.data.set([254, 250, 241, 255], (y * W + x) * 4);
  const line = (y, col) => { for (let x = 20; x < W - 20; x++) L.data.set(col, (y * W + x) * 4); };
  for (let u = 0; u <= 300; u += 50) line(gy - u, u === 0 ? [89, 70, 61, 255] : [226, 211, 190, 255]);
  line(gy - 200, [166, 90, 51, 255]); line(gy - 290, [166, 90, 51, 255]);
  const masks = {};
  for (const [k, c] of Object.entries(chars)) {
    const t = readPng(c.tier1x), [ax, ay] = c.tier1xAnchor, X = c.lineupX;
    for (let y = 0; y < t.height; y++) for (let x = 0; x < t.width; x++) {
      const so = (y * t.width + x) * 4, a = t.data[so + 3] / 255; if (!a) continue;
      const dx = X - ax + x, dy = gy - ay + y; if (dx < 0 || dy < 0 || dx >= W || dy >= H) continue;
      const o = (dy * W + dx) * 4;
      for (let k2 = 0; k2 < 3; k2++) L.data[o + k2] = Math.round(t.data[so + k2] * a + L.data[o + k2] * (1 - a));
    }
    masks[k] = bounds128(t);
  }
  writePng(`${out}/lineup.@1x.png`, L);
  report.lineup = Object.fromEntries(Object.entries(chars).map(([k, c]) => {
    const b = masks[k]; return [k, { tier: c.tier1x.split("/").pop(), heightPx: b[3] - b[1] + 1, soleRowInTier: b[3], anchorRow: c.tier1xAnchor[1],
      headTopToChinNativePx: c.chinNative - c.hairTopNative, heads: +(c.figureHeightPx / (c.chinNative - c.hairTopNative)).toFixed(2) }];
  }));
  const hb = report.lineup.boy.heightPx, hm = report.lineup.mom.heightPx;
  report.lineup.ratio = +(hm / hb).toFixed(3);
}
writeFileSync(`${out}/scale-report.json`, JSON.stringify(report, null, 1));
console.log(JSON.stringify(report, null, 1));
