const A = "/Users/mfm/code/porto-projects/app-momee/scripts/assets/";
const { readPng } = await import(A + "png.mjs");
const E = await import(process.argv[2] + "/edges.mjs");
const files = process.argv.slice(3);
const panelOf = (f) => (f.includes('/boy') || f.includes('boy-') ? [251, 247, 234] : [254, 251, 243]);
for (const f of files) {
  const im = readPng(f);
  const s = E.stats(im), h = E.halos(im, { panel: panelOf(f) }), st = E.strays(im);
  const byBand = { top30: 0, mid: 0, feet10: 0 };
  const [, y0, , y1] = s.bounds;
  for (const p of h) { const t = (p.y - y0) / (y1 - y0); t < 0.3 ? byBand.top30++ : t > 0.9 ? byBand.feet10++ : byBand.mid++; }
  console.log(JSON.stringify({ file: f.split("/").slice(-1)[0], ...s, halos: h.length, halosByBand: byBand,
    maxHaloExcess: Math.round(Math.max(0, ...h.map((p) => p.excess))), strayComponents: st.components - 1,
    strays: st.others.slice(0, 8) }));
}
