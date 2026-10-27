// M1.0j-C edge-quality analysis and optional non-destructive defringe.
// analyse(img): halo = semi-transparent pixel whose straight colour is lighter (luma + T)
//   than the darkest-luma opaque figure pixel within radius 2 — i.e. panel cream left in the edge.
// defringe(img): for halo pixels only, replace RGB with that opaque neighbour's RGB.
//   Alpha is never changed, opaque pixels are never touched, so silhouette and interior are identical.
const A = "/Users/mfm/code/porto-projects/app-momee/scripts/assets/";
const { blank } = await import(A + "png.mjs");
const luma = (d, o) => 0.2126 * d[o] + 0.7152 * d[o + 1] + 0.0722 * d[o + 2];

export function halos(img, { panel, D0 = 28, R = 2, darkGap = 70 } = {}) {
  // Halo = semi-transparent pixel whose straight colour is still close to the sheet's panel cream
  // while every opaque figure pixel within R is clearly darker (hair, outline, dark cloth).
  // Light figure parts (socks, shoe caps, skin highlights) therefore never count.
  const { width: W, height: H, data: D } = img;
  const pl = 0.2126 * panel[0] + 0.7152 * panel[1] + 0.0722 * panel[2];
  const out = [];
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const o = (y * W + x) * 4, a = D[o + 3];
    if (a === 0 || a === 255) continue;
    if (Math.max(...[0, 1, 2].map((k) => Math.abs(D[o + k] - panel[k]))) > D0) continue;
    let best = null, brightest = -1;
    for (let dy = -R; dy <= R; dy++) for (let dx = -R; dx <= R; dx++) {
      const nx = x + dx, ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
      const q = (ny * W + nx) * 4;
      if (D[q + 3] !== 255) continue;
      const l = luma(D, q);
      brightest = Math.max(brightest, l);
      if (!best || l < best.l) best = { l, q };
    }
    if (best && brightest < pl - darkGap) out.push({ o, x, y, a, src: best.q, excess: luma(D, o) - best.l });
  }
  return out;
}

export function defringe(img, opts) {
  const h = halos(img, opts);
  const outImg = { width: img.width, height: img.height, data: new Uint8Array(img.data) };
  for (const p of h) outImg.data.set(img.data.subarray(p.src, p.src + 3), p.o);
  return { image: outImg, fixed: h.length };
}

export function stats(img) {
  const { width: W, height: H, data: D } = img;
  let op = 0, pa = 0, cl = 0, bx = [W, H, -1, -1], bx128 = [W, H, -1, -1], edge = 0;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const a = D[(y * W + x) * 4 + 3];
    if (!a) { cl++; continue; }
    a === 255 ? op++ : pa++;
    bx = [Math.min(bx[0], x), Math.min(bx[1], y), Math.max(bx[2], x), Math.max(bx[3], y)];
    if (a >= 128) bx128 = [Math.min(bx128[0], x), Math.min(bx128[1], y), Math.max(bx128[2], x), Math.max(bx128[3], y)];
    if (!x || !y || x === W - 1 || y === H - 1) edge++;
  }
  return { width: W, height: H, opaque: op, partial: pa, clear: cl, bounds: bx, bounds128: bx128, edgeContact: edge };
}

// isolated components of non-zero alpha not 8-connected to the main figure
export function strays(img) {
  const { width: W, height: H, data: D } = img;
  const lab = new Int32Array(W * H).fill(-1);
  const comps = [];
  for (let i = 0; i < W * H; i++) {
    if (lab[i] >= 0 || !D[i * 4 + 3]) continue;
    const id = comps.length, m = [i];
    lab[i] = id;
    for (let k = 0; k < m.length; k++) {
      const j = m[k], x = j % W, y = (j - x) / W;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        const nx = x + dx, ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
        const n = ny * W + nx;
        if (lab[n] < 0 && D[n * 4 + 3]) { lab[n] = id; m.push(n); }
      }
    }
    let maxA = 0;
    for (const j of m) maxA = Math.max(maxA, D[j * 4 + 3]);
    comps.push({ size: m.length, maxAlpha: maxA, first: [m[0] % W, (m[0] - (m[0] % W)) / W], pixels: m });
  }
  comps.sort((a, b) => b.size - a.size);
  return { components: comps.length, main: comps[0]?.size ?? 0, others: comps.slice(1) };
}

