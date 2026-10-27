// pnpm build:logos <projectId>      build projects/<id>/logo/exports and projects/<id>/social/exports
// pnpm verify:logos <projectId>     rebuild into a temporary folder and check the committed exports match
//
// Logo lockups and the social preview image, composed from the branding masters so they can't drift from the icon:
//   inputs   branding/source/icon.svg (the tile), branding/source/glyph.svg (the symbol), logo/source/wordmark.svg
//   outputs  logo/exports/lockup-light.svg   mark + wordmark, dark ink, for light backgrounds
//            logo/exports/lockup-dark.svg    mark + wordmark, light ink, for dark backgrounds
//            logo/exports/symbol.svg         the symbol alone, transparent (from glyph.svg)
//            social/exports/og-image.png     1200x630 Open Graph / social preview
// The wordmark's ink placeholder is #18203a. Exports are never edited by hand.
import { createHash } from "node:crypto";
import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { ROOT } from "./lib/project.mjs";
import { decode, encode } from "./lib/png.mjs";
import { openBrowser } from "./lib/render.mjs";
import { hygiene, optimizeSvg } from "./lib/svg.mjs";

const INK = "#18203a";
const LIGHT_INK = "#f4f6fa";
const PAPER = "#f4f6fa";
const HAZE = "#dde2ee";
const MARK = 112; // the wordmark's line height equals the mark's size
const GAP = 30;
const OG = { width: 1200, height: 630 };
const BUDGETS = { "logo/exports/lockup-light.svg": 4096, "logo/exports/lockup-dark.svg": 4096, "logo/exports/symbol.svg": 2048, "social/exports/og-image.png": 153600 };

const inner = (svg) => svg.replace(/^[\s\S]*?<svg[^>]*>/, "").replace(/<\/svg>\s*$/, "").replace(/<title>[\s\S]*?<\/title>/, "").replace(/<!--[\s\S]*?-->/g, "");
const viewBox = (svg) => svg.match(/viewBox="([^"]+)"/)?.[1].split(/\s+/).map(Number) ?? [];

/** Mark (scaled from the 512 icon) followed by the wordmark, on one baseline. */
function lockup(icon, wordmark, ink, title) {
  const [, , width] = viewBox(wordmark);
  const total = MARK + GAP + width;
  const word = inner(wordmark).replaceAll(INK, ink);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${total} ${MARK}"><title>${title}</title>` +
    `<g transform="scale(${MARK / 512})">${inner(icon)}</g><g transform="translate(${MARK + GAP} 0)">${word}</g></svg>`;
}

/** Paper background, the light lockup centred, and the symbol as a faint watermark in the corner. */
function socialSvg(light, glyph) {
  const [, , w, h] = viewBox(light);
  const scale = 150 / h, lw = w * scale;
  const x = (OG.width - lw) / 2, y = (OG.height - 150) / 2;
  const watermark = inner(glyph).replace(/fill="#[0-9a-fA-F]{6}"/g, `fill="${HAZE}"`);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${OG.width}" height="${OG.height}" viewBox="0 0 ${OG.width} ${OG.height}">` +
    `<rect width="${OG.width}" height="${OG.height}" fill="${PAPER}"/>` +
    `<g transform="translate(860 300) scale(0.9)">${watermark}</g>` +
    `<rect x="0" y="${OG.height - 18}" width="${OG.width}" height="18" fill="#2b50d6"/>` +
    `<g transform="translate(${x} ${y}) scale(${scale})">${inner(light)}</g></svg>`;
}

async function renderPng(browser, svg, width, height) {
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  try {
    const uri = "data:image/svg+xml;base64," + Buffer.from(svg).toString("base64");
    await page.setContent(`<!doctype html><style>html,body{margin:0}img{display:block}</style><img width="${width}" height="${height}" src="${uri}">`);
    await page.evaluate(() => document.querySelector("img").decode());
    return encode(decode(await page.screenshot({ type: "png", clip: { x: 0, y: 0, width, height } })), { opaque: true });
  } finally {
    await page.close();
  }
}

export async function buildLogos(browser, id) {
  const dir = join(ROOT, "projects", id);
  const read = (file) => readFile(join(dir, file), "utf8");
  const [icon, glyph, wordmark] = await Promise.all([read("branding/source/icon.svg"), read("branding/source/glyph.svg"), read("logo/source/wordmark.svg")]);
  const problems = hygiene("wordmark.svg", wordmark.replace(/viewBox="[^"]+"/, 'viewBox="0 0 512 512"'), { source: false });
  if (problems.length) throw new Error(`Refusing to build ${id}:\n  ${problems.join("\n  ")}`);
  const name = icon.match(/<title>([^<]+)<\/title>/)?.[1] ?? id;
  const light = optimizeSvg(lockup(icon, wordmark, INK, name));
  const out = new Map([
    ["logo/exports/lockup-light.svg", Buffer.from(light)],
    ["logo/exports/lockup-dark.svg", Buffer.from(optimizeSvg(lockup(icon, wordmark, LIGHT_INK, name)))],
    ["logo/exports/symbol.svg", Buffer.from(optimizeSvg(glyph))],
  ]);
  out.set("social/exports/og-image.png", await renderPng(browser, socialSvg(light, glyph), OG.width, OG.height));
  return out;
}

const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  const verify = args.includes("--verify");
  const id = args.find((arg) => !arg.startsWith("--"));
  if (!id || !/^[a-z][a-zA-Z0-9]*$/.test(id)) throw new Error("Usage: build-logos.mjs <projectId> [--verify]");
  const browser = await openBrowser();
  let failed = 0;
  try {
    const out = await buildLogos(browser, id);
    for (const [file, bytes] of out) {
      const target = join(ROOT, "projects", id, file);
      if (verify) {
        const committed = await readFile(target).catch(() => null);
        const again = (await buildLogos(browser, id)).get(file);
        const checks = [
          [committed !== null, "exists"],
          [committed !== null && sha(committed) === sha(bytes), "matches a fresh build"],
          [sha(again) === sha(bytes), "deterministic"],
          [bytes.length <= BUDGETS[file], `size ${bytes.length} B (budget ${BUDGETS[file]})`],
        ];
        if (file.endsWith(".png")) {
          const png = decode(bytes);
          checks.push([png.width === OG.width && png.height === OG.height, `dimensions ${png.width}x${png.height}`]);
        } else {
          const text = bytes.toString("utf8");
          checks.push([/<title>/.test(text) && !/<(text|image|script|foreignObject|style)\b/i.test(text) && !/(?:href|src)\s*=/.test(text), "no text, images, scripts or external references"]);
        }
        for (const [ok, label] of checks) {
          if (!ok) failed += 1;
          console.log(`${ok ? "PASS" : "FAIL"}  ${id.padEnd(8)} ${file.padEnd(32)} ${label}`);
        }
      } else {
        await mkdir(dirname(target), { recursive: true });
        await writeFile(target, bytes);
        console.log(`${id}: ${file.padEnd(32)} ${String(bytes.length).padStart(7)} B`);
      }
    }
  } finally {
    await browser.close();
    await rm(join(ROOT, ".cache", "logos"), { recursive: true, force: true });
  }
  if (verify) {
    console.log(failed ? `\n${failed} check(s) failed` : "\nAll logo checks passed");
    process.exitCode = failed ? 1 : 0;
  }
}
