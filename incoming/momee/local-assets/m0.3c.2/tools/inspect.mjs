// M0.3c.2 visual inspection of /dev/cutout-poc (local; outputs are git-ignored).
// Usage: node inspect.mjs <baseUrl> <outDir>   (run with cwd = apps/web for Playwright)
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { inflateSync } from "node:zlib";

const require = createRequire(process.cwd() + "/package.json");
const { chromium, devices } = require("@playwright/test");
const [, , BASE, OUT] = process.argv;
mkdirSync(OUT, { recursive: true });

// --- tiny PNG decode for screenshots (8-bit RGB/RGBA, non-interlaced) ---
function decode(buf) {
  let pos = 8, w = 0, h = 0, ct = 0; const idat = [];
  while (pos < buf.length) {
    const len = buf.readUInt32BE(pos), type = buf.toString("ascii", pos + 4, pos + 8), body = buf.subarray(pos + 8, pos + 8 + len);
    if (type === "IHDR") { w = body.readUInt32BE(0); h = body.readUInt32BE(4); ct = body[9]; }
    else if (type === "IDAT") idat.push(body); else if (type === "IEND") break;
    pos += 12 + len;
  }
  const bpp = ct === 6 ? 4 : 3, raw = inflateSync(Buffer.concat(idat)), stride = w * bpp, out = new Uint8Array(w * h * 3);
  const prev = new Uint8Array(stride), cur = new Uint8Array(stride);
  for (let y = 0; y < h; y++) {
    const f = raw[y * (stride + 1)], line = raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1));
    for (let i = 0; i < stride; i++) {
      const a = i >= bpp ? cur[i - bpp] : 0, b = prev[i], c = i >= bpp ? prev[i - bpp] : 0; let v = line[i];
      if (f === 1) v += a; else if (f === 2) v += b; else if (f === 3) v += (a + b) >> 1;
      else if (f === 4) { const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c); v += pa <= pb && pa <= pc ? a : pb <= pc ? b : c; }
      cur[i] = v & 255;
    }
    for (let x = 0; x < w; x++) for (let k = 0; k < 3; k++) out[(y * w + x) * 3 + k] = cur[x * bpp + k];
    prev.set(cur);
  }
  return { w, h, d: out };
}
// Sharpness: mean absolute Laplacian of luminance (higher = crisper detail).
function sharpness({ w, h, d }) {
  const L = (x, y) => { const o = (y * w + x) * 3; return 0.2126 * d[o] + 0.7152 * d[o + 1] + 0.0722 * d[o + 2]; };
  let s = 0, n = 0;
  for (let y = 1; y < h - 1; y++) for (let x = 1; x < w - 1; x++) { s += Math.abs(4 * L(x, y) - L(x - 1, y) - L(x + 1, y) - L(x, y - 1) - L(x, y + 1)); n++; }
  return +(s / n).toFixed(2);
}
const changed = (a, b) => { let n = 0; for (let i = 0; i < a.d.length; i += 3) if (Math.abs(a.d[i] - b.d[i]) + Math.abs(a.d[i + 1] - b.d[i + 1]) + Math.abs(a.d[i + 2] - b.d[i + 2]) > 6) n++; return n; };

// World-space regions (child stands at x 520, feet y 630; 200 world units tall).
const FACE = { x: 478, y: 450, w: 80, h: 70 };
const NECK = { x: 500, y: 500, w: 40, h: 35 };
const TORSO = { x: 470, y: 480, w: 100, h: 100 };
async function worldClip(page, r) {
  const box = await page.locator("canvas").boundingBox();
  const sx = box.width / 1280, sy = box.height / 720;
  return { x: box.x + r.x * sx, y: box.y + r.y * sy, width: r.w * sx, height: r.h * sy };
}
async function ready(page, url) {
  await page.goto(url);
  await page.locator('[data-testid="poc-stage"][data-status="ready"]').waitFor({ timeout: 60000 });
  await page.waitForTimeout(600);
}

const results = { sharpness: {}, network: {}, reducedMotion: {}, metrics: {} };
const browser = await chromium.launch();

