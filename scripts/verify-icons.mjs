// pnpm verify:icons [projectId] [--variant <name>]
// Mechanical checks on masters and exports. This does NOT judge whether the artwork looks good:
// review the contact sheet (pnpm contact-sheet) for that.
import { readFile, readdir, mkdir, rm } from "node:fs/promises";
import { join, relative } from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { BUDGETS, EXPORTS, ICO_SIZES, ROOT, SOURCE_FILES, parseArgs, paths, selectProjects } from "./lib/project.mjs";
import { openBrowser, renderSvg } from "./lib/render.mjs";
import { alphaStats, componentCount, decode, pixel, runsOnColumn, runsOnRow } from "./lib/png.mjs";
import { parseIco } from "./lib/ico.mjs";
import { hygiene } from "./lib/svg.mjs";
import { buildProject } from "./build-icons.mjs";

const results = [];
const record = (status, project, check, detail = "") => results.push({ status, project, check, detail });
const pass = (p, c, d) => record("PASS", p, c, d), fail = (p, c, d) => record("FAIL", p, c, d), warn = (p, c, d) => record("WARN", p, c, d);
const check = (ok, p, c, d) => (ok ? pass : fail)(p, c, d);

const sha = b => createHash("sha256").update(b).digest("hex");
const hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
const lum = ([r, g, b]) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
const contrast = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m); return (x + 0.05) / (y + 0.05); };

