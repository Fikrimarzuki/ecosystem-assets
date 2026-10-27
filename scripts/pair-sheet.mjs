// pnpm pair-sheet <projectId> <variant>
// Side-by-side review of the current production icon (A) and one candidate variant (B) at identical displayed sizes,
// with close-ups of the left stem and the right wedge. Writes previews/<variant>-comparison.png. Nothing is replaced.
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { paths } from "./lib/project.mjs";
import { openBrowser, renderSvg } from "./lib/render.mjs";

// Close-up windows in 512-canvas units: [x, y, width, height], plus the x of the production stem's inner edge as a guide line.
const CLOSEUPS = { cv: { stem: [96, 262, 116, 128], wedge: [262, 214, 150, 176], guide: 173.4 } };
const SITE = { cv: { title: "CV | Fikri Marzuki", url: "cv.fikrimarzuki.work", label: "CV" } };
const uri = async file => `data:image/png;base64,${(await readFile(file)).toString("base64")}`;

/** Width in canvas units of the leftmost ink run on one row of the symbol alone (alpha-weighted), at 512 px. */
async function stemWidth(browser, svgFile, y) {
  const png = await renderSvg(browser, await readFile(svgFile, "utf8"), 512, { glyphOnly: true });
  let sum = 0, started = false;
  for (let x = 0; x < png.width; x++) { const a = png.data[(png.width * y + x) * 4 + 3] / 255; if (a > 0.02) { sum += a; started = true; } else if (started) break; }
  return sum;
}

async function load(label, p) {
  const f = rel => uri(join(p.exports, rel));
  return { label, i512: await f("png/icon-512.png"), i192: await f("png/icon-192.png"), f32: await f("favicon/favicon-32.png"), f16: await f("favicon/favicon-16.png"), apple: await f("apple/apple-touch-icon.png"), mask: await f("png/icon-maskable-512.png") };
}

const sizes = it => `
  <div class="big"><img src="${it.i512}" width="512" height="512" alt=""><figcaption>512 px, actual size</figcaption></div>
  <div class="row">
    <figure><img src="${it.i192}" width="192" height="192" alt=""><figcaption>192</figcaption></figure>
    <figure><img src="${it.i192}" width="64" height="64" alt=""><figcaption>64 (192 scaled)</figcaption></figure>
    <figure><img src="${it.f32}" width="32" height="32" alt=""><figcaption>32</figcaption></figure>
    <figure><img src="${it.f16}" width="16" height="16" alt=""><figcaption>16</figcaption></figure>
    <figure><img class="zoom" src="${it.f32}" width="96" height="96" alt=""><figcaption>32 at 3x</figcaption></figure>
    <figure><img class="zoom" src="${it.f16}" width="96" height="96" alt=""><figcaption>16 at 6x</figcaption></figure>
  </div>`;
const crop = (it, [x, y, w, h], z, guide) => `<div class="crop" style="width:${w * z}px;height:${h * z}px;background-image:url(${it.i512});background-size:${512 * z}px ${512 * z}px;background-position:-${x * z}px -${y * z}px">${guide !== undefined ? `<i style="left:${(guide - x) * z}px"></i>` : ""}</div>`;
const tab = (it, cls, site) => `<div class="browser ${cls}"><div class="tab"><img src="${it.f16}" width="16" height="16" alt=""><span>${site.title}</span><b>×</b></div></div>`;
const ghosts = n => Array.from({ length: n }, (_, i) => `<i class="g" style="--h:${(i * 83 + 30) % 360}"></i>`).join("");
const phone = it => `<div class="phone"><div class="home">${ghosts(3)}<img class="ios" src="${it.apple}" width="54" height="54" alt=""></div>
  <div class="home">${ghosts(1)}<img class="circle" src="${it.mask}" width="54" height="54" alt=""><img class="squircle" src="${it.mask}" width="54" height="54" alt=""><img class="rsq" src="${it.mask}" width="54" height="54" alt=""></div></div>`;

