// Review helper: print RGB/HSV along short line segments of the candidate.
import { readPng } from "./png.mjs";

const img = readPng(process.argv[2]);
const hsv = (r, g, b) => {
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  let h = 0;
  if (d) h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return [Math.round(((h * 60) + 360) % 360), mx ? +(d / mx).toFixed(2) : 0, +(mx / 255).toFixed(2)];
};
const lines = JSON.parse(process.argv[3]);
for (const [name, x0, y0, x1, y1, step] of lines) {
  console.log(`-- ${name}`);
  const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0));
  for (let i = 0; i <= n; i += step) {
    const x = Math.round(x0 + ((x1 - x0) * i) / n), y = Math.round(y0 + ((y1 - y0) * i) / n);
    const o = (y * img.width + x) * 4, [r, g, b] = img.data.slice(o, o + 3);
    console.log(`(${x},${y}) #${[r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("")} hsv ${hsv(r, g, b).join(" ")}`);
  }
}