/** Colours used by a group of markup, following url(#gradient) references into the defs. */
function colorsOf(markup, defs) {
  const out = new Set([...markup.matchAll(/fill="(#[0-9a-fA-F]{6})"/g)].map(m => m[1].toLowerCase()));
  for (const m of markup.matchAll(/url\(#([^)]+)\)/g)) {
    const grad = defs.match(new RegExp(`<linearGradient[^>]*id="${m[1]}"[\\s\\S]*?</linearGradient>`))?.[0] ?? "";
    for (const s of grad.matchAll(/stop-color="(#[0-9a-fA-F]{6})"/g)) out.add(s[1].toLowerCase());
  }
  return [...out].map(hex);
}
function groups(svg) {
  const defs = svg.match(/<defs>[\s\S]*?<\/defs>/)?.[0] ?? "";
  const bg = svg.match(/<g id="bg">[\s\S]*?<\/g>/)?.[0] ?? "";
  const glyph = svg.match(/<g id="glyph"[\s\S]*?<\/g>/)?.[0] ?? "";
  return { bg: colorsOf(bg, defs), glyph: colorsOf(glyph, defs), hasBg: !!bg };
}

async function verifyProject(browser, id, variant = null) {
  const p = paths(id, variant), P = variant ? `${id}/${variant}` : id;
  const src = {}, svgText = {};
  // 1. Masters: presence, hygiene, size
  for (const name of SOURCE_FILES) {
    const file = join(p.source, name);
    src[name] = await readFile(file).catch(() => null);
    if (!src[name]) { fail(P, `source/${name}`, "missing"); continue; }
    svgText[name] = src[name].toString("utf8");
    const problems = hygiene(name, svgText[name]);
    check(!problems.length, P, `svg hygiene ${name}`, problems.join("; ") || "viewBox 512, no text/filters/images/scripts/external refs");
    check(src[name].length <= BUDGETS[name], P, `size ${name}`, `${src[name].length} B (budget ${BUDGETS[name]})`);
  }
  if (SOURCE_FILES.some(n => !src[n])) return;
  const config = JSON.parse(await readFile(join(p.source, "icon.checks.json"), "utf8").catch(() => "{}"));

  // 2. Exports: complete, no strays, each one parses
  const onDisk = new Map();
  const walk = async dir => { for (const e of await readdir(dir, { withFileTypes: true }).catch(() => [])) { const f = join(dir, e.name); if (e.isDirectory()) await walk(f); else if (e.name !== ".DS_Store") onDisk.set(relative(p.exports, f).split("\\").join("/"), await readFile(f)); } };
  await walk(p.exports);
  const expected = new Set(EXPORTS.map(e => e.file));
  for (const f of expected) if (!onDisk.has(f)) fail(P, `export ${f}`, "missing; run pnpm build:icons");
  for (const f of onDisk.keys()) if (!expected.has(f)) fail(P, `export ${f}`, "unexpected file in exports/");
  check([...expected].every(f => onDisk.has(f)) && onDisk.size === expected.size, P, "export set", `${onDisk.size} files, expected ${expected.size}`);

  for (const spec of EXPORTS) {
    const buf = onDisk.get(spec.file);
    if (!buf) continue;
    if (BUDGETS[spec.file]) check(buf.length <= BUDGETS[spec.file], P, `size ${spec.file}`, `${buf.length} B (budget ${BUDGETS[spec.file]})`);
    if (spec.file.endsWith(".png")) {
      const png = decode(buf), size = spec.size ?? EXPORTS.find(e => e.file === spec.copyOf).size, colorType = buf[25];
      check(png.width === size && png.height === size, P, `png dimensions ${spec.file}`, `${png.width}x${png.height}`);
      const opaque = (spec.alpha ?? EXPORTS.find(e => e.file === spec.copyOf).alpha) === "opaque";
      if (opaque) check(colorType === 2 && alphaStats(png, 255).pixels === size * size, P, `opaque ${spec.file}`, `colour type ${colorType}, fully opaque full-bleed`);
      else check(png.data[3] < 255, P, `rounded corner transparency ${spec.file}`, `corner alpha ${png.data[3]}`);
    }
    if (spec.copyOf) check(sha(buf) === sha(onDisk.get(spec.copyOf)), P, `copy ${spec.file}`, `identical to ${spec.copyOf}`);
    if (spec.svg) { const problems = hygiene(spec.file, buf.toString("utf8"), { source: false }); check(!problems.length, P, `svg hygiene ${spec.file}`, problems.join("; ") || "clean"); }
  }

  // 3. ICO structure
  const ico = onDisk.get("favicon/favicon.ico");
  if (ico) {
    try {
      const frames = parseIco(ico);
      check(JSON.stringify(frames.map(f => f.width)) === JSON.stringify(ICO_SIZES), P, "ico frame sizes", frames.map(f => `${f.width}x${f.height}`).join(", "));
      for (const f of frames) {
        const png = decode(f.png);
        check(png.width === f.width && png.height === f.height && f.bpp === 32, P, `ico frame ${f.width}`, `PNG ${png.width}x${png.height}, ${f.bpp}bpp`);
        const twin = onDisk.get(`favicon/favicon-${f.width}.png`);
        if (twin) check(sha(decode(twin).data) === sha(png.data), P, `ico frame ${f.width} matches favicon-${f.width}.png`, "identical pixels");
      }
    } catch (e) { fail(P, "ico parse", e.message); }
  }

  // 4. Safe areas, centring, maskable cropping (measured on the symbol alone)
  const glyphOf = async (name, size = 512) => renderSvg(browser, svgText[name], size, { glyphOnly: true });
  const tileGlyph = alphaStats(await glyphOf("tile.svg"));
  check(!tileGlyph.empty && tileGlyph.farthest <= 205, P, "maskable safe zone (tile.svg)", `farthest glyph pixel ${tileGlyph.farthest?.toFixed(1)} from centre; limit 205 (80% circle)`);
  const insetOf = s => Math.min(s.minX, s.minY, 512 - s.maxX, 512 - s.maxY);
  for (const [name, minInset] of [["icon.svg", 56], ["favicon.svg", 40], ["glyph.svg", 20]]) {
    const s = alphaStats(await glyphOf(name));
    check(!s.empty && insetOf(s) >= minInset, P, `glyph margin ${name}`, `bbox ${s.minX},${s.minY}-${s.maxX},${s.maxY}; margin ${insetOf(s)} (min ${minInset})`);
    // opticalShift (in 512 canvas units) is the deliberate offset of the bounding box that centres the visual mass; glyph.svg and favicon.svg are scaled 1.2x about the centre.
    const scale = name === "icon.svg" ? 1 : 1.2, shift = (config.opticalShift ?? [0, 0]).map(v => v * scale), tol = config.centroidTolerance ?? 24;
    const bx = (s.minX + s.maxX) / 2, by = (s.minY + s.maxY) / 2;
    check(Math.abs(bx - 256 - shift[0]) <= 4 && Math.abs(by - 256 - shift[1]) <= 4, P, `bbox position ${name}`, `centre ${bx},${by} (expected ${256 + shift[0]},${256 + shift[1]} +-4)`);
    check(Math.abs(s.centroid[0] - 256) <= tol && Math.abs(s.centroid[1] - 256) <= tol, P, `visual centroid ${name}`, `${s.centroid.map(v => v.toFixed(1)).join(", ")} (within ${tol} of 256)`);
  }
  const mask = await glyphOf("tile.svg"); // crop under a circle covering 80% of the width, the guaranteed minimum for any launcher mask
  let lost = 0;
  for (let y = 0; y < 512; y++) for (let x = 0; x < 512; x++) if (mask.data[(512 * y + x) * 4 + 3] >= 128 && Math.hypot(x + 0.5 - 256, y + 0.5 - 256) > 204.8) lost++;
  check(lost === 0, P, "maskable crop under 80% circle", `${lost} glyph pixels outside the circle`);

  // 5. Contrast (WCAG non-text, 3:1)
  for (const name of ["icon.svg", "tile.svg", "favicon.svg"]) {
    const g = groups(svgText[name]);
    let min = Infinity;
    for (const a of g.glyph) for (const b of g.bg) min = Math.min(min, contrast(a, b));
    check(min >= 3, P, `glyph/tile contrast ${name}`, `${min.toFixed(1)}:1 (min 3:1)`);
  }
  // Tile boundary visibility, measured on the rendered pixels: the outermost opaque pixel along each side's midline
  // is the edge colour. It must stand out from the page (3:1, WCAG non-text) on white, #0d1117 and #000000.
  const PAGES = [["#ffffff", "white"], ["#0d1117", "dark"], ["#000000", "black"]];
  for (const name of ["icon.svg", "favicon.svg"]) {
    const png = await renderSvg(browser, svgText[name], 512), mid = 256, edges = [];
    for (const [fixed, step] of [[[0, mid], [1, 0]], [[511, mid], [-1, 0]], [[mid, 0], [0, 1]], [[mid, 511], [0, -1]]]) {
      let [x, y] = fixed;
      while (pixel(png, x, y)[3] < 250 && x >= 0 && x < 512 && y >= 0 && y < 512) { x += step[0]; y += step[1]; }
      edges.push(pixel(png, x, y).slice(0, 3));
    }
    const edge = edges[0], ratios = PAGES.map(([c, label]) => [label, contrast(edge, hex(c))]);
    const light = ratios[0][1], darkMin = Math.min(ratios[1][1], ratios[2][1]), text = ratios.map(([l, r]) => `${l} ${r.toFixed(1)}:1`).join(", ");
    check(light >= 3, P, `tile edge on white ${name}`, `edge rgb(${edge}) ${text}`);
    (darkMin >= 3 ? pass : warn)(P, `tile edge on dark pages ${name}`, `edge rgb(${edge}) ${text}${darkMin < 3 ? "; below 3:1 on a dark page" : ""}`);
    // Regression guard: the edge must not be bright (it should read as a subtle ring, not an outline).
    check(lum(edge) <= 0.35, P, `tile edge not overly bright ${name}`, `relative luminance ${lum(edge).toFixed(2)} (max 0.35)`);
  }
  for (const size of [32, 16]) { // the same tile edge at favicon sizes (antialiased; informational)
    const png = await renderSvg(browser, svgText["favicon.svg"], size);
    let x = 0; while (pixel(png, x, size / 2)[3] < 200 && x < size) x++;
    const e = pixel(png, x, size / 2), a = e[3] / 255, parts = PAGES.slice(1).map(([c, label]) => { const bg = hex(c), comp = e.slice(0, 3).map((v, i) => Math.round(v * a + bg[i] * (1 - a))); return `${label} ${contrast(comp, bg).toFixed(1)}:1`; });
    pass(P, `favicon ${size}px edge pixel (info)`, `rgb(${e.slice(0, 3)}) alpha ${e[3]} ${parts.join(", ")}`);
  }

  // 6. Small-size structure (proxy for legibility; not a visual review)
  for (const rule of config.smallSize ?? []) {
    const png = await glyphOf("favicon.svg", rule.size), parts = componentCount(png), coverage = alphaStats(png).pixels / (rule.size ** 2);
    // A rule scans one pixel row (scanY) or one pixel column (scanX) of the symbol and counts its separate ink runs.
    const byColumn = rule.scanX !== undefined, at = Math.floor((byColumn ? rule.scanX : rule.scanY) * rule.size);
    const runs = byColumn ? runsOnColumn(png, at) : runsOnRow(png, at);
    check(runs === rule.runs, P, `favicon ${rule.size}px ${byColumn ? "column" : "row"} runs`, `${runs} runs on ${byColumn ? "column" : "row"} ${at} (expected ${rule.runs})`);
    check(parts === (config.glyphComponents ?? 1), P, `favicon ${rule.size}px glyph pieces stay separate/joined`, `${parts} piece(s), expected ${config.glyphComponents ?? 1}`);
    check(coverage >= 0.12, P, `favicon ${rule.size}px ink coverage`, `${(coverage * 100).toFixed(1)}% of the canvas (min 12%)`);
  }
  for (const probe of config.colorProbes ?? []) {
    const got = pixel(await renderSvg(browser, svgText[probe.svg], 512), ...probe.at), want = hex(probe.expect);
    check(got.slice(0, 3).every((v, i) => Math.abs(v - want[i]) <= 3), P, `colour probe ${probe.svg} @${probe.at}`, `rendered rgb(${got.slice(0, 3)}) vs ${probe.expect}`);
  }

  // 7. Exports are current and deterministic: two clean builds must be byte-identical and equal what is committed
  const tmp = join(ROOT, ".cache", `verify-${process.pid}`);
  try {
    const a = await buildProject(browser, id, join(tmp, "a"), variant), b = await buildProject(browser, id, join(tmp, "b"), variant);
    const same = [...a].every(([f, buf]) => sha(buf) === sha(b.get(f)));
    check(same && a.size === b.size, P, "deterministic build", `${a.size} files identical across two clean builds`);
    const stale = [...a].filter(([f, buf]) => !onDisk.has(f) || sha(buf) !== sha(onDisk.get(f))).map(([f]) => f);
    check(!stale.length, P, "exports match masters", stale.length ? `stale: ${stale.join(", ")} (run pnpm build:icons)` : "committed exports equal a fresh build");
  } finally { await rm(tmp, { recursive: true, force: true }); }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const browser = await openBrowser();
  try { const args = parseArgs(process.argv.slice(2)); for (const id of await selectProjects(args.id, args.variant)) await verifyProject(browser, id, args.variant); }
  catch (e) { fail("-", "verify run", e.message); }
  finally { await browser.close(); }
  for (const r of results) console.log(`${r.status.padEnd(4)}  ${r.project.padEnd(13)} ${r.check.padEnd(46)} ${r.detail}`);
  const count = s => results.filter(r => r.status === s).length;
  console.log(`\n${count("PASS")} passed, ${count("WARN")} warnings, ${count("FAIL")} failed`);
  console.log("Note: these are mechanical checks. Visual quality and real-device rendering are NOT verified; review the contact sheet.");
  process.exitCode = count("FAIL") ? 1 : 0;
}
