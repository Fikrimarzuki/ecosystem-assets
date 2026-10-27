// Read-only screenshots of the current geometric bedroom and the M1.0f pilot preview.
// Usage: node shots.mjs <playwright-core index.mjs> <outDir> <baseURL>
const [, , pwPath, out, base] = process.argv;
const { chromium } = await import(pwPath);
const browser = await chromium.launch();
const shots = [];
async function shot(name, url, viewport, wait) {
  const page = await browser.newPage({ viewport });
  await page.goto(base + url, { waitUntil: "networkidle", timeout: 180_000 });
  await wait(page);
  await page.waitForTimeout(1200);
  await page.screenshot({ path: `${out}/${name}.png`, fullPage: false });
  shots.push(name);
  await page.close();
}
const canvas = async (page) => page.waitForSelector("canvas", { timeout: 120_000 });
const pilot = async (page) => page.getByRole("heading", { name: "Art pipeline pilot" }).waitFor({ timeout: 120_000 });
await shot("placeholder-bedroom-1280x800", "/dev/free-play", { width: 1280, height: 800 }, canvas);
await shot("m1.0f-pilot-1280x800", "/dev/art-pipeline-pilot", { width: 1280, height: 800 }, pilot);
await shot("m1.0f-pilot-390x844", "/dev/art-pipeline-pilot", { width: 390, height: 844 }, pilot);
await browser.close();
console.log(JSON.stringify(shots));