export function strayReport(img) {
  const s = strays(img);
  return { strayComponents: s.others.length, strays: s.others.map(({ size, maxAlpha, first }) => ({ size, maxAlpha, first })) };
}

export function composite(img, bg) {
  const o = blank(img.width, img.height);
  for (let i = 0; i < img.data.length; i += 4) {
    const a = img.data[i + 3] / 255;
    for (let k = 0; k < 3; k++) o.data[i + k] = Math.round(img.data[i + k] * a + bg[k] * (1 - a));
    o.data[i + 3] = 255;
  }
  return o;
}

// Paper remnants: 8-connected clusters (≤ maxSize px) of panel-cream pixels (any alpha) that touch
// transparent background and whose non-cream figure neighbours (radius 2, alpha ≥ 200) are all dark.
export function paperSpecks(img, { panel, D0 = 28, maxSize = 40, darkGap = 70 } = {}) {
  const { width: W, height: H, data: D } = img;
  const pl = 0.2126 * panel[0] + 0.7152 * panel[1] + 0.0722 * panel[2];
  // "light remnant": panel cream, or very light low-saturation paper/ringing (luma ≥ panel − 60, channel spread ≤ 40)
  const cream = (i) => {
    if (!D[i * 4 + 3]) return false;
    const c = [D[i * 4], D[i * 4 + 1], D[i * 4 + 2]];
    if (Math.max(...[0, 1, 2].map((k) => Math.abs(c[k] - panel[k]))) <= D0) return true;
    return luma(D, i * 4) >= pl - 60 && Math.max(...c) - Math.min(...c) <= 40;
  };
  const seen = new Uint8Array(W * H), found = [];
  for (let i = 0; i < W * H; i++) {
    if (seen[i] || !cream(i)) continue;
    const m = [i]; seen[i] = 1;
    for (let k = 0; k < m.length; k++) {
      const j = m[k], x = j % W, y = (j - x) / W;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        const nx = x + dx, ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
        const n = ny * W + nx;
        if (!seen[n] && cream(n)) { seen[n] = 1; m.push(n); }
      }
    }
    if (m.length > maxSize) continue;
    let touchesBg = false, lightNeighbour = false, darkNeighbour = false;
    const inM = new Set(m);
    for (const j of m) {
      const x = j % W, y = (j - x) / W;
      for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {
        const nx = x + dx, ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
        const n = ny * W + nx;
        if (inM.has(n)) continue;
        const a = D[n * 4 + 3];
        if (a === 0 && Math.abs(dx) <= 1 && Math.abs(dy) <= 1) touchesBg = true;
        if (a >= 200 && !cream(n)) (luma(D, n * 4) < pl - darkGap ? (darkNeighbour = true) : (lightNeighbour = true));
      }
    }
    if (touchesBg && darkNeighbour && !lightNeighbour) {
      const x = m[0] % W;
      found.push({ pixels: m, size: m.length, at: [x, (m[0] - x) / W] });
    }
  }
  return found;
}

export function cleanup(img, opts) {
  const specks = paperSpecks(img, opts);
  const out = { width: img.width, height: img.height, data: new Uint8Array(img.data) };
  let removed = 0;
  for (const s of specks) for (const j of s.pixels) { out.data[j * 4 + 3] = 0; out.data.fill(0, j * 4, j * 4 + 3); removed++; }
  // detached strays: components (8-connected, alpha > 0) of ≤ 10 px not connected to the figure,
  // detected AFTER speck removal (removing a speck can isolate faint edge pixels)
  for (const c of strays(out).others) if (c.size <= 10) for (const j of c.pixels) { out.data.fill(0, j * 4, j * 4 + 4); removed++; }
  const h = halos(out, opts);           // re-measured after speck removal
  for (const p of h) out.data.set(out.data.subarray(p.src, p.src + 3), p.o);
  return { image: out, specks: specks.map(({ size, at }) => ({ size, at })), removedPixels: removed, recoloured: h.length };
}
