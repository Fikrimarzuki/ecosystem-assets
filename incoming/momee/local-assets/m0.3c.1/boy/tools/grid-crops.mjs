// Review helper: gridded, enlarged crops of the candidate (no edits to the source).
import { readPng, writePng, blank } from "./png.mjs";

const [, , src, outDir] = process.argv;
const img = readPng(src);

function crop(name, x0, y0, w, h, scale, step) {
  const out = blank(w * scale, h * scale);
  for (let y = 0; y < h * scale; y++) {
    for (let x = 0; x < w * scale; x++) {
      const sx = x0 + Math.floor(x / scale), sy = y0 + Math.floor(y / scale);
      const si = (sy * img.width + sx) * 4, oi = (y * out.width + x) * 4;
      let r = img.data[si], g = img.data[si + 1], b = img.data[si + 2];
      const gx = (sx % step === 0), gy = (sy % step === 0);
      if ((gx && x % scale === 0) || (gy && y % scale === 0)) {
        const major = (gx && sx % (step * 5) === 0) || (gy && sy % (step * 5) === 0);
        r = major ? 255 : 255; g = major ? 0 : 60; b = major ? 255 : 60;
      }
      out.data[oi] = r; out.data[oi + 1] = g; out.data[oi + 2] = b; out.data[oi + 3] = 255;
    }
  }
  writePng(`${outDir}/grid-${name}.png`, out);
}

crop("face", 480, 180, 360, 340, 2, 10);   // eyes, brows, mouth, blush, ear
crop("head", 320, 20, 560, 540, 1, 20);    // hair, head outline, nape
crop("torso", 380, 480, 500, 440, 1, 20);  // neck, shirt, arms, hands
crop("legs", 440, 880, 440, 340, 1, 20);   // shorts, legs, socks, shoes
console.log("ok");
