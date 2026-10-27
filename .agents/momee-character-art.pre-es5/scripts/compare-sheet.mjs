#!/usr/bin/env node
// node compare-sheet.mjs --out <sheet.png> [--height 360] "Label=path.png[@x,y,w,h]" ...
// Side-by-side review sheet: every image (or crop) is scaled to the same displayed height, labelled, on the
// reference background colour. Uses the repository's Chromium (scripts/lib/render.mjs). Refuses to overwrite.
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const { openBrowser } = await import(fileURLToPath(new URL("../../../../scripts/lib/render.mjs", import.meta.url)));
const args = process.argv.slice(2);
const opt = name => { const i = args.indexOf(name); return i >= 0 ? args.splice(i, 2)[1] : undefined; };
const out = opt("--out"), height = Number(opt("--height") ?? 360);
if (!out || !args.length) { console.error('usage: node compare-sheet.mjs --out sheet.png [--height 360] "Label=img.png[@x,y,w,h]" ...'); process.exit(2); }
if (existsSync(out)) { console.error(`ERROR: ${out} exists; choose a new name`); process.exit(2); }

const items = args.map(a => {
  const m = a.match(/^([^=]+)=(.+?)(?:@(\d+),(\d+),(\d+),(\d+))?$/);
  if (!m) throw new Error(`bad item: ${a}`);
  const [, label, path, ...crop] = m;
  return { label, src: `data:image/png;base64,${readFileSync(path).toString("base64")}`, crop: crop[0] ? crop.map(Number) : null };
});

const browser = await openBrowser();
try {
  const page = await browser.newPage({ viewport: { width: 400, height: 200 }, deviceScaleFactor: 1 });
  await page.setContent(`<!doctype html><style>body{margin:0;background:#f8f0e5;font:600 15px system-ui;color:#5a3a2a}
    #row{display:inline-flex;gap:16px;padding:16px;align-items:flex-start}figure{margin:0}figcaption{padding-top:6px}</style><div id="row"></div>`);
  const size = await page.evaluate(async ({ items, height }) => {
    const row = document.getElementById("row");
    for (const it of items) {
      const img = new Image(); img.src = it.src; await img.decode();
      const [sx, sy, sw, sh] = it.crop ?? [0, 0, img.naturalWidth, img.naturalHeight];
      const c = document.createElement("canvas");
      c.height = height; c.width = Math.round(sw * height / sh);
      const g = c.getContext("2d"); g.imageSmoothingQuality = "high";
      g.drawImage(img, sx, sy, sw, sh, 0, 0, c.width, c.height);
      const f = document.createElement("figure"), cap = document.createElement("figcaption");
      cap.textContent = it.label; f.append(c, cap); row.append(f);
    }
    const r = row.getBoundingClientRect(); return { w: Math.ceil(r.width), h: Math.ceil(r.height) };
  }, { items, height });
  await page.setViewportSize({ width: size.w, height: size.h });
  writeFileSync(out, await page.screenshot({ clip: { x: 0, y: 0, width: size.w, height: size.h }, type: "png" }));
  console.log(`${out}: ${size.w}x${size.h}, ${items.length} panel(s) at ${height}px: ${items.map(i => i.label).join(" | ")}`);
} finally { await browser.close(); }
