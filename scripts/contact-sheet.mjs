// pnpm contact-sheet [projectId]
// Renders a review sheet from the committed exports into projects/<id>/branding/previews/contact-sheet.png.
// The sheet is for human review; it is a preview, not a production asset.
import { readFile, writeFile, mkdir, readdir, access } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { ROOT, paths, selectProjects } from "./lib/project.mjs";
import { openBrowser } from "./lib/render.mjs";

const REFERENCE = join(ROOT, "references/branding/group1-refined-concept.png");
// Where each project's concept tile sits in the 1536x1024 Group 1 sheet: [x, y, size].
const REFERENCE_CROPS = { cv: [46, 320, 178], playground: [469, 320, 178], support: [258, 320, 178], projects: [680, 320, 178], tools: [891, 320, 178], configEcosystem: [1316, 320, 178], devtools: [1104, 320, 178] };
const NAMES = { cv: "CV", playground: "Playground", support: "Support", projects: "Projects", tools: "Tools", configEcosystem: "Config Ecosystem", devtools: "DevTools" };
// Tab title, address and home-screen label as they appear on the live site.
const SITE = { cv: { title: "CV | Fikri Marzuki", url: "cv.fikrimarzuki.work", label: "CV" }, playground: { title: "Playground | Fikrimarzuki", url: "play.fikrimarzuki.work", label: "Playground" }, support: { title: "Support · FM Work", url: "support.fikrimarzuki.work", label: "Support" }, projects: { title: "MFM Projects", url: "projects.fikrimarzuki.work", label: "Projects" }, tools: { title: "MFM Tools", url: "tools.fikrimarzuki.work", label: "Tools" }, configEcosystem: { title: "Ecosystem Config", url: "config.fikrimarzuki.work", label: "Config" }, devtools: { title: "MFM Utils", url: "devtools.fikrimarzuki.work", label: "DevTools" } };

const uri = async (file, type) => `data:${type};base64,${(await readFile(file)).toString("base64")}`;

/** Other projects that already have exports, for the family-consistency section. The current project comes last. */
async function familyOf(id) {
  const ids = [];
  for (const e of await readdir(join(ROOT, "projects"), { withFileTypes: true }).catch(() => [])) {
    if (e.isDirectory() && e.name !== id && await access(join(paths(e.name).exports, "png/icon-192.png")).then(() => true, () => false)) ids.push(e.name);
  }
  const ORDER = ["cv", "playground", "support", "projects", "tools", "configEcosystem", "devtools"], all = [...new Set([...ORDER.filter(x => x === id || ids.includes(x)), ...ids.sort(), id])];
  return Promise.all(all.map(async pid => ({ id: pid, i192: await uri(join(paths(pid).exports, "png/icon-192.png"), "image/png"), f32: await uri(join(paths(pid).exports, "favicon/favicon-32.png"), "image/png"), f16: await uri(join(paths(pid).exports, "favicon/favicon-16.png"), "image/png") })));
}

