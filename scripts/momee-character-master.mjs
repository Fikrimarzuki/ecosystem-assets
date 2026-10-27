// Momee character-master intake (M1.0k-A). Two commands, Node standard library only:
//
//   place <figure.png> --char mom|boy --out <master.png> [--ppu 4]
//       Puts an already background-keyed full figure (e.g. from
//       projects/momee/candidates/m1.0j-construction/extract2.mjs) on the spec canvas
//       (character-master-spec.md §2) by one uniform premultiplied area-average DOWNscale,
//       aligning the soles to the anchor row and the feet centre to the anchor x.
//       Refuses to enlarge: resampling a smaller image never makes a master.
//
//   check <master.png> --char mom|boy [--ppu 4] [--chin-y N] [--reference <tier1x.png>]
//       Validates a candidate master against the spec and the accepted extraction.
//       Exit 1 on any FAIL; advisory metrics print as INFO.
import { readFileSync, writeFileSync } from 'node:fs';
import { inflateSync, deflateSync } from 'node:zlib';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
export const SPEC = {
  boy: { heightU: 200, canvasU: [160, 224], anchorU: [80, 216], heads: [2.4, 2.6],
    reference: 'projects/momee/exports/characters/boy/boy-three-quarter-accepted-clean.v1.@1x.png', facing: 'right', acceptedPpu: 514 / 200 },
  mom: { heightU: 290, canvasU: [200, 312], anchorU: [100, 304], heads: [3.2, 3.5],
    reference: 'projects/momee/exports/characters/mom/mom-three-quarter-accepted-clean.v1.@1x.png', facing: 'left', acceptedPpu: 514 / 290 },
};

