// M1.0k-A3 edge QC (spec §8.6) with the unchanged M1.0j-C edges.mjs. The candidate never sat on a cream panel, so the
// halo / speck "panel" colour is (a) the generator glow colour measured from the original (straight RGB of alpha 1–4 pixels)
// and (b) pure white as a conservative light-fringe probe.
// Usage: node edgeqc_k3.mjs <original.png> <image.png>...
const A = '/Users/mfm/code/porto-projects/app-momee/scripts/assets/';
const { readPng } = await import(A + 'png.mjs');
const E = await import('/Users/mfm/code/porto-projects/ecosystem-assets/projects/momee/candidates/m1.0j-c-construction/edges.mjs');
const [, , orig, ...files] = process.argv;
const o = readPng(orig), s = [0, 0, 0]; let n = 0;
for (let i = 0; i < o.data.length; i += 4) { const a = o.data[i + 3]; if (a >= 1 && a <= 4) { for (let k = 0; k < 3; k++) s[k] += o.data[i + k]; n++; } }
const glow = s.map((v) => Math.round(v / n));
console.log(JSON.stringify({ glowColour: glow, glowPixels: n }));
for (const f of files) {
  const im = readPng(f), st = E.strays(im);
  const r = { file: f.split('/').pop(), strayComponents: st.components - 1 };
  for (const [name, panel] of [['glow', glow], ['white', [255, 255, 255]]]) { r[`halos_${name}`] = E.halos(im, { panel }).length; r[`specks_${name}`] = E.paperSpecks(im, { panel }).length; }
  console.log(JSON.stringify(r));
}