async function sheetHtml(id) {
  const p = paths(id), e = f => join(p.exports, f);
  const img = {
    i512: await uri(e("png/icon-512.png"), "image/png"), i192: await uri(e("png/icon-192.png"), "image/png"),
    f32: await uri(e("favicon/favicon-32.png"), "image/png"), f16: await uri(e("favicon/favicon-16.png"), "image/png"),
    apple: await uri(e("apple/apple-touch-icon.png"), "image/png"), mask: await uri(e("png/icon-maskable-512.png"), "image/png"),
  };
  const crop = REFERENCE_CROPS[id], ref = crop ? await uri(REFERENCE, "image/png") : null;
  const site = SITE[id] ?? { title: NAMES[id] ?? id, url: "fikrimarzuki.work", label: NAMES[id] ?? id };

  const sizes = bg => `
    <div class="row">
      <figure><img src="${img.i512}" width="224" height="224" alt=""><figcaption>512 export<br>scaled to 224</figcaption></figure>
      <figure><img src="${img.i192}" width="192" height="192" alt=""><figcaption>192 export<br>actual size</figcaption></figure>
      <figure><img src="${img.i192}" width="64" height="64" alt=""><figcaption>64<br>(192 scaled)</figcaption></figure>
      <figure><img src="${img.f32}" width="32" height="32" alt=""><figcaption>32<br>actual</figcaption></figure>
      <figure><img src="${img.f16}" width="16" height="16" alt=""><figcaption>16<br>actual</figcaption></figure>
      <figure><img class="zoom" src="${img.f32}" width="96" height="96" alt=""><figcaption>32 at 3x<br>pixels</figcaption></figure>
      <figure><img class="zoom" src="${img.f16}" width="96" height="96" alt=""><figcaption>16 at 6x<br>pixels</figcaption></figure>
    </div>`;
  const tab = (name, cls) => `
    <div class="browser ${cls}"><div class="tabstrip">
      <div class="tab active"><img src="${img.f16}" width="16" height="16" alt=""><span>${site.title}</span><b>×</b></div>
      <div class="tab"><span class="dot"></span><span>New Tab</span></div>
      <div class="tab"><img src="${img.f32}" width="16" height="16" alt=""><span>2x display favicon</span></div>
    </div><div class="url">${site.url}</div><figcaption>${name}</figcaption></div>`;
  const neighbours = n => Array.from({ length: n }, (_, i) => `<div class="app ghost"><i style="--h:${(i * 57 + 20) % 360}"></i><span>App</span></div>`).join("");
  const phone = `
    <div class="phone"><div class="grid">
      ${neighbours(3)}<div class="app"><img class="ios" src="${img.apple}" width="54" height="54" alt=""><span>${site.label}</span></div>${neighbours(4)}
    </div><figcaption>iOS home screen<br>apple-touch-icon, 180 → 60pt, OS rounds corners</figcaption></div>
    <div class="phone android"><div class="grid">
      ${neighbours(2)}<div class="app"><img class="circle" src="${img.mask}" width="54" height="54" alt=""><span>${site.label}</span></div>${neighbours(2)}
      <div class="app"><img class="squircle" src="${img.mask}" width="54" height="54" alt=""><span>${site.label}</span></div>${neighbours(1)}<div class="app"><img class="rsq" src="${img.mask}" width="54" height="54" alt=""><span>${site.label}</span></div>${neighbours(2)}
    </div><figcaption>Android launcher masks<br>maskable-512 under circle, squircle, rounded square</figcaption></div>`;
  const compare = crop ? `
    <div class="cmp"><figure><div class="refcrop" style="background-image:url(${ref});background-position:-${crop[0] * 1.5}px -${crop[1] * 1.5}px;background-size:${1536 * 1.5}px ${1024 * 1.5}px;width:${crop[2] * 1.5}px;height:${crop[2] * 1.5}px"></div><figcaption>Concept (raster, from the approved sheet,<br>shown at 150% of its source size)</figcaption></figure>
    <figure><img src="${img.i512}" width="${crop[2] * 1.5}" height="${crop[2] * 1.5}" alt=""><figcaption>Production icon-512 (original SVG geometry)<br>same displayed size</figcaption></figure></div>` : "<p>No concept crop configured.</p>";

  const family = await familyOf(id);
  const famPanel = (cls, label) => `<div class="panel ${cls}"><h3>${label}</h3><div class="row">${family.map(m => `<figure><img src="${m.i192}" width="128" height="128" alt=""><figcaption>${NAMES[m.id] ?? m.id}</figcaption></figure>`).join("")}${family.map(m => `<figure><img src="${m.f32}" width="32" height="32" alt=""><figcaption>${NAMES[m.id] ?? m.id}<br>32</figcaption></figure><figure><img src="${m.f16}" width="16" height="16" alt=""><figcaption>16</figcaption></figure>`).join("")}</div></div>`;
  const famTabs = cls => `<div class="browser ${cls}"><div class="tabstrip">${family.map((m, i) => `<div class="tab${i === family.length - 1 ? " active" : ""}"><img src="${m.f16}" width="16" height="16" alt=""><span>${NAMES[m.id] ?? m.id}</span></div>`).join("")}</div><div class="url">fikrimarzuki.work</div></div>`;
  const familySection = family.length > 1 ? `<h2>Family consistency (${family.map(m => NAMES[m.id] ?? m.id).join(" + ")})</h2>
    <div class="panels">${famPanel("light", "Light background")}${famPanel("dark", "Dark background")}</div>
    <div class="panels" style="margin-top:14px">${famTabs("light")}${famTabs("dark")}</div>` : "";
  return `<!doctype html><meta charset="utf-8"><style>
  *{box-sizing:border-box}body{margin:0;width:1800px;background:#e9edf2;font:14px/1.35 -apple-system,system-ui,sans-serif;color:#1c2430;padding:32px}
  h1{margin:0 0 4px;font-size:26px}h2{margin:28px 0 10px;font-size:16px;text-transform:uppercase;letter-spacing:.08em;color:#4a5568}
  p.note{margin:0 0 4px;color:#4a5568}.panels{display:grid;grid-template-columns:1fr 1fr;gap:20px}
  .panel{border-radius:14px;padding:18px;border:1px solid #cfd6df}.panel.light{background:#fff}.panel.dark{background:#0d1117;color:#c9d1d9;border-color:#30363d}
  .panel h3{margin:0 0 14px;font-size:13px;font-weight:600;opacity:.8}.row{display:flex;gap:12px;align-items:flex-end}
  figure{margin:0;text-align:center}figcaption{margin-top:8px;font-size:11.5px;opacity:.75}img.zoom{image-rendering:pixelated}
  .browser{border-radius:12px 12px 8px 8px;padding:10px 10px 12px;width:100%}.browser.light{background:#dee1e6;color:#202124}.browser.dark{background:#202124;color:#e8eaed}
  .tabstrip{display:flex;gap:4px}.tab{display:flex;align-items:center;gap:8px;padding:8px 12px;border-radius:8px 8px 0 0;font-size:12px;min-width:200px;opacity:.7}
  .light .tab.active{background:#fff;opacity:1}.dark .tab.active{background:#35363a;opacity:1}.tab b{margin-left:auto;font-weight:400}.dot{width:16px;height:16px;border-radius:50%;background:currentColor;opacity:.25}
  .url{margin-top:0;padding:8px 14px;border-radius:0 0 8px 8px;font-size:12px}.light .url{background:#fff}.dark .url{background:#35363a}
  .browser figcaption{margin-top:8px}.mobile{display:flex;gap:28px}.phone{width:300px;background:#1b1d29;border-radius:34px;padding:22px 18px 14px;color:#fff}
  .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:18px 6px;min-height:300px;align-content:start;background:linear-gradient(160deg,#2c3e6b,#5b3d7a);border-radius:22px;padding:22px 10px}
  .app{display:flex;flex-direction:column;align-items:center;gap:4px;font-size:10px}.app i{width:54px;height:54px;border-radius:22.37%;background:hsl(var(--h) 45% 55%);opacity:.6}
  .ios{border-radius:22.37%}.circle{border-radius:50%}.squircle{border-radius:32%}.rsq{border-radius:18%}.phone figcaption{text-align:center;margin-top:12px;opacity:.7}
  .cmp{display:flex;gap:40px;background:#fff;border-radius:14px;padding:20px;border:1px solid #cfd6df;width:max-content}.refcrop{background-repeat:no-repeat;border-radius:6px}
  </style>
  <h1>${NAMES[id] ?? id}: icon contact sheet</h1><p class="note">Generated from the committed exports in projects/${id}/branding/exports. A review aid, not a verification: judge the artwork here.</p>
  <h2>Sizes on light and dark backgrounds</h2>
  <div class="panels"><div class="panel light"><h3>Light background (#ffffff)</h3>${sizes()}</div><div class="panel dark"><h3>Dark background (#0d1117)</h3>${sizes()}</div></div>
  <h2>Browser tab</h2><div class="panels">${tab("Light browser chrome", "light")}${tab("Dark browser chrome", "dark")}</div>
  <h2>Mobile home screen</h2><div class="mobile">${phone}</div>
  <h2>Comparison with the approved concept</h2>${compare}
  ${familySection}`;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const browser = await openBrowser();
  try {
    for (const id of await selectProjects(process.argv[2])) {
      const page = await browser.newPage({ viewport: { width: 1864, height: 900 }, deviceScaleFactor: 1 });
      await page.setContent(await sheetHtml(id), { waitUntil: "load" });
      await page.evaluate(() => Promise.all([...document.images].map(i => i.decode())));
      const out = join(paths(id).previews, "contact-sheet.png");
      await mkdir(paths(id).previews, { recursive: true });
      await writeFile(out, await page.screenshot({ fullPage: true, type: "png" }));
      await page.close();
      console.log(`${id}: wrote ${out}`);
    }
  } finally { await browser.close(); }
}