// ---- minimal PNG I/O (8-bit RGB/RGBA, non-interlaced) --------------------------------------
const CRC = new Int32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c; });
const crc32 = (b) => { let c = -1; for (const x of b) c = CRC[(c ^ x) & 255] ^ (c >>> 8); return (c ^ -1) >>> 0; };
export function readPng(path) {
  const b = readFileSync(path);
  if (b.subarray(0, 8).toString('hex') !== '89504e470d0a1a0a') throw new Error(`${path}: not a PNG`);
  let o = 8, ihdr, idat = [], chunks = [];
  while (o < b.length) {
    const len = b.readUInt32BE(o), type = b.toString('ascii', o + 4, o + 8), d = b.subarray(o + 8, o + 8 + len);
    chunks.push(type);
    if (type === 'IHDR') ihdr = { w: d.readUInt32BE(0), h: d.readUInt32BE(4), depth: d[8], ct: d[9], il: d[12] };
    if (type === 'IDAT') idat.push(d);
    o += 12 + len;
    if (type === 'IEND') break;
  }
  if (ihdr.depth !== 8 || ![2, 6].includes(ihdr.ct) || ihdr.il !== 0) throw new Error(`${path}: need 8-bit RGB/RGBA non-interlaced`);
  const ch = ihdr.ct === 6 ? 4 : 3, st = ihdr.w * ch, raw = inflateSync(Buffer.concat(idat));
  const data = new Uint8Array(ihdr.w * ihdr.h * 4);
  let prior = new Uint8Array(st);
  for (let y = 0; y < ihdr.h; y++) {
    const f = raw[y * (st + 1)], row = Uint8Array.from(raw.subarray(y * (st + 1) + 1, (y + 1) * (st + 1)));
    for (let i = 0; i < st; i++) {
      const a = i >= ch ? row[i - ch] : 0, u = prior[i], c = i >= ch ? prior[i - ch] : 0;
      const p = f === 1 ? a : f === 2 ? u : f === 3 ? (a + u) >> 1 : f === 4 ? (() => { const q = a + u - c, pa = Math.abs(q - a), pb = Math.abs(q - u), pc = Math.abs(q - c); return pa <= pb && pa <= pc ? a : pb <= pc ? u : c; })() : 0;
      row[i] = (row[i] + p) & 255;
    }
    for (let x = 0; x < ihdr.w; x++) for (let k = 0; k < 4; k++) data[(y * ihdr.w + x) * 4 + k] = k < ch ? row[x * ch + k] : 255;
    prior = row;
  }
  return { width: ihdr.w, height: ihdr.h, data, hasAlpha: ihdr.ct === 6, chunks };
}
export function writePng(path, { width, height, data }) {
  const raw = Buffer.alloc(height * (width * 4 + 1));
  for (let y = 0; y < height; y++) Buffer.from(data.buffer, data.byteOffset + y * width * 4, width * 4).copy(raw, y * (width * 4 + 1) + 1);
  const chunk = (t, d) => { const h = Buffer.alloc(8); h.writeUInt32BE(d.length); h.write(t, 4, 'ascii'); const c = Buffer.alloc(4); c.writeUInt32BE(crc32(Buffer.concat([Buffer.from(t, 'ascii'), d]))); return Buffer.concat([h, d, c]); };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(width); ihdr.writeUInt32BE(height, 4); ihdr.set([8, 6, 0, 0, 0], 8);
  writeFileSync(path, Buffer.concat([Buffer.from('89504e470d0a1a0a', 'hex'), chunk('IHDR', ihdr), chunk('IDAT', deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]));
}

// ---- geometry --------------------------------------------------------------------------------
export function figureBox(img, t = 1) {
  let b = [img.width, img.height, -1, -1];
  for (let y = 0; y < img.height; y++) for (let x = 0; x < img.width; x++)
    if (img.data[(y * img.width + x) * 4 + 3] >= t) b = [Math.min(b[0], x), Math.min(b[1], y), Math.max(b[2], x), Math.max(b[3], y)];
  return b;
}
export function feetX(img, box) {
  let sx = 0, n = 0;
  for (let y = box[3] - Math.round((box[3] - box[1]) * 0.03); y <= box[3]; y++)
    for (let x = 0; x < img.width; x++) if (img.data[(y * img.width + x) * 4 + 3] > 128) { sx += x; n++; }
  return n ? sx / n : NaN;
}
// uniform premultiplied area-average; source point (sax, saySole) → destination (tx, ty), scale s ≤ 1
export function resample(src, W, H, [sax, say], [tx, ty], s) {
  if (s > 1 + 1e-9) throw new Error(`refusing to enlarge (×${s.toFixed(3)}): a master needs genuinely high-resolution artwork`);
  const out = { width: W, height: H, data: new Uint8Array(W * H * 4) };
  for (let y = 0; y < H; y++) {
    const y0 = (y - ty) / s + say, y1 = (y + 1 - ty) / s + say;
    if (y1 <= 0 || y0 >= src.height) continue;
    for (let x = 0; x < W; x++) {
      const x0 = (x - tx) / s + sax, x1 = (x + 1 - tx) / s + sax;
      if (x1 <= 0 || x0 >= src.width) continue;
      let r = 0, g = 0, b = 0, a = 0;
      for (let yy = Math.max(0, Math.floor(y0)); yy < Math.min(src.height, Math.ceil(y1)); yy++) {
        const wy = Math.min(yy + 1, y1) - Math.max(yy, y0);
        for (let xx = Math.max(0, Math.floor(x0)); xx < Math.min(src.width, Math.ceil(x1)); xx++) {
          const w = wy * (Math.min(xx + 1, x1) - Math.max(xx, x0)), o = (yy * src.width + xx) * 4, pa = src.data[o + 3] / 255;
          r += src.data[o] * pa * w; g += src.data[o + 1] * pa * w; b += src.data[o + 2] * pa * w; a += pa * w;
        }
      }
      const o = (y * W + x) * 4;
      if (a > 0) out.data.set([Math.round(r / a), Math.round(g / a), Math.round(b / a)], o);
      out.data[o + 3] = Math.round(Math.min(1, a / ((x1 - x0) * (y1 - y0))) * 255);
    }
  }
  return out;
}

export function place(fig, who, ppu = 4) {
  const S = SPEC[who], box = figureBox(fig), figH = box[3] - box[1] + 1;
  const s = (S.heightU * ppu) / figH;
  // source: soles' bottom edge (box[3] + 1) and feet centre → destination: anchor row top edge and anchor x
  const out = resample(fig, S.canvasU[0] * ppu, S.canvasU[1] * ppu, [feetX(fig, box) + 0.5, box[3] + 1], [S.anchorU[0] * ppu, S.anchorU[1] * ppu], s);
  return { image: out, scale: s, figureHeightPx: figH };
}

// ---- checks --------------------------------------------------------------------------------
function iou(a, b) {
  let i = 0, u = 0;
  for (let k = 3; k < a.data.length; k += 4) { const p = a.data[k] >= 128, q = b.data[k] >= 128; if (p && q) i++; if (p || q) u++; }
  return u ? i / u : 0;
}
const mirror = (img) => { const o = { width: img.width, height: img.height, data: new Uint8Array(img.data.length) }; for (let y = 0; y < img.height; y++) for (let x = 0; x < img.width; x++) o.data.set(img.data.subarray((y * img.width + x) * 4, (y * img.width + x) * 4 + 4), (y * img.width + img.width - 1 - x) * 4); return o; };
function lab([r, g, b]) {
  const f = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  const [R, G, B] = [f(r), f(g), f(b)];
  const X = (0.4124 * R + 0.3576 * G + 0.1805 * B) / 0.95047, Y = 0.2126 * R + 0.7152 * G + 0.0722 * B, Z = (0.0193 * R + 0.1192 * G + 0.9505 * B) / 1.08883;
  const h = (t) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
  return [116 * h(Y) - 16, 500 * (h(X) - h(Y)), 200 * (h(Y) - h(Z))];
}
function dE00([L1, a1, b1], [L2, a2, b2]) { // CIEDE2000
  const rad = Math.PI / 180, C1 = Math.hypot(a1, b1), C2 = Math.hypot(a2, b2), Cm = (C1 + C2) / 2;
  const G = 0.5 * (1 - Math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7))), a1p = (1 + G) * a1, a2p = (1 + G) * a2;
  const C1p = Math.hypot(a1p, b1), C2p = Math.hypot(a2p, b2);
  const h = (b, a) => { const v = Math.atan2(b, a) / rad; return v < 0 ? v + 360 : v; };
  const h1 = h(b1, a1p), h2 = h(b2, a2p), dL = L2 - L1, dC = C2p - C1p;
  let dh = C1p * C2p === 0 ? 0 : h2 - h1; if (dh > 180) dh -= 360; if (dh < -180) dh += 360;
  const dH = 2 * Math.sqrt(C1p * C2p) * Math.sin((dh / 2) * rad), Lm = (L1 + L2) / 2, Cmp = (C1p + C2p) / 2;
  let hm = h1 + h2; if (C1p * C2p !== 0) hm = Math.abs(h1 - h2) > 180 ? (hm + 360) / 2 : hm / 2;
  const T = 1 - 0.17 * Math.cos((hm - 30) * rad) + 0.24 * Math.cos(2 * hm * rad) + 0.32 * Math.cos((3 * hm + 6) * rad) - 0.2 * Math.cos((4 * hm - 63) * rad);
  const SL = 1 + (0.015 * (Lm - 50) ** 2) / Math.sqrt(20 + (Lm - 50) ** 2), SC = 1 + 0.045 * Cmp, SH = 1 + 0.015 * Cmp * T;
  const RT = -2 * Math.sqrt(Cmp ** 7 / (Cmp ** 7 + 25 ** 7)) * Math.sin(60 * Math.exp(-(((hm - 275) / 25) ** 2)) * rad);
  return Math.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 + RT * (dC / SC) * (dH / SH));
}
function bandColours(img, box, n = 10) {
  const out = [];
  for (let k = 0; k < n; k++) {
    const y0 = Math.round(box[1] + ((box[3] - box[1] + 1) * k) / n), y1 = Math.round(box[1] + ((box[3] - box[1] + 1) * (k + 1)) / n);
    let s = [0, 0, 0], c = 0;
    for (let y = y0; y < y1; y++) for (let x = 0; x < img.width; x++) { const o = (y * img.width + x) * 4; if (img.data[o + 3] === 255) { s[0] += img.data[o]; s[1] += img.data[o + 1]; s[2] += img.data[o + 2]; c++; } }
    out.push(c ? s.map((v) => v / c) : null);
  }
  return out;
}
function strays(img) {
  const W = img.width, H = img.height, lab_ = new Int32Array(W * H).fill(-1), sizes = [];
  for (let i = 0; i < W * H; i++) {
    if (lab_[i] >= 0 || !img.data[i * 4 + 3]) continue;
    const id = sizes.length, m = [i]; lab_[i] = id;
    for (let k = 0; k < m.length; k++) { const j = m[k], x = j % W, y = (j - x) / W; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const nx = x + dx, ny = y + dy; if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue; const q = ny * W + nx; if (lab_[q] < 0 && img.data[q * 4 + 3]) { lab_[q] = id; m.push(q); } } }
    sizes.push(m.length);
  }
  return sizes.sort((a, b) => b - a).slice(1);
}

