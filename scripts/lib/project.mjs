// Project discovery and the export table shared by build, verify and contact-sheet.
import { readdir, access } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

export const ROOT = fileURLToPath(new URL("../../", import.meta.url));
export const SOURCE_FILES = ["icon.svg", "tile.svg", "glyph.svg", "favicon.svg", "mono.svg"];
export const ICO_SIZES = [16, 32, 48];

/** One row per generated file. `src` is a source SVG, `copyOf` duplicates another export byte for byte. */
export const EXPORTS = [
  { file: "png/icon-512.png", src: "icon.svg", size: 512, alpha: "any" },
  { file: "png/icon-192.png", src: "icon.svg", size: 192, alpha: "any" },
  { file: "png/icon-maskable-512.png", src: "tile.svg", size: 512, alpha: "opaque" },
  { file: "favicon/favicon-32.png", src: "favicon.svg", size: 32, alpha: "any" },
  { file: "favicon/favicon-16.png", src: "favicon.svg", size: 16, alpha: "any" },
  { file: "favicon/favicon.ico", src: "favicon.svg", ico: ICO_SIZES },
  { file: "apple/apple-touch-icon.png", src: "tile.svg", size: 180, alpha: "opaque" },
  { file: "pwa/icon-192.png", copyOf: "png/icon-192.png" },
  { file: "pwa/icon-512.png", copyOf: "png/icon-512.png" },
  { file: "pwa/icon-maskable-512.png", copyOf: "png/icon-maskable-512.png" },
  { file: "svg/icon.svg", svg: "icon.svg" },
  { file: "svg/favicon.svg", svg: "favicon.svg" },
];

/** Size budgets in bytes. */
export const BUDGETS = {
  "icon.svg": 4096, "tile.svg": 4096, "glyph.svg": 4096, "favicon.svg": 2048, "mono.svg": 2048,
  "png/icon-512.png": 81920, "png/icon-192.png": 28672, "png/icon-maskable-512.png": 65536,
  "favicon/favicon-32.png": 4096, "favicon/favicon-16.png": 2048, "favicon/favicon.ico": 16384,
  "apple/apple-touch-icon.png": 16384,
};

/** Production paths, or those of a candidate variant kept under branding/concepts/<variant>/ (never shipped). */
export const paths = (id, variant = null) => {
  const dir = join(ROOT, "projects", id, "branding"), base = variant ? join(dir, "concepts", variant) : dir;
  return { id, variant, dir, source: join(base, "source"), exports: join(base, "exports"), previews: join(dir, "previews") };
};

/** CLI: [projectId] [--variant name] [--out dir] */
export function parseArgs(argv) {
  const out = { id: null, variant: null, out: null };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--variant") out.variant = argv[++i] ?? "";
    else if (argv[i] === "--out") out.out = argv[++i] ?? "";
    else if (!argv[i].startsWith("--") && !out.id) out.id = argv[i];
    else throw new Error(`Unknown argument: ${argv[i]}`);
  }
  if (out.variant !== null && !/^[a-z][a-z0-9-]*$/.test(out.variant)) throw new Error(`Invalid variant name: ${out.variant}`);
  if (out.variant && !out.id) throw new Error("--variant needs a project id");
  return out;
}

const exists = p => access(p).then(() => true, () => false);

/** Projects that have a full-icon master. With an explicit id, that project must exist. */
export async function selectProjects(requested, variant = null) {
  if (requested) {
    if (!/^[a-z][a-zA-Z0-9]*$/.test(requested)) throw new Error(`Invalid project id: ${requested}`);
    if (!(await exists(join(paths(requested, variant).source, "icon.svg")))) throw new Error(`${paths(requested, variant).source}/icon.svg not found`);
    return [requested];
  }
  const found = [];
  for (const entry of await readdir(join(ROOT, "projects"), { withFileTypes: true }).catch(() => [])) {
    if (entry.isDirectory() && await exists(join(paths(entry.name).source, "icon.svg"))) found.push(entry.name);
  }
  if (!found.length) throw new Error("No projects with branding/source/icon.svg found");
  return found.sort();
}
