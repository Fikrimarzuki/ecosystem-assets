// Review helper: same crop from several images, side by side.
// Usage: node tools/sheet.mjs <out.png> '<json [x,y,w,h]>' <scale> <img1> <img2> ...
import { readPng, writePng, blank } from "./png.mjs";

const [, , out, boxJson, scaleArg, ...srcs] = process.argv;
const [x0, y0, w, h] = JSON.parse(boxJson);
const s = Number(scaleArg);
const cw = Math.round(w * s), ch = Math.round(h * s), gap = 6;
const sheet = blank(srcs.length * (cw + gap) + gap, ch + gap * 2);
sheet.data.fill(255);
srcs.forEach((src, n) => {
  const img = readPng(src);
  for (let y = 0; y < ch; y++) for (let x = 0; x < cw; x++) {
    const si = ((y0 + Math.floor(y / s)) * img.width + x0 + Math.floor(x / s)) * 4;
    const oi = ((gap + y) * sheet.width + gap + n * (cw + gap) + x) * 4;
    sheet.data.set(img.data.subarray(si, si + 4), oi);
  }
});
writePng(out, sheet);
