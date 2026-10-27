import type { UniversePlanet } from "@/lib/universe-config";
import { box, part, type DioramaPart } from "./diorama-primitives";

const stone = "#758187", ivory = "#d7d1b8", dark = "#283e48";
// Authored matte deck values separate architecture from terrain without new materials.
const decks: Record<UniversePlanet["theme"], string> = {
  city: "#88b4bb", terrain: "#809967", academy: "#c8b993",
  workshop: "#8198a6", creative: "#97849f", campus: "#8dab9e",
};

function tree(x: number, z: number, height = 0.8, color = "#4f785a"): DioramaPart[] {
  return [part("cylinder", [x, 0.28, z], [0.09, 0.28, 0.09], "#74614b"),
    part("cone", [x, 0.42 + height / 2, z], [0.46, height, 0.46], color)];
}

function building(x: number, z: number, w: number, h: number, d: number, roof: string, finish: { wall?: string; window?: string } = {}): DioramaPart[] {
  return [box([x, 0.17 + h / 2, z], [w, h, d], finish.wall ?? ivory),
    box([x, 0.2 + h, z], [w + 0.07, 0.09, d + 0.07], roof),
    box([x, 0.2 + h * 0.6, z + d / 2 + 0.006], [w * 0.7, h * 0.25, 0.025], finish.window ?? dark)];
}

const bind = (structureId: string, parts: DioramaPart[]) => parts.map(item => ({ ...item, structureId }));

function island(planet: UniversePlanet): DioramaPart[] {
  return [
    part("cylinder", [0, -0.15, 0], [2.65, 0.5, 2.25], planet.surface, [0, 0.14, 0]),
    part("cone", [-0.12, -0.7, -0.03], [2.5, 0.85, 2.05], planet.surface, [Math.PI, 0.14, 0.1]),
    { ...part("cylinder", [0, 0.13, 0], [2.72, 0.1, 2.32], decks[planet.theme], [0, 0.14, 0]), navigationRole: "ground" },
    part("rock", [-0.75, -0.48, 0.4], [0.75, 0.75, 0.5], planet.surface),
    part("rock", [0.6, -0.62, -0.12], [0.7, 0.8, 0.65], stone),
  ];
}

