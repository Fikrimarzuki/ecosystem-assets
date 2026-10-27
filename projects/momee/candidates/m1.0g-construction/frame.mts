const cf = await import(process.argv[2] + "/camera-framing.ts");
const bl = await import(process.argv[2] + "/bedroom-layout.ts");
const out = {};
for (const [w,h] of [[390,844],[844,390],[1280,800]]) for (const t of ["overview","bed","child-and-mom"]) {
  const fr = cf.frameCamera({viewport:{width:w,height:h}, world: bl.WORLD, target: bl.CAMERA_TARGETS[t]});
  out[`${w}x${h}:${t}`] = {zoom:+fr.zoom.toFixed(3), cx:Math.round(fr.center.x), cy:Math.round(fr.center.y), visW:Math.round(w/fr.zoom), visH:Math.round(h/fr.zoom)};
}
console.log(JSON.stringify(out));
