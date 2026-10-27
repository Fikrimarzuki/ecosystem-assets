// Deterministic PNG handling: decode the browser's screenshot and re-encode with fixed settings.
import { PNG } from "pngjs";

export const decode = buf => PNG.sync.read(buf);

/** Re-encode without metadata. Opaque output is written as RGB after confirming every alpha is 255. */
export function encode(png, { opaque = false } = {}) {
  if (opaque) {
    for (let i = 3; i < png.data.length; i += 4) if (png.data[i] !== 255) throw new Error("Expected an opaque image but found transparency");
    return PNG.sync.write(png, { colorType: 2, inputColorType: 6, inputHasAlpha: true, deflateLevel: 9 });
  }
  return PNG.sync.write(png, { colorType: 6, deflateLevel: 9 });
}

/** Chromium dithers gradients (+-1 level noise), which defeats PNG compression. Replace each fully opaque pixel
 * whose 9x9 neighbourhood is smooth (every channel within 5 levels, all opaque) by that neighbourhood's rounded
 * mean. Edges, antialiasing and transparent pixels are untouched. Deterministic; changes values by at most 2 levels. */
export function flattenDither(png, radius = 4, tolerance = 5) {
  const { width: w, height: h, data } = png, src = Buffer.from(data);
  for (let y = radius; y < h - radius; y++) for (let x = radius; x < w - radius; x++) {
    const o = (y * w + x) * 4;
    if (src[o + 3] !== 255) continue;
    const lo = [255, 255, 255], hi = [0, 0, 0], sum = [0, 0, 0];
    let smooth = true;
    for (let dy = -radius; dy <= radius && smooth; dy++) for (let dx = -radius; dx <= radius; dx++) {
      const q = ((y + dy) * w + x + dx) * 4;
      if (src[q + 3] !== 255) { smooth = false; break; }
      for (let c = 0; c < 3; c++) { const v = src[q + c]; if (v < lo[c]) lo[c] = v; if (v > hi[c]) hi[c] = v; sum[c] += v; }
    }
    if (!smooth || hi.some((v, c) => v - lo[c] > tolerance)) continue;
    const n = (2 * radius + 1) ** 2;
    for (let c = 0; c < 3; c++) data[o + c] = Math.round(sum[c] / n);
  }
  return png;
}

export const pixel = (png, x, y) => { const i = (png.width * y + x) * 4; return [png.data[i], png.data[i + 1], png.data[i + 2], png.data[i + 3]]; };

/** Alpha bounding box, centroid and the farthest opaque pixel from the centre. Coordinates are in image pixels. */
export function alphaStats(png, threshold = 128) {
  let minX = png.width, minY = png.height, maxX = -1, maxY = -1, sx = 0, sy = 0, n = 0, far = 0;
  const cx = png.width / 2, cy = png.height / 2;
  for (let y = 0; y < png.height; y++) for (let x = 0; x < png.width; x++) {
    if (png.data[(png.width * y + x) * 4 + 3] < threshold) continue;
    minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y);
    sx += x + 0.5; sy += y + 0.5; n++;
    far = Math.max(far, Math.hypot(x + 0.5 - cx, y + 0.5 - cy)); // pixel-centre distance; corners add ~0.7px
  }
  return n ? { empty: false, minX, minY, maxX: maxX + 1, maxY: maxY + 1, centroid: [sx / n, sy / n], farthest: far, pixels: n } : { empty: true };
}

/** 4-connected components of pixels with alpha >= threshold. */
export function componentCount(png, threshold = 128) {
  const { width: w, height: h } = png, seen = new Uint8Array(w * h);
  const on = i => png.data[i * 4 + 3] >= threshold;
  let count = 0;
  for (let s = 0; s < w * h; s++) {
    if (seen[s] || !on(s)) continue;
    count++; const stack = [s]; seen[s] = 1;
    while (stack.length) {
      const i = stack.pop(), x = i % w, y = (i / w) | 0;
      for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
        if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
        const j = ny * w + nx;
        if (!seen[j] && on(j)) { seen[j] = 1; stack.push(j); }
      }
    }
  }
  return count;
}

/** Number of separate runs of alpha >= threshold along one pixel row. */
export function runsOnRow(png, y, threshold = 128) {
  let runs = 0, inRun = false;
  for (let x = 0; x < png.width; x++) {
    const on = png.data[(png.width * y + x) * 4 + 3] >= threshold;
    if (on && !inRun) runs++;
    inRun = on;
  }
  return runs;
}

/** Number of separate runs of alpha >= threshold along one pixel column. */
export function runsOnColumn(png, x, threshold = 128) {
  let runs = 0, inRun = false;
  for (let y = 0; y < png.height; y++) {
    const on = png.data[(png.width * y + x) * 4 + 3] >= threshold;
    if (on && !inRun) runs++;
    inRun = on;
  }
  return runs;
}