export function check(img, who, { ppu = 4, chinY = null, reference = null } = {}) {
  const S = SPEC[who], R = [];
  const add = (level, name, detail) => R.push({ level, name, detail });
  const [W, H] = [S.canvasU[0] * ppu, S.canvasU[1] * ppu];
  add(img.width === W && img.height === H ? 'PASS' : 'FAIL', 'canvas', `${img.width}×${img.height} (spec ${W}×${H})`);
  add(img.hasAlpha ? 'PASS' : 'FAIL', 'alpha channel', img.hasAlpha ? 'RGBA' : 'RGB: no transparency');
  let edge = 0, clear = 0, partial = 0;
  for (let y = 0; y < img.height; y++) for (let x = 0; x < img.width; x++) {
    const a = img.data[(y * img.width + x) * 4 + 3];
    if (!a) clear++; else if (a < 255) partial++;
    if (a && (x < 2 || y < 2 || x >= img.width - 2 || y >= img.height - 2)) edge++;
  }
  add(clear > img.width * img.height * 0.2 ? 'PASS' : 'FAIL', 'transparent background', `${(100 * clear / (img.width * img.height)).toFixed(1)}% clear`);
  add(partial > 0 ? 'PASS' : 'FAIL', 'anti-aliased edges', `${partial} partial-alpha pixels`);
  add(edge === 0 ? 'PASS' : 'FAIL', 'nothing cropped at the canvas edge', `${edge} pixels within 2 px of the border`);
  const box = figureBox(img), h = box[3] - box[1] + 1, target = S.heightU * ppu;
  add(Math.abs(h - target) <= Math.max(2, target * 0.01) ? 'PASS' : 'FAIL', 'figure height', `${h} px (spec ${target} ±1%)`);
  const sole = S.anchorU[1] * ppu - 1;
  add(Math.abs(box[3] - sole) <= Math.max(1, ppu / 2) ? 'PASS' : 'FAIL', 'soles on the ground line', `sole row ${box[3]} (spec ${sole})`);
  const fx = feetX(img, box), ax = S.anchorU[0] * ppu;
  add(Math.abs(fx + 0.5 - ax) <= 4 * ppu ? 'PASS' : 'FAIL', 'feet centred on the anchor', `feet centre x ${(fx + 0.5).toFixed(1)} (spec ${ax} ±${4 * ppu})`);
  const st = strays(img);
  add(st.length === 0 ? 'PASS' : 'FAIL', 'no detached stray pixels', st.length ? `${st.length} components (largest ${st[0]} px)` : '0');
  // baked ground shadow: low-saturation, partially transparent, darkish pixels in the bottom 2 % band
  let shadowish = 0, band = 0;
  for (let y = Math.round(box[3] - h * 0.02); y <= box[3]; y++) for (let x = 0; x < img.width; x++) {
    const o = (y * img.width + x) * 4, a = img.data[o + 3]; if (!a) continue; band++;
    const c = [img.data[o], img.data[o + 1], img.data[o + 2]];
    if (a < 200 && Math.max(...c) - Math.min(...c) < 30 && Math.max(...c) < 200) shadowish++;
  }
  add(band && shadowish / band > 0.15 ? 'FAIL' : 'PASS', 'no baked floor shadow', `${shadowish} of ${band} bottom-band pixels look like a soft grey shadow`);
  if (chinY != null) {
    const heads = h / (chinY - box[1]);
    add(heads >= S.heads[0] && heads <= S.heads[1] ? 'PASS' : 'FAIL', 'head proportion', `${heads.toFixed(2)} heads (spec ${S.heads.join('–')})`);
  } else add('INFO', 'head proportion', 'pass --chin-y <row> (landmark read by eye) to check');
  // comparison with the accepted extraction at 1 px/u
  const ref = readPng(resolve(root, reference ?? S.reference));
  const at1 = ppu === 1 ? img : resample(img, S.canvasU[0], S.canvasU[1], [0, 0], [0, 0], 1 / ppu);
  const same = iou(at1, ref), flipped = iou(mirror(at1), ref);
  add(same >= flipped ? 'PASS' : 'FAIL', `facing (${S.facing}, as accepted)`, `IoU as drawn ${same.toFixed(3)} vs mirrored ${flipped.toFixed(3)}`);
  add(same >= 0.9 ? 'PASS' : 'INFO', 'silhouette agreement with accepted pose', `IoU ${same.toFixed(3)} (spec ≥ 0.90 for the same pose; a different pose needs owner judgement)`);
  const ca = bandColours(at1, figureBox(at1)), cb = bandColours(ref, figureBox(ref));
  const d = ca.map((c, i) => (c && cb[i] ? dE00(lab(c), lab(cb[i])) : null)).filter((v) => v != null);
  add(Math.max(...d) <= 5 ? 'PASS' : 'INFO', 'palette (10 height bands, CIEDE2000)', `max ΔE00 ${Math.max(...d).toFixed(1)}, mean ${(d.reduce((p, q) => p + q, 0) / d.length).toFixed(1)} (spec ≤ 5)`);
  if (ppu <= S.acceptedPpu) add('INFO', 'detail beyond the accepted extraction', `not applicable at ${ppu} px/u (accepted extraction is ${S.acceptedPpu.toFixed(2)} px/u)`);
  else {
    // genuine detail: energy lost when the master is reduced to the accepted extraction's density and restored
    const refPpu = S.acceptedPpu;
    const small = resample(img, Math.round(W * refPpu / ppu), Math.round(H * refPpu / ppu), [0, 0], [0, 0], refPpu / ppu);
    let sum = 0, n = 0;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const o = (y * W + x) * 4; if (img.data[o + 3] < 255) continue;
      const sx = Math.min(small.width - 1, Math.floor((x + 0.5) * refPpu / ppu)), sy = Math.min(small.height - 1, Math.floor((y + 0.5) * refPpu / ppu)), q = (sy * small.width + sx) * 4;
      for (let k = 0; k < 3; k++) sum += Math.abs(img.data[o + k] - small.data[q + k]);
      n += 3;
    }
    add('INFO', 'detail beyond the accepted extraction', `mean residual ${(sum / n).toFixed(2)} levels after reduction to ${refPpu.toFixed(2)} px/u (an enlarged cutout scores near its interpolation floor; compare with the recorded baseline)`);
  }
  return R;
}

