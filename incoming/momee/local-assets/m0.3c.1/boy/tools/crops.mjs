// Review helper: enlarged crops of a rendered check image into one contact sheet.
// Usage: node tools/crops.mjs <src.png> <out.png> '<json [[x,y,w,h],...]>' <scale>
import { readPng, writePng, blank } from "./png.mjs";

const [, , src, out, boxesJson, scaleArg] = process.argv;
const img = readPng(src);
const boxes = JSON.parse(boxesJson);
const s = Number(scaleArg || 3);
const gap = 8;
const width = boxes.reduce((t, [, , w]) => t + w * s + gap, gap);
const height = Math.max(...boxes.map(([, , , h]) => h * s)) + gap * 2;
const sheet = blank(width, height);
sheet.data.fill(255);
let ox = gap;
for (const [x0, y0, w, h] of boxes) {
  for (let y = 0; y < h * s; y++) for (let x = 0; x < w * s; x++) {
    const si = ((y0 + Math.floor(y / s)) * img.width + x0 + Math.floor(x / s)) * 4;
    const oi = ((gap + y) * width + ox + x) * 4;
    sheet.data[oi] = img.data[si]; sheet.data[oi + 1] = img.data[si + 1]; sheet.data[oi + 2] = img.data[si + 2]; sheet.data[oi + 3] = 255;
  }
  ox += w * s + gap;
}
writePng(out, sheet);