// 1) Desktop DPR 2: scaling × tier, face crop sharpness + screenshots.
for (const scaling of ["builtin", "hidpi"]) for (const tier of [1, 2]) for (const mipmaps of [1]) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 860 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  let bytes = 0; page.on("response", async (r) => { if (r.url().includes("/game/_poc/")) { try { bytes += (await r.body()).length; } catch {} } });
  await page.emulateMedia({ reducedMotion: "reduce" }); // static frame for fair comparison
  await ready(page, `${BASE}/dev/cutout-poc?tier=${tier}&scaling=${scaling}&mipmaps=${mipmaps}`);
  const name = `desktop-dpr2-${scaling}-${tier}x`;
  const face = await page.screenshot({ clip: await worldClip(page, FACE) });
  writeFileSync(`${OUT}/${name}-face.png`, face);
  if (tier === 2) await page.screenshot({ path: `${OUT}/${name}-full.png` });
  results.sharpness[name] = sharpness(decode(face));
  results.network[name] = bytes;
  results.metrics[name] = await page.locator('[data-testid="poc-stage"]').getAttribute("data-backing");
  await ctx.close();
}

// 1b) Mipmaps on vs off at a small display size (phone portrait, builtin @2x): minification quality.
for (const mipmaps of [1, 0]) {
  const ctx = await browser.newContext({ ...devices["Pixel 7"] });
  const page = await ctx.newPage();
  await page.emulateMedia({ reducedMotion: "reduce" });
  await ready(page, `${BASE}/dev/cutout-poc?tier=2&scaling=builtin&mipmaps=${mipmaps}`);
  const face = await page.screenshot({ clip: await worldClip(page, { x: 460, y: 420, w: 120, h: 220 }) });
  writeFileSync(`${OUT}/pixel7-portrait-builtin-2x-mipmaps${mipmaps}-char.png`, face);
  results.sharpness[`pixel7-builtin-2x-mipmaps${mipmaps}`] = sharpness(decode(face));
  await ctx.close();
}

// 2) Mobile screenshots (portrait + landscape), both scalings.
for (const [label, dev] of [["portrait", devices["Pixel 7"]], ["landscape", devices["Pixel 7 landscape"]]]) {
  for (const scaling of ["builtin", "hidpi"]) {
    const ctx = await browser.newContext({ ...dev });
    const page = await ctx.newPage();
    await ready(page, `${BASE}/dev/cutout-poc?tier=2&scaling=${scaling}`);
    await page.screenshot({ path: `${OUT}/pixel7-${label}-${scaling}.png` });
    results.metrics[`pixel7-${label}-${scaling}`] = await page.locator('[data-testid="poc-stage"]').getAttribute("data-backing");
    await ctx.close();
  }
}

// 3) Reduced motion: torso region changes over time only when idle is on.
for (const reduce of [false, true]) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 860 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  await page.emulateMedia({ reducedMotion: reduce ? "reduce" : "no-preference" });
  await ready(page, `${BASE}/dev/cutout-poc?tier=2&scaling=hidpi`);
  const clip = await worldClip(page, TORSO);
  const a = decode(await page.screenshot({ clip })); await page.waitForTimeout(1700);
  const b = decode(await page.screenshot({ clip }));
  results.reducedMotion[reduce ? "reduce" : "default"] = { idle: await page.locator('[data-testid="poc-stage"]').getAttribute("data-idle"), changedPx: changed(a, b) };
  if (!reduce) {
    // Seam check at the chin/neck across several breathing phases (4× zoomed crops).
    for (let k = 0; k < 4; k++) { writeFileSync(`${OUT}/seam-neck-phase${k}.png`, await page.screenshot({ clip: await worldClip(page, NECK) })); await page.waitForTimeout(450); }
    writeFileSync(`${OUT}/seam-sleeve.png`, await page.screenshot({ clip: await worldClip(page, { x: 478, y: 505, w: 30, h: 40 }) }));
  }
  await ctx.close();
}

// 4) Skin tones: 2 methods × 3 tones, hidpi @2x DPR 2.
{
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 860 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  await page.emulateMedia({ reducedMotion: "reduce" });
  await ready(page, `${BASE}/dev/cutout-poc?tier=2&scaling=hidpi`);
  for (const method of ["Prepared variants", "Runtime tint"]) {
    await page.getByRole("button", { name: method }).click();
    for (const tone of ["Light (original)", "Medium (test)", "Deep (test)"]) {
      await page.getByRole("button", { name: tone }).click();
      await page.waitForTimeout(250);
      const file = `${OUT}/skin-${method.startsWith("P") ? "painted" : "tint"}-${tone.split(" ")[0].toLowerCase()}.png`;
      writeFileSync(file, await page.screenshot({ clip: await worldClip(page, { x: 455, y: 425, w: 130, h: 215 }) }));
    }
  }
  results.metrics.fpsHeadless = await page.locator("output").textContent();
  await ctx.close();
}

await browser.close();
writeFileSync(`${OUT}/results.json`, JSON.stringify(results, null, 2));
console.log(JSON.stringify(results, null, 2));
