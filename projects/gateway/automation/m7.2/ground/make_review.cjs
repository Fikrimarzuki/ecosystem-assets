const fs = require('node:fs');
const path = require('node:path');
const sharp = require(path.resolve(__dirname, '../../../../app-gateway-fe/node_modules/sharp'));
async function main() {
  const captures = [['left-heel', 'Left heel, frame 9'], ['right-heel', 'Right heel, frame 23.75'], ['largest-knee', 'Largest knee adjustment, frame 23'], ['right-heel-boots', 'Right boot clearance, frame 23.75']];
  const layers = [];
  for (let row = 0; row < captures.length; row++) {
    for (let column = 0; column < 2; column++) {
      const version = column ? 'after' : 'before';
      const [name, label] = captures[row];
      layers.push({ input: fs.readFileSync(path.join(__dirname, `${version}-${name}.png`)), left: column * 448, top: row * 594 + 34 });
      const svg = `<svg width="448" height="34"><rect width="448" height="34" fill="#12202d"/><text x="12" y="23" fill="white" font-size="15">${version} / ${label}</text></svg>`;
      layers.push({ input: Buffer.from(svg), left: column * 448, top: row * 594 });
    }
  }
  await sharp({ create: { width: 896, height: 2376, channels: 4, background: '#12202d' } }).composite(layers).png().toFile(path.join(__dirname, 'ground-comparison.png'));
}
main().catch(error => { console.error(error); process.exitCode = 1; });
