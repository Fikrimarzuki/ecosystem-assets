// pnpm compare-sheet <projectId> <variant> [<variant> ...]
// Side-by-side review sheet: the approved concept, the current production icon and candidate variants
// (projects/<id>/branding/concepts/<variant>/). Writes previews/variant-comparison.png. Nothing is replaced.
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { ROOT, paths } from "./lib/project.mjs";
import { openBrowser } from "./lib/render.mjs";

const REFERENCE = join(ROOT, "references/branding/group1-refined-concept.png");
const REFERENCE_CROPS = { cv: [46, 320, 178] };
const uri = async file => `data:image/png;base64,${(await readFile(file)).toString("base64")}`;

async function load(label, dir) {
  const f = name => uri(join(dir, name));
  return { label, i512: await f("png/icon-512.png"), i192: await f("png/icon-192.png"), f32: await f("favicon/favicon-32.png"), f16: await f("favicon/favicon-16.png"), apple: await f("apple/apple-touch-icon.png"), mask: await f("png/icon-maskable-512.png") };
}

const sizes = it => `
  <div class="row"><img src="${it.i512}" width="200" height="200" alt=""><img src="${it.i192}" width="192" height="192" alt=""></div>
  <div class="row small">
    <img src="${it.f32}" width="32" height="32" alt=""><img src="${it.f16}" width="16" height="16" alt="">
    <img class="zoom" src="${it.f32}" width="96" height="96" alt=""><img class="zoom" src="${it.f16}" width="96" height="96" alt="">
  </div>`;
const tab = (it, cls) => `<div class="browser ${cls}"><div class="tab"><img src="${it.f16}" width="16" height="16" alt=""><span>CV | Fikri Marzuki</span><b>×</b></div></div>`;
const ghosts = n => Array.from({ length: n }, (_, i) => `<i style="--h:${(i * 83 + 30) % 360}"></i>`).join("");
const mobile = it => `<div class="home">${ghosts(3)}<img class="ios" src="${it.apple}" width="54" height="54" alt=""></div>
  <div class="home">${ghosts(1)}<img class="circle" src="${it.mask}" width="54" height="54" alt=""><img class="squircle" src="${it.mask}" width="54" height="54" alt=""><img class="rsq" src="${it.mask}" width="54" height="54" alt=""></div>`;

function column(it) {
  return `<section><h2>${it.label}</h2>
    <div class="panel light"><h3>Light #ffffff</h3>${sizes(it)}</div>
    <div class="panel dark"><h3>Dark #0d1117</h3>${sizes(it)}</div>
    <div class="panel black"><h3>Black #000000</h3><div class="row small"><img src="${it.i192}" width="96" height="96" alt=""><img src="${it.f32}" width="32" height="32" alt=""><img src="${it.f16}" width="16" height="16" alt=""></div></div>
    <h3 class="cap">Browser tab</h3>${tab(it, "light")}${tab(it, "dark")}
    <h3 class="cap">Home screen (iOS, then Android circle / squircle / rounded square)</h3><div class="phone">${mobile(it)}</div></section>`;
}

async function html(id, items) {
  const crop = REFERENCE_CROPS[id];
  if (!crop) throw new Error(`compare-sheet has no concept crop for "${id}"; add one to REFERENCE_CROPS`);
  const ref = await uri(REFERENCE), z = 200 / crop[2];
  const concept = `<section><h2>Approved concept</h2>
    <div class="panel light"><h3>Raster crop from the Group 1 sheet</h3><div class="row"><div class="refcrop" style="background-image:url(${ref});background-position:-${crop[0] * z}px -${crop[1] * z}px;background-size:${1536 * z}px ${1024 * z}px;width:200px;height:200px"></div></div></div>
    <p class="note">A conceptual raster at ${crop[2]}px source size. It has no exports at other sizes, so the size, tab and home-screen rows do not apply. Its glow and rounded corners are not reproduced in the SVG candidates (no blur filters).</p></section>`;
  return `<!doctype html><meta charset="utf-8"><style>
  *{box-sizing:border-box}body{margin:0;width:1940px;background:#e9edf2;font:13px/1.35 -apple-system,system-ui,sans-serif;color:#1c2430;padding:28px}
  h1{margin:0 0 4px;font-size:24px}p.top{margin:0 0 18px;color:#4a5568}.cols{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}
  section h2{margin:0 0 10px;font-size:15px;text-transform:uppercase;letter-spacing:.08em;color:#2d3748}
  .panel{border-radius:12px;padding:14px;margin-bottom:12px;border:1px solid #cfd6df}.panel h3{margin:0 0 10px;font-size:11.5px;font-weight:600;opacity:.75}
  .light{background:#fff}.dark{background:#0d1117;color:#c9d1d9;border-color:#30363d}.black{background:#000;color:#c9d1d9;border-color:#222}
  .row{display:flex;gap:12px;align-items:flex-end;margin-bottom:12px}.row.small{margin-bottom:0}.zoom{image-rendering:pixelated}.refcrop{background-repeat:no-repeat;border-radius:6px}
  .cap{margin:14px 0 6px;font-size:11.5px;font-weight:600;color:#4a5568}.note{color:#4a5568;font-size:12px}
  .browser{padding:8px 8px 0;border-radius:10px 10px 0 0;margin-bottom:6px}.browser.light{background:#dee1e6}.browser.dark{background:#202124;color:#e8eaed}
  .tab{display:flex;align-items:center;gap:8px;padding:8px 12px;border-radius:8px 8px 0 0;font-size:12px;width:220px}.light .tab{background:#fff;color:#202124}.dark .tab{background:#35363a}.tab b{margin-left:auto;font-weight:400}
  .phone{background:#1b1d29;border-radius:22px;padding:14px;display:flex;flex-direction:column;gap:12px;background:linear-gradient(160deg,#2c3e6b,#5b3d7a)}
  .home{display:flex;gap:12px}.home i{display:block;width:54px;height:54px;border-radius:22.37%;background:hsl(var(--h) 45% 55%);opacity:.6}
  .ios{border-radius:22.37%}.circle{border-radius:50%}.squircle{border-radius:32%}.rsq{border-radius:18%}
  </style><h1>CV: variant comparison</h1><p class="top">Generated from committed exports: the approved concept, the current A2.3b production icon and the candidate variants. Production exports are not replaced. This is a review aid; judge the artwork here.</p>
  <div class="cols">${concept}${items.map(column).join("")}</div>`;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [id, ...variants] = process.argv.slice(2);
  if (!id || !variants.length) throw new Error("Usage: pnpm compare-sheet <projectId> <variant> [<variant> ...]");
  const labels = { "variant-a": "Variant A: integrated M", "variant-b": "Variant B: minimal M" };
  const items = [await load("Current A2.3b icon", paths(id).exports), ...await Promise.all(variants.map(v => load(labels[v] ?? v, paths(id, v).exports)))];
  const browser = await openBrowser();
  try {
    const page = await browser.newPage({ viewport: { width: 1996, height: 900 }, deviceScaleFactor: 1 });
    await page.setContent(await html(id, items), { waitUntil: "load" });
    await page.evaluate(() => Promise.all([...document.images].map(i => i.decode())));
    const out = join(paths(id).previews, "variant-comparison.png");
    await mkdir(paths(id).previews, { recursive: true });
    await writeFile(out, await page.screenshot({ fullPage: true, type: "png" }));
    console.log(`${id}: wrote ${out}`);
  } finally { await browser.close(); }
}
