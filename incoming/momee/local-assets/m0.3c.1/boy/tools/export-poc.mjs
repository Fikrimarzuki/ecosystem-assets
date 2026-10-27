// M0.3c.2: export the minimum TEMPORARY runtime assets for the Phaser cutout PoC.
// Input:  work/layers/*.png + work/layers/layers.json (M0.3c.1b, technical working layers)
// Output: apps/web/public/game/_poc/boy-v1/  (atlas page per tier + rig JSON + label)
// Deterministic. No pixels are painted; skin-tone variants are colour transforms of skin layers.
//
// Usage (from assets/.local-assets/m0.3c.1/boy): node tools/export-poc.mjs
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { readPng, writePng, blank } from "./png.mjs";

const OUT = "../../../../apps/web/public/game/_poc/boy-v1";
mkdirSync(OUT, { recursive: true });
const manifest = JSON.parse(readFileSync("work/layers/layers.json", "utf8"));
const [CW, CH] = manifest.canvas;

// World scale: the character is ≈ 1180 source px tall (y 28–1208) and the working
// child height is 200 world units (asset-pipeline §4), so 5.9 source px = 1 unit.
const UNITS_PER_SRC_PX = 200 / 1180;
const TIERS = { "1": 1, "2": 2 }; // texels per world unit
const PAD = 2; // per-frame padding in the page; the inner ring of 1 px is edge extrusion

// Test skin tones (NOT approved values). Tone "a" is the original painted skin.
const BASE_SKIN = [254, 204, 150]; // #fecc96, measured base face skin
const TONES = [
  { id: "a", label: "Light (original)", color: "#fecc96", blushTint: "#ffffff", blushAlpha: 1 },
  { id: "b", label: "Medium (test)", color: "#d69a6c", blushTint: "#e6c8c0", blushAlpha: 0.8 },
  { id: "c", label: "Deep (test)", color: "#8d5a3d", blushTint: "#b8a2a0", blushAlpha: 0.55 },
];
const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const lum = (r, g, b) => 0.2126 * r + 0.7152 * g + 0.0722 * b;
const BASE_L = lum(...BASE_SKIN);
const SKIN_SLOTS = new Set(["leg-skin", "body-skin", "head-skin"]);

// ---- source frames (full canvas) ----
const sources = [];
for (const layer of manifest.layers) {
  const img = readPng(`work/layers/${layer.file}`);
  sources.push({ name: layer.slot, img, bbox: layer.bbox });
  if (!SKIN_SLOTS.has(layer.slot)) continue;
  // Neutral greyscale base for runtime MULTIPLY tint.
  const neutral = blank(CW, CH);
  // Per-channel colour transfer ("prepared variant") for tones b and c.
  const variants = Object.fromEntries(TONES.slice(1).map((t) => [t.id, blank(CW, CH)]));
  for (let i = 0; i < CW * CH; i++) {
    const o = i * 4, a = img.data[o + 3]; if (!a) continue;
    const [r, g, b] = [img.data[o], img.data[o + 1], img.data[o + 2]];
    const n = Math.min(1, lum(r, g, b) / BASE_L) * 255;
    neutral.data.set([n, n, n, a], o);
    for (const t of TONES.slice(1)) {
      const T = hex(t.color);
      variants[t.id].data.set([r * T[0] / BASE_SKIN[0], g * T[1] / BASE_SKIN[1], b * T[2] / BASE_SKIN[2], a], o);
    }
  }
  sources.push({ name: `${layer.slot}.neutral`, img: neutral, bbox: layer.bbox });
  for (const t of TONES.slice(1)) sources.push({ name: `${layer.slot}.tone-${t.id}`, img: variants[t.id], bbox: layer.bbox });
}

// ---- area-filter downscale onto a global grid (shared by all frames → exact alignment) ----
function downscale(img, bbox, g) {
  const [x0, y0, x1, y1] = bbox;
  const i0 = Math.floor(x0 * g), j0 = Math.floor(y0 * g);
  const i1 = Math.ceil((x1 + 1) * g), j1 = Math.ceil((y1 + 1) * g);
  const w = i1 - i0, h = j1 - j0, out = blank(w, h), D = out.data, S = img.data;
  for (let j = j0; j < j1; j++) for (let i = i0; i < i1; i++) {
    const sx0 = i / g, sx1 = (i + 1) / g, sy0 = j / g, sy1 = (j + 1) / g;
    let wa = 0, wr = 0, wg = 0, wb = 0, wsum = 0;
    for (let sy = Math.floor(sy0); sy < Math.ceil(sy1); sy++) {
      if (sy < 0 || sy >= img.height) continue;
      const wy = Math.min(sy + 1, sy1) - Math.max(sy, sy0);
      for (let sx = Math.floor(sx0); sx < Math.ceil(sx1); sx++) {
        if (sx < 0 || sx >= img.width) continue;
        const wx = Math.min(sx + 1, sx1) - Math.max(sx, sx0), w8 = wx * wy, o = (sy * img.width + sx) * 4;
        const a = S[o + 3] / 255;
        wsum += w8; wa += w8 * a; wr += w8 * a * S[o]; wg += w8 * a * S[o + 1]; wb += w8 * a * S[o + 2];
      }
    }
    const o = ((j - j0) * w + (i - i0)) * 4;
    if (wa > 0) { D[o] = wr / wa; D[o + 1] = wg / wa; D[o + 2] = wb / wa; D[o + 3] = (wa / wsum) * 255; }
  }
  return { img: out, origin: [i0, j0] };
}

