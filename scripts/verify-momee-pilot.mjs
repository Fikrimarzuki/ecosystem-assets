import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { inflateSync } from 'node:zlib';

const root = resolve(import.meta.dirname, '..');
const manifest = JSON.parse(readFileSync(resolve(root, 'projects/momee/manifest.json')));
const pilotIds = new Set([
  'prop.bedroom.pillow.unmade',
  'prop.bedroom.pillow.made',
  'decoration.morning-flower',
]);

function inspectPng(path, expectedWidth, expectedHeight) {
  const bytes = readFileSync(resolve(root, path));
  if (bytes.subarray(0, 8).toString('hex') !== '89504e470d0a1a0a')
    throw new Error(`${path}: invalid PNG signature`);
  let offset = 8;
  let width = 0;
  let height = 0;
  const idat = [];
  while (offset + 12 <= bytes.length) {
    const length = bytes.readUInt32BE(offset);
    const type = bytes.toString('ascii', offset + 4, offset + 8);
    const data = bytes.subarray(offset + 8, offset + 8 + length);
    if (type === 'IHDR') {
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
      if (data[8] !== 8 || data[9] !== 6 || data[12] !== 0)
        throw new Error(`${path}: expected noninterlaced RGBA8 PNG`);
    }
    if (type === 'IDAT') idat.push(data);
    offset += length + 12;
    if (type === 'IEND') break;
  }
  if (width !== expectedWidth || height !== expectedHeight)
    throw new Error(`${path}: dimension mismatch`);
  const pixels = inflateSync(Buffer.concat(idat));
  const stride = width * 4;
  if (pixels.length !== height * (stride + 1))
    throw new Error(`${path}: invalid pixel data length`);
  let prior = Buffer.alloc(stride);
  let opaque = 0;
  let clear = 0;
  let partial = 0;
  let bounds = [width, height, -1, -1];
  for (let y = 0; y < height; y++) {
    const start = y * (stride + 1);
    const filter = pixels[start];
    const row = Buffer.from(pixels.subarray(start + 1, start + 1 + stride));
    for (let i = 0; i < stride; i++) {
      const left = i >= 4 ? row[i - 4] : 0;
      const up = prior[i];
      const upperLeft = i >= 4 ? prior[i - 4] : 0;
      let predictor = 0;
      if (filter === 1) predictor = left;
      else if (filter === 2) predictor = up;
      else if (filter === 3) predictor = Math.floor((left + up) / 2);
      else if (filter === 4) {
        const p = left + up - upperLeft;
        const distances = [Math.abs(p - left), Math.abs(p - up), Math.abs(p - upperLeft)];
        predictor = distances[0] <= distances[1] && distances[0] <= distances[2]
          ? left : distances[1] <= distances[2] ? up : upperLeft;
      } else if (filter !== 0) throw new Error(`${path}: unknown PNG filter ${filter}`);
      row[i] = (row[i] + predictor) & 255;
    }
    for (let x = 0; x < width; x++) {
      const alpha = row[x * 4 + 3];
      if (alpha === 0) clear++;
      else {
        if (alpha === 255) opaque++;
        else partial++;
        bounds = [Math.min(bounds[0], x), Math.min(bounds[1], y),
          Math.max(bounds[2], x), Math.max(bounds[3], y)];
        if (x === 0 || y === 0 || x === width - 1 || y === height - 1)
          throw new Error(`${path}: artwork touches the canvas edge`);
      }
    }
    prior = row;
  }
  if (!opaque || !clear || !partial) throw new Error(`${path}: expected opaque, clear and antialiased pixels`);
  return { width, height, bounds, opaque, clear, partial };
}

const pilot = manifest.assets.filter((asset) => pilotIds.has(asset.id));
if (pilot.length !== pilotIds.size || pilot.some((asset) => asset.status !== 'Candidate'))
  throw new Error('M1.0f: three Candidate manifest entries are required');
let count = 0;
for (const asset of pilot) {
  for (const item of asset.exports.filter((entry) => entry.format === 'png')) {
    const result = inspectPng(item.path, item.width, item.height);
    console.log(`${item.path}: ${result.width}x${result.height}, alpha bounds ${result.bounds.join(',')}`);
    count++;
  }
}
if (count !== 5) throw new Error(`M1.0f: expected five PNG exports, found ${count}`);
console.log('M1.0f PNG dimensions, alpha and clear canvas edges verified.');