export function worldRecipe(planet: UniversePlanet): DioramaPart[] {
  const parts = island(planet);
  switch (planet.theme) {
    case "city": {
      parts.push({ ...box([0, 0.2, 0.38], [2.05, 0.025, 0.27], "#3b5861"), navigationRole: "path", navigationSpawn: true },
        { ...box([0.25, 0.2, 0], [0.22, 0.025, 1.75], "#3b5861"), navigationRole: "path" });
      const towers = [[-0.68, -0.35, 0.44, 0.9], [-0.12, -0.5, 0.42, 1.65], [0.65, -0.32, 0.46, 0.65], [-0.68, 0.67, 0.4, 0.42], [0.67, 0.65, 0.4, 0.33]];
      for (const [x, z, w, h] of towers) {
        const tower = building(x, z, w, h, 0.4, "#427888", { wall: "#d8d6c4" });
        parts.push(...(x === -0.12 ? bind("city-spire", tower) : tower));
        for (let y = 0.48; y < h; y += 0.27) {
          const windows = [box([x, y, z + 0.21], [w * 0.66, 0.045, 0.012], "#91b9bf")];
          parts.push(...(x === -0.12 ? bind("city-spire", windows) : windows));
        }
      }
      parts.push(...bind("city-spire", [part("cylinder", [-0.12, 2.08, -0.5], [0.035, 0.45, 0.035], ivory), part("sphere", [-0.12, 2.32, -0.5], [0.09, 0.09, 0.09], "#cfb88d")]));
      parts.push(...bind("city-spire", [box([-0.332, 1.05, -0.5], [0.016, 1.18, 0.23], "#365b68")]));
      // A small unfinished frame and data pylons imply ongoing construction.
      for (const x of [-0.16, 0.14]) parts.push(box([x, 0.39, 0.76], [0.04, 0.44, 0.04], "#b79465"));
      parts.push(box([-0.01, 0.62, 0.76], [0.36, 0.04, 0.04], "#b79465"));
      for (const x of [-0.98, 0.98]) parts.push(box([x, 0.31, 0.14], [0.1, 0.24, 0.1], ivory), box([x, 0.45, 0.14], [0.12, 0.035, 0.12], "#cbe9dd"));
      break;
    }
    case "terrain": {
      parts.push(part("rock", [-0.55, 0.28, -0.48], [1.5, 0.65, 1.2], "#607b51"), part("rock", [-0.87, 0.5, -0.63], [0.7, 1.1, 0.7], "#92967b"));
      parts.push({ ...box([0.13, 0.19, 0.48], [0.34, 0.04, 1.04], "#d1bf91", [0, -0.4, 0]), navigationRole: "path" },
        { ...box([0.58, 0.2, 0.18], [0.9, 0.04, 0.29], "#d1bf91"), navigationRole: "path", navigationSpawn: true });
      parts.push(...bind("terrain-castle", building(0.55, -0.4, 0.52, 0.83, 0.52, "#596653", { wall: "#ded5bc" })));
      for (const x of [0.34, 0.76]) for (const z of [-0.6, -0.2]) parts.push(...bind("terrain-castle", [box([x, 1.12, z], [0.13, 0.22, 0.13], ivory)]));
      parts.push(...bind("terrain-castle", [box([0.55, 0.4, -0.125], [0.16, 0.39, 0.02], "#594533"), box([0.55, 1.45, -0.4], [0.025, 0.65, 0.025], ivory), box([0.72, 1.64, -0.4], [0.32, 0.18, 0.025], "#b1785f")]));
      parts.push(...tree(-0.85, 0.18, 0.8), ...tree(-0.65, 0.71, 0.55), ...tree(0.99, 0.25, 0.57));
      // A crossing and a continuous trail make this a place, not an isolated prop.
      parts.push({ ...box([-0.4, 0.2, 0.35], [0.25, 0.025, 1.3], "#507f89", [0, 0.2, 0]), navigationRole: "path" });
      for (let i = 0; i < 5; i++) parts.push(box([-0.62 + i * 0.13, 0.28, 0.53], [0.11, 0.045, 0.38], "#896c4e"));
      parts.push(part("rock", [0.8, 0.3, 0.65], [0.4, 0.25, 0.4], stone));
      break;
    }
    case "academy": {
      parts.push({ ...box([0, 0.2, 0.58], [0.5, 0.05, 0.85], "#e1d2ae"), navigationRole: "path", navigationSpawn: true });
      parts.push(...bind("academy-hall", building(-0.22, -0.25, 1.2, 0.64, 0.7, "#9f6653", { wall: "#e1d5b6", window: "#665b51" })));
      parts.push(...bind("academy-hall", [part("cone", [-0.22, 1, -0.25], [1.5, 0.5, 1.05], "#b98165", [0, Math.PI / 4, 0])]));
      for (const x of [-0.65, -0.22, 0.21]) parts.push(...bind("academy-hall", [part("cylinder", [x, 0.53, 0.19], [0.095, 0.64, 0.095], "#f0e2c4")]));
      parts.push(...bind("academy-tower", [...building(0.7, -0.43, 0.37, 1.24, 0.4, "#945746", { wall: "#d2bd99", window: "#665b51" }), part("cone", [0.7, 1.6, -0.43], [0.6, 0.5, 0.6], "#a96c52")]));
      parts.push(part("cylinder", [-0.67, 0.3, 0.58], [0.4, 0.26, 0.4], "#887857"));
      // Open book monument in the small courtyard.
      parts.push(box([-0.77, 0.49, 0.58], [0.23, 0.045, 0.3], "#f0e2bf", [0, 0, -0.22]), box([-0.55, 0.49, 0.58], [0.23, 0.045, 0.3], "#f0e2bf", [0, 0, 0.22]));
      parts.push(...tree(-1, -0.1, 0.55, "#80936c"), ...tree(0.85, 0.58, 0.52, "#a9a16b"));
      for (let i = 0; i < 3; i++) parts.push(box([0, 0.2 + i * 0.055, 0.35 - i * 0.1], [0.65, 0.08, 0.14], ivory));
      break;
    }
    case "workshop": {
      parts.push({ ...box([0, 0.21, 0.35], [2.1, 0.05, 0.38], dark), navigationRole: "path" });
      parts.push(...bind("workshop-hall", building(-0.4, -0.25, 0.96, 0.64, 0.8, "#4b697c", { wall: "#d6d3be" })));
      parts.push(...bind("workshop-hall", [box([-0.4, 0.43, 0.17], [0.55, 0.42, 0.025], "#273a46"),
        box([-0.4, 0.68, 0.17], [0.55, 0.045, 0.025], "#b19a70"), box([-0.4, 0.9, -0.25], [0.3, 0.06, 0.38], "#344b58")]));
      for (const x of [0.48, 0.92]) parts.push(part("cylinder", [x, 0.61, -0.35], [0.34, 0.84, 0.34], "#b3bfc0"), part("sphere", [x, 1.03, -0.35], [0.35, 0.2, 0.35], "#718b94"));
      parts.push(part("cylinder", [0.7, 0.85, -0.35], [0.09, 0.45, 0.09], "#b69764", [0, 0, Math.PI / 2]));
      // Visible flywheel, teeth, bench, and angular maintenance gantry.
      parts.push(part("ring", [-0.65, 0.52, 0.65], [0.5, 0.5, 0.5], "#9d8a69"));
      for (let i = 0; i < 8; i++) {
        const a = i * Math.PI / 4;
        parts.push(box([-0.65 + Math.cos(a) * 0.26, 0.52 + Math.sin(a) * 0.26, 0.65], [0.1, 0.1, 0.11], "#9d8a69", [0, 0, a]));
      }
      parts.push(box([0.48, 0.34, 0.64], [0.65, 0.26, 0.38], "#718c94"));
      parts.push(box([-0.95, 0.9, -0.65], [0.065, 1.5, 0.065], "#9da9a8"), box([-0.5, 1.62, -0.65], [0.96, 0.07, 0.07], "#9da9a8"), box([-0.08, 1.43, -0.65], [0.025, 0.35, 0.025], dark));
      break;
    }
    case "creative": {
      parts.push(part("rock", [-0.6, 0.33, -0.18], [1.35, 0.62, 1.4], "#776782"));
      parts.push(...bind("creative-observatory", [part("cylinder", [-0.55, 0.62, -0.3], [0.74, 0.7, 0.74], "#d4c9c6"), part("sphere", [-0.55, 1, -0.3], [0.85, 0.58, 0.85], "#777e99")]));
      parts.push(...bind("creative-observatory", [box([-0.43, 1.2, -0.17], [0.13, 0.13, 0.67], "#343b54", [-0.35, -0.4, 0]),
        box([-0.55, 0.7, 0.076], [0.18, 0.28, 0.02], "#49445e")]));
      parts.push(...bind("creative-sculpture", [part("ring", [0.53, 0.9, 0.15], [1.0, 1.15, 1], "#8e709b", [0.12, 0.35, -0.3]), part("rock", [0.53, 0.92, 0.15], [0.4, 0.75, 0.4], "#d3c6ad", [0, 0, -0.22])]));
      parts.push(part("rock", [1.38, 0.25, -0.18], [0.5, 0.65, 0.6], "#85728f"), part("rock", [1.38, 0.78, -0.18], [0.18, 0.4, 0.18], "#aba0b2"));
      for (let i = 0; i < 4; i++) parts.push({ ...box([-0.4 + i * 0.25, 0.2, 0.65 - i * 0.09], [0.17, 0.05, 0.22], "#b7acb9"), navigationRole: "path", navigationSpawn: i === 0 });
      parts.push(part("rock", [-0.72, 0.45, 0.62], [0.17, 0.58, 0.2], "#c4b5db"));
      break;
    }
    case "campus": {
      parts.push({ ...box([0, 0.21, 0], [2.1, 0.045, 0.21], ivory), navigationRole: "path", navigationSpawn: [-2 / 7, 0] },
        { ...box([0, 0.21, 0], [0.2, 0.045, 1.65], ivory), navigationRole: "path" });
      // Stable corner centers/footprints; roof form and height distinguish four projects.
      for (const [x, z, h, roof, form] of [
        [-0.72, -0.47, 0.66, "#426e78", "terrace"],
        [0.72, -0.47, 0.5, "#628980", "peak"],
        [-0.72, 0.52, 0.34, "#687b76", "flat"],
        [0.72, 0.52, 0.58, "#357778", "barrels"],
      ] as const) {
        const structure = building(x, z, 0.53, h, 0.48, roof);
        if (form === "terrace") structure.push(box([x, 0.93, z], [0.38, 0.07, 0.34], "#638f94"), box([x, 1, z], [0.23, 0.07, 0.2], roof));
        if (form === "peak") structure.push(part("cone", [x, 0.88, z], [0.56, 0.3, 0.5], "#7ca295", [0, Math.PI / 4, 0]));
        if (form === "flat") structure.push(box([x, 0.605, z], [0.32, 0.035, 0.29], "#a8bcb0"));
        if (form === "barrels") for (const offset of [-0.135, 0.135]) structure.push(part("cylinder", [x + offset, 0.855, z], [0.24, 0.45, 0.24], "#74a9a1", [Math.PI / 2, 0, 0]));
        parts.push(...bind(`campus-${z < 0 ? "north" : "south"}-${x < 0 ? "west" : "east"}`, structure));
        parts.push(box([x / 2, 0.38, z], [0.42, 0.06, 0.16], "#d5ccb0"));
      }
      parts.push(...bind("campus-center", [part("cylinder", [0, 0.56, -0.1], [0.54, 0.7, 0.54], "#d9dbc9"), part("cone", [0, 1.02, -0.1], [0.71, 0.25, 0.71], "#477e7b")]));
      parts.push(...bind("campus-center", [box([0, 0.75, -0.1], [1.1, 0.09, 0.13], "#759f93")]));
      for (const x of [-1.04, 1.04]) parts.push(...tree(x, 0.05, 0.36, "#799375"));
      for (const z of [-0.83, 0.87]) parts.push(part("cylinder", [0, 0.27, z], [0.24, 0.15, 0.24], "#d4d6b8"));
      break;
    }
  }
  return parts;
}
