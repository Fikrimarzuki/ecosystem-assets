const bl = await import(process.argv[2]);
const a = (r) => `(${r.x}, ${r.y}, ${r.width}, ${r.height})`;
const lines = [
  "# Generated from app-momee/apps/web/src/adventure/bedroom-layout.ts (read-only import).",
  `FLOOR = ${a(bl.FLOOR)}`,
  `CHILD_START = (${bl.CHILD_START.x}, ${bl.CHILD_START.y})`,
  `MOM_SPOT = (${bl.MOM_SPOT.x}, ${bl.MOM_SPOT.y})`,
  `SLEEPER_HEAD = (${bl.SLEEPER_HEAD.x}, ${bl.SLEEPER_HEAD.y})`,
  "INTERACTABLES = [",
  ...bl.INTERACTABLES.map((i) => `    (${JSON.stringify(i.id)}, ${a(i.bounds)}, ${i.approach ? `(${i.approach.x}, ${i.approach.y})` : "None"}),`),
  "]",
  "CAMERA_TARGETS = [",
  ...Object.entries(bl.CAMERA_TARGETS).map(([k, t]) => `    (${JSON.stringify(k)}, ${a(t.mustSee)}),`),
  "]",
];
console.log(lines.join("\n"));
