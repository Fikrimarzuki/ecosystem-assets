// Existing local Sharp only; no installations or source-asset writes.
const fs = require('node:fs');
const path = require('node:path');
const sharp = require(path.resolve(__dirname, '../../../../app-gateway-fe/node_modules/sharp'));

async function main() {
  const rows = [['idle', 56, 'front'], ['idle', 56, 'back'], ['walk', 12, 'front'], ['walk', 12, 'back']];
  const versions = ['approved-source', 'four-influence', 'roundtrip'];
  const layers = [];
  for (let row = 0; row < rows.length; row++) {
    const [clip, frame, view] = rows[row];
    for (let column = 0; column < versions.length; column++) {
      const version = versions[column];
      layers.push({ input: fs.readFileSync(path.join(__dirname, `${version}-${clip}-${frame}-${view}.png`)), left: column * 384, top: row * 514 + 34 });
      const title = `<svg width="384" height="34"><rect width="384" height="34" fill="#12202d"/><text x="12" y="23" fill="white" font-size="15">${version} / ${clip} ${frame} / ${view}</text></svg>`;
      layers.push({ input: Buffer.from(title), left: column * 384, top: row * 514 });
    }
  }
  await sharp({ create: { width: 1152, height: 2056, channels: 4, background: '#12202d' } }).composite(layers).png().toFile(path.join(__dirname, 'export-comparison.png'));
}
async function closeups() {
  const layers = [];
  for (let row = 0; row < 2; row++) {
    const clip = row ? 'walk' : 'idle';
    for (let column = 0; column < 2; column++) {
      const version = column ? 'candidate' : 'approved-source';
      layers.push({ input: fs.readFileSync(path.join(__dirname, `closeup-${version}-${clip}.png`)), left: column * 512, top: row * 546 + 34 });
      const title = `<svg width="512" height="34"><rect width="512" height="34" fill="#12202d"/><text x="12" y="23" fill="white" font-size="16">${version} / ${row ? 'Walk wrist, frame 12' : 'Idle neck, frame 56'}</text></svg>`;
      layers.push({ input: Buffer.from(title), left: column * 512, top: row * 546 });
    }
  }
  await sharp({ create: { width: 1024, height: 1092, channels: 4, background: '#12202d' } }).composite(layers).png().toFile(path.join(__dirname, 'skinning-closeups.png'));
}
(process.argv.includes('--closeups') ? closeups() : main()).catch(error => { console.error(error); process.exitCode = 1; });
