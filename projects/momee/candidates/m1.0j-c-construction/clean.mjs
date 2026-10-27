const A = "/Users/mfm/code/porto-projects/app-momee/scripts/assets/";
const { readPng, writePng } = await import(A + "png.mjs");
const E = await import(process.argv[2] + "/edges.mjs");
const [, , , inPath, outPath, panelS] = process.argv;
const panel = panelS.split(",").map(Number);
const im = readPng(inPath);
const r = E.cleanup(im, { panel });
writePng(outPath, r.image);
// integrity: count changed pixels by kind
let alphaChanged = 0, rgbChangedOpaque = 0, rgbChangedPartial = 0;
for (let i = 0; i < im.data.length; i += 4) {
  const a0 = im.data[i + 3], a1 = r.image.data[i + 3];
  if (a0 !== a1) { alphaChanged++; continue; }
  if (a0 && [0, 1, 2].some((k) => im.data[i + k] !== r.image.data[i + k])) a0 === 255 ? rgbChangedOpaque++ : rgbChangedPartial++;
}
console.log(JSON.stringify({ in: inPath.split("/").pop(), specks: r.specks, removedPixels: r.removedPixels, recolouredEdgePixels: r.recoloured,
  alphaChanged, rgbChangedOpaque, rgbChangedPartial, after: E.stats(r.image), haloAfter: E.halos(r.image, { panel }).length, specksAfter: E.paperSpecks(r.image, { panel }).length, straysAfter: E.strayReport(r.image).strayComponents }));