// ---- CLI -----------------------------------------------------------------------------------
if (import.meta.url === `file://${process.argv[1]}`) {
  const [cmd, file, ...rest] = process.argv.slice(2);
  const opt = (k, d) => { const i = rest.indexOf(`--${k}`); return i >= 0 ? rest[i + 1] : d; };
  const who = opt('char'), ppu = Number(opt('ppu', 4));
  if (!SPEC[who] || !file || !['place', 'check'].includes(cmd)) {
    console.error('usage: place <figure.png> --char mom|boy --out <png> [--ppu 4] | check <png> --char mom|boy [--ppu 4] [--chin-y N] [--reference <png>]');
    process.exit(2);
  }
  if (cmd === 'place') {
    let r;
    try { r = place(readPng(file), who, ppu); } catch (e) { console.error(`REFUSED  ${e.message}`); process.exit(1); }
    writePng(opt('out'), r.image);
    console.log(`placed: figure ${r.figureHeightPx} px → ${SPEC[who].heightU * ppu} px (×${r.scale.toFixed(4)})`);
  } else {
    const r = check(readPng(file), who, { ppu, chinY: opt('chin-y') != null ? Number(opt('chin-y')) : null, reference: opt('reference') });
    for (const x of r) console.log(`${x.level.padEnd(4)}  ${x.name}: ${x.detail}`);
    if (r.some((x) => x.level === 'FAIL')) process.exitCode = 1;
  }
}
