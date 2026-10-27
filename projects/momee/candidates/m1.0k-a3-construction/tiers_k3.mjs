// M1.0k-A3: @1x / @2x tiers from a Mom master already on the spec canvas (800×1248, feet anchor (400, 1216)).
// One uniform premultiplied area-average downscale of the whole canvas with momee-character-master.mjs resample()
// (the same kernel as `place`; it refuses enlargement). The anchor maps exactly: ×0.5 → (200, 608), ×0.25 → (100, 304).
// Usage: node tiers_k3.mjs <master.png> <outPrefix>   → <outPrefix>.@2x.png, <outPrefix>.@1x.png
const T = await import('/Users/mfm/code/porto-projects/ecosystem-assets/scripts/momee-character-master.mjs');
const [, , src, prefix] = process.argv;
const m = T.readPng(src), S = T.SPEC.mom;
if (m.width !== S.canvasU[0] * 4 || m.height !== S.canvasU[1] * 4) throw new Error('not a 4 px/u Mom master canvas');
for (const ppu of [2, 1]) {
  const s = ppu / 4, out = T.resample(m, S.canvasU[0] * ppu, S.canvasU[1] * ppu, [S.anchorU[0] * 4, S.anchorU[1] * 4], [S.anchorU[0] * ppu, S.anchorU[1] * ppu], s);
  T.writePng(`${prefix}.@${ppu}x.png`, out);
  console.log(`@${ppu}x ${out.width}×${out.height} scale ${s} figureBox ${JSON.stringify(T.figureBox(out))}`);
}