function column(it, cfg, site, widths) {
  const z = 4;
  return `<section><h2>${it.label}</h2>
    <div class="panel light"><h3>Light #ffffff</h3>${sizes(it)}</div>
    <div class="panel dark"><h3>Dark #0d1117</h3>${sizes(it)}</div>
    <h3 class="cap">Close-ups: left stem (4x, the red line marks the production stem's inner edge) and right wedge (3x)</h3>
    <div class="closeups">${crop(it, cfg.stem, z, cfg.guide)}${crop(it, cfg.wedge, 3)}</div>
    <p class="note">Stem width ${widths.detail.toFixed(1)} units (512 px) · favicon stem ${widths.fav32.toFixed(2)} px at 32 · ${widths.fav16.toFixed(2)} px at 16</p>
    <h3 class="cap">Browser tab</h3>${tab(it, "light", site)}${tab(it, "dark", site)}
    <h3 class="cap">Home screen (iOS, then Android circle / squircle / rounded square)</h3>${phone(it)}</section>`;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [id, variant] = process.argv.slice(2);
  if (!id || !variant) throw new Error("Usage: pnpm pair-sheet <projectId> <variant>");
  const cfg = CLOSEUPS[id];
  if (!cfg) throw new Error(`pair-sheet has no close-up windows for "${id}"; add them to CLOSEUPS`);
  const site = SITE[id] ?? { title: id, url: "fikrimarzuki.work", label: id };
  const prod = paths(id), cand = paths(id, variant), browser = await openBrowser();
  try {
    const widths = async p => {
      const fav = await readFile(join(p.source, "favicon.svg"), "utf8"), row = (png, y) => { let s = 0, st = false; for (let x = 0; x < png.width; x++) { const a = png.data[(png.width * y + x) * 4 + 3] / 255; if (a > 0.02) { s += a; st = true; } else if (st) break; } return s; };
      return { detail: await stemWidth(browser, join(p.source, "icon.svg"), 340), fav32: row(await renderSvg(browser, fav, 32, { glyphOnly: true }), 23), fav16: row(await renderSvg(browser, fav, 16, { glyphOnly: true }), 11) };
    };
    const a = await load("A · Current approved production icon", prod), b = await load(`B · Candidate: ${variant}`, cand);
    const html = `<!doctype html><meta charset="utf-8"><style>
    *{box-sizing:border-box}body{margin:0;width:1320px;background:#e9edf2;font:13px/1.35 -apple-system,system-ui,sans-serif;color:#1c2430;padding:28px}
    h1{margin:0 0 4px;font-size:24px}p.top{margin:0 0 18px;color:#4a5568}.cols{display:grid;grid-template-columns:1fr 1fr;gap:28px}
    section h2{margin:0 0 10px;font-size:15px;text-transform:uppercase;letter-spacing:.08em;color:#2d3748}
    .panel{border-radius:12px;padding:14px;margin-bottom:12px;border:1px solid #cfd6df}.panel h3{margin:0 0 10px;font-size:11.5px;font-weight:600;opacity:.75}
    .light{background:#fff}.dark{background:#0d1117;color:#c9d1d9;border-color:#30363d}
    .big{margin-bottom:12px;text-align:center}.big figcaption,figcaption{margin-top:6px;font-size:11px;opacity:.75;text-align:center}
    .row{display:flex;gap:10px;align-items:flex-end}figure{margin:0}.zoom{image-rendering:pixelated}
    .cap{margin:14px 0 6px;font-size:11.5px;font-weight:600;color:#4a5568}.note{margin:6px 0 0;color:#4a5568;font-size:12px}
    .closeups{display:flex;gap:14px;align-items:flex-start;background:#0d1117;padding:12px;border-radius:12px}.crop{position:relative;background-repeat:no-repeat;image-rendering:auto;border-radius:6px;flex:none}
    .crop i{position:absolute;top:0;bottom:0;width:2px;background:#ff4d6d;opacity:.8}
    .browser{padding:8px 8px 0;border-radius:10px 10px 0 0;margin-bottom:6px}.browser.light{background:#dee1e6}.browser.dark{background:#202124;color:#e8eaed}
    .tab{display:flex;align-items:center;gap:8px;padding:8px 12px;border-radius:8px 8px 0 0;font-size:12px;width:230px}.light .tab{background:#fff;color:#202124}.dark .tab{background:#35363a}.tab b{margin-left:auto;font-weight:400}
    .phone{background:linear-gradient(160deg,#2c3e6b,#5b3d7a);border-radius:22px;padding:14px;display:flex;flex-direction:column;gap:12px}
    .home{display:flex;gap:12px}.g{display:block;width:54px;height:54px;border-radius:22.37%;background:hsl(var(--h) 45% 55%);opacity:.6}
    .ios{border-radius:22.37%}.circle{border-radius:50%}.squircle{border-radius:32%}.rsq{border-radius:18%}
    </style><h1>${id.toUpperCase()}: optical balance, current vs candidate</h1>
    <p class="top">Both icons are shown at identical displayed sizes, generated from committed or locally built exports. The candidate is not promoted. This is a review aid; judge the artwork here.</p>
    <div class="cols">${column(a, cfg, site, await widths(prod))}${column(b, cfg, site, await widths(cand))}</div>`;
    const page = await browser.newPage({ viewport: { width: 1376, height: 900 }, deviceScaleFactor: 1 });
    await page.setContent(html, { waitUntil: "load" });
    await page.evaluate(() => Promise.all([...document.images].map(i => i.decode())));
    const out = join(prod.previews, `${variant}-comparison.png`);
    await mkdir(prod.previews, { recursive: true });
    await writeFile(out, await page.screenshot({ fullPage: true, type: "png" }));
    console.log(`${id}: wrote ${out}`);
  } finally { await browser.close(); }
}