// ---- shelf packing into the smallest power-of-two page (mipmaps need POT; max 2048) ----
const POT = [64, 128, 256, 512, 1024, 2048];
function pack(frames) {
  const sorted = [...frames].sort((a, b) => b.img.height - a.img.height || a.name.localeCompare(b.name));
  let best = null;
  for (const width of POT) {
    let x = 0, y = 0, rowH = 0, ok = true;
    const placed = [];
    for (const f of sorted) {
      const w = f.img.width + PAD * 2, h = f.img.height + PAD * 2;
      if (x + w > width) { x = 0; y += rowH; rowH = 0; }
      if (w > width) { ok = false; break; }
      placed.push({ ...f, x: x + PAD, y: y + PAD });
      x += w; rowH = Math.max(rowH, h);
    }
    const height = POT.find((p) => p >= y + rowH);
    if (!ok || !height) continue;
    // Smallest area; ties go to the squarer page (keeps both sides well under the 2048 limit).
    const better = !best || width * height < best.w * best.h || (width * height === best.w * best.h && Math.max(width, height) < Math.max(best.w, best.h));
    if (better) best = { w: width, h: height, placed };
  }
  if (!best) throw new Error("frames do not fit in a 2048 page");
  return best;
}

const sha = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");
const rigTiers = {};
for (const [tier, tpu] of Object.entries(TIERS)) {
  const g = tpu * UNITS_PER_SRC_PX; // texels per source px
  const frames = sources.map((s) => ({ name: s.name, ...downscale(s.img, s.bbox, g) }));
  const { w: pw, h: ph, placed } = pack(frames);
  const page = blank(pw, ph), P = page.data;
  const atlas = { frames: {}, meta: { app: "momee export-poc.mjs", image: `parts.v1.@${tier}x.png`, format: "RGBA8888", size: { w: pw, h: ph }, scale: "1" } };
  const origins = {};
  for (const f of placed) {
    const { width: w, height: h, data } = f.img;
    // Copy with 1 px edge extrusion into the padding ring (prevents bleeding at frame edges).
    for (let y = -1; y <= h; y++) for (let x = -1; x <= w; x++) {
      const sx = Math.min(w - 1, Math.max(0, x)), sy = Math.min(h - 1, Math.max(0, y));
      P.set(data.subarray((sy * w + sx) * 4, (sy * w + sx) * 4 + 4), ((f.y + y) * pw + f.x + x) * 4);
    }
    atlas.frames[f.name] = { frame: { x: f.x, y: f.y, w, h }, rotated: false, trimmed: false, spriteSourceSize: { x: 0, y: 0, w, h }, sourceSize: { w, h } };
    origins[f.name] = f.origin;
  }
  writePng(`${OUT}/parts.v1.@${tier}x.png`, page);
  writeFileSync(`${OUT}/parts.v1.@${tier}x.json`, JSON.stringify(atlas, null, 2) + "\n");
  rigTiers[tier] = {
    texelsPerUnit: tpu,
    atlas: `parts.v1.@${tier}x.json`,
    image: `parts.v1.@${tier}x.png`,
    page: [pw, ph],
    origins,
    sha256: sha(`${OUT}/parts.v1.@${tier}x.png`),
  };
  console.log(`@${tier}x: page ${pw}×${ph}, ${placed.length} frames`);
}

const rig = {
  schemaVersion: 1,
  status: "TEMPORARY TEST ASSET: technical proof of concept (M0.3c.2) only. Not approved production art. Do not reuse.",
  source: { layers: "assets/.local-assets/m0.3c.1/boy/work/layers/layers.json", candidateSha256: manifest.source.sha256 },
  rig: "child",
  view: "three-quarter, facing right",
  worldUnitsPerSourcePx: UNITS_PER_SRC_PX,
  sourceCanvas: [CW, CH],
  groups: Object.fromEntries(Object.entries(manifest.groups).map(([k, v]) => [k, { parent: v.parent ?? null, pivot: v.pivot }])),
  layers: manifest.layers.map((l) => ({ slot: l.slot, group: l.group, skin: SKIN_SLOTS.has(l.slot) })),
  skinToneTest: { base: "#fecc96", tones: TONES, note: "Test tones only; not reviewed or approved (asset-pipeline O17)." },
  tiers: rigTiers,
};
writeFileSync(`${OUT}/rig.v1.json`, JSON.stringify(rig, null, 2) + "\n");
writeFileSync(
  `${OUT}/TEMPORARY-TEST-ASSETS.md`,
  `# Temporary test assets: Boy cutout PoC (M0.3c.2)

These files exist only for the Phaser cutout proof of concept at \`/dev/cutout-poc\`.

- **Not approved production art.** Derived from the technical working layers of
  Boy candidate v1 (M0.3c.1b), approved for technical testing only.
- Skin tones b and c are **test values**, not reviewed tones.
- Generated by \`assets/.local-assets/m0.3c.1/boy/tools/export-poc.mjs\` (local, not versioned).
- Delete or replace when production assets are approved (asset-pipeline §11).
`,
);
console.log("rig written");
