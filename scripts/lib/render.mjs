// Renders SVG with Chromium (the reference renderer for web icons).
import { chromium } from "playwright-core";
import { decode, flattenDither } from "./png.mjs";

export async function openBrowser() {
  try { return await chromium.launch(); }
  catch (error) {
    throw new Error(`Could not start Chromium. playwright-core 1.64.0 expects its cached browser (run once: pnpm exec playwright-core install chromium-headless-shell). ${error.message.split("\n")[0]}`);
  }
}

const PAGE = body => `<!doctype html><meta charset="utf-8"><style>html,body{margin:0;padding:0;background:transparent}svg,img{display:block}</style>${body}`;

/** Render an SVG source to a decoded RGBA PNG at size x size.
 * glyphOnly: remove the #bg group so only the symbol remains (used for measurements). */
export async function renderSvg(browser, svgText, size, { glyphOnly = false } = {}) {
  const page = await browser.newPage({ viewport: { width: size, height: size }, deviceScaleFactor: 1 });
  try {
    if (glyphOnly) {
      await page.setContent(PAGE(svgText));
      await page.evaluate(n => {
        const svg = document.querySelector("svg");
        svg.setAttribute("width", n); svg.setAttribute("height", n);
        svg.querySelector("#bg")?.remove();
      }, size);
    } else {
      const uri = "data:image/svg+xml;base64," + Buffer.from(svgText).toString("base64");
      await page.setContent(PAGE(`<img alt="" width="${size}" height="${size}" src="${uri}">`));
      await page.evaluate(() => document.querySelector("img").decode());
    }
    const shot = await page.screenshot({ omitBackground: true, clip: { x: 0, y: 0, width: size, height: size }, type: "png" });
    const png = decode(shot);
    return glyphOnly ? png : flattenDither(png);
  } finally { await page.close(); }
}
